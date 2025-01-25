from io import BytesIO
from os import listdir, environ, pathsep, path as px
from json import dumps

from pdf2image import convert_from_bytes
from pypdf import PdfMerger
from tesserocr import PyTessBaseAPI
from imageworks import improve_image, img2bytes, bytes2img

from helper import isWindows, cpus, chunkify, pool
from hocrworks import hocr_transform


if isWindows():
    binpath = px.join(px.dirname(px.realpath(__file__)), "bin\\")
    for x in listdir(binpath):
        environ['PATH'] += pathsep + px.join(px.dirname(px.realpath(__file__)), "bin\\" + x)
    environ['PATH'] += pathsep + px.join(px.dirname(px.realpath(__file__)), "bin")

    tessenvirons = ["OMP_NUM_THREADS","OMP_THREAD_LIMIT","MKL_NUM_THREADS","NUMEXPR_NUM_THREADS","VECLIB_MAXIMUM_THREADS","OCR_THREADS"]
    for x in tessenvirons:
        environ[x] = str(1)

def pdf_to_images(file_bytes, img_down=False):
    images = convert_from_bytes(file_bytes, dpi=300, thread_count=cpus)
    if img_down:
        images_improved = pool.map(improve_image, images)
        return [(img2bytes(a), b) for a, b in zip(images, images_improved)]
    return [img2bytes(a) for a in images]

def ocr_images(images,  lang="srp+srp_latn"):
    for chunk in chunkify(images):
        results = pool.map(ocr_img, ((img, lang) for img in chunk))
        for result in results:
            yield f"data: {dumps({'html': hocr_transform(result)})}\n\n"

def ocr_img(profile):
    img, lang = profile
    img = (improve_image(bytes2img(img)))
    tessdata_path = px.join(px.dirname(px.realpath(__file__)), "bin/Tesseract-OCR/tessdata")
    with PyTessBaseAPI(lang=lang, path=tessdata_path) as api:
        api.SetImage(bytes2img(img))
        hocr = api.GetHOCRText(0)
    return hocr

def merge_pages(pages):
    output = BytesIO()
    merger = PdfMerger()
    for page in pages:
        merger.append(BytesIO(page))
    merger.write(output)
    return output.getbuffer().tobytes()