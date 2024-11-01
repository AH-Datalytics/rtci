document.addEventListener("DOMContentLoaded", function () {
    const dataPath = "../app_data/scorecard.csv";
    let allData = [];
    
    // Set default values for state and agency
    let selectedState = "Nationwide";
    let selectedAgency = "Full Sample";
    
    // Define years as strings for dynamic labeling
    const currentYear = new Date().getFullYear();
    const yearLabels = {
        twoPrev: (currentYear - 2).toString(), 
        onePrev: (currentYear - 1).toString(), 
        current: currentYear.toString()
    };

    // Load data
    d3.csv(dataPath).then(data => {
        allData = data;
        console.log("Data loaded:", data);
        populateDropdowns(data);
        updateYearHeaders();
        
        // Set the dropdowns to the default values
        document.getElementById("state-btn").textContent = selectedState;
        document.getElementById("agency-btn").textContent = selectedAgency;

        // Trigger filtering and display of data with default values
        filterAndDisplayData();
    }).catch(error => console.error("Error loading data:", error));

    function populateDropdowns(data) {
        const states = [...new Set(data.map(row => row.state_name))].sort();
        createSearchableDropdown("state-dropdown", "state-btn", states, true);
        createSearchableDropdown("agency-dropdown", "agency-btn", [], false);
    }

    function createSearchableDropdown(dropdownId, buttonId, options, isState) {
        const dropdown = document.getElementById(dropdownId);
        const button = document.getElementById(buttonId);

        const searchInput = document.createElement("input");
        searchInput.type = "text";
        searchInput.placeholder = "Search...";
        searchInput.className = "dropdown-search";

        dropdown.innerHTML = "";
        dropdown.appendChild(searchInput);

        function filterOptions() {
            const filter = searchInput.value.toLowerCase();
            const filteredOptions = options.filter(option => option.toLowerCase().includes(filter));
            const existingItems = dropdown.querySelectorAll(".dropdown-item");
            existingItems.forEach(item => item.remove());

            filteredOptions.forEach(option => {
                const item = document.createElement("div");
                item.className = "dropdown-item";
                item.textContent = option;
                item.addEventListener("click", () => {
                    button.textContent = option;
                    dropdown.classList.remove("show");

                    if (isState) {
                        selectedState = option;
                        updateAgencyDropdown(selectedState);
                    } else {
                        selectedAgency = option;
                    }
                    updateFilterSentence();
                    filterAndDisplayData();
                });
                dropdown.appendChild(item);
            });
        }

        searchInput.addEventListener("input", filterOptions);
        filterOptions();

        button.addEventListener("click", function (event) {
            event.stopPropagation();
            closeAllDropdowns();
            dropdown.classList.toggle("show");
        });

        document.addEventListener("click", closeAllDropdowns);
        dropdown.addEventListener("click", event => event.stopPropagation());
    }

    function updateAgencyDropdown(state) {
        // Get unique agencies for the selected state
        let agencies = [...new Set(allData.filter(row => row.state_name === state).map(row => row.agency_name))].sort();
        
        // Move "Full Sample" to the top if it exists
        const fullSampleIndex = agencies.indexOf("Full Sample");
        if (fullSampleIndex !== -1) {
            agencies.splice(fullSampleIndex, 1); // Remove "Full Sample" from its current position
            agencies.unshift("Full Sample"); // Add it to the beginning of the array
        }
    
        // Create the dropdown with "Full Sample" as the first option
        createSearchableDropdown("agency-dropdown", "agency-btn", agencies, false);
        
        // If state is "Nationwide," set the agency to "Full Sample" by default
        if (state === "Nationwide") {
            selectedAgency = "Full Sample";
            document.getElementById("agency-btn").textContent = "Full Sample";
        }
    }
    

    function closeAllDropdowns() {
        const dropdownMenus = document.querySelectorAll(".dropdown-menu");
        dropdownMenus.forEach(menu => menu.classList.remove("show"));
    }

    function updateFilterSentence() {
        document.getElementById("filters-container").querySelector("span").textContent =
            `Show me the reported crime scorecard for`;
    }

    function filterAndDisplayData() {
        if (selectedState && selectedAgency) {
            const filteredData = allData.filter(row =>
                row.state_name === selectedState && row.agency_name === selectedAgency
            );

            if (filteredData.length > 0) {
                console.log("Filtered data:", filteredData);
                renderScorecard(filteredData);
            }
        }
    }

    function renderScorecard(data) {
        const tbody = document.getElementById("scorecard-body");
        tbody.innerHTML = "";

        data.forEach(row => {
            const rowElement = document.createElement("tr");
            rowElement.innerHTML = `
                <td>${formatCrimeType(row.crime_type)}</td>
                <td>${row.two_years_prior_full || 'N/A'}</td>
                <td>${row.previous_year_full || 'N/A'}</td>
                <td style="color: ${getColor(row.two_years_prior_previous_year_full_pct_change)};">
                    ${formatPercentage(row.two_years_prior_previous_year_full_pct_change)}
                </td>
                <td>${row.ytd_month_range.replace(/ \d{4}$/, '') || 'N/A'}</td> <!-- Remove year from YTD range -->
                <td>${row.two_years_prior_ytd || 'N/A'}</td>
                <td>${row.previous_year_ytd || 'N/A'}</td>
                <td>${row.current_year_ytd || 'N/A'}</td>
                <td style="color: ${getColor(row.two_years_prior_current_year_ytd_pct_change)};">
                    ${formatPercentage(row.two_years_prior_current_year_ytd_pct_change)}
                </td>
                <td style="color: ${getColor(row.previous_year_current_year_ytd_pct_change)};">
                    ${formatPercentage(row.previous_year_current_year_ytd_pct_change)}
                </td>
            `;
            tbody.appendChild(rowElement);
        });
    }

    function formatCrimeType(crimeType) {
        return crimeType.replace(/_/g, ' ').replace(/\b\w/g, char => char.toUpperCase());
    }

    function formatPercentage(value) {
        return value ? `${parseFloat(value).toFixed(1)}%` : 'N/A';
    }

    function getColor(value) {
        const parsedValue = parseFloat(value);
        if (isNaN(parsedValue)) return '#000'; // Default color for N/A or undefined values
        return parsedValue > 0 ? "#f28106" : "#2d5ef9";
    }

    function updateYearHeaders() {
        document.querySelector("#scorecard-table thead tr:nth-child(2)").innerHTML = `
            <th style="background-color: #00333a; color: white;"></th>
            <th style="background-color: #00333a; color: white;">${yearLabels.twoPrev}</th>
            <th style="background-color: #00333a; color: white;">${yearLabels.onePrev}</th>
            <th style="background-color: #00333a; color: white;">% Change ${yearLabels.twoPrev}-${yearLabels.onePrev}</th>
            <th style="background-color: #00333a; color: white;">YTD Range</th>
            <th style="background-color: #00333a; color: white;">${yearLabels.twoPrev} (YTD)</th>
            <th style="background-color: #00333a; color: white;">${yearLabels.onePrev} (YTD)</th>
            <th style="background-color: #00333a; color: white;">${yearLabels.current} (YTD)</th>
            <th style="background-color: #00333a; color: white;">% Change ${yearLabels.twoPrev}-${yearLabels.current} (YTD)</th>
            <th style="background-color: #00333a; color: white;">% Change ${yearLabels.onePrev}-${yearLabels.current} (YTD)</th>
        `;
    }
});
