from multiprocessing import cpu_count
from os import name, path as px
from json import load
from time import time
from zipfile import ZIP_DEFLATED, ZipFile
from io import BytesIO
from base64 import b64encode, b64decode
from psutil import cpu_count
from multiprocessing.dummy import Pool as ThreadPool
from uuid import uuid4


cpus = cpu_count()
pool = ThreadPool(cpus)


def make_id():
   return str(uuid4()) 


def load_conf(path=None):
    if not path:
        path = px.join(px.dirname(__file__), "config.json")
    with open(path, "r", encoding="utf-8") as cf:
        return load(cf)

cfg = load_conf()

def isWindows():
    return name == 'nt'


def zip_bytes_string(images_in_bytes):
    zip_stream = BytesIO()
    with ZipFile(zip_stream, 'w', ZIP_DEFLATED) as zip_file:
        for filename, image_bytes in images_in_bytes.items():
            zip_file.writestr(filename, image_bytes)

    zip_stream.seek(0)
    return zip_stream

def read_zip(file):
    if isinstance(file, bytes):
        memory_file = BytesIO(file)
    else:
        memory_file = BytesIO()
        file.save(memory_file)
    memory_file.seek(0)
    result = []
    
    with ZipFile(memory_file, 'r') as zip_ref:
        for file_info in zip_ref.infolist():
            if file_info.filename.endswith(('png', 'jpg', 'jpeg')):
                with zip_ref.open(file_info) as image_file:
                    result.append(image_file.read())
    return result

def encode_images(images):
    return [b64encode(image_data).decode('utf-8') for image_data in images]


def decode_images(images):
    return [b64decode(image) for image in images]

def group_into_sentences(words):
    sentences = []
    current_sentence = []

    for word in words:
        current_sentence.append(word)
        if word.endswith('.'):
            sentences.append(current_sentence)
            current_sentence = []

    if current_sentence:
        sentences.append(current_sentence)

    return sentences


def do(f, x):
    print(f.__name__)
    start_time = time()
    if isinstance(x, tuple):
        x = f(*x)
    else:
        x = f(x)
    end_time = time()
    execution_time = end_time - start_time
    print(f"Time: {execution_time} seconds")
    return x


def chunkify(lst, n=cpus):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


# python -m pipreqs.pipreqs --use-local --force .
# pyinstaller digiteks.spec
