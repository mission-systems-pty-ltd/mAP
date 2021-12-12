import sys
import os
import argparse
import xml.etree.ElementTree as ET
from logzero import logger

"""
This converter ALMOST follows the specified YOLO format
as defined in the https://github.com/AlexeyAB/Yolo_mark/issues/60:

EXCERPT
-------
    .txt-file for each .jpg-image-file - in the same directory and with the same name, but with .txt-extension, and put
    to file: object number and object coordinates on this image, for each object in new line: 
    
    <object-class> <x> <y> <width> <height>
    
    Where:
        <object-class> - integer number of object from 0 to (classes-1)
        <x> <y> <width> <height> - float values relative to width and height of image, it can be equal from (0.0 to 1.0]
        for example: <x> = <absolute_x> / <image_width> or <height> = <absolute_height> / <image_height>
        atention: <x> <y> - are center of rectangle (are not top-left corner)
        For example for img1.jpg you will be created img1.txt containing:
        
        1 0.716797 0.395833 0.216406 0.147222
        0 0.687109 0.379167 0.255469 0.158333
        1 0.420312 0.395833 0.140625 0.16666

        
ONE BIG DIFFERENCE
------------------
    <object-class> - in this case I've decided to leave it as the class label because the class number itself depends on
    the training class order - with respect to calculating mAP scores within this toolkit this DOES NOT MATTER.
    
    If you intend to use this library to convert datasets for training i suggest you convert the dataset and then do
    something along the lines of:
        
        import fileinput
        with fileinput.FileInput(os.path.join(converted_anno_dir, tf), inplace=True) as file:
            for line in file:
                for idx, val in enumerate(classes_list):
                    print(line.replace(val, str(idx)), end='')

"""


def main(arguments):
    args = parse_args(argv=arguments)
    if args.ground_truth_dir is not None:
        gt_dir = os.path.join(args.output_dir, "ground_truth")
        converted_gt_file_dir = convert_ground_truth_xml(ground_truth_dir=args.ground_truth_dir, out_dir=gt_dir)
        logger.info("Ground Truth at: " + converted_gt_file_dir)
    if args.predictions_dir is not None:
        pred_dir = os.path.join(args.output_dir, "predictions")
        converted_pr_file_dir = convert_prediction_xml(predictions_dir=args.predictions_dir, out_dir=pred_dir)
        logger.info("Ground Truth at: " + converted_pr_file_dir)


def convert_ground_truth_xml(ground_truth_dir: str, out_dir: str):
    if os.path.exists(out_dir):
        logger.error("ERROR: path exists at {} - try a different output path.".format(out_dir))
        sys.exit(1)
    else:
        os.makedirs(out_dir)
    file_list = [f for f in os.listdir(ground_truth_dir) if os.path.isfile(os.path.join(ground_truth_dir, f))]
    xml_list = [f for f in file_list if f.endswith('.xml')]
    logger.info("Num files to convert: {}".format(len(xml_list)))
    if len(xml_list) == 0:
        logger.error("ERROR: no .xml files found in ground-truth - exiting task.")
        sys.exit(1)

    for xf in xml_list:
        file_name, file_ext = os.path.splitext(xf)
        with open(os.path.join(out_dir, file_name + '.txt'), 'w+') as new_f:
            root = ET.parse(os.path.join(ground_truth_dir, xf)).getroot()
            size = root.find('size')
            width = int(size.find('width').text)
            height = int(size.find('height').text)
            for obj in root.findall('object'):
                obj_name = obj.find('name').text
                bndbox = obj.find('bndbox')
                xmin = int(bndbox.find('xmin').text)
                ymin = int(bndbox.find('ymin').text)
                xmax = int(bndbox.find('xmax').text)
                ymax = int(bndbox.find('ymax').text)
                norm_c_x = ((xmax + xmin)/2)/width
                norm_c_y = ((ymax + ymin)/2)/height
                norm_bbox_width = (xmax - xmin)/width
                norm_bbox_height = (ymax - ymin)/height
                line = "{} {:.6f} {:.6f} {:.6f} {:.6f}\n".format(obj_name, norm_c_x, norm_c_y, norm_bbox_width, norm_bbox_height)
                new_f.write(line)
    logger.info("Conversion completed! Output at: " + out_dir)
    return out_dir

def convert_ground_truth_xml_to_pd(ground_truth_dir: str, out_dir: str):
    file_list = [f for f in os.listdir(ground_truth_dir) if os.path.isfile(os.path.join(ground_truth_dir, f))]
    xml_list = [f for f in file_list if f.endswith('.xml')]
    logger.info("Num files to convert: {}".format(len(xml_list)))
    if len(xml_list) == 0:
        logger.error("ERROR: no .xml files found in ground-truth - exiting task.")
        sys.exit(1)

    file_name, file_ext = os.path.splitext(xml_list[0])
    if os.path.exists(out_dir):
        logger.error("ERROR: path exists at {} - try a different output path.".format(out_dir))
        return out_dir, file_name
        sys.exit(1)
    else:
        os.makedirs(out_dir)

    with open(os.path.join(out_dir, file_name + '.txt'), 'w+') as new_f:
        for xf in xml_list:
            root = ET.parse(os.path.join(ground_truth_dir, xf)).getroot()
            size = root.find('size')
            for obj in root.findall('object'):
                obj_name = obj.find('name').text
                bndbox = obj.find('bndbox')
                xmin = int(bndbox.find('xmin').text)
                ymin = int(bndbox.find('ymin').text)
                xmax = int(bndbox.find('xmax').text)
                ymax = int(bndbox.find('ymax').text)
                line = "{} {} {:.6f} {:.6f} {:.6f} {:.6f}\n".format(xf[:-4]+".png", obj_name, xmin, ymin, xmax, ymax)
                new_f.write(line)
    logger.info("Conversion completed! Output at: " + out_dir)
    return out_dir, file_name

def convert_prediction_xml(predictions_dir: str, out_dir: str):
    if os.path.exists(out_dir):
        logger.error("ERROR: path exists at {} - try a different output path.".format(out_dir))
        sys.exit(1)
    else:
        os.makedirs(out_dir)
    file_list = [f for f in os.listdir(predictions_dir) if os.path.isfile(os.path.join(predictions_dir, f))]
    xml_list = [f for f in file_list if f.endswith('.xml')]
    logger.info("Num files to convert: {}".format(len(xml_list)))
    if len(xml_list) == 0:
        logger.error("ERROR: no .xml files found in ground-truth - exiting task.")
        sys.exit(1)

    for xf in xml_list:
        file_name, file_ext = os.path.splitext(xf)
        with open(os.path.join(out_dir, file_name + '.txt'), 'w+') as new_f:
            root = ET.parse(os.path.join(predictions_dir, xf)).getroot()
            size = root.find('size')
            width = int(size.find('width').text)
            height = int(size.find('height').text)
            for obj in root.findall('object'):
                obj_name = obj.find('name').text
                confidence = obj.find('confidence').text
                bndbox = obj.find('bndbox')
                xmin = int(bndbox.find('xmin').text)
                ymin = int(bndbox.find('ymin').text)
                xmax = int(bndbox.find('xmax').text)
                ymax = int(bndbox.find('ymax').text)
                norm_c_x = ((xmax + xmin)/2)/width
                norm_c_y = ((ymax + ymin)/2)/height
                norm_bbox_width = (xmax - xmin)/width
                norm_bbox_height = (ymax - ymin)/height
                line = "{} {} {:.6f} {:.6f} {:.6f} {:.6f}\n".format(obj_name, confidence, norm_c_x, norm_c_y, norm_bbox_width, norm_bbox_height)
                new_f.write(line)
    logger.info("Conversion completed! Output at: " + out_dir)
    return out_dir, file_name


def parse_args(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("-gt", "--ground_truth_dir", help="path to ground truth annotations", default=None)
    parser.add_argument("-pr", "--predictions_dir", help="path to prediction annotations", default=None)
    parser.add_argument("-od", "--output_dir", help="path to output files", default=None)
    arguments = parser.parse_args(argv[1:])
    return arguments


if __name__ == '__main__':
    main(sys.argv)
