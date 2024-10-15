$(document).ready(function () {
    $('#sidebarCollapse').on('click', function () {
        $('#sidebar').toggleClass('active');
    });

    // Load sidebar
    $('#sidebar').load('sidebar.html');

    // Default load page
    loadPage('page1.html');
});

function loadPage(page) {
    $("#page-content").load(page);
}
