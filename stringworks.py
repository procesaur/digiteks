from rapidfuzz import process, fuzz
from re import compile
from string import digits, punctuation
from helper import cpus, pool
from numpy import uint8


split_pattern = compile(r'([ ]?[a-zđšćžčŠĐČĆŽA-Zа-џЂ-Я]+)?([ ]?\d+)?([^a-zđšćžčŠĐČĆŽA-Zа-џЂ-Я]+)?$')
split_pattern2 = compile(r'([ ]?[a-zđšćžčŠĐČĆŽA-Zа-џЂ-Я]+)([^a-zđšćžčŠĐČĆŽA-Zа-џЂ-Я0-9])([a-zđšćžčŠĐČĆŽA-Zа-џЂ-Я]+)([^a-zđšćžčŠĐČĆŽA-Zа-џЂ-Я0-9])$')
split_pattern3 = compile(r'([ ]?[^a-zđšćžčŠĐČĆŽA-Zа-џЂ-Я\s]+)([a-zđšćžčŠĐČĆŽA-Zа-џЂ-Я]+)$')

roman = {x.lower(): x for x in [
        "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X",
        "XI", "XII", "XIII", "XIV", "XV", "XVI", "XVII", "XVIII", "XIX", "XX",
        "XXI", "XXII", "XXIII", "XXIV", "XXV", "XXVI", "XXVII", "XXVIII", "XXIX", "XXX",
        "XXXI", "XXXII", "XXXIII", "XXXIV", "XXXV", "XXXVI", "XXXVII", "XXXVIII", "XXXIX", "XL",
        "XLI", "XLII", "XLIII", "XLIV", "XLV", "XLVI", "XLVII", "XLVIII"
    ]}


numbers = set(digits).union(set(punctuation))


visual_similarity = {
    'а': ['д'],
    'б': ['6'],
    'в': ['з', '3'],
    'ђ': ['ћ', '5'],
    'ж': ['х', 'x'],
	'ј': ['1', 'i' 'т'],
    'и': ['п', 'н', 'њ', 'л', 'љ', 'ii'],
    'о': ['с','е','р', '0', 'ф'],
    'ц': ['ч', 'џ', ],
    'у': ['м', 'v'],
    'ш': ['iii'],

    'а': ['a'],
    'б': ['b'],
    'ђ': ['s', 'š'],
	'ј': ['j', 'l', 't', 'f'],
    'и': ['n', 'h'],
    'о': ['g', 'd', 'e', 'o', 'ć', 'č', 'c', 'q'],
    'у': ['m', 'y'],
    'ш': ['w'],
    '2' : ['ž', 'z'],
    'к' : ['k'],
    'р' : ['p'],
    'г' : ['r']
}


def isnumber(x):
    return all(c in numbers for c in x.strip())


def xsplit(x):
    x = x.replace("_", "")
    if x in [" н", " H", " Н", " м", " М", " M"]:
        x = " и"
    match = split_pattern.match(x)
    if not match:
        mg = []
    else:
        mg = [y for y in match.groups() if y]

    if len(mg) < 2:
        match = split_pattern2.match(x)
        if match:
            mg = [y for y in match.groups() if y]

    if len(mg) < 2:
        match = split_pattern3.match(x)
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


def strip_non_alphanumeric(s):
    i = len(s) - 1
    while i >= 0 and not s[i].isalnum():
        i -= 1
    return s[:i + 1]


def map_visual_similarity(word):
    word = word.lower()
    for x in visual_similarity:
        for y in visual_similarity[x]:
            word = word.replace(y,x)
    return word


def calculate_similarities(a, b):
    scores = process.cdist(
    a, b, scorer=fuzz.ratio,
    dtype=uint8, score_cutoff=10, workers=cpus)
    return scores/100


def harmonize(args):
    x, y = args
    if x in roman:
        return roman[x]
    if y.strip().isupper():
        return x.upper()
    if y.strip()[0].isupper():
        if x[0]!= " ":
            return x.capitalize()
        return " " + x.lstrip().capitalize()
    return x


def harmonize_array(a, b):
    return pool.map(harmonize, zip(a,b))
