from io import BytesIO
from math import radians
from typing import Tuple, Union
from os import listdir, environ, pathsep, path as px
from multiprocessing.dummy import Pool as ThreadPool

from PIL import Image
from pdf2image import convert_from_bytes
from cv2 import cvtColor, resize, threshold, dilate, erode, warpAffine, getRotationMatrix2D, medianBlur, adaptiveThreshold, GaussianBlur, bilateralFilter, filter2D
from cv2 import COLOR_BGR2RGB, COLOR_RGB2BGR, COLOR_BGR2GRAY, THRESH_OTSU, THRESH_BINARY, INTER_CUBIC, ADAPTIVE_THRESH_GAUSSIAN_C
from PyPDF2 import PdfMerger
from numpy import ndarray, cos, sin, array as nparray, ones, uint8
from deskew import determine_skew
from psutil import cpu_count
from tesserocr import PyTessBaseAPI


print(cpu_count())
pool = ThreadPool(cpu_count())

for x in listdir("./bin"):
    environ['PATH'] += pathsep + px.join(px.dirname(px.realpath(__file__)), "bin\\" + x)
environ['PATH'] += pathsep + px.join(px.dirname(px.realpath(__file__)), "bin")


tessenvirons = ["OMP_NUM_THREADS","OMP_THREAD_LIMIT","MKL_NUM_THREADS","NUMEXPR_NUM_THREADS","VECLIB_MAXIMUM_THREADS","OCR_THREADS"]
for x in tessenvirons:
    environ[x] = str(1)


def ocr_pdf(file_bytes):
    print ("convert to images")
    images = convert_from_bytes(file_bytes, dpi=300, thread_count=cpu_count())
    print ("enhance")
    results = pool.map(ocr_img, images)
    return results


def ocr_img(img):
    lang = "srp+srp_latn"
    tessdata_path = px.join(px.dirname(px.realpath(__file__)), "bin\\Tesseract-OCR\\tessdata")
    # return img2bytes(image)
    img = improve_image(img)
    with PyTessBaseAPI(lang=lang, path=tessdata_path) as api:
        api.SetImage(img)
        hocr = api.GetHOCRText(0)
    return hocr


def improve_image(image):
    img = convert_from_image_to_cv2(image)
    img = resize_img(img)
    img = cvtColor(img, COLOR_BGR2GRAY)
    img = erode_img(img)
    img = blur_img(img)
    img = rotate_img(img, determine_skew(img), (0, 0, 0))
    return convert_from_cv2_to_image(img)


def img2bytes(img):
    img_byte_arr = BytesIO()
    img.save(img_byte_arr, format='PNG')
    return img_byte_arr.getvalue()


def sharpen_img(img):
    sharpen_kernel = nparray([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
    sharpen = filter2D(img, -1, sharpen_kernel)
    return sharpen


def resize_img(img):
    #img = resize(img, (0, 0), fx=2, fy=2)
    img = resize(img, None, fx=1.2, fy=1.2, interpolation=INTER_CUBIC)
    return img


def erode_img(img):
    kernel = ones((1, 1), uint8)
    img = dilate(img, kernel, iterations=1)
    img = erode(img, kernel, iterations=1)
    return img


def blur_img(img):
    img = threshold(medianBlur(img, 3), 0, 255, THRESH_BINARY + THRESH_OTSU)[1]  
    # img = threshold(GaussianBlur(img, (5, 5), 0), 0, 255, THRESH_BINARY + THRESH_OTSU)[1]
    # img = threshold(bilateralFilter(img, 5, 75, 75), 0, 255, THRESH_BINARY + THRESH_OTSU)[1]
    # img = adaptiveThreshold(GaussianBlur(img, (5, 5), 0), 255, ADAPTIVE_THRESH_GAUSSIAN_C, THRESH_BINARY, 31, 2)
    # img = adaptiveThreshold(bilateralFilter(img, 9, 75, 75), 255, ADAPTIVE_THRESH_GAUSSIAN_C, THRESH_BINARY, 31, 2)
    #img = adaptiveThreshold(medianBlur(img, 3), 255, ADAPTIVE_THRESH_GAUSSIAN_C, THRESH_BINARY, 31, 2)
    # img = threshold(img, 0, 255, THRESH_BINARY + THRESH_OTSU)[1]
    return img


def rotate_img(image: ndarray, angle: float, background: Union[int, Tuple[int, int, int]]) -> ndarray:
    old_width, old_height = image.shape[:2]
    angle_radian = radians(angle)
    width = abs(sin(angle_radian) * old_height) + abs(cos(angle_radian) * old_width)
    height = abs(sin(angle_radian) * old_width) + abs(cos(angle_radian) * old_height)

    image_center = tuple(nparray(image.shape[1::-1]) / 2)
    rot_mat = getRotationMatrix2D(image_center, angle, 1.0)
    rot_mat[1, 2] += (width - old_width) / 2
    rot_mat[0, 2] += (height - old_height) / 2
    return warpAffine(image, rot_mat, (int(round(height)), int(round(width))), borderValue=background)


def convert_from_cv2_to_image(img: ndarray) -> Image:
    return Image.fromarray(cvtColor(img, COLOR_BGR2RGB))


def convert_from_image_to_cv2(img: Image) -> ndarray:
    return cvtColor(nparray(img), COLOR_RGB2BGR)


def merge_pages(pages):
    output = BytesIO()
    merger = PdfMerger()
    for page in pages:
        merger.append(BytesIO(page))
    merger.write(output)
    return output.getbuffer().tobytes()



