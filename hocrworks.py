from bs4 import BeautifulSoup as bs4
from lmworks import lm_inspect, lm_fix_words, confidence_rework
from helper import do, strip_non_alphanumeric


lineclass = ["ocr_line", "ocr_caption", "ocr_textfloat", "ocr_header"]

def hocr_transform(hocr):
    processes = (make_soup, enrich_soup, arrange_fix, newline_fix)
    for p in processes:
        hocr = p(hocr)
    processes = (lm_processing,)
    for p in processes:
        hocr = do(p, hocr)
    return str(hocr)

def make_soup(hocr):
    return bs4(hocr, 'html.parser')

def enrich_soup(soup):
    pages = soup.find_all(class_='ocr_page')

    for hocr_element in pages:
        global_bounds = get_global_bounds(hocr_element)
        mid_x = (global_bounds['minX'] + global_bounds['maxX']) / 2
        l_bounds = {'minX': global_bounds['minX'], 'maxX': mid_x}
        r_bounds = {'minX': mid_x, 'maxX': global_bounds['maxX']}
        y_groups = group_paragraphs_by_y(hocr_element)
        for group in y_groups:
            layout_type = determine_layout_type_for_group(group, mid_x)
            for paragraph in group:
                column_type = determine_column_type(paragraph, mid_x)
                paragraph['column-type'] = column_type
                paragraph['layout-type'] = layout_type

        paragraphs = hocr_element.find_all(class_='ocr_par')
        for paragraph in paragraphs:
            column_class = paragraph.get('column-type')
            column_n = paragraph.get('layout-type')
            if column_n != 2:
                paragraph.decompose()
            else:
                if column_class == 'left column':
                    process_paragraph(paragraph, l_bounds, column_n)
                    get_and_set_word_paddings(paragraph, l_bounds)
                elif column_class == 'right column':
                    process_paragraph(paragraph, r_bounds, column_n)
                    get_and_set_word_paddings(paragraph, r_bounds)
    return soup


def newline_fix(soup):
    lines = soup.find_all("span", {"class": lineclass})
    dahses = ["-", "«", "－", "-", "﹣", "֊", "᠆", "‐", "-", "–", "—", "﹘", "―", "⁓", "⹝", "〜", "𐺭", "⸚", "־", "−", "⁻", "₋", "~"]
    not_dashes = [",", ".", "\""]
    for i, line in enumerate(lines):
        try:
            last = lines[i].find_all("span", {"class": "ocrx_word"})[-1]
            next = lines[i+1].find_all("span", {"class": "ocrx_word"})[0]
            ends_with_dash = last.getText()[-1] in dahses
            not_a_char = len(last.getText()) > 1
            ends_strange = not last.getText()[-1].isalnum() and last.getText()[-1] not in not_dashes
            maybe_broken = last["maybe_broken"] == "yes"
            next_maybe_broken = next["maybe_broken"] == "yes"
            possible_hit = ends_strange and maybe_broken and next_maybe_broken
            if not_a_char and (ends_with_dash or possible_hit):
                last.string = strip_non_alphanumeric(last.getText()) + next.getText()
                next.decompose()
        except:
            pass
    return soup

def lm_processing(soup):
    spans = soup.find_all("span", {"class": "ocrx_word"})
    words = [span.get_text() for span in spans]
    ocr_confs = [int(span['title'].split('x_wconf ')[1])/100 for span in spans]
    lm_confs, _ = lm_inspect(words, pre_confs=ocr_confs)
    new_confs = confidence_rework(ocr_confs, lm_confs)
    for span, ocr_conf, lm_conf, new_conf in zip(spans, ocr_confs, lm_confs, new_confs):
        span["ocr_conf"] = ocr_conf
        span["lm_conf"] = lm_conf
        span["new_conf"] = new_conf

    new_words = lm_fix_words(words, new_confs)
    for span, word, new_word in zip(spans, words, new_words):
        if word != new_word:
            span.string = word + " > " + new_word
            span['style'] = "--red:255; --conf:1"
    return soup


def arrange_fix(soup):
    return soup


def get_global_bounds(hocr_element):
    min_x = float('inf')
    max_x = float('-inf')
    paragraphs = hocr_element.find_all(class_='ocr_par')

    for paragraph in paragraphs:
        title = paragraph.get('title', '')
        parts = title.split(';')
        bbox = next((part for part in parts if 'bbox' in part), None)
        if bbox:
            bbox_values = bbox.split()[1:]  # Skip 'bbox' and take the numeric values
            x1, _, x2, _ = map(int, bbox_values)
            if x1 < min_x:
                min_x = x1
            if x2 > max_x:
                max_x = x2

    return {'minX': min_x, 'maxX': max_x}


def group_paragraphs_by_y(hocr_element, tolerance=20):
    y_groups = []
    paragraphs = hocr_element.find_all(class_='ocr_par')

    for paragraph in paragraphs:
        title = paragraph.get('title', '')
        parts = title.split(';')
        bbox = next((part for part in parts if 'bbox' in part), None)
        if bbox:
            bbox_values = bbox.split()[1:]  # Skip 'bbox' and take the numeric values
            _, y1, _, y2 = map(int, bbox_values)
            added_to_group = False

            for group in y_groups:
                group_bbox = group[0].get('title', '').split(';')[0].split()[1:]
                group_y1, group_y2 = int(group_bbox[1]), int(group_bbox[3])

                if ((y1 >= group_y1 - tolerance and y1 <= group_y2 + tolerance) or
                    (y2 >= group_y1 - tolerance and y2 <= group_y2 + tolerance) or
                    (group_y1 >= y1 - tolerance and group_y1 <= y2 + tolerance) or
                    (group_y2 >= y1 - tolerance and group_y2 <= y2 + tolerance)):
                    group.append(paragraph)
                    added_to_group = True
                    break

            if not added_to_group:
                y_groups.append([paragraph])

    return y_groups


def process_y_groups(hocr_element):
    global_bounds = get_global_bounds(hocr_element)
    mid_x = (global_bounds['minX'] + global_bounds['maxX']) / 2
    y_groups = group_paragraphs_by_y(hocr_element)

    for group in y_groups:
        layout_type = determine_layout_type_for_group(group, mid_x)
        for paragraph in group:
            column_type = determine_column_type(paragraph, mid_x)
            paragraph['column-type'] = column_type
            paragraph['layout-type'] = layout_type


def determine_column_type(paragraph, mid_x, tolerance=1):
    title = paragraph.get('title', '')
    parts = title.split(';')
    bbox = next((part for part in parts if 'bbox' in part), None)
    if bbox:
        bbox_values = bbox.split()[1:]  # Skip 'bbox' and take the numeric values
        x1, x2 = int(bbox_values[0]), int(bbox_values[2])

        if x1 < mid_x + tolerance and x2 <= mid_x + tolerance:
            return 'left column'
        elif x1 >= mid_x - tolerance and x2 > mid_x - tolerance:
            return 'right column'
        elif (x1 < mid_x + tolerance and x2 > mid_x - tolerance) or (x1 < mid_x and x2 > mid_x):
            return 'middle column'
    return 'unknown column'


def determine_layout_type_for_group(group, mid_x):
    three_column = False

    for paragraph in group:
        column_type = determine_column_type(paragraph, mid_x)
        if column_type == 'middle column':
            three_column = True

    return 3 if three_column else 2


def process_paragraph(paragraph, global_bounds, column_n=2, tolerance=150):
    title = paragraph.get('title', '')
    parts = title.split(';')
    bbox = next((part for part in parts if 'bbox' in part), None)
    if bbox:
        bbox_values = bbox.split()[1:]  # Skip 'bbox' and take the numeric values
        x1, y1, x2, y2 = int(bbox_values[0]), int(bbox_values[1]), int(bbox_values[2]), int(bbox_values[3])

        left_padding = x1 - global_bounds['minX']
        right_padding = global_bounds['maxX'] - x2

        # Adjust the threshold values more aggressively for right alignment
        if left_padding + tolerance < right_padding:  # Lower threshold for right alignment
            align = 'left'
        elif right_padding + tolerance < left_padding:  # Increased threshold for left alignment
            align = 'right'
        elif left_padding > tolerance and right_padding > tolerance:  # Lower threshold for center alignment
            align = 'center'
        else:
            align = 'justify'

        if column_n != 2:
                return '', '', '', x1, y1, x2, y2

        paragraph["right_padding"] = right_padding
        paragraph["left_padding"] = left_padding
        paragraph["xalign"] = align
        paragraph["x1"] = x1
        paragraph["x2"] = x2
        paragraph["y1"] = y1
        paragraph["y2"] = y2


def get_and_set_word_paddings(paragraph, global_bounds, tolerance=50):
    words = paragraph.find_all(class_='ocrx_word')
    for word in words:
        word["data-original"] = word.get_text()
        title = word.get('title', '')
        parts = title.split(';')
        bbox = next((part for part in parts if 'bbox' in part), None)
        if bbox:
            bbox_values = bbox.split()[1:]  # Skip 'bbox' and take the numeric values
            x1, x2 = int(bbox_values[0]), int(bbox_values[2])
            left_padding = x1 - global_bounds['minX']
            right_padding = global_bounds['maxX'] - x2
            word['left_padding'] = left_padding
            word['right_padding'] = right_padding
            if right_padding < tolerance or left_padding < tolerance:
                word["maybe_broken"] = "yes"
            else:
                word["maybe_broken"] = "no"