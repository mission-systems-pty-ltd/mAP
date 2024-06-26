import glob
import json
import os
import shutil
import operator
import sys
import argparse
import math
import cv2
import matplotlib.pyplot as plt
import numpy as np
from logzero import logger
from datetime import datetime as dt

from icecream import ic
name = 'evaluate_mAP_scaores'
def log( entry: str) -> None:
    print("[ {} | {}] ".format(dt.now().strftime("%Y-%m-%d %H:%M:%S.%f"), name) + entry)
    return None

def intersect_gt_and_pred(DR_PATH, GT_PATH):
    # make sure that the cwd() in the beginning is the location of the python script (so that every path makes sense)
    #os.chdir(os.path.dirname(os.path.abspath(__file__)))
    backup_folder = 'backup_no_matches_found' # must end without slash

    os.chdir(GT_PATH)
    gt_files = glob.glob('*.txt')
    if len(gt_files) == 0:
        print("Error: no .txt files found in", GT_PATH)
        sys.exit()
    os.chdir(DR_PATH)
    dr_files = glob.glob('*.txt')
    if len(dr_files) == 0:
        print("Error: no .txt files found in", DR_PATH)
        sys.exit()

    gt_files = set(gt_files)
    dr_files = set(dr_files)
    log('total ground-truth files: {}'.format(len(gt_files)))
    log('total detection-results files: {}'.format(len(dr_files)))

    gt_backup = gt_files - dr_files
    dr_backup = dr_files - gt_files

    backup(GT_PATH, gt_backup, backup_folder)
    backup(DR_PATH, dr_backup, backup_folder)
    if gt_backup:
        log('total ground-truth backup files: {}'.format(len(gt_backup)))
    if dr_backup:
        log('total detection-results backup files: {}'.format(len(dr_backup)))

    intersection = gt_files & dr_files
    log('total intersected files: {}'.format(len(intersection)))
    log("Intersection completed!")

def backup(src_folder, backup_files, backup_folder):
    # non-intersection files (txt format) will be moved to a backup folder
    if not backup_files:
        log('No backup required for {}'.format(src_folder))
        return
    os.chdir(src_folder)
    ## create the backup dir if it doesn't exist already
    if not os.path.exists(backup_folder):
        os.makedirs(backup_folder)
    for file in backup_files:
        os.rename(file, backup_folder + '/' + file)

def main(arguments):
    logger.info("mAP CLI Tool")
    args = parse_args(argv=arguments)
    mAP_score = calculate_mAP_scores(ground_truth_dir=args.ground_truth_dir,
                                     prediction_dir=args.prediction_dir,
                                     img_dir=args.image_dir,
                                     out_dir=args.output_dir,
                                     animate=args.animate,
                                     draw_plot=args.plot,
                                     quiet=args.quiet,
                                     ignore=args.ignore,
                                     set_class_iou=args.set_class_iou)
    print("This is the overall mAP score: " + str(mAP_score))
    clean_exit(exit_code=0)


def parse_args(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("-pd", "--prediction_dir", help="path to predicted annotations", required=True)
    parser.add_argument("-gt", "--ground_truth_dir", help="path to ground truth annotations", required=True)
    parser.add_argument("-id", "--image_dir", help="path to images", default=None)
    parser.add_argument("-od", "--output_dir", help="path to output files", default=None)
    parser.add_argument('-a', '--animate', help="show animation", action="store_true", default=False)
    parser.add_argument('-p', '--plot', help="display plot", action="store_true", default=False)
    parser.add_argument('-q', '--quiet', help="minimalistic console output.", action="store_true", default=False)
    # argparse receiving list of classes to be ignored (e.g., python main.py --ignore person book)
    parser.add_argument('-i', '--ignore', nargs='+', type=str, help="ignore a list of classes.", default=[])
    # argparse receiving list of classes with specific IoU (e.g., python main.py --set_class_iou person 0.7)
    parser.add_argument('--set_class_iou', nargs='+', type=str, help="set IoU for a specific class.", default=[])
    arguments = parser.parse_args(argv[1:])
    return arguments


def check_image_files_exist(image_dir: str) -> bool:
    if image_dir is None:
        logger.warning("Animation option selected - but no image directory provided. Please provide a path to a"
                       " directory of images (see option -id)")
        return False
    else:
        if os.path.exists(image_dir) is False:
            logger.warning("No image directory {} - animations deactivated!".format(image_dir))
            return False
        else:
            for (root,dirs,files) in os.walk(image_dir, topdown=True):
                if not files:
                    logger.warning("No images in directory {} - animations deactivated!".format(image_dir))
                    return False
            return True

def clean_up(clean_up_dirs: list = ['.temp_files']):
    for cud in clean_up_dirs:
        if os.path.exists(cud):  # reset the output directory
            shutil.rmtree(cud)


def clean_exit(exit_code: int, msg: str = " ", clean_up_dirs: list = ['.temp_files']):
    clean_up(clean_up_dirs=clean_up_dirs)
    if exit_code == 0:
        logger.info('DONE! mAP Score Calculated. {}'.format(msg))
    else:
        logger.error('FAIL! {}'.format(msg))
    exit(exit_code)


def calculate_mAP_scores(ground_truth_dir: str,
                         prediction_dir: str,
                         img_dir: str = None,
                         out_dir: str = None,
                         animate: bool = False,
                         draw_plot: bool = False,
                         quiet: bool = False,
                         ignore: list = [],
                         set_class_iou: list = []):
    '''
        0,0 ------> x (width)
         |
         |  (Left,Top)
         |      *_________
         |      |         |
                |         |
         y      |_________|
      (height)            *
                    (Right,Bottom)
    '''
    logger.info("Calculating mAP Score")
    MINOVERLAP = 0.5  # default value (defined in the PASCAL VOC2012 challenge)
    ignore = ['tgt_box_11', 'tgt_box_3','tgt_craypot', 'tmp']
    log('Ignoring the following classes: {}'.format(ignore))
    #exit(1)
    if set_class_iou is not None:
        specific_iou_flagged = True if len(set_class_iou) > 0 else False
    else:
        specific_iou_flagged = False

    GT_PATH = ground_truth_dir  # os.path.join(os.getcwd(), 'input', 'ground-truth')
    DR_PATH = prediction_dir  # os.path.join(os.getcwd(), 'input', 'detection-results')
    # if there are no images then no animation can be shown
    IMG_PATH = img_dir  # os.path.join(os.getcwd(), 'input', 'images-optional')

    if animate:
        animate = check_image_files_exist(image_dir=IMG_PATH)

    """
     Create a ".temp_files/" and "output/" directory
    """
    TEMP_FILES_PATH = os.path.expanduser("~")+"/tmp"+"/out/"
    directories_to_clean = [TEMP_FILES_PATH]

    if not os.path.exists(TEMP_FILES_PATH):  # if it doesn't exist already
        os.makedirs(TEMP_FILES_PATH)

    if out_dir is None:
        output_files_path = os.path.join(os.path.expanduser("~"), 'out', 'mAP', 'calculate_mAP' + format(str(dt.strftime(dt.now(), '%Y_%m_%d_%Hh_%Mm_%Ss'))))
        directories_to_clean.append(output_files_path)
    else:
        output_files_path = out_dir
    if output_files_path is not None:
        if os.path.exists(output_files_path) is False:
            os.makedirs(output_files_path)
        else:
            logger.warning("Warning! Output path already exists - writing into the same directory!")
        if draw_plot:
            os.makedirs(os.path.join(output_files_path, "classes"))
        if animate:
            os.makedirs(os.path.join(output_files_path, "images", "detections_one_by_one"))

    """
     ground-truth
         Load each of the ground-truth files into a temporary ".json" file.
         Create a list of all the class names present in the ground-truth (gt_classes).
    """
    intersect_gt_and_pred(DR_PATH, GT_PATH)
    ground_truth_files_list = [os.path.join(GT_PATH, f) for f in os.listdir(GT_PATH) if f.endswith('.txt')]
    if len(ground_truth_files_list) == 0:
        clean_exit(exit_code=1, msg="Error: No ground-truth files found!", clean_up_dirs=directories_to_clean)
    ground_truth_files_list.sort()
    # dictionary with counter per class
    gt_counter_per_class = {}
    counter_images_per_class = {}

    gt_files = []
    for txt_file in ground_truth_files_list:
        file_id = txt_file.split(".txt", 1)[0]
        file_id = os.path.basename(os.path.normpath(file_id))
        # check if there is a correspondent detection-results file
        temp_path = os.path.join(DR_PATH, (file_id + ".txt"))
        if not os.path.exists(temp_path):
            error_msg = "Error. File not found: {}\n".format(temp_path)
            error_msg += "(You can avoid this error message by running extra/intersect-gt-and-dr.py)"
            clean_exit(exit_code=1, msg=error_msg, clean_up_dirs=directories_to_clean)
        lines_list = file_lines_to_list(txt_file)
        # create ground-truth dictionary
        bounding_boxes = []
        is_difficult = False
        already_seen_classes = []
        for line in lines_list:
            class_name = None
            try:
                if "difficult" in line:
                    class_name, left, top, right, bottom, _difficult = line.split()
                    is_difficult = True
                else:
                    class_name, left, top, right, bottom = line.split()
            except ValueError:
                error_msg = "Error: File " + txt_file + " in the wrong format.\n"
                error_msg += " Expected: <class_name> <left> <top> <right> <bottom> ['difficult']\n"
                error_msg += " Received: " + line
                error_msg += "\n\nIf you have a <class_name> with spaces between words you should remove them\n"
                error_msg += "by running the script \"remove_space.py\" or \"rename_class.py\" in the \"extra/\" folder."
                clean_exit(exit_code=1, msg=error_msg, clean_up_dirs=directories_to_clean)
            # check if class is in the ignore list, if yes skip
            if class_name in ignore:
                continue
            class_name = 'MLO'
            bbox = left + " " + top + " " + right + " " + bottom
            if is_difficult:
                bounding_boxes.append({"class_name": class_name, "bbox": bbox, "used": False, "difficult": True})
                is_difficult = False
            else:
                bounding_boxes.append({"class_name": class_name, "bbox": bbox, "used": False})
                # count that object
                if class_name in gt_counter_per_class:
                    gt_counter_per_class[class_name] += 1
                else:
                    # if class didn't exist yet
                    gt_counter_per_class[class_name] = 1

                if class_name not in already_seen_classes:
                    if class_name in counter_images_per_class:
                        counter_images_per_class[class_name] += 1
                    else:
                        # if class didn't exist yet
                        counter_images_per_class[class_name] = 1
                    already_seen_classes.append(class_name)

        # dump bounding_boxes into a ".json" file
        new_temp_file = TEMP_FILES_PATH + "/" + file_id + "_ground_truth.json"
        if not os.path.exists(TEMP_FILES_PATH):
            os.makedirs(TEMP_FILES_PATH)
        gt_files.append(new_temp_file)
        with open(new_temp_file, 'w') as outfile:
            json.dump(bounding_boxes, outfile, ensure_ascii=False, indent=4)
    gt_classes = list(gt_counter_per_class.keys())
    # let's sort the classes alphabetically
    gt_classes = ['MLO']
    n_classes = len(gt_classes)

    """
     Check format of the flag --set_class_iou (if used)
        e.g. check if class exists
    """
    if specific_iou_flagged:
        n_args = len(set_class_iou)
        error_msg = \
            '\n --set_class_iou [class_1] [IoU_1] [class_2] [IoU_2] [...]'
        if n_args % 2 != 0:
            error_msg = 'Error, missing arguments. Flag usage:' + error_msg
            clean_exit(exit_code=1, msg=error_msg, clean_up_dirs=directories_to_clean)
        # [class_1] [IoU_1] [class_2] [IoU_2]
        # specific_iou_classes = ['class_1', 'class_2']
        specific_iou_classes = set_class_iou[::2]  # even
        # iou_list = ['IoU_1', 'IoU_2']
        iou_list = set_class_iou[1::2]  # odd
        if len(specific_iou_classes) != len(iou_list):
            error_msg = 'Error, missing arguments. Flag usage:' + error_msg
            clean_exit(exit_code=1, msg=error_msg, clean_up_dirs=directories_to_clean)
        for tmp_class in specific_iou_classes:
            if tmp_class not in gt_classes:
                error_msg = 'Error, unknown class \"' + tmp_class + '\". Flag usage:' + error_msg
                clean_exit(exit_code=1, msg=error_msg, clean_up_dirs=directories_to_clean)
        for num in iou_list:
            if not is_float_between_0_and_1(num):
                error_msg = 'Error, IoU must be between 0.0 and 1.0. Flag usage:' + error_msg
                clean_exit(exit_code=1, msg=error_msg, clean_up_dirs=directories_to_clean)

    """
     detection-results
         Load each of the detection-results files into a temporary ".json" file.
    """
    # get a list with the detection-results files
    dr_files_list = glob.glob(DR_PATH + '/*.txt')
    dr_files_list.sort()

    for class_index, class_name in enumerate(gt_classes):
        bounding_boxes = []
        for txt_file in dr_files_list:
            # print(txt_file)
            # the first time it checks if all the corresponding ground-truth files exist
            file_id = txt_file.split(".txt", 1)[0]
            file_id = os.path.basename(os.path.normpath(file_id))
            temp_path = os.path.join(GT_PATH, (file_id + ".txt"))
            if class_index == 0:
                if not os.path.exists(temp_path):
                    error_msg = "Error. File not found: {}\n".format(temp_path)
                    error_msg += "(You can avoid this error message by running extra/intersect-gt-and-dr.py)"
                    clean_exit(exit_code=1, msg=error_msg, clean_up_dirs=directories_to_clean)
            lines = file_lines_to_list(txt_file)
            for line in lines:
                try:
                    tmp_class_name, confidence, left, top, right, bottom = line.split()
                    tmp_class_name = 'MLO'
                except ValueError:
                    error_msg = "Error: File " + txt_file + " in the wrong format.\n"
                    error_msg += " Expected: <class_name> <confidence> <left> <top> <right> <bottom>\n"
                    error_msg += " Received: " + line
                    clean_exit(exit_code=1, msg=error_msg, clean_up_dirs=directories_to_clean)
                if tmp_class_name == class_name:
                    # print("match")
                    bbox = left + " " + top + " " + right + " " + bottom
                    bounding_boxes.append({"confidence": confidence, "file_id": file_id, "bbox": bbox})
                    # print(bounding_boxes)
        # sort detection-results by decreasing confidence
        bounding_boxes.sort(key=lambda x: float(x['confidence']), reverse=True)
        with open(TEMP_FILES_PATH + "/" + class_name + "_dr.json", 'w') as outfile:
            json.dump(bounding_boxes, outfile)

    """
     Calculate the AP for each class
    """
    sum_AP = 0.0
    ap_dictionary = {}
    lamr_dictionary = {}
    with open(os.path.join(output_files_path, "output.txt"), 'w') as output_file:
        output_file.write("# AP and precision/recall per class\n")
        count_true_positives = {}
        for class_index, class_name in enumerate(gt_classes):
            count_true_positives[class_name] = 0
            """
             Load detection-results of that class
            """
            dr_file = TEMP_FILES_PATH + "/" + class_name + "_dr.json"
            dr_data = json.load(open(dr_file))

            """
             Assign detection-results to ground-truth objects
            """
            nd = len(dr_data)
            tp = [0] * nd  # creates an array of zeros of size nd
            fp = [0] * nd
            for idx, detection in enumerate(dr_data):
                file_id = detection["file_id"]
                if animate:
                    # find ground truth image
                    ground_truth_img = glob.glob1(IMG_PATH, file_id + ".*")
                    # tifCounter = len(glob.glob1(myPath,"*.tif"))
                    if len(ground_truth_img) == 0:
                        error_msg ="Error. Image not found with id: " + file_id
                        clean_exit(exit_code=1, msg=error_msg, clean_up_dirs=directories_to_clean)
                    elif len(ground_truth_img) > 1:
                        error_msg = "Error. Multiple image with id: " + file_id
                        clean_exit(exit_code=1, msg=error_msg, clean_up_dirs=directories_to_clean)
                    else:  # found image
                        # Load image
                        img = cv2.imread(IMG_PATH + "/" + ground_truth_img[0])
                        # load image with draws of multiple detections
                        img_cumulative_path = output_files_path + "/images/" + ground_truth_img[0]
                        if os.path.isfile(img_cumulative_path):
                            img_cumulative = cv2.imread(img_cumulative_path)
                        else:
                            img_cumulative = img.copy()
                        # Add bottom border to image
                        bottom_border = 60
                        BLACK = [0, 0, 0]
                        img = cv2.copyMakeBorder(img, 0, bottom_border, 0, 0, cv2.BORDER_CONSTANT, value=BLACK)
                # assign detection-results to ground truth object if any
                # open ground-truth with that file_id
                gt_file = TEMP_FILES_PATH + "/" + file_id + "_ground_truth.json"
                ground_truth_data = json.load(open(gt_file))
                ovmax = -1
                gt_match = -1
                # load detected object bounding-box
                bb = [float(x) for x in detection["bbox"].split()]
                for obj in ground_truth_data:
                    obj['class_name'] = 'MLO'

                    # look for a class_name match
                    if obj["class_name"] == class_name:
                        bbgt = [float(x) for x in obj["bbox"].split()]
                        bi = [max(bb[0], bbgt[0]), max(bb[1], bbgt[1]), min(bb[2], bbgt[2]), min(bb[3], bbgt[3])]
                        iw = bi[2] - bi[0] + 1
                        ih = bi[3] - bi[1] + 1
                        if iw > 0 and ih > 0:
                            # compute overlap (IoU) = area of intersection / area of union
                            ua = (bb[2] - bb[0] + 1) * (bb[3] - bb[1] + 1) + (bbgt[2] - bbgt[0]
                                                                              + 1) * (bbgt[3] - bbgt[1] + 1) - iw * ih
                            ov = iw * ih / ua
                            ic(ovmax)
                            if ov > ovmax:
                                ovmax = ov
                                gt_match = obj

                # assign detection as true positive/don't care/false positive
                if animate:
                    status = "NO MATCH FOUND!"  # status is only used in the animation
                # set minimum overlap
                ic(ovmax)
                min_overlap = MINOVERLAP
                if specific_iou_flagged:
                    if class_name in specific_iou_classes:
                        index = specific_iou_classes.index(class_name)
                        min_overlap = float(iou_list[index])
                if ovmax >= min_overlap:
                    if "difficult" not in gt_match:
                        if not bool(gt_match["used"]):
                            # true positive
                            tp[idx] = 1
                            gt_match["used"] = True
                            count_true_positives[class_name] += 1
                            # update the ".json" file
                            with open(gt_file, 'w') as f:
                                f.write(json.dumps(ground_truth_data))
                            if animate:
                                status = "MATCH!"
                        else:
                            # false positive (multiple detection)
                            fp[idx] = 1
                            if animate:
                                status = "REPEATED MATCH!"
                else:
                    # false positive
                    fp[idx] = 1
                    if ovmax > 0:
                        status = "INSUFFICIENT OVERLAP"

                """
                 Draw image to show animation
                """
                if animate:
                    height, width = img.shape[:2]
                    # colors (OpenCV works with BGR)
                    white = (255, 255, 255)
                    light_blue = (255, 200, 100)
                    green = (0, 255, 0)
                    light_red = (30, 30, 255)
                    # 1st line
                    margin = 10
                    v_pos = int(height - margin - (bottom_border / 2.0))
                    text = "Image: " + ground_truth_img[0] + " "
                    img, line_width = draw_text_in_image(img, text, (margin, v_pos), white, 0)
                    text = "Class [" + str(class_index) + "/" + str(n_classes) + "]: " + class_name + " "
                    img, line_width = draw_text_in_image(img, text, (margin + line_width, v_pos), light_blue,
                                                         line_width)
                    if ovmax != -1:
                        color = light_red
                        if status == "INSUFFICIENT OVERLAP":
                            text = "IoU: {0:.2f}% ".format(ovmax * 100) + "< {0:.2f}% ".format(min_overlap * 100)
                        else:
                            text = "IoU: {0:.2f}% ".format(ovmax * 100) + ">= {0:.2f}% ".format(min_overlap * 100)
                            color = green
                        img, _ = draw_text_in_image(img, text, (margin + line_width, v_pos), color, line_width)
                    # 2nd line
                    v_pos += int(bottom_border / 2.0)
                    rank_pos = str(idx + 1)  # rank position (idx starts at 0)
                    text = "Detection #rank: " + rank_pos + " confidence: {0:.2f}% ".format(
                        float(detection["confidence"]) * 100)
                    img, line_width = draw_text_in_image(img, text, (margin, v_pos), white, 0)
                    color = light_red
                    if status == "MATCH!":
                        color = green
                    text = "Result: " + status + " "
                    img, line_width = draw_text_in_image(img, text, (margin + line_width, v_pos), color, line_width)

                    font = cv2.FONT_HERSHEY_SIMPLEX
                    if ovmax > 0:  # if there is intersections between the bounding-boxes
                        bbgt = [int(round(float(x))) for x in gt_match["bbox"].split()]
                        cv2.rectangle(img, (bbgt[0], bbgt[1]), (bbgt[2], bbgt[3]), light_blue, 2)
                        cv2.rectangle(img_cumulative, (bbgt[0], bbgt[1]), (bbgt[2], bbgt[3]), light_blue, 2)
                        cv2.putText(img_cumulative, class_name, (bbgt[0], bbgt[1] - 5), font, 0.6, light_blue, 1,
                                    cv2.LINE_AA)
                    bb = [int(i) for i in bb]
                    cv2.rectangle(img, (bb[0], bb[1]), (bb[2], bb[3]), color, 2)
                    cv2.rectangle(img_cumulative, (bb[0], bb[1]), (bb[2], bb[3]), color, 2)
                    cv2.putText(img_cumulative, class_name, (bb[0], bb[1] - 5), font, 0.6, color, 1, cv2.LINE_AA)
                    # show image
                    cv2.imshow("Animation", img)
                    cv2.waitKey(20)  # show for 20 ms
                    # save image to output
                    output_img_path = output_files_path + "/images/detections_one_by_one/" + class_name + "_detection" + str(
                        idx) + ".jpg"
                    cv2.imwrite(output_img_path, img)
                    # save the image with all the objects drawn to it
                    cv2.imwrite(img_cumulative_path, img_cumulative)

            # print(tp)
            # compute precision/recall
            cumsum = 0
            for idx, val in enumerate(fp):
                fp[idx] += cumsum
                cumsum += val
            cumsum = 0
            for idx, val in enumerate(tp):
                tp[idx] += cumsum
                cumsum += val
            # print(tp)
            rec = tp[:]
            for idx, val in enumerate(tp):
                rec[idx] = float(tp[idx]) / gt_counter_per_class[class_name]
            # print(rec)
            prec = tp[:]
            for idx, val in enumerate(tp):
                prec[idx] = float(tp[idx]) / (fp[idx] + tp[idx])
            # print(prec)

            ap, mrec, mprec = voc_ap(rec[:], prec[:])
            sum_AP += ap
            text = "{0:.2f}%".format(
                ap * 100) + " = " + class_name + " AP "  # class_name + " AP = {0:.2f}%".format(ap*100)
            """
             Write to output.txt
            """
            rounded_prec = ['%.2f' % elem for elem in prec]
            rounded_rec = ['%.2f' % elem for elem in rec]
            output_file.write(text + "\n Precision: " + str(rounded_prec) + "\n Recall :" + str(rounded_rec) + "\n\n")
            if quiet is False:
                print(text)
            ap_dictionary[class_name] = ap

            n_images = counter_images_per_class[class_name]
            lamr, mr, fppi = log_average_miss_rate(np.array(prec), np.array(rec), n_images)
            lamr_dictionary[class_name] = lamr

            """
             Draw plot
            """
            if draw_plot:
                plt.plot(rec, prec, '-o')
                # add a new penultimate point to the list (mrec[-2], 0.0)
                # since the last line segment (and respective area) do not affect the AP value
                area_under_curve_x = mrec[:-1] + [mrec[-2]] + [mrec[-1]]
                area_under_curve_y = mprec[:-1] + [0.0] + [mprec[-1]]
                plt.fill_between(area_under_curve_x, 0, area_under_curve_y, alpha=0.2, edgecolor='r')
                # set window title
                fig = plt.gcf()  # gcf - get current figure
                #fig.canvas.set_window_title('AP ' + class_name)
                # set plot title
                plt.title('class: ' + text)
                # plt.suptitle('This is a somewhat long figure title', fontsize=16)
                # set axis titles
                plt.xlabel('Recall')
                plt.ylabel('Precision')
                # optional - set axes
                axes = plt.gca()  # gca - get current axes
                axes.set_xlim([0.0, 1.0])
                axes.set_ylim([0.0, 1.05])  # .05 to give some extra space
                # Alternative option -> wait for button to be pressed
                # while not plt.waitforbuttonpress(): pass # wait for key display
                # Alternative option -> normal display
                # plt.show()
                # save the plot
                fig.savefig(output_files_path + "/classes/" + class_name + ".png")
                plt.cla()  # clear axes for next plot

        if animate:
            cv2.destroyAllWindows()

        output_file.write("\n# mAP of all classes\n")
        mAP = sum_AP / n_classes
        text = "mAP = {0:.2f}%".format(mAP * 100)
        output_file.write(text + "\n")
        print(text)

    """
     Draw false negatives
    """
    """
    if animate:
        pink = (203, 192, 255)
        for tmp_file in gt_files:
            ground_truth_data = json.load(open(tmp_file))
            # print(ground_truth_data)
            # get name of corresponding image
            start = TEMP_FILES_PATH + '/'
            img_id = tmp_file[tmp_file.find(start) + len(start):tmp_file.rfind('_ground_truth.json')]
            img_cumulative_path = output_files_path + "/images/" + img_id + ".jpg"
            img = cv2.imread(img_cumulative_path)
            if img is None:
                img_path = IMG_PATH + '/' + img_id + ".jpg"
                img = cv2.imread(img_path)
            # draw false negatives
            for obj in ground_truth_data:
                if not obj['used']:
                    bbgt = [int(round(float(x))) for x in obj["bbox"].split()]
                    cv2.rectangle(img, (bbgt[0], bbgt[1]), (bbgt[2], bbgt[3]), pink, 2)
            cv2.imwrite(img_cumulative_path, img)
    """
    # remove the temp_files directory
    shutil.rmtree(TEMP_FILES_PATH)

    """
     Count total of detection-results
    """
    # iterate through all the files
    det_counter_per_class = {}
    for txt_file in dr_files_list:
        # get lines to list
        lines_list = file_lines_to_list(txt_file)
        for line in lines_list:
            class_name = line.split()[0]
            # check if class is in the ignore list, if yes skip
            if class_name in ignore:
                continue
            class_name = 'MLO'
            # count that object
            if class_name in det_counter_per_class:
                det_counter_per_class[class_name] += 1
            else:
                # if class didn't exist yet
                det_counter_per_class[class_name] = 1
    # print(det_counter_per_class)
    dr_classes = list(det_counter_per_class.keys())

    """
     Plot the total number of occurences of each class in the ground-truth
    """
    if draw_plot:
        window_title = "ground-truth-info"
        plot_title = "ground-truth\n"
        plot_title += "(" + str(len(ground_truth_files_list)) + " files and " + str(n_classes) + " classes)"
        x_label = "Number of objects per class"
        output_path = output_files_path + "/ground-truth-info.png"
        to_show = False
        plot_color = 'forestgreen'
        draw_plot_func(
            gt_counter_per_class,
            n_classes,
            window_title,
            plot_title,
            x_label,
            output_path,
            to_show,
            plot_color,
            '',
        )

    """
     Write number of ground-truth objects per class to results.txt
    """
    with open(output_files_path + "/output.txt", 'a') as output_file:
        output_file.write("\n# Number of ground-truth objects per class\n")
        for class_name in sorted(gt_counter_per_class):
            output_file.write(class_name + ": " + str(gt_counter_per_class[class_name]) + "\n")

    """
     Finish counting true positives
    """
    for class_name in dr_classes:
        # if class exists in detection-result but not in ground-truth then there are no true positives in that class
        if class_name not in gt_classes:
            count_true_positives[class_name] = 0
    # print(count_true_positives)

    """
     Plot the total number of occurences of each class in the "detection-results" folder
    """
    if draw_plot:
        window_title = "detection-results-info"
        # Plot title
        plot_title = "detection-results\n"
        plot_title += "(" + str(len(dr_files_list)) + " files and "
        count_non_zero_values_in_dictionary = sum(int(x) > 0 for x in list(det_counter_per_class.values()))
        plot_title += str(count_non_zero_values_in_dictionary) + " detected classes)"
        # end Plot title
        x_label = "Number of objects per class"
        output_path = output_files_path + "/detection-results-info.png"
        to_show = False
        plot_color = 'forestgreen'
        true_p_bar = count_true_positives
        ic(len(det_counter_per_class))
        draw_plot_func(
            det_counter_per_class,
            len(det_counter_per_class),
            window_title,
            plot_title,
            x_label,
            output_path,
            to_show,
            plot_color,
            true_p_bar
        )

    """
     Write number of detected objects per class to output.txt
    """
    with open(output_files_path + "/output.txt", 'a') as output_file:
        output_file.write("\n# Number of detected objects per class\n")
        for class_name in sorted(dr_classes):
            n_det = det_counter_per_class[class_name]
            text = class_name + ": " + str(n_det)
            text += " (tp:" + str(count_true_positives[class_name]) + ""
            text += ", fp:" + str(n_det - count_true_positives[class_name]) + ")\n"
            output_file.write(text)

    """
     Draw log-average miss rate plot (Show lamr of all classes in decreasing order)
    """
    if draw_plot:
        window_title = "lamr"
        plot_title = "log-average miss rate"
        x_label = "log-average miss rate"
        output_path = output_files_path + "/lamr.png"
        to_show = False
        plot_color = 'royalblue'
        draw_plot_func(
            lamr_dictionary,
            n_classes,
            window_title,
            plot_title,
            x_label,
            output_path,
            to_show,
            plot_color,
            ""
        )

    """
     Draw mAP plot (Show AP's of all classes in decreasing order)
    """
    if draw_plot:
        window_title = "mAP"
        plot_title = "mAP = {0:.2f}%".format(mAP * 100)
        x_label = "Average Precision"
        output_path = output_files_path + "/mAP.png"
        to_show = True
        plot_color = 'royalblue'
        draw_plot_func(
            ap_dictionary,
            n_classes,
            window_title,
            plot_title,
            x_label,
            output_path,
            to_show,
            plot_color,
            ""
        )
    clean_up(clean_up_dirs=directories_to_clean)
    return mAP


def log_average_miss_rate(prec, rec, num_images):
    """
        log-average miss rate:
            Calculated by averaging miss rates at 9 evenly spaced FPPI points
            between 10e-2 and 10e0, in log-space.

        output:
                lamr | log-average miss rate
                mr | miss rate
                fppi | false positives per image

        references:
            [1] Dollar, Piotr, et al. "Pedestrian Detection: An Evaluation of the
               State of the Art." Pattern Analysis and Machine Intelligence, IEEE
               Transactions on 34.4 (2012): 743 - 761.
    """

    # if there were no detections of that class
    if prec.size == 0:
        lamr = 0
        mr = 1
        fppi = 0
        return lamr, mr, fppi

    fppi = (1 - prec)
    mr = (1 - rec)

    fppi_tmp = np.insert(fppi, 0, -1.0)
    mr_tmp = np.insert(mr, 0, 1.0)

    # Use 9 evenly spaced reference points in log-space
    ref = np.logspace(-2.0, 0.0, num = 9)
    for i, ref_i in enumerate(ref):
        # np.where() will always find at least 1 index, since min(ref) = 0.01 and min(fppi_tmp) = -1.0
        j = np.where(fppi_tmp <= ref_i)[-1][-1]
        ref[i] = mr_tmp[j]

    # log(0) is undefined, so we use the np.maximum(1e-10, ref)
    lamr = math.exp(np.mean(np.log(np.maximum(1e-10, ref))))

    return lamr, mr, fppi


def is_float_between_0_and_1(value):
    """
     check if the number is a float between 0.0 and 1.0
    """
    try:
        val = float(value)
        if val > 0.0 and val < 1.0:
            return True
        else:
            return False
    except ValueError:
        return False


def voc_ap(rec, prec):
    """
     Calculate the AP given the recall and precision array
        1st) We compute a version of the measured precision/recall curve with
             precision monotonically decreasing
        2nd) We compute the AP as the area under this curve by numerical integration.
    """
    """
    --- Official matlab code VOC2012---
    mrec=[0 ; rec ; 1];
    mpre=[0 ; prec ; 0];
    for i=numel(mpre)-1:-1:1
            mpre(i)=max(mpre(i),mpre(i+1));
    end
    i=find(mrec(2:end)~=mrec(1:end-1))+1;
    ap=sum((mrec(i)-mrec(i-1)).*mpre(i));
    """
    rec.insert(0, 0.0) # insert 0.0 at begining of list
    rec.append(1.0) # insert 1.0 at end of list
    mrec = rec[:]
    prec.insert(0, 0.0) # insert 0.0 at begining of list
    prec.append(0.0) # insert 0.0 at end of list
    mpre = prec[:]
    """
     This part makes the precision monotonically decreasing
        (goes from the end to the beginning)
        matlab: for i=numel(mpre)-1:-1:1
                    mpre(i)=max(mpre(i),mpre(i+1));
    """
    # matlab indexes start in 1 but python in 0, so I have to do:
    #     range(start=(len(mpre) - 2), end=0, step=-1)
    # also the python function range excludes the end, resulting in:
    #     range(start=(len(mpre) - 2), end=-1, step=-1)
    for i in range(len(mpre)-2, -1, -1):
        mpre[i] = max(mpre[i], mpre[i+1])
    """
     This part creates a list of indexes where the recall changes
        matlab: i=find(mrec(2:end)~=mrec(1:end-1))+1;
    """
    i_list = []
    for i in range(1, len(mrec)):
        if mrec[i] != mrec[i-1]:
            i_list.append(i) # if it was matlab would be i + 1
    """
     The Average Precision (AP) is the area under the curve
        (numerical integration)
        matlab: ap=sum((mrec(i)-mrec(i-1)).*mpre(i));
    """
    ap = 0.0
    for i in i_list:
        ap += ((mrec[i]-mrec[i-1])*mpre[i])
    return ap, mrec, mpre


def file_lines_to_list(path):
    """
     Convert the lines of a file to a list
    """
    # open txt file lines to a list
    with open(path) as f:
        content = f.readlines()
    # remove whitespace characters like `\n` at the end of each line
    content = [x.strip() for x in content]
    return content


def draw_text_in_image(img, text, pos, color, line_width):
    """
     Draws text in image
    """
    font = cv2.FONT_HERSHEY_PLAIN
    fontScale = 1
    lineType = 1
    bottomLeftCornerOfText = pos
    cv2.putText(img, text,
            bottomLeftCornerOfText,
            font,
            fontScale,
            color,
            lineType)
    text_width, _ = cv2.getTextSize(text, font, fontScale, lineType)[0]
    return img, (line_width + text_width)


def adjust_axes(r, t, fig, axes):
    """
     Plot - adjust axes
    """
    # get text width for re-scaling
    bb = t.get_window_extent(renderer=r)
    text_width_inches = bb.width / fig.dpi
    # get axis width in inches
    current_fig_width = fig.get_figwidth()
    new_fig_width = current_fig_width + text_width_inches
    propotion = new_fig_width / current_fig_width
    # get axis limit
    x_lim = axes.get_xlim()
    axes.set_xlim([x_lim[0], x_lim[1]*propotion])


def draw_plot_func(dictionary, n_classes, window_title, plot_title, x_label, output_path, to_show, plot_color, true_p_bar):
    """
     Draw plot using Matplotlib
    """
    # sort the dictionary by decreasing value, into a list of tuples
    sorted_dic_by_value = sorted(dictionary.items(), key=operator.itemgetter(1))
    # unpacking the list of tuples into two lists
    sorted_keys, sorted_values = zip(*sorted_dic_by_value)
    # 
    if true_p_bar != "":
        """
         Special case to draw in:
            - green -> TP: True Positives (object detected and matches ground-truth)
            - red -> FP: False Positives (object detected but does not match ground-truth)
            - pink -> FN: False Negatives (object not detected but present in the ground-truth)
        """
        fp_sorted = []
        tp_sorted = []
        for key in sorted_keys:
            fp_sorted.append(dictionary[key] - true_p_bar[key])
            tp_sorted.append(true_p_bar[key])
        plt.barh(range(n_classes), fp_sorted, align='center', color='crimson', label='False Positive')
        plt.barh(range(n_classes), tp_sorted, align='center', color='forestgreen', label='True Positive', left=fp_sorted)
        # add legend
        plt.legend(loc='lower right')
        """
         Write number on side of bar
        """
        fig = plt.gcf() # gcf - get current figure
        axes = plt.gca()
        r = fig.canvas.get_renderer()
        for i, val in enumerate(sorted_values):
            fp_val = fp_sorted[i]
            tp_val = tp_sorted[i]
            fp_str_val = " " + str(fp_val)
            tp_str_val = fp_str_val + " " + str(tp_val)
            # trick to paint multicolor with offset:
            # first paint everything and then repaint the first number
            t = plt.text(val, i, tp_str_val, color='forestgreen', va='center', fontweight='bold')
            plt.text(val, i, fp_str_val, color='crimson', va='center', fontweight='bold')
            if i == (len(sorted_values)-1): # largest bar
                adjust_axes(r, t, fig, axes)
    else:
        plt.barh(range(n_classes), sorted_values, color=plot_color)
        """
         Write number on side of bar
        """
        fig = plt.gcf() # gcf - get current figure
        axes = plt.gca()
        r = fig.canvas.get_renderer()
        for i, val in enumerate(sorted_values):
            str_val = " " + str(val) # add a space before
            if val < 1.0:
                str_val = " {0:.2f}".format(val)
            t = plt.text(val, i, str_val, color=plot_color, va='center', fontweight='bold')
            # re-set axes to show number inside the figure
            if i == (len(sorted_values)-1): # largest bar
                adjust_axes(r, t, fig, axes)
    # set window title
    #fig.canvas.set_window_title(window_title)
    # write classes in y axis
    tick_font_size = 12
    plt.yticks(range(n_classes), sorted_keys, fontsize=tick_font_size)
    """
     Re-scale height accordingly
    """
    init_height = fig.get_figheight()
    # comput the matrix height in points and inches
    dpi = fig.dpi
    height_pt = n_classes * (tick_font_size * 1.4) # 1.4 (some spacing)
    height_in = height_pt / dpi
    # compute the required figure height 
    top_margin = 0.15 # in percentage of the figure height
    bottom_margin = 0.05 # in percentage of the figure height
    figure_height = height_in / (1 - top_margin - bottom_margin)
    # set new height
    if figure_height > init_height:
        fig.set_figheight(figure_height)

    # set plot title
    plt.title(plot_title, fontsize=14)
    # set axis titles
    # plt.xlabel('classes')
    plt.xlabel(x_label, fontsize='large')
    # adjust size of window
    fig.tight_layout()
    # save the plot
    fig.savefig(output_path)
    # show image
    if to_show:
        plt.show()
    # close the plot
    plt.close()


if __name__ == '__main__':
    main(sys.argv)
