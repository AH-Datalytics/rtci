document.addEventListener("DOMContentLoaded", function() {
    const dataPath = "../app_data/sources.csv";
    const tableBody = document.getElementById("source-table-container");
    const agencyBtn = document.getElementById("agency-btn");
    const stateBtn = document.getElementById("state-btn");
    const agencyDropdown = document.getElementById("agency-dropdown");
    const stateDropdown = document.getElementById("state-dropdown");
    const agenciesNumBox = document.getElementById("agencies-num-box");

    let allData = [];
    let filteredAgencies = [];

    // Load data
    d3.csv(dataPath).then(data => {
        allData = data;  // Store all data for filtering
        populateFilters(data);
        displayNationalSample();  // Display rows where in_national_sample is TRUE on page load

        // Set the filter labels to "Nationwide" and "Full Sample" on page load
        stateBtn.textContent = "Nationwide";
        agencyBtn.textContent = "Full Sample";
        updateAgenciesNumBox(allData.filter(row => row.in_national_sample === "TRUE").length);
    }).catch(error => {
        console.error("Error loading the CSV data:", error);
    });

    function formatAndPopulateTable(data) {
        tableBody.innerHTML = "";  // Clear any existing content
    
        // Sort data by population (biggest to smallest)
        data.sort((a, b) => b.population - a.population);
    
        // Create a table element
        const table = document.createElement("table");
    
        // Create the table headers
        const headers = ["Agency", "Population Covered", "Source Type", "Source Method", "Most Recent Data", "Primary Link"];
        const thead = document.createElement("thead");
        const headerRow = document.createElement("tr");
    
        headers.forEach(header => {
            const th = document.createElement("th");
            th.textContent = header;
            headerRow.appendChild(th);
        });
    
        thead.appendChild(headerRow);
        table.appendChild(thead);
    
        // Create the table body
        const tbody = document.createElement("tbody");
    
        data.forEach(row => {
            const tr = document.createElement("tr");
    
            const columns = ["agency_full", "population", "source_type", "source_method", "most_recent_month", "source_link"];
    
            columns.forEach(col => {
                const td = document.createElement("td");
                if (col === "population") {
                    td.textContent = parseInt(row[col]).toLocaleString(); // Format population with commas
                } else if (col === "source_link") {
                    td.innerHTML = `<a href="${row[col]}" target="_blank">Click Here</a>`;
                } else {
                    td.textContent = row[col];
                }
                tr.appendChild(td);
            });
    
            tbody.appendChild(tr);
        });
    
        table.appendChild(tbody);
        tableBody.appendChild(table);
    }
    
    
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

    function displayNationalSample() {
        const filteredData = allData.filter(row => row.in_national_sample === "TRUE");
        formatAndPopulateTable(filteredData);
        updateAgenciesNumBox(filteredData.length);
    }

    function updateAgencyFilter(state) {
        if (state === "Nationwide" && agencyBtn.textContent === "Full Sample") {
            displayNationalSample();
        } else {
            let agencies = [...new Set(allData.filter(row => row.state_name === state).map(row => row.agency_name))];
    
            const fullSampleIndex = agencies.indexOf("Full Sample");
            if (fullSampleIndex > -1) {
                agencies.splice(fullSampleIndex, 1);
                agencies.sort();
                agencies.unshift("Full Sample");
            } else {
                agencies.sort();
            }
    
            createSearchableDropdown(agencyDropdown, agencyBtn, agencies);
    
            const savedFilters = JSON.parse(sessionStorage.getItem('sourceTableFilters'));
            const savedAgency = savedFilters ? savedFilters.agency : null;
    
            if (agencies.includes(savedAgency)) {
                agencyBtn.textContent = savedAgency;
            } else if (agencies.length > 0) {
                agencyBtn.textContent = agencies[0];
            } else {
                agencyBtn.textContent = "Agency";
            }
    
            filterData();
    
            const items = agencyDropdown.querySelectorAll('.dropdown-item');
            items.forEach(item => item.classList.remove('selected'));
            const agencyOption = agencyDropdown.querySelector(`[data-value="${agencyBtn.textContent}"]`);
            if (agencyOption) agencyOption.classList.add('selected');
        }
    }
    
    function filterData() {
        const selectedState = stateBtn.textContent;
        const selectedAgency = agencyBtn.textContent;
    
        if (selectedState === "Nationwide" && selectedAgency === "Full Sample") {
            displayNationalSample();
        } else if (selectedState !== "State" && selectedAgency !== "Agency") {
            const filteredData = allData.filter(row => row.state_name === selectedState && row.agency_name === selectedAgency);
            formatAndPopulateTable(filteredData);
            updateAgenciesNumBox(filteredData.length);
        }
    }

    function updateAgenciesNumBox(count) {
        agenciesNumBox.innerHTML = `Number of Agencies: <strong>${count}</strong>`;
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
        sessionStorage.setItem('sourceTableFilters', JSON.stringify(filters));
    }
});
