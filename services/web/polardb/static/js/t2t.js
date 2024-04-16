$(document).ready(function(){
    $('#searchInput').on('keyup', function(){
        var searchText = $(this).val().toLowerCase();
        $('#cardContainer .card').each(function(){
            var initials = $(this).find('.card-title').text().toLowerCase();
            var id = $(this).find('.card-text').text().toLowerCase();
            if(initials.indexOf(searchText) === -1 && id.indexOf(searchText) === -1){
                $(this).hide();
            }else{
                $(this).show();
            }
        });
        countGuys();
    });
});

function typeFilter(checkbox){
    const grchBox = $('#dropdownGRCh38');
    const t2tBox = $('#dropdownT2T');
    const anyBox = $('#dropdownAny');  
    const typeDropdown = document.getElementById('typeDropdown');          
    const runType = checkbox.value;

    if(runType == 'Any'){
        grchBox.prop('checked', false);
        t2tBox.prop('checked', false);
    } else {
        anyBox.prop('checked', false);
    }
    
    $('#cardContainer .card').each(function(){
        var guyGRChBox = $(this).find('#grchBox');
        var guyT2TBox = $(this).find('#t2tBox');
        
        if(anyBox.prop('checked')){
            $(this).show();
        } else {
            var valid = true;
            if(guyGRChBox.prop('checked') !== grchBox.prop('checked')){
                valid = false;
            }
            if(guyT2TBox.prop('checked') !== t2tBox.prop('checked')){
                valid = false;
            }
            if(valid == false){
                $(this).hide();
            } else {
                $(this).show();
            }
        }
    });

    if(!grchBox.prop('checked') && !t2tBox.prop('checked') && anyBox.prop('checked')){
        typeDropdown.classList.remove('active');
    }else{
        typeDropdown.classList.add('active');
    }

    countGuys();
}

function countGuys() {
    var cardlist = document.querySelectorAll('#guy-inner-card');
    let count = 0;
    cardlist.forEach(element => {
        const computedStyle = window.getComputedStyle(element);
        if (computedStyle.display !== 'none') {
            count++;
        }
    });
    var totaltext = document.getElementById('total-count');
    totaltext.innerText = 'Total: ' + count;
}

function getCardValue(card, category){
    var val = Array.from(card.querySelectorAll('#'+category))[0].innerText;
    return val
}

function sortGuys(category, direction){
    // console.log(category, direction);
    var guyresult = document.querySelectorAll('#guy-card');
    var guys = Array.from(guyresult);
    // console.log(guys);
    var sortedList = [];

    while (guys.length > 0) {
        var max = -1;
        var max_index = -1;
        var index = 0;
        guys.forEach(element => {
            var cardVal = getCardValue(element, category);
            if(max == -1){
                max = cardVal;
                max_index = index;
            }
            if(category == 'az'){
                if(cardVal < max){
                    max = cardVal;
                    max_index = index;
                }
            }else if(category == 'date'){
                if (cardVal > max){
                    max = cardVal;
                    max_index = index;
                }
            }else{
                if(parseInt(cardVal) > parseInt(max)){
                    max = parseInt(cardVal);
                    max_index = index;
                }
            }
            
            index++;
        });
        sortedList.push(guys[max_index]);
        guys.splice(max_index, 1);
    }
    const cardCont = document.getElementById('cardContainer');
    while (cardCont.firstChild) {
        cardCont.removeChild(cardCont.firstChild);
    }
    while(sortedList[0]){
        // console.log(sortedList[0]);
        if(direction == 'up-arrow'){
            cardCont.appendChild(sortedList[sortedList.length-1]);
            sortedList.splice(sortedList.length-1, 1);
        }else{
            cardCont.appendChild(sortedList[0]);
            sortedList.splice(0,1);
        }
        
    }
}  

function toggleButton(button) {
    if(button.classList.contains('active')){
        var arrows = button.children;
        var activeArrow = button.firstChild;
        Array.from(arrows).forEach(element => {
            element.classList.toggle('show-arrow');
            if(element.classList.contains('show-arrow')){
                sortGuys(button.value, element.id);
            }
        });

    }else{
        const filterButtons = document.querySelectorAll("#filterButtons");
        filterButtons.forEach(element => {
            if(element.classList.contains('active')){
                element.classList.remove('active');
                var uparrow = element.children[0];
                var downarrow = element.children[1];
                if(!downarrow.classList.contains('show-arrow')){
                    downarrow.classList.add('show-arrow');
                }
                if(uparrow.classList.contains('show-arrow')){
                    uparrow.classList.remove('show-arrow');
                }
            }
        });
        button.classList.add('active');
        sortGuys(button.value, 'down-arrow');
    }
}
function stopEventPropagation(event) {
    event.stopPropagation();
}

function exportGuys(){
    var exportList = [];
    var cardlist = document.querySelectorAll('#guy-inner-card');
    cardlist.forEach(element => {
        const computedStyle = window.getComputedStyle(element);
        if (computedStyle.display !== 'none') {
            exportList.push(element.dataset.value);
        }
    });
    // console.log(exportList);
    fetch('/export', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(exportList)
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.blob();
    })
    .then(blob => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'polar-db-export.tsv';
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
    })
    .catch(error => {
        // Handle error
        console.error('Error:', error);
    });
}
