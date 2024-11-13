document.addEventListener("DOMContentLoaded", function () {
    const dataPath = "../app_data/scorecard.csv";
    let allData = [];
    let selectedState = "Nationwide"; // Default state to "Nationwide"
    let selectedAgency = "Full Sample"; // Default agency to "Full Sample"

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
        populateFilters(allData);
        updateYearHeaders();
        setDefaultFilters(); // Set default filter values on load
        filterAndDisplayData(); // Display default data for "Nationwide" and "Full Sample"
    }).catch(error => console.error("Error loading data:", error));

    // Function to adjust the width of the tracker container
    function adjustTrackerWidth() {
        const trackerContainer = document.getElementById("trackers-container");
        const scorecardTable = document.getElementById("scorecard-table");
        trackerContainer.style.width = `${scorecardTable.scrollWidth}px`;
    }

    // Re-adjust width on window resize
    window.addEventListener("resize", adjustTrackerWidth);

    function populateFilters(data) {
        let states = [...new Set(data.map(row => row.state_name))].sort();
        
        // Ensure "Nationwide" is always the first option
        const nationwideIndex = states.indexOf("Nationwide");
        if (nationwideIndex !== -1) {
            states.splice(nationwideIndex, 1);
            states.unshift("Nationwide");
        }
        
        createSearchableDropdown("state-dropdown", "state-btn", states, true);
        createSearchableDropdown("agency-dropdown", "agency-btn", [], false);
    }

    function setDefaultFilters() {
        // Set "Nationwide" and "Full Sample" as defaults on page load
        document.getElementById("state-btn").textContent = "Nationwide";
        document.getElementById("agency-btn").textContent = "Full Sample";
        selectedState = "Nationwide";
        selectedAgency = "Full Sample";
        updateAgencyDropdown(selectedState); // Populate agency dropdown for "Nationwide"
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
                const dropdownOption = createDropdownOption(option, dropdown, button, isState);
                dropdown.appendChild(dropdownOption);
            });
        }

        searchInput.addEventListener("input", filterOptions);
        filterOptions();

        button.addEventListener("click", event => {
            event.stopPropagation();
            closeAllDropdowns();
            dropdown.classList.toggle("show");
        });

        document.addEventListener("click", closeAllDropdowns);
        dropdown.addEventListener("click", event => event.stopPropagation());
    }

    function createDropdownOption(optionText, dropdown, button, isState) {
        const option = document.createElement("div");
        option.className = "dropdown-item";
        option.textContent = optionText;

        // Bold the selected option
        if ((isState && optionText === selectedState) || (!isState && optionText === selectedAgency)) {
            option.classList.add('selected'); // Add bold styling to selected item
        }

        option.addEventListener("click", () => {
            const items = dropdown.querySelectorAll('.dropdown-item');
            items.forEach(item => item.classList.remove('selected'));
            option.classList.add('selected');

            button.textContent = optionText;
            dropdown.classList.remove("show");

            if (isState) {
                selectedState = optionText;
                updateAgencyDropdown(selectedState);
            } else {
                selectedAgency = optionText;
            }
            filterAndDisplayData();
        });

        return option;
    }

    function updateAgencyDropdown(state) {
        // Get unique agencies for the selected state
        let agencies = [...new Set(allData.filter(row => row.state_name === state).map(row => row.agency_name))].sort();
    
        if (state === "Nationwide") {
            const nationwideOrder = ["Full Sample", "Cities of 1M+", "Cities of 250K - 1M", "Cities of 100K - 250K", "Cities of < 100K"];
            agencies = agencies.filter(agency => nationwideOrder.includes(agency))
                               .sort((a, b) => nationwideOrder.indexOf(a) - nationwideOrder.indexOf(b));
        } else {
            agencies = agencies.sort((a, b) => (a === "Full Sample" ? -1 : b === "Full Sample" ? 1 : a.localeCompare(b)));
        }
    
        createSearchableDropdown("agency-dropdown", "agency-btn", agencies, false);
    
        // Automatically select and display the first agency in the list, and bold it
        if (agencies.length > 0) {
            selectedAgency = agencies[0];
            document.getElementById("agency-btn").textContent = selectedAgency;
    
            // Bold the first agency in the dropdown
            const dropdown = document.getElementById("agency-dropdown");
            const items = dropdown.querySelectorAll('.dropdown-item');
            items.forEach(item => item.classList.remove('selected')); // Remove bolding from all items
            items[0].classList.add('selected'); // Bold the first item
    
            filterAndDisplayData(); // Filter and display data for the selected state and the first agency
        }
    }
    

    function filterAndDisplayData() {
        if (selectedState && selectedAgency) {
            const filteredData = allData.filter(row => row.state_name === selectedState && row.agency_name === selectedAgency);
    
            if (filteredData.length > 0) {
                // Calculate the previous year
                const previousYear = currentYear - 1;
    
                // Populate the trackers with dynamic previous year for population
                document.getElementById("tracker-agency").innerHTML = `<span class="tracker-agency-name">${selectedAgency}, ${selectedState} </span>`;
               // document.getElementById("tracker-source-type").textContent = filteredData[0].source_type || 'N/A';
               // document.getElementById("tracker-source-method").textContent = filteredData[0].source_method || 'N/A';
               // document.getElementById("tracker-population").innerHTML = `<strong>${previousYear} Population:</strong> ${filteredData[0].population ? parseInt(filteredData[0].population).toLocaleString() : 'N/A'}`;
                document.getElementById("tracker-ytd-range").textContent = filteredData[0].ytd_month_range || 'N/A';
    
                console.log("Filtered data:", filteredData);
                renderScorecard(filteredData);
            }
        }
    }
    
    

    function renderScorecard(data) {
        const tbody = document.getElementById("scorecard-body");
        tbody.innerHTML = "";
    
        // Define the order for crime types based on severity
        const crimeOrder = [
            { crime: "violent_crime", isHeader: true },
            { crime: "murder", isHeader: false },
            { crime: "rape", isHeader: false },
            { crime: "robbery", isHeader: false },
            { crime: "aggravated_assault", isHeader: false },
            { crime: "property_crime", isHeader: true },
            { crime: "burglary", isHeader: false },
            { crime: "theft", isHeader: false },
            { crime: "motor_vehicle_theft", isHeader: false }
        ];
    
        // Loop through crimeOrder to display each type, formatted
        crimeOrder.forEach(orderItem => {
            const filteredData = data.filter(row => row.crime_type.toLowerCase() === orderItem.crime.toLowerCase());
    
            // Log if a specific crime type isn't showing up
            if (filteredData.length === 0) console.log(`Missing data for crime type: ${orderItem.crime}`);
    
            filteredData.forEach(row => {
                const isHeader = orderItem.isHeader;
                const fontWeight = isHeader ? "bold" : "normal";
                const fontSize = isHeader ? "1.2em" : "1.1em";
                const color = isHeader ? "#00333a" : ""; // Color for headers
    
                const rowElement = document.createElement("tr");
                rowElement.innerHTML = `
                <td style="font-weight: ${fontWeight}; font-size: ${fontSize}; color: ${color};">${formatCrimeType(row.crime_type)}</td>
                <td>${formatNumber(row.current_year_ytd)}</td>
                <td>${formatNumber(row.previous_year_ytd)}</td>
                <td>${formatNumber(row.two_years_prior_ytd)}</td>
                <td style="color: ${getColor(row.previous_year_current_year_ytd_pct_change)};">
                    ${formatPercentage(row.previous_year_current_year_ytd_pct_change)}
                </td>
                <td style="color: ${getColor(row.two_years_prior_current_year_ytd_pct_change)};">
                    ${formatPercentage(row.two_years_prior_current_year_ytd_pct_change)}
                </td>
                <td>${formatNumber(row.previous_year_full)}</td>
                <td>${formatNumber(row.two_years_prior_full)}</td>
                <td style="color: ${getColor(row.two_years_prior_previous_year_full_pct_change)};">
                    ${formatPercentage(row.two_years_prior_previous_year_full_pct_change)}
                </td>
                `;
                tbody.appendChild(rowElement);
            });
        });
    }
    
    
    // Helper function to format numbers with commas
    function formatNumber(value) {
        return value ? parseInt(value).toLocaleString() : 'N/A';
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
        document.querySelector("#scorecard-table thead tr:nth-child(1)").innerHTML = `
            <th style="background-color: #00333a; color: white;"></th>
            <th style="background-color: #00333a; color: white;">${yearLabels.current} (YTD)</th>
            <th style="background-color: #00333a; color: white;">${yearLabels.onePrev} (YTD)</th>
            <th style="background-color: #00333a; color: white;">${yearLabels.twoPrev} (YTD)</th>
            <th style="background-color: #00333a; color: white;">% Change ${yearLabels.onePrev}-${yearLabels.current} (YTD)</th>
            <th style="background-color: #00333a; color: white;">% Change ${yearLabels.twoPrev}-${yearLabels.current} (YTD)</th>
            <th style="background-color: #00333a; color: white;">${yearLabels.onePrev} (Full Year)</th>
            <th style="background-color: #00333a; color: white;">${yearLabels.twoPrev} (Full Year)</th>
            <th style="background-color: #00333a; color: white;">% Change ${yearLabels.twoPrev}-${yearLabels.onePrev} (Full Year)</th>
        `;
    }
    
    


    function closeAllDropdowns() {
        const dropdownMenus = document.querySelectorAll(".dropdown-menu");
        dropdownMenus.forEach(menu => menu.classList.remove("show"));
    }
});

