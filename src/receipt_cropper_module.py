from PIL import Image
import pytesseract
import os
from pathlib import Path
import shutil


def _get_column_bits(im, threshold=110):
    """
    Convert an image into a binary representation of its columns.

    Each column is classified as:
        0 - completely blank (all pixels above threshold)
        1 - contains image content

    This creates a simple map used to detect the horizontal boundaries
    between scanned documents.
    """
    gray_im = im.convert("L")

    column_bits = []

    for x in range(gray_im.width):
        column_pixels = [gray_im.getpixel((x, y)) for y in range(gray_im.height)]

        # A column is considered empty if every pixel is bright enough
        if all(pixel >= threshold for pixel in column_pixels):
            column_bits.append(0)
        else:
            column_bits.append(1)

    return column_bits


def _get_row_bits(im, xStart, xEnd, threshold=110):
    """
    Convert a horizontal section of an image into a binary row map.

    Only the supplied x-range is analyzed. This allows each detected
    receipt region to have its own vertical boundary detection.
    """
    gray_im = im.convert("L")

    row_bits = []

    for y in range(gray_im.height):
        row_pixels = [gray_im.getpixel((x, y)) for x in range(xStart, xEnd)]

        # A row is considered empty if all pixels are above threshold
        if all(pixel >= threshold for pixel in row_pixels):
            row_bits.append(0)
        else:
            row_bits.append(1)

    return row_bits


def _get_data(arr):
    """
    Convert a binary array into a list of continuous regions.

    Returns:
        List of tuples containing:
        (start index, end index, region length)

    Regions are sorted from largest to smallest, allowing the largest
    detected objects to be processed first.
    """
    result = []
    start = None

    for i, val in enumerate(arr):
        if val:
            if start is None:
                start = i

        elif start is not None:
            result.append((start, i - 1, i - start))
            start = None

    # Handle a region that extends to the end of the array
    if start is not None:
        result.append((start, len(arr) - 1, len(arr) - start))

    return sorted(result, key=lambda x: x[2], reverse=True)


def _smooth_Bits(column_Bits, column_Data, maxIndex, reach, growthSize):
    """
    Expand detected regions to bridge gaps between characters or rows of characters.

    Returns:
        Number of changes made during this pass.
    """
    changes = 0

    for blockStart, blockEnd, blockLength in column_Data:

        # Only process large enough regions
        if blockLength > growthSize:

            # Extend region forward if another nearby region exists
            if blockEnd < (maxIndex - 1):
                if blockEnd + reach >= maxIndex:
                    changes += 1

                    for j in range(blockEnd + 1, maxIndex):
                        column_Bits[j] = True

                elif any(column_Bits[blockEnd + 1:blockEnd + reach]):
                    changes += 1

                    for j in range(
                        blockEnd + 1,
                        blockEnd + reach + 1 if blockEnd + reach + 1 < maxIndex else maxIndex
                    ):
                        column_Bits[j] = True

            # Extend region backward if another nearby region exists
            if blockStart > 0:
                if blockStart <= reach:
                    changes += 1

                    for j in range(0, blockStart):
                        column_Bits[j] = True

                elif any(column_Bits[blockStart - 1:blockStart - reach]):
                    changes += 1

                    for j in range(
                        blockStart - 1,
                        blockStart - reach - 1 if blockStart - reach - 1 > 0 else 0
                    ):
                        column_Bits[j] = True

    return changes


def _get_xBounds(column_Bits, column_Data, imWidth):
    """
    Determine the horizontal crop boundaries for individual receipts.

    The smoothing step attempts to merge fragmented regions before
    selecting large enough areas as receipt candidates.
    """
    result = []

    while _smooth_Bits(column_Bits, column_Data, imWidth, 25, 30) > 0:
        column_Data = _get_data(column_Bits)

    for start, end, length in column_Data:

        # Ignore small regions that are unlikely to be receipts
        if length > 225:

            # Add padding around detected receipt boundaries
            start = 0 if start < 30 else start - 30
            end = imWidth if end + 30 > imWidth else end + 30

            result.append((start, end))

    return result


def _get_yBound(row_Bits, row_Data, imHeight):
    """
    Determine the vertical boundary of a receipt.

    Returns the bottom-most detected content boundary.
    """
    result = 1

    while _smooth_Bits(row_Bits, row_Data, imHeight, 50, 20) > 0:
        row_Data = _get_data(row_Bits)

    for start, end, length in row_Data:

        if length > 20:
            end = imHeight if end + 30 > imHeight else end + 30

            if end > result:
                result = end

    return result


def _get_next_temp_number(directory):
    """
    Find the next available image number for generated receipt files.
    """
    files = os.listdir(directory)

    temp_files = [
        file for file in files
        if file.startswith('IMG') and file.endswith('.jpg')
    ]

    temp_numbers = [
        int(file[3:-4])
        for file in temp_files
    ]

    return max(temp_numbers) + 1 if temp_numbers else 0


def _crop_image(im, x_start, x_end, yEnd):
    """
    Crop an image using detected receipt boundaries.
    """
    print(f"Cropping IMG {index} at x:({xStart}, {xEnd}), y:(0, {yEnd})")

    return im.crop((x_start, 0, x_end, yEnd))


def _crop_Scan(im):
    """
    Split a scanned image containing multiple receipts into individual images.

    The scan is analyzed in two stages:
        1. Detect receipt columns.
        2. Detect receipt height within each column.

    Returns:
        List of cropped PIL Image objects.
    """
    results = []

    # Detect horizontal receipt regions
    column_Bits = _get_column_bits(im)
    column_Data = _get_data(column_Bits)
    xCoordinates = _get_xBounds(column_Bits, column_Data, im.width)

    # Detect vertical receipt boundaries for each region
    for xStart, xEnd in xCoordinates:
        row_Bits = _get_row_bits(im, xStart, xEnd)
        row_Data = _get_data(row_Bits)

        yEnd = _get_yBound(row_Bits, row_Data, im.height)

        results.append(
            im.crop((xStart, 0, xEnd, yEnd))
        )

    return results


def create_text_file(file_name, file_contents):
    """
    Write OCR output to a text file.
    """
    with open(file_name, "w") as f:
        f.write(file_contents)


def proccess_Scan(fileName, output_dir):
    """
    Process a single scan file.

    The image is cropped into individual receipts, saved, and passed
    through OCR to extract text.
    """
    im = Image.open(fileName)

    results = _crop_Scan(im)

    for i, rct in enumerate(results, _get_next_temp_number(output_dir)):
        rct.save(f"IMG {i}.jpg")

    create_text_file(
        f"IMG{i}.txt",
        pytesseract.image_to_string(i)
    )

def configure_tesseract():
    """
    Locate and configure the Tesseract OCR executable.
    """

    # First: check if tesseract is already in PATH
    tesseract_path = shutil.which("tesseract")

    if tesseract_path:
        pytesseract.pytesseract.tesseract_cmd = tesseract_path
        return tesseract_path


    # Second: check common Windows install locations
    common_paths = [
        Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe"),
        Path(r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"),
    ]

    for path in common_paths:
        if path.exists():
            pytesseract.pytesseract.tesseract_cmd = str(path)
            return str(path)


    raise RuntimeError(
        "Tesseract OCR executable not found. "
        "Install Tesseract or add it to your system PATH."
    )


#################################################################################
#                                Main                                           #
#################################################################################

if __name__ == '__main__':

    # Store all cropped receipt images before saving/OCR processing
    img_Images = []

    # Configure Tesseract OCR executable location
    tesseract = configure_tesseract()
    print(f"Using Tesseract: {tesseract}")
    #pytesseract.pytesseract.tesseract_cmd = (
    #    r'X:\Your\Folder\Tesseract-OCR\tesseract'
    #

    # Change to directory containing new scans
    PROJECT_ROOT = Path(__file__).parent.parent
    ARCHIVE_DIR = os.path.join(PROJECT_ROOT, "verification images", "Archive")
    CROPPED_DIR = os.path.join(PROJECT_ROOT, "verification images", "Cropped")
    SCANNED_DIR = os.path.join(PROJECT_ROOT, "verification images", "Scanned")
    TEXT_DIR = os.path.join(PROJECT_ROOT, "verification images", "Text")
    os.chdir(SCANNED_DIR)

    # Ignore previously generated IMG files
    jpeg_files = [
        f for f in os.listdir()
        if f.endswith('.jpg') and not f.startswith("IMG")
    ]
    
    # Process each scanned page
    for jpeg in jpeg_files:

        print(jpeg)

        im = Image.open(jpeg)

        # Extract individual receipts
        img_Images.extend(_crop_Scan(im))

        # Archive original scan
        im.save(os.path.join(ARCHIVE_DIR, jpeg))

        os.remove(jpeg)

    # Save cropped receipts and perform OCR
    for i, rct in enumerate(img_Images, _get_next_temp_number(CROPPED_DIR)):
        rct.save(os.path.join(CROPPED_DIR, f"IMG{i}.jpg"))

        create_text_file(os.path.join(TEXT_DIR, f"IMG{i}.txt"), pytesseract.image_to_string(rct))

    print(os.getcwd())
    print(f"Scanned Images:  {len(jpeg_files)}")
    print(f"Receipts:        {len(img_Images)}")
    print("........Complete.........")

    input("...Press Enter to Exit...")