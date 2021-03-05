import sys
import os
import argparse
import glob
import xml.etree.ElementTree as ET


def main(arguments):
    parse_args(argv=arguments)


def do_the_thing():
    print("ERROR NOT WORKING")
    sys.exit(1)
    # make sure that the cwd() in the beginning is the location of the python script (so that every path makes sense)
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    # change directory to the one with the files to be changed
    parent_path = os.path.abspath(os.path.join(os.getcwd(), os.pardir))
    parent_path = os.path.abspath(os.path.join(parent_path, os.pardir))
    GT_PATH = os.path.join(parent_path, 'input', 'ground-truth')
    # print(GT_PATH)
    os.chdir(GT_PATH)

    # old files (xml format) will be moved to a "backup" folder
    ## create the backup dir if it doesn't exist already
    if not os.path.exists("backup"):
        os.makedirs("backup")

    # create VOC format files
    xml_list = glob.glob('*.xml')
    if len(xml_list) == 0:
        print("Error: no .xml files found in ground-truth")
        sys.exit()
    for tmp_file in xml_list:
        # print(tmp_file)
        # 1. create new file (VOC format)
        with open(tmp_file.replace(".xml", ".txt"), "a") as new_f:
            root = ET.parse(tmp_file).getroot()
            for obj in root.findall('object'):
                obj_name = obj.find('name').text
                bndbox = obj.find('bndbox')
                left = bndbox.find('xmin').text
                top = bndbox.find('ymin').text
                right = bndbox.find('xmax').text
                bottom = bndbox.find('ymax').text
                new_f.write("%s %s %s %s %s\n" % (obj_name, left, top, right, bottom))
        # 2. move old file (xml format) to backup
        os.rename(tmp_file, os.path.join("backup", tmp_file))
    print("Conversion completed!")


def parse_args(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("-gt", "--ground_truth_dir", help="path to ground truth annotations", required=True)
    parser.add_argument("-od", "--output_dir", help="path to output files", default=None)
    arguments = parser.parse_args(argv[1:])
    return arguments


if __name__ == '__main__':
    main(sys.argv)
