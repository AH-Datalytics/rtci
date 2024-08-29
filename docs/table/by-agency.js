document.addEventListener("DOMContentLoaded", function() {
    const dataPath = "../app_data/by_agency_table.csv";
    const tableBody = document.getElementById("by-agency-table-body");
    const agencyBtn = document.getElementById("agency-btn");
    const stateBtn = document.getElementById("state-btn");
    const agencyDropdown = document.getElementById("agency-dropdown");
    const stateDropdown = document.getElementById("state-dropdown");

    let allData = [];
    let currentSortColumn = 'month_year'; // Set default sort column here
    let currentSortOrder = 'desc'; // Set default sort order here
    let currentHeaderIndex = 0; // Track the currently sorted column index

    // Default filter values
    const defaultFilters = {
        state: "Nationwide",
        agency: "Full Sample"
    };

    // Load data
    d3.csv(dataPath).then(data => {
        allData = data;  // Store all data for filtering
        retrieveFilterValues(defaultFilters);
        filterData(); // Apply the default filter and sorting on load
        populateFilters(data);
        addSortingListeners(); // Add sorting listeners after populating table
    }).catch(error => {
        console.error("Error loading the CSV data:", error);
    });

    function formatAndPopulateTable(data) {
        tableBody.innerHTML = "";

        const formatNumber = d3.format(","); // Formatter for numbers with commas

        data.forEach(row => {
            const tr = document.createElement("tr");

            ["month_year", "agency_abbr", "violent_crime", "murder", "rape", "robbery", "aggravated_assault", "property_crime", "burglary", "theft", "motor_vehicle_theft"].forEach(col => {
                const td = document.createElement("td");
                if (["aggravated_assault", "burglary", "motor_vehicle_theft", "murder", "rape", "robbery", "theft", "property_crime", "violent_crime"].includes(col)) {
                    td.textContent = formatNumber(row[col]); // Format with commas
                } else {
                    td.textContent = row[col];
                }
                tr.appendChild(td);
            });

            tableBody.appendChild(tr);
        });
    }

    // Function to sort the table by a specific column
    function sortTableByColumn(columnKey, headerIndex) {
        if (currentSortColumn === columnKey) {
            // Toggle the sort order if the same column is clicked by the user
            currentSortOrder = currentSortOrder === 'asc' ? 'desc' : 'asc';
        } else {
            // Set the new sort column and start with descending order
            currentSortColumn = columnKey;
            currentSortOrder = 'desc'; // Default to descending order on new column sort
        }

        currentHeaderIndex = headerIndex; // Track the current sorted column index

        const filteredData = allData.filter(row => row.state_name === stateBtn.textContent && row.agency_name === agencyBtn.textContent);
        applyCurrentSort(filteredData); // Apply sorting
    }

    // Apply the current sorting without toggling (used in filtering)
    function applyCurrentSort(data) {
        data.sort((a, b) => {
            let aValue = a[currentSortColumn];
            let bValue = b[currentSortColumn];
    
            // Handle date sorting specifically
            if (currentSortColumn === 'month_year') {
                aValue = new Date(aValue);
                bValue = new Date(bValue);
            } else if (["aggravated_assault", "burglary", "motor_vehicle_theft", "murder", "rape", "robbery", "theft", "property_crime", "violent_crime"].includes(currentSortColumn)) {
                // Convert crime columns to integers for numerical sorting
                aValue = parseInt(aValue);
                bValue = parseInt(bValue);
            } else {
                // Treat other columns as strings
                aValue = aValue.toLowerCase();
                bValue = bValue.toLowerCase();
            }
    
            if (aValue < bValue) return currentSortOrder === 'asc' ? -1 : 1;
            if (aValue > bValue) return currentSortOrder === 'asc' ? 1 : -1;
            return 0;
        });
    
        formatAndPopulateTable(data);
        updateSortedColumnClass(currentSortColumn); // Keep the current sorted column highlighted
    }
    

    // Add event listeners to header spans for sorting
    function addSortingListeners() {
        document.querySelectorAll('.blue-header-table th span').forEach((span, index) => {
            const columnKey = span.dataset.key; // Ensure the span has a data-key attribute corresponding to the column
            span.style.cursor = 'pointer'; // Change cursor to pointer on hover
            span.addEventListener('click', () => sortTableByColumn(columnKey, index));
        });
    }

    // Function to update the sorted column class and add arrows
    function updateSortedColumnClass(columnKey) {
        // Remove 'sorted' class and arrows from all header spans
        document.querySelectorAll('.blue-header-table th span').forEach(span => {
            span.classList.remove('sorted');
            // Reset the span's inner HTML to just the text content without any arrows
            span.innerHTML = span.textContent.replace(/ ▲| ▼/g, ''); // Removes any existing arrow
        });

        // Add 'sorted' class and the appropriate arrow to the currently sorted column
        const sortedHeader = document.querySelector(`.blue-header-table th span[data-key="${columnKey}"]`);
        sortedHeader.classList.add('sorted');

        // Add the correct arrow based on the sort order
        const arrow = currentSortOrder === 'asc' ? ' ▲' : ' ▼';
        sortedHeader.innerHTML += arrow;
    }

    // Populate filters
    function populateFilters(data) {
        let states = [...new Set(data.map(row => row.state_name))];

        // Remove "Nationwide" from the list if it exists
        const nationwideIndex = states.indexOf("Nationwide");
        if (nationwideIndex > -1) {
            states.splice(nationwideIndex, 1);  // Remove "Nationwide" from its original position
        }

        // Sort the remaining states alphabetically
        states.sort();

        // Add "Nationwide" back at the beginning of the list
        states.unshift("Nationwide");

        // Create the dropdown with the ordered list
        createSearchableDropdown(stateDropdown, stateBtn, states);
    }

    function updateAgencyFilter(state) {
        let agencies = [...new Set(allData.filter(row => row.state_name === state).map(row => row.agency_name))];

        // Check if "Full Sample" exists
        const fullSampleIndex = agencies.indexOf("Full Sample");
        if (fullSampleIndex > -1) {
            agencies.splice(fullSampleIndex, 1);  // Remove "Full Sample" from its original position
            agencies.sort();  // Sort the remaining agencies alphabetically
            agencies.unshift("Full Sample");  // Add "Full Sample" back at the top
        } else {
            agencies.sort();  // Just sort if "Full Sample" doesn't exist
        }

        createSearchableDropdown(agencyDropdown, agencyBtn, agencies);

        const savedFilters = JSON.parse(sessionStorage.getItem('byAgencyTableFilters'));
        const savedAgency = savedFilters ? savedFilters.agency : null;

        // Default to "Full Sample" if available, otherwise saved agency or first agency
        if (agencies.includes(savedAgency)) {
            agencyBtn.textContent = savedAgency;
        } else if (agencies.length > 0) {
            agencyBtn.textContent = agencies[0];
        } else {
            agencyBtn.textContent = "Agency";
        }

        // Automatically filter the table after setting the agency
        filterData();

        // Ensure only the saved agency is bolded
        const items = agencyDropdown.querySelectorAll('.dropdown-item');
        items.forEach(item => item.classList.remove('selected'));
        const agencyOption = agencyDropdown.querySelector(`[data-value="${agencyBtn.textContent}"]`);
        if (agencyOption) agencyOption.classList.add('selected');
    }

    function filterData() {
        const selectedState = stateBtn.textContent;
        const selectedAgency = agencyBtn.textContent;

        if (selectedState !== "State" && selectedAgency !== "Agency") {
            const filteredData = allData.filter(row => row.state_name === selectedState && row.agency_name === selectedAgency);

            // Sort the filtered data using the current sort column and order without toggling
            applyCurrentSort(filteredData);
        }
    }

    // Toggle dropdown visibility with only one open at a time
    function closeAllDropdowns() {
        const dropdownMenus = document.querySelectorAll(".dropdown-menu");
        dropdownMenus.forEach(menu => menu.classList.remove("show"));
    }

    function toggleDropdown(button, dropdown) {
        button.addEventListener('click', function(event) {
            event.stopPropagation();
            closeAllDropdowns();
            dropdown.classList.toggle("show");
        });

        document.addEventListener('click', function() {
            closeAllDropdowns();
        });

        dropdown.addEventListener('click', function(event) {
            event.stopPropagation();
        });
    }

    toggleDropdown(stateBtn, stateDropdown);
    toggleDropdown(agencyBtn, agencyDropdown);

    // Search functionality for dropdowns
    function createSearchableDropdown(dropdown, button, options) {
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
                const dropdownOption = createDropdownOption(option, option, dropdown, button);
                dropdown.appendChild(dropdownOption);
            });
        }

        searchInput.addEventListener("input", filterOptions);

        options.forEach(option => {
            const dropdownOption = createDropdownOption(option, option, dropdown, button);
            dropdown.appendChild(dropdownOption);
        });

        // Add 'selected' class to the current filter value
        const selectedOption = dropdown.querySelector(`[data-value="${button.textContent}"]`);
        if (selectedOption) selectedOption.classList.add('selected');
    }

    function createDropdownOption(value, text, dropdown, button) {
        const option = document.createElement("div");
        option.className = "dropdown-item";
        option.dataset.value = value;
        option.textContent = text;

        if (button.textContent === value) {
            option.classList.add('selected');
        }

        option.addEventListener('click', function() {
            const items = dropdown.querySelectorAll('.dropdown-item');
            items.forEach(item => item.classList.remove('selected'));
            option.classList.add('selected');
            button.textContent = text;
            dropdown.classList.remove("show");

            if (button === stateBtn) {
                updateAgencyFilter(value);
            } else {
                filterData();
            }

            saveFilterValues(); // Save filter values whenever a filter changes
        });

        return option;
    }

    function saveFilterValues() {
        const filters = {
            state: stateBtn.textContent,
            agency: agencyBtn.textContent
        };
        sessionStorage.setItem('byAgencyTableFilters', JSON.stringify(filters));
    }

    function retrieveFilterValues(defaultFilters) {
        const savedFilters = JSON.parse(sessionStorage.getItem('byAgencyTableFilters')) || defaultFilters;

        stateBtn.textContent = savedFilters.state;
        agencyBtn.textContent = savedFilters.agency;

        const stateOption = stateDropdown.querySelector(`[data-value="${savedFilters.state}"]`);
        if (stateOption) stateOption.classList.add('selected');

        updateAgencyFilter(savedFilters.state);
    }

    window.navigateTo = function(page) {
        window.location.href = page;
    };

    // Function to convert table data to CSV and trigger download
    function downloadCSV(data, filename) {
        if (!data || !data.length) {
            console.error("No data available for download.");
            return;
        }

        const headers = [
            "month_year",
            "agency_name",
            "state_name",
            "violent_crime",
            "murder",
            "rape",
            "robbery",
            "aggravated_assault",
            "property_crime",
            "burglary",
            "theft",
            "motor_vehicle_theft",
            "Last Updated"
        ];
        const csvData = [headers.join(",")];

        data.forEach(row => {
            const values = [
                `"${row.month_year}"`,
                `"${row.agency_name}"`,
                `"${row.state_name}"`,
                `${row.violent_crime}`,
                `${row.murder}`,
                `${row.rape}`,
                `${row.robbery}`,
                `${row.aggravated_assault}`,
                `${row.property_crime}`,
                `${row.burglary}`,
                `${row.theft}`,
                `${row.motor_vehicle_theft}`,
                `${row["Last Updated"]}` // Add the "Last Updated" value here
            ];
            csvData.push(values.join(","));
        });

        const csvString = csvData.join("\n");
        const blob = new Blob([csvString], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement("a");
        link.href = URL.createObjectURL(blob);
        link.setAttribute("download", filename);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }

    // Event listener for download button
    document.getElementById("table-download").addEventListener("click", function() {
        const selectedState = stateBtn.textContent;
        const selectedAgency = agencyBtn.textContent;

        if (selectedState !== "State" && selectedAgency !== "Agency") {
            const filteredData = allData.filter(row => row.state_name === selectedState && row.agency_name === selectedAgency);
            downloadCSV(filteredData, `${selectedAgency}_${selectedState}_Filtered.csv`);
        }
    });

});
