from flask import Flask, request, render_template, Response, make_response
from os import environ, path as px
from rq_handler import process_req
from base64 import b64encode
from ocrworks import ocr_pdf
from hocrworks import hocr_transform
from webbrowser import open_new
from threading import Timer
from helper import img_debug


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

@app.route('/process', methods=['POST', 'GET'])
def api():
    file_bytes, filename = process_req(request)
    hocr = ocr_pdf(file_bytes)

    if img_debug:
        response = make_response(hocr)
        response.headers.set('Content-Type', 'image/jpeg')
        response.headers.set(
            'Content-Disposition', 'attachment', filename=filename + '.jpg')
        return response

    hocr = hocr_transform(hocr)
    return render_template('gui_response.html', data=hocr, filename=filename)


def open_browser():
    open_new("http://127.0.0.1:5001")

if __name__ == "__main__":
    Timer(1, open_browser).start()
    port = int(environ.get("PORT", 5001))
    app.run(host='0.0.0.0', port=port)
