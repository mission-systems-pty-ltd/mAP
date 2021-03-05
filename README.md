# mAP (mean Average Precision)

CLI Tool & importable library for evaluating object detection performance with mAP (mean Average Precision) scores.

The higher your mAP score the better your model is performing.

--- 
#Citation & Contributions

This repository is a fork of [Cartucho/mAP](https://github.com/Cartucho/mAP) [![GitHub stars](https://img.shields.io/github/stars/Cartucho/mAP.svg?style=social&label=Stars)](https://github.com/Cartucho/mAP) and further developments have been made to allow this codebase to be more usable as a library as well as via a CLI tool.

1. [**João Cartucho**](https://github.com/Cartucho) - Imperial College London
    - credit for original scripts & paper submission, explanation, etc.

2. [**Kausthub Krishnamurthy**](https://github.com/KausthubK)
    - while at Mission Systems Pty. Ltd. conversion to CLI flexible tool and importable library to allow this codebase to be used programatically within other Python programs.

[![GitHub stars](https://img.shields.io/github/stars/mission-systems-pty-ltd/mAP.svg?style=social&label=Stars)](https://github.com/mission-systems-pty-ltd/mAP)

[![GitHub contributors](https://img.shields.io/github/contributors/mission-systems-pty-ltd/mAP.svg)](https://github.com/mission-systems-pty-ltd/mAP/graphs/contributors)

---

# Usage

## evaluate_mAP_scores.py

```
python3 evaluate_mAP_scores.py [-h] -pd PREDICTION_DIR -gt GROUND_TRUTH_DIR [-id IMAGE_DIR]
                [-od OUTPUT_DIR] [-a] [-np] [-q] [-i IGNORE [IGNORE ...]]
                [--set-class-iou SET_CLASS_IOU [SET_CLASS_IOU ...]]

optional arguments:
  -h, --help            show this help message and exit
  -pd PREDICTION_DIR, --prediction_dir PREDICTION_DIR
                        path to predicted annotations
  -gt GROUND_TRUTH_DIR, --ground_truth_dir GROUND_TRUTH_DIR
                        path to ground truth annotations
  -id IMAGE_DIR, --image_dir IMAGE_DIR
                        path to images
  -od OUTPUT_DIR, --output_dir OUTPUT_DIR
                        path to output files
  -a, --animate         show animation
  -np, --no-plot        no plot is shown.
  -q, --quiet           minimalistic console output.
  -i IGNORE [IGNORE ...], --ignore IGNORE [IGNORE ...]
                        ignore a list of classes.
  --set-class-iou SET_CLASS_IOU [SET_CLASS_IOU ...]
                        set IoU for a specific class.
```

### Working Example
```
 python evaluate_mAP_scores.py \
 -pd input/detection-results \
 -gt input/ground-truth \
 -id input/images-optional/ \
 -od ~/out/mAP/example
```
N.B.: including an image directory with ```-id``` is purely optional if you want to see the **animation** - in which case you will need the -a flag.


## utils
| Utility | Type | Description |
| ------- | ------- | ------- |
| convert_gt_xml | CLI & Library | Converts xml annotations to |

## scripts/extra
Collection of python scripts that convert from different annotation formats to the format required for this tool.
These are from the original repository and are not yet folded into the new library & CLI structure.

[convert_gt_xml](utils/convert_gt_xml.py) is an example of a script that has been moved from scripts/extra to utils after being refactored, and can be imported into other python scripts.

Consider this directory a "to do" list for conversion capabilities. At this stage there is no urgent intention to convert these other scripts - should there be a need feel free to convert it in the same manner and create a pull request. 

---

# Explanation of mAP Score Calculation

**N.B.: This explanation is from the original repository - authored by  [João Cartucho](https://github.com/Cartucho) - I've left this as is because it's a fantastic explanation of mAP scores.**

This code will evaluate the performance of your neural net for object recognition.

<p align="center">
  <img src="https://user-images.githubusercontent.com/15831541/37559643-6738bcc8-2a21-11e8-8a07-ed836f19c5d9.gif" width="450" height="300" />
</p>

In practice, a **higher mAP** value indicates a **better performance** of your neural net, given your ground-truth and set of classes.

---

The performance of your neural net will be judged using the mAP criterium defined in the [PASCAL VOC 2012 competition](http://host.robots.ox.ac.uk/pascal/VOC/voc2012/). We simply adapted the [official Matlab code](http://host.robots.ox.ac.uk/pascal/VOC/voc2012/#devkit) into Python (in our tests they both give the same results).

First (**1.**), we calculate the Average Precision (AP), for each of the classes present in the ground-truth. Finally (**2.**), we calculate the mAP (mean Average Precision) value.

## 1. Calculate AP

For each class:

First, your neural net **detection-results** are sorted by decreasing confidence and are assigned to **ground-truth objects**. We have "a match" when they share the **same label and an IoU >= 0.5** (Intersection over Union greater than 50%). This "match" is considered a true positive if that ground-truth object has not been already used (to avoid multiple detections of the same object). 

<img src="https://user-images.githubusercontent.com/15831541/37725175-45b9e1a6-2d2a-11e8-8c15-2fb4d716ca9a.png" width="35%" height="35%" />

Using this criterium, we calculate the precision/recall curve. E.g:

<img src="https://user-images.githubusercontent.com/15831541/43008995-64dd53ce-8c34-11e8-8a2c-4567b1311910.png" width="45%" height="45%" />

Then we compute a version of the measured precision/recall curve with **precision monotonically decreasing** (shown in light red), by setting the precision for recall `r` to the maximum precision obtained for any recall `r' > r`.

Finally, we compute the AP as the **area under this curve** (shown in light blue) by numerical integration.
No approximation is involved since the curve is piecewise constant.


## 2. Calculate mAP

We calculate the mean of all the AP's, resulting in an mAP value from 0 to 100%. E.g:

<img src="https://user-images.githubusercontent.com/15831541/38933241-5f9556ae-4310-11e8-9d47-cb205f9b103b.png"/>

<img src="https://user-images.githubusercontent.com/15831541/38933180-366b6fca-4310-11e8-99b9-17ad4b159b86.png" />

---

# Annotation Format
**This section is an excerpt from the original.**

In the [scripts/extra](https://github.com/Cartucho/mAP/tree/master/scripts/extra) folder you can find additional scripts to convert **PASCAL VOC**, **darkflow** and **YOLO** files into the required format.

## Create the ground-truth files

- Create a separate ground-truth text file for each image.
- Use **matching names** for the files (e.g. image: "image_1.jpg", ground-truth: "image_1.txt").
- In these files, each line should be in the following format:
    ```
    <class_name> <left> <top> <right> <bottom> [<difficult>]
    ```
- The `difficult` parameter is optional, use it if you want the calculation to ignore a specific detection.
- E.g. "image_1.txt":
    ```
    tvmonitor 2 10 173 238
    book 439 157 556 241
    book 437 246 518 351 difficult
    pottedplant 272 190 316 259
    ```

## Create the detection-results files

- Create a separate detection-results text file for each image.
- Use **matching names** for the files (e.g. image: "image_1.jpg", detection-results: "image_1.txt").
- In these files, each line should be in the following format:
    ```
    <class_name> <confidence> <left> <top> <right> <bottom>
    ```
- E.g. "image_1.txt":
    ```
    tvmonitor 0.471781 0 13 174 244
    cup 0.414941 274 226 301 265
    book 0.460851 429 219 528 247
    chair 0.292345 0 199 88 436
    book 0.269833 433 260 506 336
    ```


---
