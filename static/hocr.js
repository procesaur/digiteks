function editable() {
    const words = document.querySelectorAll('.ocrx_word');

    for ( i = 0; i < words.length; i++ ) {
        var val = 0.9 - parseInt(words[i].title.substring(words[i].title.lastIndexOf(' ') + 1))/100;
        words[i].style.background  = "rgba(255,255,0,"+val+")"; 
        words[i].contentEditable = 'true';
    }  
}
window.onload = editable;
