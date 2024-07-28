from PIL import Image
from ocrmypdf import ocr as pdf_ocr
from io import BytesIO
from cv2 import cvtColor, resize, threshold, THRESH_OTSU, THRESH_BINARY, erode
from cv2 import COLOR_BGR2RGB, COLOR_RGB2BGR, COLOR_BGR2GRAY
from numpy import array as nparray, ndarray
from os import environ, pathsep, path as px, listdir


for x in listdir("./bin"):
    environ['PATH'] += pathsep + px.join(px.dirname(px.realpath(__file__)), "bin\\" + x)
environ['PATH'] += pathsep + px.join(px.dirname(px.realpath(__file__)), "bin")



def ocr_pdf(file_bytes):
    bytesio = BytesIO(file_bytes)
    lang = "srp+srp_latn"
    output = BytesIO()

    kwargs = {}
    kwargs["language"] = lang
    kwargs["clean"] = True
    # kwargs["oversample"] = 300
    kwargs["deskew"] = True
    kwargs["force_ocr"] = True
    #kwargs["skip_text"] = True

    pdf_ocr(input_file=bytesio, output_file=output, optimize=3, **kwargs)
    return output.getbuffer().tobytes()


def convert_from_cv2_to_image(img: ndarray) -> Image:
    return Image.fromarray(cvtColor(img, COLOR_BGR2RGB))


def convert_from_image_to_cv2(img: Image) -> ndarray:
    return cvtColor(nparray(img), COLOR_RGB2BGR)


def improve_image(image):
    img = convert_from_image_to_cv2(image)
    img = resize(img, (0, 0), fx=2, fy=2)
    gry = cvtColor(img, COLOR_BGR2GRAY)
    erd = erode(gry, None, iterations=1)
    thr = threshold(erd, 0, 255, THRESH_BINARY + THRESH_OTSU)[1]
    return convert_from_cv2_to_image(thr)

