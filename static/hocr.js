function editable(top=0.94, saturation=0.5) {
    const words = document.querySelectorAll('.ocrx_word');

    for ( i = 0; i < words.length; i++ ) {
        var conf = parseInt(words[i].title.substring(words[i].title.lastIndexOf(' ')))/100;
        words[i].style  = "--conf:"+conf;
        words[i].contentEditable = 'true';
    }  
}
window.onload = editable;
