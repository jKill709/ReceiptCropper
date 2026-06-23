import os
from pathlib import Path
from PIL import Image, ImageDraw
import pytest
import sys
from pathlib import Path

sys.path.append(
    str(Path(__file__).parent.parent / "src")
)

import receipt_cropper_module


# ---------------------------------------------------------
# Helpers
# ---------------------------------------------------------

def create_blank_image(width=100, height=100):
    """
    Create a completely white image.
    """
    return Image.new("RGB", (width, height), "white")


def create_receipt_image(width=400, height=300):
    """
    Create a fake scanned page containing two black rectangles
    representing receipts.
    """

    img = Image.new("RGB", (width, height), "white")

    draw = ImageDraw.Draw(img)

    # Receipt 1
    draw.rectangle(
        (20, 20, 150, 250),
        fill="black"
    )

    # Receipt 2
    draw.rectangle(
        (220, 20, 350, 220),
        fill="black"
    )

    return img


# ---------------------------------------------------------
# _get_column_bits
# ---------------------------------------------------------

def test_get_column_bits_blank_image():

    img = create_blank_image()

    result = receipt_cropper_module._get_column_bits(img)

    assert len(result) == img.width
    assert all(bit == 0 for bit in result)



def test_get_column_bits_detects_content():

    img = create_blank_image(10, 10)

    draw = ImageDraw.Draw(img)

    draw.rectangle(
        (5,0,5,9),
        fill="black"
    )

    result = receipt_cropper_module._get_column_bits(img)

    assert result[5] == 1
    assert sum(result) == 1



# ---------------------------------------------------------
# _get_row_bits
# ---------------------------------------------------------

def test_get_row_bits_detects_horizontal_content():

    img = create_blank_image(20,20)

    draw = ImageDraw.Draw(img)

    draw.rectangle(
        (0,10,19,10),
        fill="black"
    )

    result = receipt_cropper_module._get_row_bits(
        img,
        0,
        20
    )

    assert result[10] == 1



# ---------------------------------------------------------
# _get_data
# ---------------------------------------------------------

def test_get_data_extracts_regions():

    bits = [
        0,
        1,
        1,
        1,
        0,
        1,
        1,
        0
    ]

    result = receipt_cropper_module._get_data(bits)


    assert result == [
        (1,3,3),
        (5,6,2)
    ]



def test_get_data_handles_end_region():

    bits = [0,1,1]

    result = receipt_cropper_module._get_data(bits)

    assert result == [
        (1,2,2)
    ]



# ---------------------------------------------------------
# smoothing
# ---------------------------------------------------------

def test_smooth_bits_connects_nearby_regions():

    bits = [
        True,
        True,
        False,
        True,
        True
    ]

    data = receipt_cropper_module._get_data(bits)

    changes = receipt_cropper_module._smooth_Bits(
        bits,
        data,
        len(bits),
        2,
        1
    )

    assert changes > 0



# ---------------------------------------------------------
# x bounds
# ---------------------------------------------------------

def test_get_xBounds_detects_receipts():

    img = create_receipt_image()

    bits = receipt_cropper_module._get_column_bits(img)

    data = receipt_cropper_module._get_data(bits)

    result = receipt_cropper_module._get_xBounds(
        bits,
        data,
        img.width
    )

    assert len(result) == 2



# ---------------------------------------------------------
# y bounds
# ---------------------------------------------------------

def test_get_yBound_detects_bottom():

    img = create_receipt_image()

    rows = receipt_cropper_module._get_row_bits(
        img,
        20,
        150
    )

    data = receipt_cropper_module._get_data(rows)

    result = receipt_cropper_module._get_yBound(
        rows,
        data,
        img.height
    )

    assert result > 200



# ---------------------------------------------------------
# full crop pipeline
# ---------------------------------------------------------

def test_crop_scan_returns_multiple_receipts():

    img = create_receipt_image()

    results = receipt_cropper_module._crop_Scan(img)


    assert len(results) == 2

    for receipt in results:
        assert isinstance(receipt, Image.Image)



# ---------------------------------------------------------
# temp numbering
# ---------------------------------------------------------

def test_get_next_temp_number(tmp_path):

    (tmp_path / "IMG0.jpg").touch()
    (tmp_path / "IMG1.jpg").touch()
    (tmp_path / "other.jpg").touch()


    result = receipt_cropper_module._get_next_temp_number(
        tmp_path
    )


    assert result == 2



def test_get_next_temp_number_empty(tmp_path):

    assert (
        receipt_cropper_module._get_next_temp_number(tmp_path)
        == 0
    )



# ---------------------------------------------------------
# OCR output
# ---------------------------------------------------------

def test_create_text_file(tmp_path):

    file = tmp_path / "test.txt"

    receipt_cropper_module.create_text_file(
        file,
        "hello world"
    )


    assert file.exists()

    assert file.read_text() == "hello world"



# ---------------------------------------------------------
# tesseract configuration
# ---------------------------------------------------------

def test_configure_tesseract_from_path(monkeypatch):

    monkeypatch.setattr(
        receipt_cropper_module.shutil,
        "which",
        lambda x: "/fake/tesseract"
    )


    result = receipt_cropper_module.configure_tesseract()


    assert result == "/fake/tesseract"



def test_configure_tesseract_not_found(monkeypatch):

    monkeypatch.setattr(
        receipt_cropper_module.shutil,
        "which",
        lambda x: None
    )


    monkeypatch.setattr(
        Path,
        "exists",
        lambda self: False
    )


    with pytest.raises(RuntimeError):

        receipt_cropper_module.configure_tesseract()



# ---------------------------------------------------------
# OCR integration mock
# ---------------------------------------------------------

def test_process_scan_with_mock_ocr(
    tmp_path,
    monkeypatch
):

    img = create_receipt_image()

    input_file = tmp_path / "scan.jpg"

    img.save(input_file)


    output = []


    monkeypatch.setattr(
        receipt_cropper_module.pytesseract,
        "image_to_string",
        lambda img: "receipt text"
    )


    monkeypatch.chdir(tmp_path)


    receipt_cropper_module.proccess_Scan(
        input_file
    )


    files = list(tmp_path.iterdir())


    assert any(
        f.suffix == ".jpg"
        for f in files
    )