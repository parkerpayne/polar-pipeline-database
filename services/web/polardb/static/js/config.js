$(document).ready(function() {
    $('.PathField').prop('disabled', true);
    $('.MergedField').prop('disabled', true);
    $('.DataField').prop('disabled', true);
});

function editToggle(path_type){
    $('.'+path_type+'Field').each(function() {
        $(this).prop('disabled', function(i, value) {
            return !value;
        });
    });
    $('.new'+path_type+'Button').each(function() {
        $(this).toggle();
    });
    $('.confirm'+path_type+'Button').each(function() {
        $(this).toggle();
    });
    $('.delete'+path_type+'Button').each(function(){
        $(this).toggle();
    });

    deletePath(path_type);
}

function addNewPath(path_type){
    var inputline = `
    <div class="input-group mb-2">
        <input class="form-control `+path_type+`Field" type="text" value="">
        <button class="btn btn-danger delete`+path_type+`Button" type="button" onclick="deletePath('`+path_type+`')">Delete</button>
    </div>
    `
    var text_input_container = document.getElementById(path_type+'Container');
    text_input_container.insertAdjacentHTML('beforeend', inputline);
    deletePath(path_type);
}

function confirmChanges(path_type){
    var paths = []
    $('.'+path_type+'Field').each(function() {
        if($(this)[0].value !== ''){
            paths.push($(this)[0].value);
        }else{
            $(this).closest('.input-group').remove();
        }
    });

    $.ajax({
        url: '/update_paths',
        type: 'POST',
        data: JSON.stringify({
            path_type: path_type,
            path_list: paths
        }),
        contentType: 'application/json',
        success: function(response) {
            editToggle(path_type);
        },
        error: function(xhr, status, error) {
            var errorMessage = xhr.responseJSON.error;
            alert(errorMessage);
        }
    });

    
}

function deletePath(path_type){
    $('.delete'+path_type+'Button').on('click', function() {
        $(this).closest('.input-group').remove();
    });
}