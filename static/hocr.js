function prepare(top=0.94, saturation=0.5) {

    const ocrCareas = document.querySelectorAll('.ocr_carea');
    ocrCareas.forEach(carea => {
        const ocrPars = carea.querySelectorAll('.ocr_par');
        ocrPars.forEach(par => {
            carea.parentNode.appendChild(par);
        });
        carea.remove();
    });

    const words = document.querySelectorAll('.ocrx_word');

    Array.from(words).forEach(function (word) {
        var conf = parseInt(word.title.substring(word.title.lastIndexOf(' ')))/100;
        var conf = word.getAttribute("y_wconf");
        word.style  = "--red:255; --conf:"+conf;
        word.dataset.original = word.innerText;
        word.contentEditable = 'true';
        word.setAttribute("onblur", "handleTextChange(event)");
        word.setAttribute("onkeydown", "MaybeDelete(event)");
    });

    const lines = document.querySelectorAll('.ocr_line, .ocr_caption');

    Array.from(lines).forEach(function (line) {
        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.name = line.id;
        checkbox.className = 'dynamic-checkbox';
        line.style.position = 'relative'; 
        line.insertBefore(checkbox, line.firstChild);
    }); 

    const pars = document.querySelectorAll('.ocr_par');

    Array.from(pars).forEach(function (par) {

        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.className = 'dynamic-checkbox par-checkbox';
        par.style.position = 'relative'; 
        par.insertBefore(checkbox, par.firstChild);
        par.setAttribute("onclick", "checkall(event)");
    }); 

}

window.onload = prepare;

function help(){
    document.getElementById('if').src = "/help";
}

function dwn(x, mime, filename, ext){
    var base64doc = btoa(unescape(encodeURIComponent(x))),
    a = document.createElement('a'),
    e = new MouseEvent('click');

    a.download = filename + ext;
    a.href = 'data:' + mime + ';base64,' + base64doc;
    a.dispatchEvent(e);
}

function getHocr(filename){
    var body = document.getElementById("full_hocr");
    var head = document.getElementById("full_hocr_head");
    dwn(`<!DOCTYPE html><html><head>${head.innerHTML}</head><body>${body.innerHTML}</body></html>`, "text/html", filename, ".html");
}

function getHtml(filename){
    var body = document.getElementById("digiteks_hocr_content");

    dwn(`<!DOCTYPE html><html><body>${hocrToPlainHtml(body)}</body></html>`, "text/html", filename, ".html");
}




function getAlignmentClass(paragraph, globalBounds, columnN=2) {
    const bbox = paragraph.getAttribute('title').match(/bbox (\d+) (\d+) (\d+) (\d+)/);
    tolerance = 150;
    if (bbox) {
        if (columnN!=2){
            return '';
        }
        const x1 = parseInt(bbox[1], 10);
        const x2 = parseInt(bbox[3], 10);

        const leftPadding = x1 - globalBounds.minX;
        const rightPadding = globalBounds.maxX - x2;

        // Adjust the threshold values more aggressively for right alignment
        if (leftPadding + tolerance < rightPadding) { // Lower threshold for right alignment
            return 'Basic-Paragraph';
        } else if (rightPadding + tolerance < leftPadding) { // Increased threshold for left alignment
            return 'potpis';
        } else if (leftPadding > tolerance && rightPadding > tolerance) { // Lower threshold for center alignment
            return 'odluka-zakon';
        } else {
            return 'Basic-Paragraph';
        }
    }
    return 'Basic-Paragraph'; // Default to justify if bbox is not found
}

function hocrToPlainHtml(hocrElementx) {
    let plainHtml = "";

    const pages = hocrElementx.getElementsByClassName('ocr_page');
    Array.from(pages).forEach(hocrElement => {
        const globalBounds = getGlobalBounds(hocrElement);
        const midX = (globalBounds.minX + globalBounds.maxX) / 2;
        const lBounds = {minX : globalBounds.minX, maxX : midX};
        const rBounds = {minX : midX, maxX : globalBounds.maxX};

        const yGroups = groupParagraphsByY(hocrElement);

        for (const y in yGroups) {
            const group = yGroups[y];
            const layoutType = determineLayoutTypeForGroup(group, midX);

            group.forEach(paragraph => {
                const columnType = determineColumnType(paragraph, midX);               
                paragraph.setAttribute("xxx", columnType);
                paragraph.setAttribute("yyy", layoutType);
                });
            }

        const paragraphs = hocrElement.getElementsByClassName('ocr_par');
        Array.from(paragraphs).forEach(paragraph => {
            const columnClass = paragraph.getAttribute("xxx")
            const columnN = paragraph.getAttribute("yyy")
            var alignmentClass = '';
            if (columnClass == 'left column' ){
                alignmentClass = getAlignmentClass(paragraph, lBounds, columnN);
            }
            else if (columnClass == 'right column'){
                alignmentClass = getAlignmentClass(paragraph, rBounds, columnN);
            }
 
            //plainHtml += `<p class="${alignmentClass} ${columnClass}_${columnN}">`;
            plainHtml += `<p class="${alignmentClass}">`;
            
            const words = paragraph.getElementsByClassName('ocrx_word');
            Array.from(words).forEach((word, index) => {
                plainHtml += word.textContent;
                if (index < words.length - 1) {
                    plainHtml += " ";
                }
            });
            plainHtml += "</p>\n";
        });
    });

    return plainHtml;
}



function groupParagraphsByY(hocrElement) {
    const yGroups = [];
    const tolerance = 20; // Adjust tolerance value as needed
    const paragraphs = hocrElement.getElementsByClassName('ocr_par');
    
    Array.from(paragraphs).forEach(paragraph => {
        const bbox = paragraph.getAttribute('title').match(/bbox (\d+) (\d+) (\d+) (\d+)/);
        if (bbox) {
            const y1 = parseInt(bbox[2], 10);
            const y2 = parseInt(bbox[4], 10);
            let addedToGroup = false;

            for (const group of yGroups) {
                const groupY1 = parseInt(group[0].getAttribute('title').match(/bbox (\d+) (\d+) (\d+) (\d+)/)[2], 10);
                const groupY2 = parseInt(group[0].getAttribute('title').match(/bbox (\d+) (\d+) (\d+) (\d+)/)[4], 10);

                if ((y1 >= groupY1 - tolerance && y1 <= groupY2 + tolerance) || 
                    (y2 >= groupY1 - tolerance && y2 <= groupY2 + tolerance) || 
                    (groupY1 >= y1 - tolerance && groupY1 <= y2 + tolerance) || 
                    (groupY2 >= y1 - tolerance && groupY2 <= y2 + tolerance)) {
                    group.push(paragraph);
                    addedToGroup = true;
                    break;
                }
            }
            if (!addedToGroup) {
                yGroups.push([paragraph]);
            }
        }
    });
    
    return yGroups;
}

function determineColumnType(paragraph, midX, tolerance=1) {
    const bbox = paragraph.getAttribute('title').match(/bbox (\d+) (\d+) (\d+) (\d+)/);
    if (bbox) {
        const x1 = parseInt(bbox[1], 10);
        const x2 = parseInt(bbox[3], 10);
        
        if (x1 < midX + tolerance && x2 <= midX + tolerance) {
            return 'left column';
        } else if (x1 >= midX - tolerance && x2 > midX - tolerance) {
            return 'right column';
        } else if ((x1 < midX + tolerance && x2 > midX - tolerance) || (x1 < midX && x2 > midX)) {
            return 'middle column';
        }
    }
    return 'unknown column';
}

function determineLayoutTypeForGroup(group, midX) {
    let threeColumn = false;

    group.forEach(paragraph => {
        const columnType = determineColumnType(paragraph, midX);
        if (columnType === 'middle column') {
            threeColumn = true;
        }
    });

    return threeColumn ? 3 : 2;
}

function getGlobalBounds(hocrElement) {
    let minX = Infinity;
    let maxX = -Infinity;
    const paragraphs = hocrElement.getElementsByClassName('ocr_par');
    Array.from(paragraphs).forEach(paragraph => {
        const bbox = paragraph.getAttribute('title').match(/bbox (\d+) (\d+) (\d+) (\d+)/);
        if (bbox) {
            const x1 = parseInt(bbox[1], 10);
            const x2 = parseInt(bbox[3], 10);
            if (x1 < minX) minX = x1;
            if (x2 > maxX) maxX = x2;
        }
    });
    return { minX, maxX };
}

function getText(filename){
    var html = document.getElementById("full_hocr")
    var x = html.textContent;
    x = x.replace(/\s\s+/g, ' ');
    dwn(x, "text/plain", filename, ".txt");
}

function uploadHocr(event){
    const file = event.target.files[0];
    if (file) {
        const reader = new FileReader();
        reader.onload = function(e) {
            // Parse the uploaded HTML file content
            const parser = new DOMParser();
            const doc = parser.parseFromString(e.target.result, 'text/html');
            const newContent = doc.querySelector('#digiteks_hocr_content');
            console.error('Element with id dasdasdasddigiteks_hocr_content not found in the uploaded file.');
            // Replace the existing element with the new content
            if (newContent) {
                const existingContent = document.getElementById('digiteks_hocr_content');
                if (existingContent) {
                    existingContent.innerHTML = newContent.innerHTML;
                }
            } else {
                console.error('Element with id #digiteks_hocr_content not found in the uploaded file.');
            }
        };
        reader.readAsText(file);
    }
}