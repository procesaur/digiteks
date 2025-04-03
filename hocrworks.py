from bs4 import BeautifulSoup as bs4, Tag
from lmworks import lm_inspect, lm_fix_words, confidence_rework, should_merge
from helper import do, make_id, cfg
from stringworks import strip_non_alphanumeric, xsplit
from imageworks import crop_image


lineclass = ["ocr_line", "ocr_caption", "ocr_textfloat", "ocr_header"]


def hocr_transform(hocr, image=None):
    hocr = make_soup(hocr)
    hocr = enrich_soup(hocr, image)

    processes = (arrange_fix, newline_fix, punct_separation)
    for p in processes:
        hocr = p(hocr)
    processes = (lm_processing, lm_fix)
    for p in processes:
        hocr = do(p, hocr)
    hocr = prepare_hocr(hocr)
    return str(hocr)


def make_soup(hocr):
    return bs4(hocr, 'html.parser')


def enrich_soup(soup, image=None):
    if image:
        img_id = make_id()
        img_tag = soup.new_tag('img', **{
            'class': 'page_image',
            'id' : img_id,
            'src' :  f"data:image/png;base64,{image}",
            'onload': "document.querySelector('#SaveimagesData').insertBefore(this.parentElement, Array.from(document.querySelectorAll('#SaveimagesData img')).pop())",
            'style': 'width:100%'
            })

        img_cont = soup.new_tag('div', **{'class': 'image-container'})
        canv = soup.new_tag('canvas ', **{'class': 'overlay-canvas', 'id' : "c"+img_id})
        img_cont.append(img_tag)
        img_cont.append(canv)
        soup.append(img_cont)

    hocr_elements = soup.find_all('div', class_='ocr_photo')
    page = soup.find('div', class_='ocr_page')
    page["id"] = "p_" + img_id
    for hocr_element in hocr_elements:
        img_element = soup.new_tag('img')
       
        title_attr = hocr_element.get('title')
        if title_attr:
            bbox = title_attr.split('bbox ')[1].split()
            x1, y1, x2, y2 = map(int, bbox)
            if x2 > x1 and y2 > y1 and image:
                img_element['src'] = f'data:image/jpeg;base64,{crop_image(image, x1, y1, x2, y2)}'


        new_div = soup.new_tag('p', **{'class': 'ocr_par', 'title': hocr_element['title'] })
        new_div2 = soup.new_tag('span', **{'class': 'ocr_image' })

        new_div2.attrs['style'] = 'position: relative;'
        new_div.attrs['style'] = 'position: relative;'

        new_div2.append(img_element)
        new_div.append(new_div2)

        hocr_element.replace_with(new_div)

    global_bounds = get_global_bounds(soup)
    mid_x = (global_bounds['minX'] + global_bounds['maxX']) / 2
    l_bounds = {'minX': global_bounds['minX'], 'maxX': mid_x}
    r_bounds = {'minX': mid_x, 'maxX': global_bounds['maxX']}
    y_groups = group_paragraphs_by_y(soup)
    for group in y_groups:
        layout_type = determine_layout_type_for_group(group, mid_x)
        for paragraph in group:
            column_type = determine_column_type(paragraph, mid_x)
            paragraph['column-type'] = column_type
            paragraph['layout-type'] = layout_type

    paragraphs = soup.find_all(class_='ocr_par')
    for paragraph in paragraphs:
        paragraph["image_id"] = img_id
        column_class = paragraph.get('column-type')
        column_n = paragraph.get('layout-type')
        if column_n not in cfg["valid_columns"]:
            paragraph["del-candidate"] = "yes"
        if column_n != 2:
            process_paragraph(paragraph, global_bounds, column_n)
            get_and_set_word_paddings(paragraph, global_bounds)
        else:
            if column_class == 'left column':
                process_paragraph(paragraph, l_bounds, column_n)
                get_and_set_word_paddings(paragraph, l_bounds)
            elif column_class == 'right column':
                process_paragraph(paragraph, r_bounds, column_n)
                get_and_set_word_paddings(paragraph, r_bounds)
            else:
                process_paragraph(paragraph, global_bounds, column_n)
                get_and_set_word_paddings(paragraph, global_bounds)
    return soup


def newline_fix(soup):
    lines = soup.find_all("span", {"class": lineclass})
    dahses = ["-", "«", "－", "-", "﹣", "֊", "᠆", "‐", "-", "–", "—", "﹘", "―", "⁓", "⹝", "〜", "𐺭", "⸚", "־", "−", "⁻", "₋", "~", "="]
    not_dashes = [",", ".", "\"", ":", ";", ")", "!", "?",]
    for i, line in enumerate(lines):
        if lines[i].find_all("span", {"class": "ocrx_word"}):
            last = lines[i].find_all("span", {"class": "ocrx_word"})[-1]
            try:
                second_to_last = lines[i].find_all("span", {"class": "ocrx_word"})[-2]
                while len(strip_non_alphanumeric(last.getText())) < 1 and second_to_last["maybe_broken"] == "yes":
                    last.decompose()
                    last = lines[i].find_all("span", {"class": "ocrx_word"})[-1]
                    second_to_last = lines[i].find_all("span", {"class": "ocrx_word"})[-2]
            except:
                pass

        if len(lines) > i+1:
            if lines[i+1].find_all("span", {"class": "ocrx_word"}):
                next = lines[i+1].find_all("span", {"class": "ocrx_word"})[0]
                try:
                    second_next = lines[i+1].find_all("span", {"class": "ocrx_word"})[1]
                    while len(strip_non_alphanumeric(next.getText())) < 1 and strip_non_alphanumeric(next.getText()) not in dahses and second_next["maybe_broken"] == "yes":
                        next.decompose()
                        next = lines[i+1].find_all("span", {"class": "ocrx_word"})[0]
                        second_next = lines[i+1].find_all("span", {"class": "ocrx_word"})[1]
                except:
                    pass
        
        if last and next:
            try:
                if last["maybe_broken"] == "yes" and  next["maybe_broken"] == "yes" and not next.getText().strip().isnumeric():
                    if last.getText()[-1] in dahses:
                        last.string = strip_non_alphanumeric(last.getText()) + next.getText().lstrip()
                        next.decompose()
                    elif not last.getText()[-1].isalnum():
                        if last.getText()[-1] not in not_dashes:
                            last.string = strip_non_alphanumeric(last.getText()) + next.getText().lstrip()
                            last["data-original"] = last.string
                            next.decompose()
                        else:
                            if should_merge(strip_non_alphanumeric(last.getText()), next.getText(), strip_non_alphanumeric(last.getText()) + next.getText().lstrip()):
                                last.string = strip_non_alphanumeric(last.getText()) + next.getText().lstrip()
                                last["data-original"] = last.string
                                next.decompose()
                else:
                    if last.getText()[-1] in dahses:
                        if should_merge(strip_non_alphanumeric(last.getText()), next.getText(), strip_non_alphanumeric(last.getText()) + next.getText().lstrip()):
                            last.string = strip_non_alphanumeric(last.getText()) + next.getText().lstrip()
                            last["data-original"] = last.string
                            next.decompose()
            except:
                pass

    return soup


def punct_separation(soup):
    spans = soup.find_all("span", {"class": "ocrx_word"})
    for span in spans:
        mg = xsplit(span.text)
        if mg == [" 1"]:
            next_sibling = span.find_next_sibling("span", {"class": "ocrx_word"})
            prev_sibling = span.find_previous_sibling("span", {"class": "ocrx_word"})
            if not next_sibling and not prev_sibling:
                mg = [" I"]
        new_spans = []
        for x in mg:
            new_word_span = Tag(name="span", attrs=span.attrs)
            new_word_span.string = x
            new_word_span["data-original"] = x
            new_spans.append(new_word_span)
        span.replace_with(*new_spans)
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
    return soup


def lm_fix(soup):
    spans = soup.find_all("span", {"class": "ocrx_word"})
    words = [span.get_text() for span in spans]
    ocr_confs= [span["ocr_conf"] for span in spans]
    new_confs = [span["new_conf"] for span in spans]
    new_words = lm_fix_words(words, new_confs, ocr_confs)
    for span, word, new_word in zip(spans, words, new_words):
        span.string = new_word
        if word != new_word:
            if new_word != "":
                span['lm_guess'] = new_word
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


def group_paragraphs_by_y(hocr_element, tolerance=10):
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


def determine_column_type(paragraph, mid_x, tolerance=100):
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

        paragraph["right_padding"] = right_padding
        paragraph["left_padding"] = left_padding
        paragraph["xalign"] = align
        paragraph["x1"] = x1
        paragraph["x2"] = x2
        paragraph["y1"] = y1
        paragraph["y2"] = y2


def get_and_set_word_paddings(paragraph, global_bounds, tolerance=100):
    words = paragraph.find_all(class_='ocrx_word')
    for word in words:
        word["data-original"] = " " + word.get_text()
        word.string = " " + word.get_text()
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


def prepare_hocr(element, top=0.94, saturation=0.5):
     # Move '.ocr_par' elements from '.ocr_carea' to their parent and remove '.ocr_carea'
    ocr_careas = element.select('.ocr_carea')
    for carea in ocr_careas:
        ocr_pars = carea.select('.ocr_par')
        for par in ocr_pars:
            carea.parent.append(par)  # Move '.ocr_par' to parent
        carea.decompose()  # Remove '.ocr_carea'

    # Process '.ocrx_word' elements
    words = element.select('.ocrx_word')
    for word in words:
        conf = word.get('new_conf')  # Assuming new_conf is an attribute
        old_value = word.get('data-original')
        new_value = word.text

        if old_value != new_value and new_value == word.get('lm_guess'):
            word['style'] = f"--red:0; --blue:255; --conf:{conf};"
        else:
            word['style'] = f"--red:255; --blue:0; --conf:{conf};"

        word['contenteditable'] = 'true'
        word['onblur'] = 'handleTextChange(event)'
        word['onkeydown'] = 'MaybeDelete(event)'

    # Process lines (example using a variable `lc` for selectors)
    lc = ".ocr_line, .ocr_caption, .ocr_textfloat, .ocr_header, .ocr_image, .break"
    lines = element.select(lc)
    for line in lines:
        checkbox = element.new_tag('input', attrs={'type':'checkbox', 'class':'dynamic-checkbox'})
        line['style'] = 'position: relative;'
        line.insert(0, checkbox)  # Insert the checkbox at the beginning

    # Process '.ocr_par' elements
    ocr_pars = element.select('.ocr_par')
    for par in ocr_pars:
        checkbox = element.new_tag('input', attrs={'type':'checkbox', 'class':'dynamic-checkbox par-checkbox'})
        button = element.new_tag('button', onclick='showPopupevent(event)')
        button.string = '🔍'
        button['style'] = 'float: right;'

        par['style'] = 'position: relative;'
        par.insert(0, button)  # Insert button at the beginning
        par.insert(0, checkbox)  # Insert checkbox at the beginning
        par['onclick'] = 'checkall(event)'

    return element