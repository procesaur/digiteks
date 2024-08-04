from io import BytesIO
from os import listdir, environ, pathsep, path as px
from multiprocessing.dummy import Pool as ThreadPool

from pdf2image import convert_from_bytes
from PyPDF2 import PdfMerger
from psutil import cpu_count
from tesserocr import PyTessBaseAPI
from imageworks import improve_image, img2bytes


print(cpu_count())
pool = ThreadPool(cpu_count())

binpath = px.join(px.dirname(px.realpath(__file__)), "bin\\")
for x in listdir(binpath):
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
    print(len(results))
    return results


def ocr_img(img):
    lang = "srp+srp_latn"
    tessdata_path = px.join(px.dirname(px.realpath(__file__)), "bin\\Tesseract-OCR\\tessdata")
    img = improve_image(img)
    #return img2bytes(img)

    with PyTessBaseAPI(lang=lang, path=tessdata_path) as api:
        api.SetImage(img)
        hocr = api.GetHOCRText(0)
    return hocr


def merge_pages(pages):
    output = BytesIO()
    merger = PdfMerger()
    for page in pages:
        merger.append(BytesIO(page))
    merger.write(output)
    return output.getbuffer().tobytes()