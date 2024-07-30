function openTab(event, tabName) {
    // Hide all tab contents
    var tabContents = document.getElementsByClassName('tab-content');
    for (var i = 0; i < tabContents.length; i++) {
        tabContents[i].style.display = 'none';
        tabContents[i].classList.remove('active');
    }
    // Remove active class from all tab links
    var tabLinks = document.getElementsByClassName('tab-link');
    for (var i = 0; i < tabLinks.length; i++) {
        tabLinks[i].classList.remove('active');
    }
    // Show the current tab content and add active class to the clicked tab link
    document.getElementById(tabName).style.display = 'block';
    document.getElementById(tabName).classList.add('active');
    event.currentTarget.classList.add('active');
}

// Initialize the dashboard tab as active
document.addEventListener('DOMContentLoaded', function() {
    document.getElementById('dashboard').style.display = 'block';
    document.getElementById('dashboard').classList.add('active');
});
