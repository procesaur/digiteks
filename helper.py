from multiprocessing import cpu_count
from os import name, path as px
from json import load
from time import time
from zipfile import ZIP_DEFLATED, ZipFile
from io import BytesIO
from base64 import b64encode, b64decode
from psutil import cpu_count
from multiprocessing.dummy import Pool as ThreadPool
from fuzzywuzzy import fuzz
from re import compile


cpus = cpu_count()
pool = ThreadPool(cpus)
split_pattern = compile(r'([ ]?\w+)?(\d+)?(\W+)?$')


def xsplit(x):
    match = split_pattern.match(x)
    if not match:
        return [x]
    mg = [y for y in match.groups() if y]
    return mg

def textsplit(text):
    result = []
    words = [" " + x for x in text.rstrip().replace("\n", " ").split()]
    for x in words:
        result+=xsplit(x)
    print(result)
    return result

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


def image_zip_to_images(file):
    if isinstance(file, bytes):
        memory_file = BytesIO(file)
    else:
        memory_file = BytesIO()
        file.save(memory_file)
    memory_file.seek(0)
    images = []
    
    with ZipFile(memory_file, 'r') as zip_ref:
        for file_info in zip_ref.infolist():
            if file_info.filename.endswith(('png', 'jpg', 'jpeg')):
                with zip_ref.open(file_info) as image_file:
                    images.append(image_file.read())
    return images


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


def strip_non_alphanumeric(s):
    i = len(s) - 1
    while i >= 0 and not s[i].isalnum():
        i -= 1
    return s[:i + 1]

roman = [
        "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X",
        "XI", "XII", "XIII", "XIV", "XV", "XVI", "XVII", "XVIII", "XIX", "XX",
        "XXI", "XXII", "XXIII", "XXIV", "XXV", "XXVI", "XXVII", "XXVIII", "XXIX", "XXX",
        "XXXI", "XXXII", "XXXIII", "XXXIV", "XXXV", "XXXVI", "XXXVII", "XXXVIII", "XXXIX", "XL",
        "XLI", "XLII", "XLIII", "XLIV", "XLV", "XLVI", "XLVII", "XLVIII"
    ]

cyr2lat_map = {
    'Љ': 'Lj',
    'Њ': 'Nj',
    'Џ': 'Dž',
    'А': 'A',
    'Б': 'B',
    'В': 'V',
    'Г': 'G',
    'Д': 'D',
    'Ђ': 'Đ',
    'Е': 'E',
    'Ж': 'Ž',
    'З': 'Z',
    'И': 'I',
    'Ј': 'J',
    'К': 'K',
    'Л': 'L',
    'М': 'M',
    'Н': 'N',
    'О': 'O',
    'П': 'P',
    'Р': 'R',
    'С': 'S',
    'Т': 'T',
    'Ћ': 'Ć',
    'У': 'U',
    'Ф': 'F',
    'Х': 'H',
    'Ц': 'C',
    'Ч': 'Č',
    'Ш': 'Š',
    'љ': 'lj',
    'њ': 'nj',
    'џ': 'dž',
    'а': 'a',
    'б': 'b',
    'в': 'v',
    'г': 'g',
    'д': 'd',
    'ђ': 'đ',
    'е': 'e',
    'ж': 'ž',
    'з': 'z',
    'и': 'i',
    'ј': 'j',
    'к': 'k',
    'л': 'l',
    'м': 'm',
    'н': 'n',
    'о': 'o',
    'п': 'p',
    'р': 'r',
    'с': 's',
    'т': 't',
    'ћ': 'ć',
    'у': 'u',
    'ф': 'f',
    'х': 'h',
    'ц': 'c',
    'ч': 'č',
    'ш': 'š'
}

lat2cyr_map = {v: k for k, v in cyr2lat_map.items()}

def cyr2lat(x):
    for key in cyr2lat_map.keys():
        x = (x.replace(key, cyr2lat_map[key]))
    return x
    
def lat2cyr(x):
    for key in lat2cyr_map.keys():
        x = (x.replace(key, lat2cyr_map[key]))
    return x

visual_similarity = {
    'а': ['г'],
    'б': ['6'],
    'в': ['з', '3'],
    'ђ': ['ћ', '5'],
    'ж': ['х'],
	'ј': ['1'],
    'и': ['п', 'н', 'њ', 'л', 'љ'],
    'о': ['с','е','р', '0'],
    'ц': ['ч', 'џ', 'д']
}

def map_visual_similarity(word):
    word = word.lower()
    for x in visual_similarity:
        for y in visual_similarity[x]:
            word = word.replace(y,x)
    return word

def visual_similarity_score(x, y):
    mapped_x = map_visual_similarity(x)
    mapped_y = map_visual_similarity(y)
    return fuzz.ratio(mapped_x, mapped_y)

def length_similarity(x, y):
    len_x = len(x)
    len_y = len(y)
    return 100 - abs(len_x - len_y) / max(len_x, len_y)

def combined_similarity(x, y, weight_fuzzy=0.25, weight_length=0.25, weight_visual=0.5):
    fuzzy_score = fuzz.ratio(x, y)
    length_score = length_similarity(x, y)
    visual_score = visual_similarity_score(x, y)
    return weight_fuzzy * fuzzy_score + weight_length * length_score + weight_visual * visual_score

def find_most_similar_word(x, xconf, a, threshold=0.5):
    most_similar_word = None
    highest_combined_score = float('-inf')
    similarity_scores = []

    for word, prob in a:
        combined_score = (combined_similarity(x, word)**xconf)*prob**(1-xconf)
        similarity_scores.append((word, combined_score))
        if combined_score > highest_combined_score:
            highest_combined_score = combined_score
            most_similar_word = word

    if highest_combined_score < threshold:
        return ""

    return most_similar_word

# python -m pipreqs.pipreqs --use-local --force .
# pyinstaller digiteks.spec