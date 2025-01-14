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

function dwn(x, mime, ext){
    var base64doc = btoa(unescape(encodeURIComponent(x))),
    a = document.createElement('a'),
    e = new MouseEvent('click');

    a.download = '{{filename}}' + ext;
    a.href = 'data:' + mime + ';base64,' + base64doc;
    a.dispatchEvent(e);
}

function getHocr(){
    var body = document.getElementById("full_hocr")
    var head = document.getElementById("full_hocr_head")
    dwn(`<!DOCTYPE html><html><head>${head.innerHTML}</head><body>${body.innerHTML}</body></html>`, "text/html", ".html");
}

function getHtml(){
    var html = document.getElementById("full_hocr")
    var x = html.innerHTML;
    dwn(x, "text/xml", ".html");
}

function getText(){
    var html = document.getElementById("full_hocr")
    var x = html.textContent;
    x = x.replace(/\s\s+/g, ' ');
    dwn(x, "text/plain", ".txt");
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