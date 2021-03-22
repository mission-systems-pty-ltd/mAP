import os
import shutil
import unittest
from utils import convert_darkflow_json_to_pvoc_xml


class TestConvertDarkflowJsonToPascalVocXml(unittest.TestCase):
    def setUp(self) -> None:
        self.test_gt_dir = 'sample_data/ground_truth/json'
        self.test_pr_dir = 'sample_data/predictions/json'
        self.test_out_dir = './out'

    def test_convert_gt(self):
        if os.path.exists(self.test_out_dir):
            shutil.rmtree(self.test_out_dir)
        out_dir = convert_darkflow_json_to_pvoc_xml.convert_ground_truth_darkflow_json(
            ground_truth_dir=self.test_gt_dir, out_dir=self.test_out_dir)
        self.assertEqual(self.test_out_dir, out_dir)
        self.assertEqual(len(os.listdir(self.test_gt_dir)), len(os.listdir(out_dir)))
        if os.path.exists(self.test_out_dir):
            shutil.rmtree(self.test_out_dir)

    def test_convert_pr(self):
        if os.path.exists(self.test_out_dir):
            shutil.rmtree(self.test_out_dir)
        out_dir = convert_darkflow_json_to_pvoc_xml.convert_prediction_darkflow_json(predictions_dir=self.test_pr_dir,
                                                                                     out_dir=self.test_out_dir)
        self.assertEqual(self.test_out_dir, out_dir)
        self.assertEqual(len(os.listdir(self.test_pr_dir)), len(os.listdir(out_dir)))
        if os.path.exists(self.test_out_dir):
            shutil.rmtree(self.test_out_dir)

    def test_write_list_of_pvoc_annotations_to_xml(self):
        test_gt_file = os.path.join(self.test_gt_dir, os.listdir(self.test_gt_dir)[0])
        gt_annotation_01 = [['car', 1.0, 520, 248, 609, 298],
                            ['car', 1.0, 584, 302, 682, 345],
                            ['militaryTruck', 1.0, 231, 453, 324, 539]]
        if os.path.exists(self.test_out_dir):
            shutil.rmtree(self.test_out_dir)
        os.makedirs(self.test_out_dir)
        convert_darkflow_json_to_pvoc_xml.write_list_of_pvoc_annotations_to_pvoc_xml(
            list_of_pvoc_annotations=gt_annotation_01,
            output_file_path=os.path.join(self.test_out_dir, os.path.splitext(
                                                                os.path.basename(test_gt_file))[0] + '.xml'),
            segmented_annotation=False,
            debug=True)
        self.assertTrue(os.path.isfile(os.path.join(self.test_out_dir, os.path.splitext(
                                                                os.path.basename(test_gt_file))[0] + '.xml')))
        if os.path.exists(self.test_out_dir):
            shutil.rmtree(self.test_out_dir)

    def test_cli(self):
        if os.path.exists(self.test_out_dir):
            shutil.rmtree(self.test_out_dir)
        arguments = ['convert_darkflow_json_to_txt.py',
                     '-gt', self.test_gt_dir,
                     '-pr', self.test_pr_dir,
                     '-od', self.test_out_dir]
        convert_darkflow_json_to_pvoc_xml.main(arguments=arguments)
        self.assertEqual(len(os.listdir(self.test_gt_dir)),
                         len(os.listdir(os.path.join(self.test_out_dir, 'ground_truth'))))
        self.assertEqual(len(os.listdir(self.test_pr_dir)),
                         len(os.listdir(os.path.join(self.test_out_dir, 'predictions'))))


if __name__ == '__main__':
    unittest.main()
