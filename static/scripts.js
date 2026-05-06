const copyPrefabs = {
    "button": '<a href="https://eli.toys"><img src="https://eli.toys/static/img/88x31/eli.gif" width="88" height="31" alt="eli.toys"/></a>'
}

function copyToClipboard(text) {

    console.log(text);

    if (text in copyPrefabs) {
        var copyText = copyPrefabs[text];
    } else {
        var copyText = text;
    }
    console.log(copyText);

    navigator.clipboard.writeText(copyText);

    if (text == "button") {
        alert("copied html to clipboard!\n\nfeel free to hotlink, i dont mind :3");
    } else {
        alert("copied address to clipboard!");
    }
}