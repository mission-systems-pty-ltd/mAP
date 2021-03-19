import sys
import os
import argparse
import json
from datetime import datetime as dt
from xml.dom import minidom
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
        list_of_objects = []
        file_name, file_ext = os.path.splitext(jf)
        data = json.load(open(os.path.join(ground_truth_dir, jf)))
        for obj in data:
            obj_name = obj['label']
            x_min = obj['topleft']['x']
            y_min = obj['topleft']['y']
            x_max = obj['bottomright']['x']
            y_max = obj['bottomright']['y']
            list_of_objects.append([obj_name, 1.0, x_min, x_max, y_min, y_max])
        write_list_of_pvoc_annotations_to_pvoc_xml(list_of_pvoc_annotations=list_of_objects,
                                                   output_file_path=os.path.join(out_dir, file_name+'.xml'),
                                                   segmented_annotation=False)
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
        list_of_objects = []
        file_name, file_ext = os.path.splitext(jf)
        data = json.load(open(os.path.join(predictions_dir, jf)))
        for obj in data:
            obj_name = obj['label']
            conf = obj['confidence']
            x_min = obj['topleft']['x']
            y_min = obj['topleft']['y']
            x_max = obj['bottomright']['x']
            y_max = obj['bottomright']['y']
            list_of_objects.append([obj_name, conf, x_min, x_max, y_min, y_max])
        write_list_of_pvoc_annotations_to_pvoc_xml(list_of_pvoc_annotations=list_of_objects,
                                                   output_file_path=os.path.join(out_dir, file_name+'.xml'),
                                                   segmented_annotation=False)
    logger.info("Conversion completed! Output at: " + out_dir)
    return out_dir


def write_list_of_pvoc_annotations_to_pvoc_xml(list_of_pvoc_annotations: list, output_file_path: str,
                                               segmented_annotation: bool = False, debug=False):
    """
    Call this once for each image with a list of pvoc bbox annotations.
    Args:
        list_of_pvoc_annotations (list): [ [str label, float confidence, int x_min, int x_max, int y_min, int y_max] ]
        output_file_path (str): output file path
        segmented_annotation (bool): True/False if data as a segmentation data annotation
        debug (bool): default False for printing extra print statements.
    Returns:
        Saves an .xml file as a labelling annotation.
        Returns nothing
    """
    doc = minidom.Document()
    doc.appendChild(doc.createComment("Annotations generated on: " + str(dt.now())))

    annotation = doc.createElement('annotation')
    doc.appendChild(annotation)

    # segmented
    segmented = doc.createElement('segmented')
    if segmented_annotation is True:
        segmented.appendChild(doc.createTextNode('1'))
    else:
        segmented.appendChild(doc.createTextNode('0'))
    annotation.appendChild(segmented)

    if len(list_of_pvoc_annotations) > 0:
        for a in list_of_pvoc_annotations:
            cls = a[0]
            confidence_val = a[1]
            xmin_val = a[2]
            xmax_val = a[3]
            ymin_val = a[4]
            ymax_val = a[5]
            # object
            obj = doc.createElement('object')
            annotation.appendChild(obj)

            name = doc.createElement('name')
            name.appendChild(doc.createTextNode(str(cls).strip()))
            obj.appendChild(name)

            pose = doc.createElement('pose')
            pose.appendChild(doc.createTextNode('Unspecified'))
            obj.appendChild(pose)

            truncated = doc.createElement('truncated')
            truncated.appendChild(doc.createTextNode('0'))
            obj.appendChild(truncated)

            difficult = doc.createElement('difficult')
            difficult.appendChild(doc.createTextNode('0'))
            obj.appendChild(difficult)

            occluded = doc.createElement('occluded')
            occluded.appendChild(doc.createTextNode('0'))
            obj.appendChild(occluded)

            confidence = doc.createElement('confidence')
            confidence.appendChild(doc.createTextNode(str(confidence_val)))
            obj.appendChild(confidence)

            # obj boundbox
            bndbox = doc.createElement('bndbox')
            obj.appendChild(bndbox)

            xmin = doc.createElement('xmin')
            xmin.appendChild(doc.createTextNode(str(xmin_val)))
            bndbox.appendChild(xmin)

            ymin = doc.createElement('ymin')
            ymin.appendChild(doc.createTextNode(str(ymin_val)))
            bndbox.appendChild(ymin)

            xmax = doc.createElement('xmax')
            xmax.appendChild(doc.createTextNode(str(xmax_val)))
            bndbox.appendChild(xmax)

            ymax = doc.createElement('ymax')
            ymax.appendChild(doc.createTextNode(str(ymax_val)))
            bndbox.appendChild(ymax)
    if debug:
        logger.debug(doc.toprettyxml(indent='   '))

    with open(os.path.join(output_file_path), 'w') as output:
        output.write(doc.toprettyxml(indent='   '))
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
