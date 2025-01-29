from flask import Flask, request, render_template, send_file, Response, jsonify, send_from_directory
from os import environ, path as px
from rq_handler import process_req, process_req_glasnik
from ocrworks import pdf_to_images, ocr_images
from webbrowser import open_new
from threading import Timer
from lmworks import lm_inspect
from helper import zip_bytes_string, image_zip_to_images, do, encode_images, decode_images
import uuid


app = Flask(__name__)
app.config["DEBUG"] = False
session_images = {}


@app.route('/')
def home():
    return render_template('ui.html')

@app.route('/help')
def about():
    return render_template('help.html', cover=px.join('static', 'cover.png'))

@app.route('/img')
def img():
    return render_template('img.html', cover=px.join('static', 'cover.png'))

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(px.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/load')
def load():
    return render_template('img.html', cover=px.join('static', 'load.gif'))

@app.route('/process/<lang>', methods=['POST', 'GET'])
def ini(lang):
    file_bytes, filename = process_req(request)
    if filename.endswith(".pdf"):
        images = pdf_to_images(file_bytes)
    else:
        images = image_zip_to_images(file_bytes)
    return render_template('gui_response_new.html', lang=lang, images=encode_images(images), filename=filename)

@app.route('/imgdown', methods=['POST', 'GET'])
def imgdown():
    file_bytes, filename = process_req(request)
    images_in_bytes = pdf_to_images(file_bytes, img_down=True)
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
        images = image_zip_to_images(file)
        images = encode_images(images)
        return render_template("images.html", images=images)
    return 'Invalid file'

@app.route('/ocr/<lang>', methods=['POST'])
def api(lang):
    session_id = str(uuid.uuid4())
    image_data = request.json.get('images') 
    session_images[session_id] = decode_images(image_data), lang
    return jsonify({'status': 'OCR started', 'session_id': session_id})

@app.route('/stream/<session_id>')
def stream(session_id):
    decoded_images, lang = session_images[session_id]
    return Response(ocr_images(decoded_images, lang), content_type='text/event-stream')

@app.route('/posthere', methods=['POST'])
def posthtml():
    file = request.files['file']
    if file and file.filename.endswith('.html'):
        content = file.read().decode('utf-8')
        return Response(content, mimetype='text/html')
    return 'Invalid file'


#@app.route('/glasnik', methods=['GET','POST'])
#def glasnik():
   # try:
    #    input = process_req_glasnik(request)
    #except:
    #    input = ""
    #if input:
    #    output = [x for x in fill_mask(input) if x["token"]>4]
    #else:
    #    output = []
    #return render_template('inference.html', input=input, output=output)

@app.route('/glasnik2', methods=['GET','POST'])
def glasnik2():
    mp = 800
    try:
        input, mp = process_req_glasnik(request, fields=["text", "mp"])
    except:
        input, vals, tokens = "", [], []
    vals, tokens = lm_inspect(input, max_perplexity=int(mp))
    return render_template('visualize.html', input=input, vals=[1-x for x in vals], tokens=tokens, mp=mp)

def open_browser():
    open_new("http://127.0.0.1:5001")

if __name__ == "__main__":
    Timer(1, open_browser).start()
    port = int(environ.get("PORT", 5001))
    app.run(host='0.0.0.0', port=port)
