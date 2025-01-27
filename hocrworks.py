from bs4 import BeautifulSoup as bs4
from lmworks import inspect
from helper import do


def hocr_transform(hocr):
    processes = (make_soup, arrange_fix, newline_fix, word_fix)
    processes = (make_soup, arrange_fix, newline_fix, word_fix)
    for p in processes:
        hocr = do(p, hocr)
    return str(hocr)

def make_soup(hocr):
    return bs4(hocr, 'html.parser')

def newline_fix(soup):
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
    return soup

def word_fix(soup):
    spans = soup.find_all("span", {"class": "ocrx_word"})
    ids = [span['id'] for span in spans]
    prior_probs = []
    words = [span.get_text() for span in spans]
    probs, _ = inspect(words, prior_probs=prior_probs)
    for word, prob in zip(spans, probs):
        word["y_wconf"] = 100-prob
    return soup

def arrange_fix(soup):
    return soup