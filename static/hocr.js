function editable() {
    const elements = document.querySelectorAll('.ocrx_word');

    for ( i = 0; i < elements.length; i++ ) {
        var val = 0.9 - parseInt(elements[i].title.substring(elements[i].title.lastIndexOf(' ') + 1))/100;
        elements[i].style.background  = "rgba(255,255,0,"+val+")"; 
        elements[i].contentEditable = 'true';
    }  
}
window.onload = editable;

