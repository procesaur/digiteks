function prepare(top=0.94, saturation=0.5) {
    const words = document.querySelectorAll('.ocrx_word');

    Array.from(words).forEach(function (word) {
        var conf = parseInt(word.title.substring(word.title.lastIndexOf(' ')))/100;
        word.style  = "--red:255; --conf:"+conf;
        word.dataset.original = word.innerText;
        word.contentEditable = 'true';
        word.setAttribute("onblur", "handleTextChange(event)");
    });

    const pars = document.querySelectorAll('.ocr_carea');

    Array.from(pars).forEach(function (par) {
        const moveUpButton = document.createElement('button');
        moveUpButton.textContent = '↑'; // Unicode arrow up
        moveUpButton.style.position = 'absolute';
        moveUpButton.style.top = '5px';
        moveUpButton.style.right = '30px'; // Move slightly towards the corner
        moveUpButton.style.padding = '3px 5px'; // Smaller size
        moveUpButton.style.fontSize = '14px'; // Smaller font size
        moveUpButton.style.border = 'none'; // Optional: remove border
        moveUpButton.style.backgroundColor = 'transparent'; // Optional: remove background
        moveUpButton.style.cursor = 'pointer'; // Optional: cursor style for better UX
    
        // Create the "Move Down" button
        const moveDownButton = document.createElement('button');
        moveDownButton.textContent = '↓'; // Unicode arrow down
        moveDownButton.style.position = 'absolute';
        moveDownButton.style.top = '5px';
        moveDownButton.style.right = '5px'; // Move closer to the right corner
        moveDownButton.style.padding = '3px 5px'; // Smaller size
        moveDownButton.style.fontSize = '14px'; // Smaller font size
        moveDownButton.style.border = 'none'; // Optional: remove border
        moveDownButton.style.backgroundColor = 'transparent'; // Optional: remove background
        moveDownButton.style.cursor = 'pointer'; // Optional: cursor style for better U
        
        moveUpButton.setAttribute("onclick", "moveup(event)");
        moveDownButton.setAttribute("onclick", "movedown(event)");

        par.style.position = 'relative'; 
        par.appendChild(moveUpButton);
        par.appendChild(moveDownButton);
    }); 
}



window.onload = prepare;