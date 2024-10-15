$(document).ready(function() {
    // Function to load content based on the clicked link
    function loadContent(page) {
        $('#content').load(page);
    }

    // Load the home page by default
    loadContent('./Pages/Dashboard.html');

    // Handle navigation link clicks
    $('.nav-link').on('click', function(e) {
        e.preventDefault();
        var page = $(this).attr('href');
        loadContent(page);
    });
});
