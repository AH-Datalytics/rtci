document.addEventListener("DOMContentLoaded", function() {
    const fullSampleBtn = document.getElementById("full-sample-btn");
    const byAgencyBtn = document.getElementById("by-agency-btn");

    fullSampleBtn.addEventListener("click", function() {
        window.location.href = "table.html"; // Navigate to the full sample page
    });

    byAgencyBtn.addEventListener("click", function() {
        window.location.href = "by-agency.html"; // Ensure we're on the by-agency page
    });

    // Placeholder for future data loading and filtering logic
    // Function to populate the dropdowns and handle filtering will be added here
});
