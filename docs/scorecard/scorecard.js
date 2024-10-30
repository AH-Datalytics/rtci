document.addEventListener("DOMContentLoaded", function () {
    const dataPath = "../app_data/by_agency_table.csv"; // Update this path if necessary
    let allData = [];
    let selectedState = "State";
    let selectedAgency = "Agency";
    
    const currentYear = new Date().getFullYear();
    const yearLabels = { 
        twoPrev: currentYear - 2, 
        onePrev: currentYear - 1, 
        current: currentYear 
    };

    // Load data
    d3.csv(dataPath).then(data => {
        allData = data;
        console.log("Data loaded:", data); // Log to confirm data load
        populateDropdowns(data);
        updateYearHeaders(); // Set dynamic year headers in the scorecard
    }).catch(error => console.error("Error loading data:", error));

    function populateDropdowns(data) {
        const states = [...new Set(data.map(row => row.state_name))].sort();
        createSearchableDropdown("state-dropdown", "state-btn", states, true);

        // Initialize with empty agencies until state is selected
        createSearchableDropdown("agency-dropdown", "agency-btn", [], false);
    }

    function createSearchableDropdown(dropdownId, buttonId, options, isState) {
        const dropdown = document.getElementById(dropdownId);
        const button = document.getElementById(buttonId);

        // Create search input for the dropdown
        const searchInput = document.createElement("input");
        searchInput.type = "text";
        searchInput.placeholder = "Search...";
        searchInput.className = "dropdown-search";

        dropdown.innerHTML = ""; // Clear existing options
        dropdown.appendChild(searchInput);

        // Filter function to dynamically display options
        function filterOptions() {
            const filter = searchInput.value.toLowerCase();
            const filteredOptions = options.filter(option => option.toLowerCase().includes(filter));

            // Clear current options
            const existingItems = dropdown.querySelectorAll(".dropdown-item");
            existingItems.forEach(item => item.remove());

            // Append new options based on filter
            filteredOptions.forEach(option => {
                const item = document.createElement("div");
                item.className = "dropdown-item";
                item.textContent = option;
                item.addEventListener("click", () => {
                    button.textContent = option;
                    dropdown.classList.remove("show");

                    if (isState) {
                        selectedState = option;
                        updateAgencyDropdown(selectedState); // Update agency options based on state
                    } else {
                        selectedAgency = option;
                    }
                    updateFilterSentence(); // Update sentence only once selections are complete
                    filterAndDisplayData();
                });
                dropdown.appendChild(item);
            });
        }

        searchInput.addEventListener("input", filterOptions);
        filterOptions(); // Initialize with all options

        // Toggle dropdown visibility
        button.addEventListener("click", function (event) {
            event.stopPropagation();
            closeAllDropdowns();
            dropdown.classList.toggle("show");
        });

        document.addEventListener("click", closeAllDropdowns);
        dropdown.addEventListener("click", event => event.stopPropagation());
    }

    function updateAgencyDropdown(state) {
        const agencies = [...new Set(allData.filter(row => row.state_name === state).map(row => row.agency_name))].sort();
        createSearchableDropdown("agency-dropdown", "agency-btn", agencies, false);
    }

    function closeAllDropdowns() {
        const dropdownMenus = document.querySelectorAll(".dropdown-menu");
        dropdownMenus.forEach(menu => menu.classList.remove("show"));
    }

    function updateFilterSentence() {
        document.getElementById("filters-container").querySelector("span").textContent =
            `Show me the reported crime scorecard for ${selectedState} for ${selectedAgency}`;
    }

    function filterAndDisplayData() {
        if (selectedState !== "State" && selectedAgency !== "Agency") {
            const filteredData = allData.filter(row =>
                row.state_name === selectedState && row.agency_name === selectedAgency
            );

            if (filteredData.length > 0) {
                console.log("Filtered data:", filteredData); // Log to verify filtered data
                const crimeData = calculateAggregates(filteredData);
                renderScorecard(crimeData);
            }
        }
    }

    function calculateAggregates(data) {
        const crimeTypes = [
            "aggravated_assault", "burglary", "motor_vehicle_theft", "murder", "rape", "robbery", "theft"
        ];

        const result = [];

        crimeTypes.forEach(crime => {
            const yearCounts = {};

            data.forEach(row => {
                const year = new Date(row.date).getFullYear();
                if (!yearCounts[year]) yearCounts[year] = 0;
                yearCounts[year] += parseInt(row[crime]) || 0;
            });

            const twoPrev = yearCounts[yearLabels.twoPrev] || 0;
            const onePrev = yearCounts[yearLabels.onePrev] || 0;
            const current = yearCounts[yearLabels.current] || 0;

            const fullYearChange = calculatePercentChange(onePrev, twoPrev);
            const ytdChangeTwoPrevCurrent = calculatePercentChange(current, twoPrev);
            const ytdChangeOnePrevCurrent = calculatePercentChange(current, onePrev);

            result.push({
                crime: formatCrimeType(crime),
                fullYear: { twoPrev, onePrev, fullYearChange },
                ytd: { twoPrev, onePrev, current, ytdChangeTwoPrevCurrent, ytdChangeOnePrevCurrent }
            });
        });

        return result;
    }

    function calculatePercentChange(newVal, oldVal) {
        if (oldVal === 0) return newVal === 0 ? 0 : 100;
        const change = (((newVal - oldVal) / oldVal) * 100).toFixed(1);
        return (change > 0 ? "+" : "") + change; // Add "+" for positive changes
    }

    function formatCrimeType(crime) {
        return crime.replace(/_/g, ' ').replace(/\b\w/g, char => char.toUpperCase());
    }

    function renderScorecard(data) {
        const tbody = document.getElementById("scorecard-body");
        tbody.innerHTML = ""; // Clear previous content

        data.forEach(item => {
            const row = document.createElement("tr");
            row.innerHTML = `
                <td>${item.crime}</td>
                <td>${item.fullYear.twoPrev}</td>
                <td>${item.fullYear.onePrev}</td>
                <td style="color: ${getColor(item.fullYear.fullYearChange)};">
                    ${item.fullYear.fullYearChange}%
                </td>
                <td>${item.ytd.twoPrev}</td>
                <td>${item.ytd.onePrev}</td>
                <td>${item.ytd.current}</td>
                <td style="color: ${getColor(item.ytd.ytdChangeTwoPrevCurrent)};">
                    ${item.ytd.ytdChangeTwoPrevCurrent}%
                </td>
                <td style="color: ${getColor(item.ytd.ytdChangeOnePrevCurrent)};">
                    ${item.ytd.ytdChangeOnePrevCurrent}%
                </td>
            `;
            tbody.appendChild(row);
        });
    }

    function getColor(value) {
        return value.startsWith("+") ? "#f28106" : "#2d5ef9"; // Orange for positive, blue for negative
    }

    function updateYearHeaders() {
        document.querySelector("#scorecard-table thead tr:nth-child(2)").innerHTML = `
            <th style="background-color: #00333a; color: white;"></th>
            <th style="background-color: #00333a; color: white;">${yearLabels.twoPrev}</th>
            <th style="background-color: #00333a; color: white;">${yearLabels.onePrev}</th>
            <th style="background-color: #00333a; color: white;">% Change ${yearLabels.twoPrev}-${yearLabels.onePrev}</th>
            <th style="background-color: #00333a; color: white;">${yearLabels.twoPrev}</th>
            <th style="background-color: #00333a; color: white;">${yearLabels.onePrev}</th>
            <th style="background-color: #00333a; color: white;">${yearLabels.current}</th>
            <th style="background-color: #00333a; color: white;">% Change ${yearLabels.twoPrev}-${yearLabels.current}</th>
            <th style="background-color: #00333a; color: white;">% Change ${yearLabels.onePrev}-${yearLabels.current}</th>
        `;
    }
});
