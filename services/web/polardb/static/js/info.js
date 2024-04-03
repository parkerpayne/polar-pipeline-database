const summaryTable = document.getElementById('runSummaryTable');
$(document).ready(function() {
    $('body').on('click', '#runSummaryButton', function() {
        var buttonValue = $(this).data('value');
        $.ajax({
            url: '/runsummary',
            type: 'POST',
            data: {value: buttonValue},
            success: function(response) {
                while (summaryTable.firstChild) {
                    summaryTable.removeChild(summaryTable.firstChild);
                }
                response.forEach(element => {
                    var key = element[0]
                    var val = element[1]
                    var summaryRow = `
                        <tr>
                            <td>
                                `+key+`
                            </td>
                            <td class="summary-value">
                                `+val+`
                            </td>
                        </tr>
                    `;
                    summaryTable.insertAdjacentHTML('beforeend', summaryRow);
                    //append to summaryTable
                });
                // console.log(response);
            },
            error: function(xhr) {
                alert('Error: ' + xhr.responseText);
            }
        });
    });
});

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
    const divId = tabId + '-div';
    document.getElementById('runs-div').hidden = true;
    document.getElementById('fastqs-div').hidden = true;
    document.getElementById('data-folders-div').hidden = true;
    document.getElementById(divId).hidden = false;
}

function exportGuys(){
    var uid = document.getElementById('guy_uid').value;
    // console.log(exportList);
    fetch('/export', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify([uid])
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