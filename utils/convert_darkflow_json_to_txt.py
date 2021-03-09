import argparse
import sys
import os
import glob
import json
from logzero import logger


def main(arguments):
    args = parse_args(argv=arguments)
    if args.ground_truth_dir is not None:
        gt_dir = os.path.join(args.output_dir, "ground_truth")
        converted_gt_file_dir = convert_ground_truth_darkflow_json(ground_truth_dir=args.ground_truth_dir, out_dir=gt_dir)
        logger.info("Ground Truth at: " + converted_gt_file_dir)
    if args.predictions_dir is not None:
        pred_dir = os.path.join(args.output_dir, "predictions")
        converted_pr_file_dir = convert_prediction_darkflow_json(predictions_dir=args.predictions_dir, out_dir=pred_dir)
        logger.info("Ground Truth at: " + converted_pr_file_dir)


def convert_ground_truth_darkflow_json(ground_truth_dir: str, out_dir: str):
    if os.path.exists(out_dir):
        logger.error("ERROR: path exists at {} - try a different output path.".format(out_dir))
        sys.exit(1)
    else:
        os.makedirs(out_dir)
    file_list = [f for f in os.listdir(ground_truth_dir) if os.path.isfile(os.path.join(ground_truth_dir, f))]
    json_list = [f for f in file_list if f.endswith('.json')]
    logger.info("Num files to convert: {}".format(len(json_list)))
    if len(json_list) == 0:
        logger.error("ERROR: no .json files found in ground-truth - exiting task.")
        sys.exit(1)

    for jf in json_list:
        file_name, file_ext = os.path.splitext(jf)

        with open(os.path.join(out_dir, file_name + '.txt'), 'w+') as new_f:
            data = json.load(open(os.path.join(ground_truth_dir, jf)))
            for obj in data:
                obj_name = obj['label']
                left = obj['topleft']['x']
                top = obj['topleft']['y']
                right = obj['bottomright']['x']
                bottom = obj['bottomright']['y']
                new_f.write(
                    obj_name + " " + str(left) + " " + str(top) + " " + str(right) + " " + str(
                        bottom) + '\n')
    logger.info("Conversion completed! Output at: " + out_dir)
    return out_dir


def convert_prediction_darkflow_json(predictions_dir: str, out_dir: str):
    if os.path.exists(out_dir):
        logger.error("ERROR: path exists at {} - try a different output path.".format(out_dir))
        sys.exit(1)
    else:
        os.makedirs(out_dir)
    file_list = [f for f in os.listdir(predictions_dir) if os.path.isfile(os.path.join(predictions_dir, f))]
    json_list = [f for f in file_list if f.endswith('.json')]

    logger.info("Num files to convert: {}".format(len(json_list)))
    if len(json_list) == 0:
        logger.error("ERROR: no .json files found in ground-truth - exiting task.")
        sys.exit(1)

    for jf in json_list:
        file_name, file_ext = os.path.splitext(jf)

        with open(os.path.join(out_dir, file_name + '.txt'), 'w+') as new_f:
            data = json.load(open(os.path.join(predictions_dir, jf)))
            for obj in data:
                obj_name = obj['label']
                conf = obj['confidence']
                left = obj['topleft']['x']
                top = obj['topleft']['y']
                right = obj['bottomright']['x']
                bottom = obj['bottomright']['y']
                new_f.write(
                    obj_name + " " + str(conf) + " " + str(left) + " " + str(top) + " " + str(right) + " " + str(
                        bottom) + '\n')
    logger.info("Conversion completed! Output at: " + out_dir)
    return out_dir


def parse_args(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("-gt", "--ground_truth_dir", help="path to ground truth annotations", default=None)
    parser.add_argument("-pr", "--predictions_dir", help="path to prediction annotations", default=None)
    parser.add_argument("-od", "--output_dir", help="path to output files", default=None)
    arguments = parser.parse_args(argv[1:])
    return arguments


if __name__ == '__main__':
    main(sys.argv)
