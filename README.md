# Receipt Cropper Module

A Python-based image processing module for detecting and cropping receipt images. This project contains scripts used for testing image preprocessing, thresholding, OCR preparation, and receipt boundary detection techniques.  Though intended to be used as a module, it can run as its own demo.

## Project Structure
```
.
├── .gitignore
├── LICENSE
├── README.md
│
├── src
│   └── receipt_cropper_module.py
│
├── tests
│   └── test_receipt_cropper.py
│
└── verification images
    ├── Archive
    ├── Cropped
    ├── Scanned
    │   ├── Test Image 1.jpg
    │   ├── Test Image 2.jpg
    │   ├── Test Image 3.jpg
    │   └── Test Image 4.jpg
    └── Text
```

Test images are located in the 'Scanned' folder, which is where the demo will look for them.  After the demo runs, the uncropped orginals will be placed into the 'Archive' folder, and the Cropped outputs will be placed in the 'Cropped' folder.  OCR Output will be in the 'Text' folder.  To reset the demo, you must delete the output files in 'Cropped' and 'Text' directoies, and move test images from 'Archived' back to 'Scanned'.

## Purpose

The goal of this project is to develop a reusable Python module capable of:

Processing receipt images
Detecting receipt boundaries
Cropping unwanted background areas
Preparing images for OCR and further analysis

The included verification images are sample inputs used to test the cropping functionality.

## Requirements

Python 3.14.3

Install required dependencies:

pip install pillow pytesseract

Additionally, pytesseract requires the Tesseract OCR engine to be installed:

https://github.com/tesseract-ocr/tesseract

## Usage

Run the module as a demo:

python "src/Reciept Cropper Module.py"

The module can also be imported into another Python project:

from Reciept_Cropper_Module import *

## Development Notes

This repository contains a demo version of the receipt cropping module.

Additional experimental scripts used during development are intentionally excluded from version control. The .gitignore file is configured to include only:

src/Reciept Cropper Module.py
Verification images used for testing

## Potential enhancements:

Improve receipt edge detection reliability
Add automatic perspective correction
Improve OCR integration pipeline
Create a command-line interface
Add automated unit tests
Package as a reusable Python library

This project is licensed under the MIT License.