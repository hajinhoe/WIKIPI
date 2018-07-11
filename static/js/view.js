$(document).ready(function () {
    if (document.getElementById('index') !== undefined) {
        var index_elements = document.getElementById('index').children;
        var margin_length;
        for (var i = 1; i < index_elements.length; i++) {
            if (index_elements[i].getElementsByTagName('a')[0] != undefined) {
                margin_length = ((index_elements[i].getElementsByTagName('a')[0].textContent.match(/\./g) || []).length - 1) * 10;
                index_elements[i].getElementsByTagName('a')[0].parentNode.style.marginLeft = margin_length + 'px';
        }
    }
    }
});