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