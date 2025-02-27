from io import BytesIO
from os import listdir, environ, pathsep, path as px
from json import dumps

from pypdf import PdfMerger
from tesserocr import PyTessBaseAPI

from imageworks import improve_image, bytes2img
from helper import do, isWindows, chunkify, pool, b64encode
from hocrworks import hocr_transform


if isWindows():
    binpath = px.join(px.dirname(px.realpath(__file__)), "bin\\")
    for x in listdir(binpath):
        environ['PATH'] += pathsep + px.join(px.dirname(px.realpath(__file__)), "bin\\" + x)
    environ['PATH'] += pathsep + px.join(px.dirname(px.realpath(__file__)), "bin")

    tessenvirons = ["OMP_NUM_THREADS","OMP_THREAD_LIMIT","MKL_NUM_THREADS","NUMEXPR_NUM_THREADS","VECLIB_MAXIMUM_THREADS","OCR_THREADS"]
    for x in tessenvirons:
        environ[x] = str(1)


def ocr_images(images,  lang="srp+srp_latn"):  
    for chunk in chunkify(images):        
        results = pool.map(ocr_img, ((img, lang) for img in chunk))
        for result in results:
            yield f"data: {dumps({'html': hocr_transform(result[0], b64encode(result[1]).decode('utf-8'))})}\n\n"


def ocr_img(profile):
    img, lang = profile
    img = do(improve_image, bytes2img(img))

    def ocr(img):
        tessdata_path = px.join(px.dirname(px.realpath(__file__)), "bin/Tesseract-OCR/tessdata")
        with PyTessBaseAPI(lang=lang, path=tessdata_path, psm=1) as api:
            api.SetImage(bytes2img(img))
            hocr = api.GetHOCRText(0)
        return hocr, img
    return do(ocr, img)


def merge_pages(pages):
    output = BytesIO()
    merger = PdfMerger()
    for page in pages:
        merger.append(BytesIO(page))
    merger.write(output)
    return output.getbuffer().tobytes()