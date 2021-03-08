import os
import shutil
import unittest
from utils import convert_gt_xml


class TestConvertGTXML(unittest.TestCase):
    def setUp(self) -> None:
        self.test_gt_dir = 'sample_data/xml'
        self.test_out_dir = './out'

    def test_convert_gt_xml(self):
        if os.path.exists(self.test_out_dir):
            shutil.rmtree(self.test_out_dir)
        out_dir = convert_gt_xml.convert_gt_xml(ground_truth_dir=self.test_gt_dir, out_dir=self.test_out_dir)
        self.assertEqual(self.test_out_dir, out_dir)
        self.assertEqual(len(os.listdir(self.test_gt_dir)), len(os.listdir(out_dir)))
        if os.path.exists(self.test_out_dir):
            shutil.rmtree(self.test_out_dir)

    def test_cli(self):
        if os.path.exists(self.test_out_dir):
            shutil.rmtree(self.test_out_dir)
        arguments = ['convert_gt_xml.py',
                     '-gt', self.test_gt_dir,
                     '-od', self.test_out_dir]
        convert_gt_xml.main(arguments=arguments)
        self.assertEqual(1, len(os.listdir(self.test_out_dir)))
        if os.path.exists(self.test_out_dir):
            shutil.rmtree(self.test_out_dir)


if __name__ == '__main__':
    unittest.main()
