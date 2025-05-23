import argparse
from os import walk, path as px, makedirs
from sys import exit
from helper import read_file_bytes, cfg, js, css
from imageworks import pdf_to_images
from ocrworks import ocr_images
from flask import render_template, Flask


app = Flask(__name__)
app.config['SERVER_NAME'] = 'localhost:5000' 
app.config['APPLICATION_ROOT'] = '/'         
app.config['PREFERRED_URL_SCHEME'] = 'http'
output_types = ["hocr"] # ["html", "hocr"]
langs = ["srp+srp_latn+eng", "srp_latn+srp+eng", "srp", "srp_latn", "eng", "equ"]
image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff']


def list_files(directory):
    images = []
    pdfs = []

    for root, _, files in walk(directory):
        for file in files:
            if px.splitext(file)[1].lower() in image_extensions:
                images.append(px.join(root, file))
            elif px.splitext(file)[1].lower() == '.pdf':
                pdfs.append(px.join(root, file))
    return pdfs, images


def process_file(path, out_type, lang, pdf):
    file_bytes = read_file_bytes(path)
    if pdf:
        images_in_bytes = pdf_to_images(file_bytes)
    else:
        images_in_bytes = [file_bytes]
    
    hocrs = ocr_images(images_in_bytes, lang, just_result=True)
    with app.app_context():
        result = render_template('digiteks.html', lang=lang, html_conf=cfg["html_config"], images=[], js=js, css=css, filename=px.basename(path), hocr = "<br/>".join(hocrs))
    return result


def process_files(directory, pdfs, images, output, lang, name="procesirano"):
    procesirano_path = px.join(directory, name)

    def process_single(file_path, output, lang, pdf=False):
        relative_path = px.relpath(file_path, directory)
        new_dir = px.join(procesirano_path, px.dirname(relative_path))
        if not px.exists(new_dir):
            makedirs(new_dir)
        base_name = px.splitext(px.basename(file_path))[0]
        html_file_path = px.join(new_dir, base_name + ".html")

        if True:
            result = process_file(file_path, output, lang, pdf)
            if result:
                with open(html_file_path, 'w', encoding="utf-8") as f:
                    f.write(result)
        else:
           print(f"Neuspešno za {file_path}")

    for path in pdfs:
        process_single(path, output, lang, True)

    for path in images:
        process_single(path, output, lang, False)


def main():
    parser = argparse.ArgumentParser(description="")
    parser.add_argument('dir', type=str, help="<putanja_do_direktorijuma>")
    parser.add_argument('-j', '--jezik', type=str, help=f"<ocr_jezik> {langs}", default=langs[0])
    parser.add_argument('-i', '--izlaz', type=str, help=f"<tip_izlaza> {output_types}", default=output_types[0])
  
    args = parser.parse_args()
    directory = args.dir
    lang = args.jezik
    output = args.izlaz

    if not px.isdir(directory):
        print("Direktorijum ne postoji ili nije dostupan.")
        exit(1)

    if lang not in langs:
        print(f"Pogrešan izbor jezika. Mogući izbor: {langs}")
        exit(1)

    if output not in output_types:
        print(f"Pogrešan izbor izlazog formata. Mogući izbor: {output_types}")
        exit(1)

    pdfs, images = list_files(directory)
    if pdfs or images:
        process_files(directory, pdfs, images, output, lang)
    else:
        print("Direktorijum ne sadrži obradive datoteke.")
        exit(1)

if __name__ == "__main__":
    main()
