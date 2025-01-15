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

function getAlignmentClass(paragraph, globalBounds) {
    const bbox = paragraph.getAttribute('title').match(/bbox (\d+) (\d+) (\d+) (\d+)/);
    if (bbox) {
        const x1 = parseInt(bbox[1], 10);
        const x2 = parseInt(bbox[3], 10);

        const leftPadding = x1 - globalBounds.minX;
        const rightPadding = globalBounds.maxX - x2;

        // Adjust the threshold values more aggressively for right alignment
        if (leftPadding > 20 && rightPadding < 20) { // Lower threshold for right alignment
            return 'align-right';
        } else if (rightPadding > 60 && leftPadding < 60) { // Increased threshold for left alignment
            return 'align-left';
        } else if (leftPadding > 20 && rightPadding > 20) { // Lower threshold for center alignment
            return 'align-center';
        } else {
            return 'align-justify';
        }
    }
    return 'align-justify'; // Default to justify if bbox is not found
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

function getGlobalXBounds(hocrElement, column, globalBounds) {
    let minX = Infinity;
    let maxX = -Infinity;

    const paragraphs = hocrElement.getElementsByClassName('ocr_par');
    
    Array.from(paragraphs).forEach(paragraph => {
        const bbox = paragraph.getAttribute('title').match(/bbox (\d+) (\d+) (\d+) (\d+)/);
        if (bbox) {
            const x1 = parseInt(bbox[1], 10);
            const x2 = parseInt(bbox[3], 10);

            const midX = (globalBounds.minX + globalBounds.maxX) / 2;

            if ((column === 'left' && x1 < midX) || (column === 'right' && x1 >= midX)) {
                if (x1 < minX) minX = x1;
                if (x2 > maxX) maxX = x2;
            }
        }
    });

    return { minX, maxX };
}

function getColumnClass(paragraph, globalBounds) {
    const bbox = paragraph.getAttribute('title').match(/bbox (\d+) (\d+) (\d+) (\d+)/);
    if (bbox) {
        const x1 = parseInt(bbox[1], 10);
        const midX = (globalBounds.minX + globalBounds.maxX) / 2;
        return x1 < midX ? 'column-left' : 'column-right';
    }
    return '';
}

function hocrToPlainHtml(hocrElement) {
    let plainHtml = "";

    // Get global minimum and maximum x-coordinates for the entire text
    const globalBounds = getGlobalBounds(hocrElement);

    // Separate bounds for left and right columns
    const leftColumnBounds = getGlobalXBounds(hocrElement, 'left', globalBounds);
    const rightColumnBounds = getGlobalXBounds(hocrElement, 'right', globalBounds);

    // Get all paragraph blocks
    const paragraphs = hocrElement.getElementsByClassName('ocr_par');
    
    Array.from(paragraphs).forEach(paragraph => {
        const columnClass = getColumnClass(paragraph, globalBounds);
        const alignmentClass = columnClass === 'column-left'
            ? getAlignmentClass(paragraph, leftColumnBounds)
            : getAlignmentClass(paragraph, rightColumnBounds);
        
        plainHtml += `<p class="${alignmentClass} ${columnClass}">`;

        const words = paragraph.getElementsByClassName('ocrx_word');
        Array.from(words).forEach((word, index) => {
            plainHtml += word.textContent;
            if (index < words.length - 1) {
                plainHtml += " ";
            }
        });

        plainHtml += "</p>\n";
    });

    return plainHtml;
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