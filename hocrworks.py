from bs4 import BeautifulSoup as bs4


def hocr_transform(hocr):
    hocr = arrange_fix(hocr)
    hocr = newline_fix(hocr)
    return hocr


def newline_fix(hocr):
    hocrs = []
    for x in hocr:
        soup = bs4(x, 'html.parser')
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


def arrange_fix(hocr):
    return hocr