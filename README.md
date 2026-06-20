# Receipt Cropper Module

A Python-based image processing module for detecting and cropping receipt images. This project contains experimental scripts used for testing image preprocessing, thresholding, OCR preparation, and receipt boundary detection techniques.

## Project Structure
```
.
├── src
│   └── Reciept Cropper Module.py
│
└── verification images
    ├── Test Image 1.jpg
    ├── Test Image 2.jpg
    ├── Test Image 3.jpg
    └── Test Image 4.jpg
```

## Purpose

The goal of this project is to develop a reusable Python module capable of:

Processing receipt images
Detecting receipt boundaries
Cropping unwanted background areas
Preparing images for OCR and further analysis

The included verification images are sample inputs used to test the cropping functionality.

## Requirements

Python 3.x

Install required dependencies:

pip install pillow pytesseract opencv-python

Additionally, pytesseract requires the Tesseract OCR engine to be installed:

https://github.com/tesseract-ocr/tesseract

## Usage

Run the module:

python "src/Reciept Cropper Module.py"

The module can also be imported into another Python project:

from Reciept_Cropper_Module import *

## Development Notes

This repository contains the current working version of the receipt cropping module.

Additional experimental scripts used during development are intentionally excluded from version control. The .gitignore file is configured to include only:

src/Reciept Cropper Module.py
Verification images used for testing
Future Improvements

## Potential enhancements:

Improve receipt edge detection reliability
Add automatic perspective correction
Add OCR integration pipeline
Create a command-line interface
Add automated unit tests
Package as a reusable Python library

This project is licensed under the MIT License.