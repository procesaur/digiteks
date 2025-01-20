from io import BytesIO
from os import listdir, environ, pathsep, path as px
from multiprocessing.dummy import Pool as ThreadPool

from pdf2image import convert_from_bytes
from pypdf import PdfMerger
from psutil import cpu_count
from tesserocr import PyTessBaseAPI
from imageworks import improve_image, img2bytes, bytes2img

from helper import isWindows, image_zip_to_html, do


print(cpu_count())
pool = ThreadPool(cpu_count())

if isWindows():
    binpath = px.join(px.dirname(px.realpath(__file__)), "bin\\")
    for x in listdir(binpath):
        environ['PATH'] += pathsep + px.join(px.dirname(px.realpath(__file__)), "bin\\" + x)
    environ['PATH'] += pathsep + px.join(px.dirname(px.realpath(__file__)), "bin")

    tessenvirons = ["OMP_NUM_THREADS","OMP_THREAD_LIMIT","MKL_NUM_THREADS","NUMEXPR_NUM_THREADS","VECLIB_MAXIMUM_THREADS","OCR_THREADS"]
    for x in tessenvirons:
        environ[x] = str(1)


def ocr_pdf(file_bytes, img_down=False, lang="srp+srp_latn"):
    images = convert_from_bytes(file_bytes, dpi=300, thread_count=cpu_count())
    images = ((x, lang, img_down) for x in images)
    results = pool.map(ocr_img, images)
    return results

def ocr_zip(file_bytes, img_down=False, lang="srp+srp_latn"):
    images = image_zip_to_html(file_bytes)
    images = ((bytes2img(x), lang, img_down) for x in images)
    results = pool.map(ocr_img, images)
    return results


def ocr_img(profile):
    img, lang, img_down = profile
    tessdata_path = px.join(px.dirname(px.realpath(__file__)), "bin/Tesseract-OCR/tessdata")
    improved = improve_image(img)
    if img_down:
        return img2bytes(img), img2bytes(improved)
    with PyTessBaseAPI(lang=lang, path=tessdata_path) as api:
        api.SetImage(improved)
        hocr = api.GetHOCRText(0)
    return hocr


def merge_pages(pages):
    output = BytesIO()
    merger = PdfMerger()
    for page in pages:
        merger.append(BytesIO(page))
    merger.write(output)
    return output.getbuffer().tobytes()