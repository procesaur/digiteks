const lc = '.ocr_line, .ocr_caption, .ocr_textfloat, .ocr_header, .ocr_image, .break';
const originalContents = new Map();
const historyQueue = [];
const redoQueue = [];



function hocrToPlainHtml(hocrString) {
    const parser = new DOMParser();
    const hocrElement = parser.parseFromString(hocrString, "text/html");

    let plainHtml = '';
    const paragraphs = hocrElement.querySelectorAll('.ocr_par');
    paragraphs.forEach(function (paragraph, paragraphIndex) {
        // Get alignment class
        const align = paragraph.getAttribute('xalign');
        plainHtml += `<p class="${getAlignmentClass(align)}">`;

        // Process lines within the paragraph
        const lines = paragraph.querySelectorAll(lc);
        lines.forEach(function (line) {
            const words = line.querySelectorAll('.ocrx_word');
            words.forEach(function (word) {
                plainHtml += word.textContent;
            });
        });

        // Append images within the paragraph
        const imgs = paragraph.querySelectorAll('img');
        imgs.forEach(function (img) {
            plainHtml += img.outerHTML;
        });

        plainHtml += '</p>\n';
    });

    return postprocess_html(plainHtml);
}

function hocrToPlainText(hocrString) {
    const parser = new DOMParser();
    const hocrElement = parser.parseFromString(hocrString, "text/html");
    var plainText = '';

    var paragraphs = hocrElement.querySelectorAll('.ocr_par');
    paragraphs.forEach(function(paragraph) {
        var words = paragraph.querySelectorAll('.ocrx_word');
        words.forEach(function(word) {
            plainText += word.textContent;
        });
        plainText += '\n';
    });


    return plainText;
}

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
    var body = document.querySelector('body');
    var head = document.querySelector('head');
    dwn(`<!DOCTYPE html><html><head>${head.innerHTML}</head><body>${body.innerHTML}</body></html>`, "text/html", filename, ".html");
}

function getHtml(filename){
    var hocrContent = document.getElementById("digiteks_hocr_content");
    htmls = split(hocrContent)
    htmls.forEach((html) => dwn(`<!DOCTYPE html><html><head><style>img {max-width:90vw}</style><meta charset="UTF-8"><link href="${css_href}" type="text/css" rel="stylesheet"></head><body>${hocrToPlainHtml(html)}</body></html>`, "text/html", filename, ".html"));
}

function getText(filename){
    var hocrContent = document.getElementById("digiteks_hocr_content");
    dwn(hocrToPlainText(hocrContent), "text/plain", filename, ".txt");
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
function handleStreaming(sessionId, loadingGif, images, imagesDataElement) {
    const eventSource = new EventSource(`/stream/${sessionId}`);

    eventSource.onmessage = function(event) {
        const data = JSON.parse(event.data);
        const resultElement = document.createElement('div');
        resultElement.innerHTML =  data.html;

        // Append the result to the digiteks_hocr_content element
        const resultsDiv = document.getElementById('digiteks_hocr_content');
        resultsDiv.appendChild(resultElement);

        if (images.length != 0) {
            const pages = resultElement.querySelectorAll('.ocr_page');

            pages.forEach(page => {
                originalContents.set(page.id, page.innerHTML);
            });
        }
        // Remove the processed image from the images data
        images.shift();
        imagesDataElement.dataset.images = JSON.stringify(images);

        // Remove the hidden div containing images data when all images are processed
        if (images.length === 0) {
            loadingGif.style.display = 'none';
            insert_breaks(resultsDiv, break_regex, break_message);
            const pages2 = resultsDiv.querySelectorAll('.ocr_page');
            pages2.forEach(page => {
                originalContents.set(page.id, page.innerHTML);
            });
            eventSource.close();
            const imagesDataDiv = document.getElementById('imagesData');
            if (imagesDataDiv != null){
                imagesDataDiv.remove();
            }

        }
    };

    eventSource.onerror = function(event) {
        //console.error('EventSource error:', event); // Debugging: Print error event
        // Hide the loading GIF when done or on error
        loadingGif.style.display = 'none';
        eventSource.close();
        const imagesDataDiv = document.getElementById('imagesData');
        if (imagesDataDiv != null){
            imagesDataDiv.remove();
        }
    };
}

function stream_ocr(lang, loadingGif, imagesDataElement ) {

    if (imagesDataElement){
        let images = JSON.parse(imagesDataElement.dataset.images);
        loadingGif.style.display = 'block';
        // Send the images data to the /start_ocr endpoint
        fetch(`/ocr/${lang}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ images: images })
        })
        .then(response => response.json())
        .then(data => {
            console.log('Start OCR response:', data); // Debugging: Print start OCR response
            if (data.status === 'OCR started') {
                handleStreaming(data.session_id, loadingGif, images, imagesDataElement);
            }
        })
        .catch(error => {
            console.error('Fetch error:', error); // Debugging: Print fetch error
            loadingGif.style.display = 'none';
            insert_breaks(document.getElementById('digiteks_hocr_content'), break_regex, break_message);
        });
    }
    else{
        loadingGif.style.display = 'none';
    }
}


function handleTextChange(event) {
    const oldValue = event.target.dataset.original.trim();
    const newValue = event.target.innerText.trim();
    if (oldValue != newValue){
        event.target.style  = "--red:0; --conf:0; --blue: 0";
    }
    else{
        event.target.style  = "--red:255; --conf:1; --blue: 0";
    }
    saveCurrentState(event);
}

function openhocrsettings(event){
    const popup = document.getElementById('popup_settings_hocr');
    const topconfSlider = document.getElementById('topconfSlider');
    const saturationSlider = document.getElementById('saturationSlider');
    const topconfValue = document.getElementById('topconfValue');
    const saturationValue = document.getElementById('saturationValue');
    
    topconfSlider.addEventListener('input', function () {
        const value = topconfSlider.value;
        document.documentElement.style.setProperty('--topconf', value);
        topconfValue.textContent = value; // Show the value next to the slider
    });

    saturationSlider.addEventListener('input', function () {
        const value = saturationSlider.value;
        document.documentElement.style.setProperty('--saturation', value);
        saturationValue.textContent = value; // Show the value next to the slider
    });
    popup.style.display = 'block';
}

function closehocrsettings(event){
    const popup = document.getElementById('popup_settings_hocr');
    popup.style.display = 'none';
}

function getSelected(){
    var lines = document.querySelectorAll(lc);
    var elements = [];
    var parentPages = new Set();
    lines.forEach(function(line) {
        var checkbox = line.querySelector('input[type="checkbox"]');
        if (checkbox && checkbox.checked) {
            elements.push(line);
            var parentPage = line.closest('.ocr_page');
            if (parentPage) {
                parentPages.add(parentPage);
            }
        }
    });

    const areas = new Map();
    elements.forEach(element => {
        if (element.classList.contains("break")){
            areas.set(element, []);
            areas.get(element).push(element);
        }
        else{
            const parentArea = element.closest('.ocr_par');
            if (parentArea) {
                if (!areas.has(parentArea)) {
                    areas.set(parentArea, []);
                }
                areas.get(parentArea).push(element);
            }
        }
    });
    return {elements: elements,
            areas: areas,
            pages:  Array.from(parentPages)
    };
}

function checkall(event){
    const childCheckboxes = event.target.parentElement.querySelectorAll('.dynamic-checkbox');
    childCheckboxes.forEach(childCheckbox => { childCheckbox.checked = event.target.checked;});
}

function MoveUp() {
    const selected = getSelected();
    const areas = selected.areas;
    const pages = selected.pages;

    areas.forEach((selectedLines, area) => {
        const allLines = Array.from(area.querySelectorAll(lc));
        var parcheckbox = area.querySelector('.par-checkbox');
        if (selectedLines.length >= allLines.length && parcheckbox && parcheckbox.checked) {
            // If all lines are selected, move the entire '.ocr_par'
            const prevArea = area.previousElementSibling;
            if (prevArea && prevArea.classList.contains('ocr_par')) {
                area.parentNode.insertBefore(area, prevArea);
            }
        } else {
            // If not all lines are selected, move selected lines within the '.ocr_par'
            selectedLines.forEach(line => {
            const prevSibling = line.previousElementSibling;
            if (prevSibling && prevSibling.tagName.toLowerCase()=="span") {
                area.insertBefore(line, prevSibling); // Switch with previous sibling
            } else {
                const prevArea = area.previousElementSibling;
                if (prevArea && prevArea.classList.contains('ocr_par')) {
                    prevArea.appendChild(line); // Move to the end of the previous '.ocr_par'
                }
            }
        });
        }
    });
    saveCurrentStatePages(pages);
}

function MoveDown() {
    const selected = getSelected();
    const areas = selected.areas;
    const pages = selected.pages;

    areas.forEach((selectedLines, area) => {
        const allLines = Array.from(area.querySelectorAll(lc));
        var parcheckbox = area.querySelector('.par-checkbox');
        if (selectedLines.length >= allLines.length && parcheckbox && parcheckbox.checked) {
            // If all lines are selected, move the entire '.ocr_par'
            const nextArea = area.nextElementSibling;
            if (nextArea && nextArea.classList.contains('ocr_par')) {
                area.parentNode.insertBefore(nextArea, area);
            }
        } else {
            // If not all lines are selected, move selected lines within the '.ocr_par'
            selectedLines.forEach(line => {
                const nextSibling = line.nextElementSibling;

                if (nextSibling && nextSibling.tagName.toLowerCase()=="span") {
                    area.insertBefore(nextSibling, line); // Switch with next sibling
                } else {
                    const nextArea = area.nextElementSibling;
                    if (nextArea && nextArea.classList.contains('ocr_par')) {
                        nextArea.insertBefore(line, nextArea.firstChild); // Move to the beginning of the next '.ocr_par'
                    }
                }
            });
        }
    });
    saveCurrentStatePages(pages);
}

function MaybeDelete(){
if (event.key === 'Delete') { 
    event.preventDefault();
    event.target.innerHTML = "";
    }
}


function saveCurrentState(event) {
    const parentPage = event.target.closest('.ocr_page');
    if (parentPage) {
        saveCurrentStatePage(parentPage)
    }
}


function saveCurrentStatePage(page) {
    historyQueue.push({
        id: page.id,
        newValue: [page.innerHTML]
    });
    redoQueue.length = 0; 
    if (historyQueue.length > 10) {
        historyQueue.shift(); 
    }      
}


function saveCurrentStatePages(pages) {
    pages.forEach(function(page) {
        saveCurrentStatePage(page)
    });   
}


function undo() {
    if (historyQueue.length > 0) {
        const lastChange = historyQueue.pop();
        redoQueue.push(lastChange);
        const page = document.getElementById(lastChange.id);
        const originalValue = originalContents.get(lastChange.id);
        page.innerHTML = originalValue; // Restore the original state
        originalContents.set(lastChange.id, originalValue); // Reset original state
        // Apply remaining changes
        historyQueue.forEach(change => {
            if (change.id === lastChange.id) {
                page.innerHTML = change.newValue;
            }
        });
    }
}

function redo() {
    if (redoQueue.length > 0) {
        const lastRedo = redoQueue.pop();
        historyQueue.push(lastRedo);
        const page = document.getElementById(lastRedo.id);
        page.innerHTML = lastRedo.newValue;
    }
}

function Uncheck() {
    const checkboxes = document.querySelectorAll('.dynamic-checkbox');
    checkboxes.forEach(checkbox => { checkbox.checked = false; }); 
}


function Figurize() {
    const selected = getSelected();
    const pages = selected.pages;
    const areas = Array.from(selected.areas.keys());

    var x1s = [];
    var x2s = [];
    var y1s = [];
    var y2s = [];
    var image_ids = [];

    areas.forEach(function(element) {
        var x1 = element.getAttribute('x1');
        var x2 = element.getAttribute('x2');
        var y1 = element.getAttribute('y1');
        var y2 = element.getAttribute('y2');
        var image_id = element.getAttribute('image_id');
        
        if (x1 !== null) {
            x1s.push(x1);
        }
        if (x2 !== null) {
            x2s.push(x2);
        }
        if (y1 !== null) {
            y1s.push(y1);
        }
        if (y2 !== null) {
            y2s.push(y2);
        }
        if (image_id !== null) {
            image_ids.push(image_id);
        }
    });

    const allSameImageId = image_ids.every((val, i, arr) => val === arr[0]);

    if (!allSameImageId) {
        console.log('Сви параграфи морају бити са исте стране.');
        return;
    }
    
    const image_id = image_ids[0];
    const min_x1 = Math.min(...x1s);
    const min_y1 = Math.min(...y1s);
    const max_x2 = Math.max(...x2s);
    const max_y2 = Math.max(...y2s);

    var originalImg = document.getElementById(image_id);
    // Create a canvas to crop the image
    var canvas = document.createElement('canvas');
    var ctx = canvas.getContext('2d');

    // Set canvas dimensions to the crop size
    canvas.width = max_x2 - min_x1;
    canvas.height = max_y2 - min_y1;

    // Draw the cropped image onto the canvas
    ctx.drawImage(originalImg, min_x1, min_y1, canvas.width, canvas.height, 0, 0, canvas.width, canvas.height);

    // Get the cropped image data URL
    var croppedImageSrc = canvas.toDataURL('image/jpeg');

    // Create new img element with the cropped image as src
    var newImg = document.createElement('img');
    newImg.src = croppedImageSrc;
    
    // Create a new span element with class="ocr_par"
    var newSpan = document.createElement('p');
    var newLine = document.createElement('span');
    newSpan.className = 'ocr_par';
    newLine.className = 'ocr_image';
    newSpan.setAttribute('x1', min_x1);
    newSpan.setAttribute('y1', min_y1);
    newSpan.setAttribute('x2', max_x2);
    newSpan.setAttribute('y2', max_y2);
    newSpan.setAttribute('image_id', image_id);

    const checkbox = document.createElement('input');
    checkbox.type = 'checkbox';
    checkbox.className = 'dynamic-checkbox';
    newLine.style.position = 'relative';

    const checkbox2 = document.createElement('input');
    checkbox2.type = 'checkbox';
    checkbox2.className = 'dynamic-checkbox par-checkbox';

    var button = document.createElement("button");
    button.innerHTML = "🔍";  
    button.setAttribute("onclick", "showPopupevent(event)");
    button.setAttribute("style", "float:right");

    newLine.insertBefore(checkbox, newLine.firstChild);
    newSpan.insertBefore(button, newSpan.firstChild);
    newSpan.insertBefore(checkbox2, newSpan.firstChild);

    newLine.appendChild(newImg);
    newSpan.appendChild(newLine);
    newSpan.setAttribute("onclick", "checkall(event)");
    areas.forEach(function(element, index) {
        if (index === 0) {
            element.parentNode.replaceChild(newSpan, element);
        } else {
            element.remove();
        }
    });
    saveCurrentStatePages(pages);
}

function deleteCheckedElements() {
    const selected = getSelected();
    const areas = selected.areas;
    const pages = selected.pages;

    areas.forEach((selectedLines, area) => {
        const allLines = Array.from(area.querySelectorAll(lc));
        if (selectedLines.length === allLines.length) {
            area.remove();
        } else {
            selectedLines.forEach(line => {
                line.remove();
            });
        }
    });
    saveCurrentStatePages(pages);
}

function VerifyBulk() {
    const selected = getSelected();
    const elements = selected.elements;
    const pages = selected.pages;

    elements.forEach(line => {
        const words = line.querySelectorAll('.ocrx_word');
        words.forEach(word => {
            word.style  = "--red:255; --conf:1";
        });
    });
    saveCurrentStatePages(pages);
}

function add_break() {
    const selected = getSelected();
    const areas = selected.areas;
    const pages = selected.pages;
    areas.forEach((selectedLines, area) => {
        insert_break_before(area);
    });
    saveCurrentStatePages(pages);
}


function showPopup_old(image_id, x1, x2, y1, y2) {
    if (x1 && x2 && y1 && y2 && image_id){
        var img = document.getElementById(image_id);
        var canvas = document.getElementById('canvas');
        var ctx = canvas.getContext('2d');

        var cropWidth = x2 - x1;
        var cropHeight = y2 - y1;
        canvas.width = cropWidth;
        canvas.height = cropHeight;
        var image = new Image();
        image.src = img.src;
        image.onload = function() {
            ctx.drawImage(image, x1, y1, cropWidth, cropHeight, 0, 0, cropWidth, cropHeight);
        };

        document.getElementById('overlay').style.display = 'block';
        document.getElementById('popup').style.display = 'block';
    }
}

function mark_text(canvas, x1, x2, y1, y2, padding, scaleX, scaleY){
    var ctx = canvas.getContext('2d');
    ctx.strokeStyle = 'red';
    ctx.lineWidth = 2;
    ctx.strokeRect(x1 * scaleX - padding, y1 * scaleY - padding, (x2 - x1) * scaleX + 2*padding, (y2 - y1) * scaleY + 2*padding);
}

function MarkAndZoom(image_id, x1, x2, y1, y2, zoom=2, padding = 4) {
    if (x1 && x2 && y1 && y2 && image_id) {
        x1 = parseInt(x1);
        x2 = parseInt(x2);
        y1 = parseInt(y1);
        y2 = parseInt(y2);
        var cont = document.getElementById("SaveimagesData");
        cont.style.width = '100%';
        var img = document.getElementById(image_id);
        var canvas = document.getElementById("c" + image_id);

        canvas.width = img.clientWidth;
        canvas.height = img.clientHeight;
        var scaleX = canvas.width / img.naturalWidth;
        var scaleY = canvas.height / img.naturalHeight;

        contW = cont.parentElement.offsetWidth;
        contH = cont.parentElement.offsetHeight;
        rectW = x2 - x1
        rectH = y2 - y1
        if (contW<rectW*scaleX*zoom || contH<rectH*scaleY*zoom){
            zoom = 1;
        }
        cont.style.width = `${zoom*100}%`;

        mark_text(canvas, x1, x2, y1, y2, padding, scaleX, scaleY)

        const rectCenterX = (x1 + rectW / 2) * scaleX * zoom;
        const rectCenterY = (y1 + rectH / 2) * scaleY * zoom;
        const containerCenterX = contW / 2;
        const containerCenterY = contH / 2;

        // Calculate cumulative offset for y-axis
        const images = Array.from(document.querySelectorAll('#SaveimagesData img'));
        let cumulativeOffsetY = 0;
        for (const imag of images) {
            if (imag.id === image_id) break;
            cumulativeOffsetY += imag.offsetHeight;
        }

        const offsetX = rectCenterX - containerCenterX;
        const offsetY = rectCenterY  + cumulativeOffsetY - containerCenterY;

        cont.parentElement.scrollLeft = Math.max(0, offsetX);
        cont.parentElement.scrollTop = Math.max(0, offsetY);
    }
}


function hidePopup() {
    document.getElementById('overlay').style.display = 'none';
    document.getElementById('popup').style.display = 'none';
}

function showPopupevent(event) {
    const parent = event.target.parentElement;
    const image_id = parent.getAttribute('image_id');
    const x1 = parent.getAttribute('x1');
    const x2 = parent.getAttribute('x2');
    const y1 = parent.getAttribute('y1');
    const y2 = parent.getAttribute('y2');
    MarkAndZoom(image_id, x1, x2, y1, y2);
}

function setupZoomAndDrag(container) {
    let scale = 1;
    let isDragging = false;
    let startX, startY;

    function zoom(event) {
        
        if (event.ctrlKey) { // Check if Ctrl key is pressed
            event.preventDefault();
            const newScale = scale + event.deltaY * -0.001;
            if (newScale >= 1 && newScale <= 3) {
                scale = newScale;
                container.style.width = `${scale * 100}%`;
            }
        }
    }

    function startDrag(event) {
        isDragging = true;
        startX = event.clientX;
        startY = event.clientY;
        scrollLeft = container.parentElement.scrollLeft;
        scrollTop = container.parentElement.scrollTop;
        container.style.cursor = 'grabbing'; 
    }

    function drag(event) {
        if (isDragging) {
            event.preventDefault();
            const x = event.clientX - startX;
            const y = event.clientY - startY;
            container.parentElement.scrollLeft = scrollLeft - x;
            container.parentElement.scrollTop = scrollTop - y;
        }
    }

    function stopDrag() {
        isDragging = false;
        container.style.cursor = 'grab';
    }

    container.addEventListener('mousedown', startDrag);
    document.addEventListener('mousemove', drag);
    document.addEventListener('mouseup', stopDrag);
    container.addEventListener('wheel', zoom, { passive: false });
}

function split(doc){
    const brojElements = Array.from(doc.querySelectorAll(".break"));

    if (brojElements.length === 0) {
        return [doc];
    }
    const splitDocs = [];

    brojElements.forEach((broj, index) => {
        const newDoc = document.implementation.createHTMLDocument("Split Doc");
        //newDoc.body.appendChild(broj.cloneNode(true));
        let currentNode = broj.nextSibling;
        while (currentNode && !currentNode.matches?.(".break")) {
            const nextNode = currentNode.nextSibling; // Save reference to the next node
            newDoc.body.appendChild(currentNode.cloneNode(true)); // Clone and append to the new document
            currentNode = nextNode;
        }
        splitDocs.push(newDoc.documentElement.outerHTML);
    });
    return splitDocs;
}

function findBestConsecutiveKeys(data, distance = 4, allowGap = true) {
    const keys = Object.keys(data).map(Number); // Extract keys as numbers
    const values = Object.values(data); // Extract values
    let result = [];

    // Iterate through the values
    values.forEach((value, index) => {
        let currentSequence = [{ key: keys[index], value }]; // Start a new sequence with the current item

        for (let i = 0; i < values.length; i++) {
            if (i === index) continue; // Skip the current value itself

            const nextKey = keys[i];
            const nextValue = values[i];
            const keyDifference = nextKey - currentSequence[currentSequence.length - 1].key;
            const valueDifference = nextValue - currentSequence[currentSequence.length - 1].value;

            // Check if conditions for consecutiveness (and key distance) are met
            if (
                keyDifference >= distance &&
                (valueDifference === 1 || (allowGap && valueDifference === 2))
            ) {
                currentSequence.push({ key: nextKey, value: nextValue });
            }
        }
        // Add the found sequence to the result
        if (currentSequence.length > 1) {
            result.push(currentSequence);
        }
    });

    // Find the longest sequence
    let longestSequence = result.reduce((longest, current) => 
        current.length > longest.length ? current : longest, []);

    // Extract and return the keys of the longest sequence
    const longestKeys = longestSequence.map(item => item.key);
    return longestKeys;
}

function insert_break_before(x){
    const checkbox = document.createElement('input');
    checkbox.type = 'checkbox';
    checkbox.className = 'dynamic-checkbox par-checkbox';

    const breakElement = document.createElement("p");
    breakElement.classList.add("break");
    breakElement.innerHTML = "BREAK"

    breakElement.style.position = 'relative'; 
    breakElement.insertBefore(checkbox, breakElement.firstChild);

    x.parentNode.insertBefore(breakElement, x);
}

function insert_breaks(doc, break_regex="", message="") {
    if (break_regex != ""){
        const possibleIndexes = {};
        const lines = doc.querySelectorAll(lc); // Adjust for JS DOM
    
        lines.forEach((line, i) => {
            const words = line.querySelectorAll(".ocrx_word");
            if (words.length === 1) {
                const word = words[0].textContent.trim();
                if (word.match(break_regex) != null) {
                    possibleIndexes[i] = parseInt(word, 10); // Save index and numeric value
                }
            }
        });
    
        const bestIndexes = findBestConsecutiveKeys(possibleIndexes);
        const filteredLines = Array.from(lines).filter((_, i) => bestIndexes.includes(i));
        const classList = lc.replace(/\./g, '').split(', '); // Remove dots and split into an array

        filteredLines.forEach(line => {
            // Step 1: Check if the line has previous and next siblings
            const prevSiblings = [];
            let prev = line.previousElementSibling; // Only consider element siblings
            while (prev && classList.some(cls => prev.classList.contains(cls))) {
                prevSiblings.unshift(prev); // Collect previous siblings
                prev = prev.previousElementSibling;
            }
    
            const nextSiblings = [];
            let next = line.nextElementSibling; // Only consider element siblings
            while (next && classList.some(cls => next.classList.contains(cls))) {
                nextSiblings.push(next); // Collect next siblings
                next = next.nextElementSibling;
            }
    
            // Get the parent ".ocrx_par" element
            const parentPar = line.closest(".ocr_par");
            if (!parentPar) {
                console.warn("No parent with class '.ocr_par' found for", line);
                return;
            }
    
            // Step 2: Split the parent ".ocrx_par" into groups
            const parentAttributes = Array.from(parentPar.attributes); // Copy original attributes
            const buttonsAndInputs = parentPar.querySelectorAll(":scope > button, :scope > input"); // Select all buttons and inputs

            // Create new parent for previous siblings (if exist)
            if (prevSiblings.length > 0) {
                const newPrevPar = document.createElement("p");
                newPrevPar.classList.add("ocr_par");
                parentAttributes.forEach((attr) => newPrevPar.setAttribute(attr.name, attr.value));
                prevSiblings.forEach((sibling) => newPrevPar.appendChild(sibling));
                parentPar.parentNode.insertBefore(newPrevPar, parentPar);
                buttonsAndInputs.forEach((element) => {
                    const clonedElement = element.cloneNode(true); // Clone the element (true for deep cloning)
                    newPrevPar.insertBefore(clonedElement, newPrevPar.firstChild); // Prepend cloned element to newPrevPar // Append cloned element to newPrevPar
                });
            }
    
            // Create new parent for next siblings (if exist)
            if (nextSiblings.length > 0) {
                const newNextPar = document.createElement("p");
                newNextPar.classList.add("ocr_par");
                parentAttributes.forEach((attr) => newNextPar.setAttribute(attr.name, attr.value));
                nextSiblings.forEach((sibling) => newNextPar.appendChild(sibling));
                parentPar.parentNode.insertBefore(newNextPar, parentPar.nextSibling);
                buttonsAndInputs.forEach((element) => {
                    const clonedElement = element.cloneNode(true); // Clone the element (true for deep cloning)
                    newNextPar.insertBefore(clonedElement, newNextPar.firstChild); // Prepend cloned element to newPrevPar // Append cloned element to newPrevPar
                });
            }

            insert_break_before(parentPar);

        });
        if (message != ""){
            console.log(message);
        }
        
    }
}
