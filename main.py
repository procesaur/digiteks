from flask import Flask, request, render_template, Response
from os import environ, path as px
from rq_handler import process_req
from base64 import b64encode
from ocrworks import ocr_pdf
from hocrworks import hocr_transform


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

@app.route('/process', methods=['POST', 'GET'])
def api():
    file_bytes, filename = process_req(request)
    hocr = ocr_pdf(file_bytes)
    hocr = hocr_transform(hocr)
    return render_template('gui_response.html', data=hocr, filename=filename)
  

if __name__ == "__main__":
    port = int(environ.get("PORT", 5001))
    app.run(host='0.0.0.0', port=port)
