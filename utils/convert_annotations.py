import os
from logzero import logger
import sys
import argparse
from . import convert_pvoc_xml_to_txt
from . import convert_darkflow_json_to_txt


def main(arguments):
    args = parse_args(argv=arguments)
    if args.ground_truth_dir is not None:
        gt_dir = os.path.join(args.output_dir, "ground_truth")
        converted_gt_file_dir = convert_ground_truth_files(ground_truth_dir=args.ground_truth_dir, out_dir=gt_dir)
        logger.info("Ground Truth at: " + converted_gt_file_dir)
    if args.predictions_dir is not None:
        pred_dir = os.path.join(args.output_dir, "predictions")
        converted_pr_file_dir = convert_prediction_files(predictions_dir=args.predictions_dir, out_dir=pred_dir)
        logger.info("Ground Truth at: " + converted_pr_file_dir)


def convert_ground_truth_files(ground_truth_dir: str, out_dir: str):
    file_exts = [os.path.splitext(f)[1] for f in os.listdir(ground_truth_dir) if os.path.isfile(os.path.join(ground_truth_dir, f))]
    ext_list = list(set(file_exts))
    if len(ext_list) == 1:
        if ext_list[0] == '.xml':
            gt_dir = convert_pvoc_xml_to_txt.convert_ground_truth_xml(ground_truth_dir=ground_truth_dir,
                                                                      out_dir=out_dir)
            return gt_dir
        elif ext_list[0] == '.json':
            gt_dir = convert_darkflow_json_to_txt.convert_ground_truth_darkflow_json(ground_truth_dir=ground_truth_dir,
                                                                                     out_dir=out_dir)
            return gt_dir
        else:
            logger.error("Converter not implemented for annotation file type {}".format(ext_list[0]))
    elif len(ext_list) > 1:
        logger.error("More than one file extension type - this dataset is probably broken.")
        sys.exit(1)
    else:
        logger.error("Less than one file extension type - this dataset is probably broken.")
        sys.exit(1)
    return


def convert_prediction_files(predictions_dir: str, out_dir: str):
    file_exts = [os.path.splitext(f)[1] for f in os.listdir(predictions_dir)
                 if os.path.isfile(os.path.join(predictions_dir, f))]
    ext_list = list(set(file_exts))
    if len(ext_list) == 1:
        if ext_list[0] == '.xml':
            pr_dir = convert_pvoc_xml_to_txt.convert_prediction_xml(predictions_dir=predictions_dir,
                                                                    out_dir=out_dir)
            return pr_dir
        elif ext_list[0] == '.json':
            pr_dir = convert_darkflow_json_to_txt.convert_prediction_darkflow_json(predictions_dir=predictions_dir,
                                                                                   out_dir=out_dir)
            return pr_dir
        else:
            logger.error("Converter not implemented for annotation file type {}".format(ext_list[0]))
    elif len(ext_list) > 1:
        logger.error("More than one file extension type - this dataset is probably broken.")
        sys.exit(1)
    else:
        logger.error("Less than one file extension type - this dataset is probably broken.")
        sys.exit(1)
    return


def parse_args(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("-gt", "--ground_truth_dir", help="path to ground truth annotations", default=None)
    parser.add_argument("-pr", "--predictions_dir", help="path to prediction annotations", default=None)
    parser.add_argument("-od", "--output_dir", help="path to output files", default=None)
    arguments = parser.parse_args(argv[1:])
    return arguments


if __name__ == '__main__':
    main(sys.argv)
