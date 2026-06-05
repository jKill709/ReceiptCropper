from PIL import Image
import pytesseract
import os

def _get_column_bits(im, threshold=110):
    # Convert the image to grayscale
    gray_im = im.convert("L")
    # Initialize the list to store the column bits
    column_bits = []
    # Iterate through each column of the image
    for x in range(gray_im.width):
        # Get all the pixels in the current column
        column_pixels = [gray_im.getpixel((x, y)) for y in range(gray_im.height)]
        # Check if all the pixels in the column are above the threshold
        if all(pixel >= threshold for pixel in column_pixels):
            column_bits.append(0)
        else:
            column_bits.append(1)
    return column_bits

def _get_row_bits(im, xStart, xEnd, threshold=110):
    # Convert the image to grayscale
    gray_im = im.convert("L")
    # Initialize the list to store the row bits
    row_bits = []
    # Iterate through each row of the image
    for y in range(gray_im.height):
        # Get all the pixels in the current row
        row_pixels = [gray_im.getpixel((x, y)) for x in range(xStart, xEnd)]
        # Check if all the pixels in the row are above the threshold
        if all(pixel >= threshold for pixel in row_pixels):
            row_bits.append(0)
        else:
            row_bits.append(1)
    return row_bits

def _get_data(arr):
    result = []
    start = None
    for i, val in enumerate(arr):
        if val:
            if start is None:
                start = i
        elif start is not None:
            result.append((start, i-1, (i-start)))
            start = None
    if start is not None:
        result.append((start, len(arr)-1, (len(arr) - start)))
    return sorted(result, key=lambda x: x[2], reverse=True)

def _smooth_Bits(column_Bits, column_Data, maxIndex, reach, growthSize):
    changes = 0
    for blockStart, blockEnd, blockLength in column_Data:
        if blockLength > growthSize:
            #if any(column_Bits[blockEnd+1: blockEnd+reach]):
            if blockEnd < (maxIndex - 1):
                if blockEnd + reach >= maxIndex:
                    changes += 1

                    for j in range(blockEnd+1, maxIndex):
                        column_Bits[j] = True
                elif any(column_Bits[blockEnd+1: blockEnd+reach]):
                        changes += 1
                        for j in range(blockEnd+1, blockEnd+reach+1 if blockEnd+reach+1 < maxIndex else maxIndex):
                            column_Bits[j] = True
            if blockStart > 0:
                if blockStart <= reach:
                    changes +=1
                    for j in range(0, blockStart):
                        column_Bits[j] = True
                elif any(column_Bits[blockStart-1: blockStart-reach]):
                    changes += 1
                    for j in range(blockStart-1, blockStart-reach-1 if blockStart-reach-1 > 0 else 0):
                        column_Bits[j] = True
    return changes

def _get_xBounds(column_Bits, column_Data, imWidth):
    result = []

    while _smooth_Bits(column_Bits, column_Data, imWidth, 25, 30) > 0:
        column_Data = _get_data(column_Bits)
    
    for start, end, length in column_Data:
        if length > 225:
            if start < 30:
                start = 0
            else:
                start -= 30
            if end + 30 > imWidth:
                end = imWidth
            else:
                end += 30
            result.append((start, end))
    return result

def _get_yBound(row_Bits, row_Data, imHeight):
    result = 1
    while _smooth_Bits(row_Bits, row_Data, imHeight, 50, 20) > 0:
        row_Data = _get_data(row_Bits)

    for start, end, length in row_Data:
        if length > 20:
            if end + 30 > imHeight:
                end = imHeight
            else:
                end += 30
            if end > result:
                result = end
    return result

def _get_next_temp_number():
    files = os.listdir()
    temp_files = [file for file in files if file.startswith('IMG') and file.endswith('.jpg')]
    temp_numbers = [int(file[3:-4]) for file in temp_files]
    if temp_numbers:
        next_number = max(temp_numbers) + 1
    else:
        next_number = 0
    return next_number

def _crop_image(im, x_start, x_end, yEnd):
    print(f"Cropping IMG {index} at x:({xStart}, {xEnd}), y:(0, {yEnd})")
    return im.crop((x_start, 0, x_end, yEnd))

# Accepts a pil.image containing a raw scan and returns a list of pil.images containing cropped reciepts
def _crop_Scan(im):
    results = []
    
    # Proccess X Data
    column_Bits = _get_column_bits(im)
    column_Data = _get_data(column_Bits)
    xCoordinates = _get_xBounds(column_Bits, column_Data, im.width)

    # Process Y Data
    for i, (xStart, xEnd) in enumerate(xCoordinates):
        row_Bits = _get_row_bits(im, xStart, xEnd)
        row_Data = _get_data(row_Bits)
        yEnd = _get_yBound(row_Bits, row_Data, im.height)
        results.append(im.crop((xStart, 0, xEnd, yEnd)))
    return results

def create_text_file(file_name, file_contents):
    with open(file_name, "w") as f:
        f.write(file_contents)
        
# Accepts a string containing a file name in the current directory and processes it
def proccess_Scan(fileName):
    results = []
    im = Image.open(fileName)
    results = _crop_Scan(im)
    for i, rct in enumerate(results, _get_next_temp_number()):
        rct.save(f"IMG {i}.jpg")
    im.save(os.path.join(os.path.join(os.path.abspath(os.path.join(os.getcwd(), os.pardir)), "Raw Scans"), jpeg))
    os.remove(jpeg)
    
    # OCR Setup and Console Print
    pytesseract.pytesseract.tesseract_cmd = r'C:\Users\jerem\AppData\Local\Programs\Tesseract-OCR\tesseract'
    create_text_file(f"IMG{index}.txt", pytesseract.image_to_string(f"IMG{index}.jpg"))
    

#################################################################################
#                                Main                                           #
#################################################################################
if __name__ == '__main__':
    # list to store cropped images
    img_Images = []
    # set the path to tesseract OCR executable
    pytesseract.pytesseract.tesseract_cmd = r'C:\Users\jerem\AppData\Local\Programs\Tesseract-OCR\tesseract'

    # change directory and list all .jpg files in the folder that does not start with "IMG"
    os.chdir(r"C:\Users\jerem\OneDrive\Documents\Income\dat\Reciepts\New")
    jpeg_files = [f for f in os.listdir() if f.endswith('.jpg') and not f.startswith("IMG")]

    # loop through all the jpeg files
    for jpeg in jpeg_files:
        # print the name of the current jpeg file being processed
        print(jpeg)
    
        # open the image file
        im = Image.open(jpeg)
        img_Images.extend(_crop_Scan(im))
        im.save(os.path.join(os.path.join(os.path.abspath(os.path.join(os.getcwd(), os.pardir)), "Raw Scans"), jpeg))
        os.remove(jpeg)

    # loop through the cropped images
    for i, rct in enumerate(img_Images, _get_next_temp_number()):
        # save the cropped image and the orc output
        rct.save(f"IMG{i}.jpg")
        create_text_file(f"IMG{i}.txt", pytesseract.image_to_string(f"IMG{i}.jpg"))

    # print the exit data
    print(os.getcwd())
    print(f"Scanned Images:  {len(jpeg_files)}")
    print(f"Reciepts:        {len(img_Images)}")
    print("........Complete.........")
    input("...Press Enter to Exit...")

