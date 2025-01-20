from flask import Flask, request, render_template, send_file, render_template_string
from os import environ, path as px
from rq_handler import process_req, process_req_glasnik
from ocrworks import ocr_pdf, ocr_zip
from hocrworks import hocr_transform
from webbrowser import open_new
from threading import Timer
from lmworks import fill_mask, visualize
from helper import zip_bytes_string, image_zip_to_html, do


app = Flask(__name__)
app.config["DEBUG"] = False


@app.route('/')
def home():
    return render_template('ui.html')

@app.route('/help')
def about():
    return render_template('help.html', cover=px.join('static', 'cover.png'))

@app.route('/img')
def img():
    return render_template('img.html', cover=px.join('static', 'cover.png'))

@app.route('/load')
def load():
    return render_template('img.html', cover=px.join('static', 'load.gif'))

@app.route('/process/<lang>', methods=['POST', 'GET'])
def api(lang):
    file_bytes, filename = process_req(request)
    if filename.endswith(".pdf"):
        hocr = do(ocr_pdf, file_bytes)
    else:
        hocr = ocr_zip(file_bytes, lang=lang)  
    hocr = hocr_transform(hocr)
    return render_template('gui_response.html', data=hocr, filename=filename)

@app.route('/imgdown', methods=['POST', 'GET'])
def imgdown():
    file_bytes, filename = process_req(request)
    images_in_bytes = ocr_pdf(file_bytes, img_down=True)
    improved_images_in_bytes = {f"image{i}_enhanced.png": img[1] for i, img in enumerate(images_in_bytes)}
    images_in_bytes = {f"image{i}_.png": img[0] for i, img in enumerate(images_in_bytes)}
    images_in_bytes.update(improved_images_in_bytes)
    return send_file(
        zip_bytes_string(images_in_bytes),
        mimetype='application/zip',
        as_attachment=True,
        download_name=filename + '_images.zip'
    )

@app.route('/showzip', methods=['POST'])
def showzip():
    file = request.files['file']
    if file and file.filename.endswith('.zip'):
        images = image_zip_to_html(file, encode=True)
        return render_template("images.html", images=images)
    return 'Invalid file'


@app.route('/glasnik', methods=['GET','POST'])
def glasnik():
    try:
        input = process_req_glasnik(request)
    except:
        input = ""
    if input:
        output = [x for x in fill_mask(input) if x["token"]>4]
    else:
        output = []
    return render_template('inference.html', input=input, output=output)


@app.route('/glasnik2', methods=['GET','POST'])
def glasnik2():
    try:
        input = process_req_glasnik(request)
    except:
        input = ""
    if input:
        vals, tokens = visualize(input)
    else:
        vals, tokens = [], []
    return render_template('visualize.html', input=input, vals=vals, tokens=tokens)


def open_browser():
    open_new("http://127.0.0.1:5001")

if __name__ == "__main__":
    Timer(1, open_browser).start()
    port = int(environ.get("PORT", 5001))
    app.run(host='0.0.0.0', port=port)
