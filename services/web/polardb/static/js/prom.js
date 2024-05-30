function switchTab(button) {
    // Remove 'active' class from all buttons
    document.querySelectorAll('.nav-link').forEach(btn => {
        btn.classList.remove('active');
    });

    // Add 'active' class to the clicked button
    button.classList.add('active');

    // Hide all tab contents
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.style.display = 'none';
    });

    // Show the corresponding tab content based on data-value attribute
    const tabId = button.getAttribute('data-value');
    const divId = tabId;
    document.getElementById('needs-work').hidden = true;
    document.getElementById('ready-to-delete').hidden = true;
    document.getElementById(divId).hidden = false;
}

var thinkingboxes = [];
var greenboxes = [];
var redboxes = [];

function removeCardFromThinkingBoxes(card) {
    // Find the index of the card in the thinkingboxes array
    const index = thinkingboxes.indexOf(card);
    
    // If the index is found (not -1), remove the card from the array
    if (index !== -1) {
        thinkingboxes.splice(index, 1);
    }
}

function compareDirectories(card){
    card.classList.remove('delete-card');
    card.classList.remove('incorrect');
    thinkingboxes.push(card);
    const [prom_path, syn_path] = card.getAttribute('data-value').split(',');
    // console.log(prom_path);
    // console.log(syn_path);
    $.ajax({
        url: '/comparedirectories',
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({
            prom: prom_path,
            syn: syn_path
        }),
        success: function(response) {
            // console.log('in handleAnimationEnd function');
            // console.log('Card:', card);
            // console.log('Response:', response);
            
            const hover_text = card.querySelector('#hover-text');
            var errortext = '';
            removeCardFromThinkingBoxes(card);
            if (response.includes('file_count')) {
                redboxes.push(card);
                errortext += 'File Count Mismatch';
            }
            if (response.includes('file_size')) {
                redboxes.push(card);
                if (errortext) {
                    errortext += '\n';
                }
                errortext += 'File Size Mismatch';
            } 
            if (errortext == ''){
                greenboxes.push(card);
                card.onclick = '';
            }
            hover_text.innerText = errortext;
        },
        error: function(jqXHR, textStatus, errorThrown) {
            // Handle errors (e.g., network error, server error)
            card.classList.add('incorrect');
            errortext = 'SERVER ERROR\n' + textStatus + '\n' + errorThrown;
            console.error('Error occurred:', textStatus, errorThrown);
        }
    });
}

function animateBoxes(){
    thinkingboxes.forEach(element => {
        // console.log(element);
        if (!element.classList.contains('thinking-card')){
            element.classList.add('thinking-card');
        }
        element.classList.toggle('thinking-card-alt');
    });
    greenboxes.forEach(element => {
        if (element.classList.contains('thinking-card')){
            element.classList.remove('thinking-card');
        }
        if (element.classList.contains('thinking-card-alt')){
            element.classList.remove('thinking-card-alt');
        }
        if (!element.classList.contains('correct')){
            element.classList.add('correct');
        }
    });
    redboxes.forEach(element => {
        if (element.classList.contains('thinking-card')){
            element.classList.remove('thinking-card');
        }
        if (element.classList.contains('thinking-card-alt')){
            element.classList.remove('thinking-card-alt');
        }
        if (!element.classList.contains('incorrect')){
            element.classList.add('incorrect');
        }
        
    });
}

setInterval(function () {
    animateBoxes();
}, 2000);