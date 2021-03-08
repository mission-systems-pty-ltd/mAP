import unittest
import os
import shutil
import evaluate_mAP_scores as mAP_lib


class TestEvaluateMAPScores(unittest.TestCase):
    def setUp(self) -> None:
        self.test_gt_dir = '../input/ground-truth'
        self.test_img_dir = '../input/images-optional'
        self.test_det_res_dir = '../input/detection-results'
        self.test_out_dir = './out'

    def test_calculate_mAP_scores(self):
        if os.path.exists(self.test_out_dir):
            shutil.rmtree(self.test_out_dir)
        mAP = mAP_lib.calculate_mAP_scores(ground_truth_dir=self.test_gt_dir,
                                           prediction_dir=self.test_det_res_dir)
        self.assertEqual(0.31047718500906324, mAP)
        if os.path.exists(self.test_out_dir):
            shutil.rmtree(self.test_out_dir)

    def test_calculate_mAP_scores_with_output(self):
        if os.path.exists(self.test_out_dir):
            shutil.rmtree(self.test_out_dir)
        mAP = mAP_lib.calculate_mAP_scores(ground_truth_dir=self.test_gt_dir,
                                           prediction_dir=self.test_det_res_dir,
                                           out_dir=self.test_out_dir)
        self.assertTrue(os.path.exists(self.test_out_dir))
        self.assertEqual(0.31047718500906324, mAP)
        if os.path.exists(self.test_out_dir):
            shutil.rmtree(self.test_out_dir)

    def test_cli_basic(self):
        if os.path.exists(self.test_out_dir):
            shutil.rmtree(self.test_out_dir)
        #  python3 evaluate_mAP_scores.py -pd ./input/detection-results/ -gt ./input/ground-truth/
        arguments = ['evaluate_mAP_scores.py',
                     '-pd', self.test_det_res_dir,
                     '-gt', self.test_gt_dir,
                     '-od', self.test_out_dir]
        mAP_lib.main(arguments=arguments)
        self.assertEqual(1, len(os.listdir(self.test_out_dir)))
        if os.path.exists(self.test_out_dir):
            shutil.rmtree(self.test_out_dir)


if __name__ == '__main__':
    unittest.main()
