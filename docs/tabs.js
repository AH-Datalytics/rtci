// tabs.js

function openTab(tabName) {
    // Hide all tab contents
    var tabContents = document.getElementsByClassName('tab-content');
    for (var i = 0; i < tabContents.length; i++) {
        tabContents[i].style.display = 'none';
    }
    // Remove active class from all tab links
    var tabLinks = document.getElementsByClassName('tab-link');
    for (var i = 0; i < tabLinks.length; i++) {
        tabLinks[i].classList.remove('active');
    }
    // Show the current tab content and add active class to the clicked tab link
    document.getElementById(tabName).style.display = 'block';
    event.currentTarget.classList.add('active');
}

// Initialize the dashboard tab as active
document.addEventListener('DOMContentLoaded', function() {
    document.getElementById('dashboard').style.display = 'block';
});
