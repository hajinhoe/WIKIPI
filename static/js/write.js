//임시
$(document).ready(function() {
    var caretpos, lastitem;
    $('input[type=text], textarea').on('click', function(){
        lastitem = $(this).attr('id');
        caretpos = $('#'+lastitem)[0].selectionStart;
    });
    $('#input_tab').click(function(event) {
        event.preventDefault();

        // this is fine
        var char = '\t'

        textval = $('#'+lastitem).val();
        $('#'+lastitem).val(textval.substring(0, caretpos) + char + textval.substring(caretpos) );
        // update 'element' content here by inserting 'char'
    });
});