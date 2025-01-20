from bs4 import BeautifulSoup as bs4
from lmworks import inspect
from helper import do


def hocr_transform(hocr):
    processes = (make_soup, arrange_fix, newline_fix, word_fix)
    processes = (make_soup, arrange_fix, newline_fix)

    for p in processes:
        hocr = do(p, hocr)
    return hocr


def make_soup(hocr):
    hocr = [bs4(x, 'html.parser') for x in hocr]
    return hocr

def newline_fix(hocr):
    hocrs = []
    for soup in hocr:
        lines = soup.find_all("span", {"class": "ocr_line"})
        for i, line in enumerate(lines):
            try:
                last = lines[i].find_all("span", {"class": "ocrx_word"})[-1]
                if last.getText()[-1] in ["-", "«", "－", "-", "﹣", "֊", "᠆", "‐", "-", "–", "—", "﹘", "―", "⁓", "⹝", "〜", "𐺭", "⸚", "־", "−", "⁻", "₋", "~"]:
                    next = lines[i+1].find_all("span", {"class": "ocrx_word"})[0]
                    last.string = last.getText()[:-1] + next.getText()
                    next.decompose()
            except:
                pass
        hocrs.append(soup)
    return hocrs


def word_fix(hocr):
    hocrs = []
    for soup in hocr:
        words = soup.find_all("span", {"class": "ocrx_word"})
        ids = [span['id'] for span in words]
        prior_probs = []
        words = [span.get_text() for span in words]
        probs, _ = inspect(words, prior_probs=prior_probs)
        for word, prob in zip(words, probs):
            word["y_wconf"] = prob
        hocrs.append(soup)
    return hocrs

def arrange_fix(hocr):
    return hocr