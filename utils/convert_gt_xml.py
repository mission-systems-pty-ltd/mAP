import sys
import os
import argparse
import xml.etree.ElementTree as ET
from colorama import Fore


def main(arguments):
    args = parse_args(argv=arguments)
    converted_file_dir = convert_gt_xml(ground_truth_dir=args.ground_truth_dir, out_dir=args.output_dir)
    print("Output at: " + converted_file_dir)


def convert_gt_xml(ground_truth_dir: str, out_dir: str):
    if os.path.exists(out_dir):
        print(Fore.RED + "ERROR: path exists at {} - try a different output path.".format(out_dir) + Fore.RESET)
        sys.exit(1)
    else:
        os.mkdir(out_dir)
    file_list = [f for f in os.listdir(ground_truth_dir) if os.path.isfile(os.path.join(ground_truth_dir, f))]
    xml_list = [f for f in file_list if f.endswith('.xml')]
    print("Num files to convert: {}".format(len(xml_list)))
    if len(xml_list) == 0:
        print(Fore.RED + "ERROR: no .xml files found in ground-truth - exiting task." + Fore.RESET)
        sys.exit(1)

    for xf in xml_list:
        file_name, file_ext = os.path.splitext(xf)

        with open(os.path.join(out_dir, file_name + '.txt'), 'w+') as new_f:
            root = ET.parse(os.path.join(ground_truth_dir, xf)).getroot()
            for obj in root.findall('object'):
                obj_name = obj.find('name').text
                bndbox = obj.find('bndbox')
                left = bndbox.find('xmin').text
                top = bndbox.find('ymin').text
                right = bndbox.find('xmax').text
                bottom = bndbox.find('ymax').text
                new_f.write("%s %s %s %s %s\n" % (obj_name, left, top, right, bottom))
    print("Conversion completed!")
    return out_dir


def parse_args(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("-gt", "--ground_truth_dir", help="path to ground truth annotations", required=True)
    parser.add_argument("-od", "--output_dir", help="path to output files", default=None)
    arguments = parser.parse_args(argv[1:])
    return arguments


if __name__ == '__main__':
    main(sys.argv)
