from rapidfuzz import fuzz
from rapidfuzz.distance import Hamming
from re import compile
from string import digits, punctuation



split_pattern = compile(r'([ ]?\w+)?(\d+)?(\W+)?$')

roman = [
        "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X",
        "XI", "XII", "XIII", "XIV", "XV", "XVI", "XVII", "XVIII", "XIX", "XX",
        "XXI", "XXII", "XXIII", "XXIV", "XXV", "XXVI", "XXVII", "XXVIII", "XXIX", "XXX",
        "XXXI", "XXXII", "XXXIII", "XXXIV", "XXXV", "XXXVI", "XXXVII", "XXXVIII", "XXXIX", "XL",
        "XLI", "XLII", "XLIII", "XLIV", "XLV", "XLVI", "XLVII", "XLVIII"
    ]

numbers = set(digits).union(set(punctuation))

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

visual_similarity = {
    'а': ['г'],
    'б': ['6'],
    'в': ['з', '3'],
    'ђ': ['ћ', '5'],
    'ж': ['х', 'X'],
	'ј': ['1'],
    'и': ['п', 'н', 'њ', 'л', 'љ', 'II'],
    'о': ['с','е','р', '0', 'ф'],
    'ц': ['ч', 'џ', 'д'],
    'V': ["м", "у"],
    'III': ['ш']
}


def isnumber(x):
    return all(c in numbers for c in x.strip())


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


def cyr2lat(x):
    for key in cyr2lat_map.keys():
        x = (x.replace(key, cyr2lat_map[key]))
    return x


def lat2cyr(x):
    for key in lat2cyr_map.keys():
        x = (x.replace(key, lat2cyr_map[key]))
    return x


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


def length_similarity(x, y):
    len_x = len(x)
    len_y = len(y)
    return 1 - abs(len_x - len_y) / max(len_x, len_y)


def combined_similarity(x, y, mapped_x, mapped_y, weight_fuzzy=0.1, weight_hamming=0.2, weight_length=0.2, weight_hvisual=0.3, weight_visual=0.2):
    length_score = length_similarity(x, y) * weight_length
    fuzzy_score = fuzz.ratio(x, y)/100 * weight_fuzzy
    visual_score = fuzz.ratio(mapped_x, mapped_y) * weight_visual
    hamming_score = similarity(x, y)/100 * weight_hamming
    hamming_visual = similarity(mapped_x, mapped_y) * weight_hvisual
    return fuzzy_score + length_score + visual_score + hamming_score + hamming_visual


def similarity(str1, str2):
    distance = Hamming.distance(str1, str2)
    max_len = max(len(str1), len(str2))
    similarity = 1 - (distance / max_len)
    return similarity


def find_most_similar_word(x, mapped_x, xconf, a, threshold=0.1):
    most_similar_word = None
    highest_combined_score = 0
    similarity_scores = []

    for word, mapped_y, prob in a:
        cs = combined_similarity(x, word, mapped_x, mapped_y)
        combined_score = (cs*xconf)+prob*(1-xconf)
        similarity_scores.append((word, combined_score))
        if combined_score > highest_combined_score:
            highest_combined_score = combined_score
            most_similar_word = word

    if highest_combined_score < threshold:
        return ""

    return most_similar_word