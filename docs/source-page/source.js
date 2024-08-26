document.addEventListener("DOMContentLoaded", function() {
    const dataPath = "../app_data/sources.csv";
    const tableBody = document.getElementById("source-table-body");
    const agencyBtn = document.getElementById("agency-btn");
    const stateBtn = document.getElementById("state-btn");
    const agencyDropdown = document.getElementById("agency-dropdown");
    const stateDropdown = document.getElementById("state-dropdown");
    const agenciesNumBox = document.getElementById("agencies-num-box");

    let allData = [];

    // Load data
    d3.csv(dataPath).then(data => {
        allData = data;  // Store all data for filtering
        console.log(allData);  // Log the data to see if it’s loading correctly
        populateFilters(data);
        createStaticHeaders();  // Ensure headers are always displayed
        filterData();  // Automatically filter data based on initial dropdown values
    }).catch(error => {
        console.error("Error loading the CSV data:", error);
    });

    // Function to create and insert static headers
    function createStaticHeaders() {
        tableBody.innerHTML = ""; // Clear any existing content

        const headers = [
            { label: "Agency", key: "agency_full" },
            { label: "Population Covered", key: "population" },
            { label: "Source Type", key: "source_type" },
            { label: "Source Method", key: "source_method" },
            { label: "Most Recent Data", key: "most_recent_month" },
            { label: "Primary Link", key: "source_link" }
        ];

        headers.forEach(header => {
            const tr = document.createElement("tr");

            const th = document.createElement("td");
            th.textContent = header.label;
            th.style.fontWeight = "bold";
            th.style.backgroundColor = "#00333a";
            th.style.color = "white";
            tr.appendChild(th);

            const td = document.createElement("td");
            td.textContent = ''; // Empty by default, data will fill this
            tr.appendChild(td);

            tableBody.appendChild(tr);
        });
    }

    // Function to populate the data rows
    function populateDataRows(data) {
        const rows = tableBody.querySelectorAll("tr");

        rows.forEach((row, index) => {
            const td = row.querySelectorAll("td")[1]; // Select the data cell

            switch (index) {
                case 0:
                    td.textContent = data.length > 0 ? data[0].agency_full : '';
                    break;
                case 1:
                    td.textContent = data.length > 0 ? parseInt(data[0].population).toLocaleString() : '';
                    break;
                case 2:
                    td.textContent = data.length > 0 ? data[0].source_type : '';
                    break;
                case 3:
                    td.textContent = data.length > 0 ? data[0].source_method : '';
                    break;
                case 4:
                    td.textContent = data.length > 0 ? data[0].most_recent_month : '';
                    break;
                case 5:
                    if (data.length > 0 && data[0].agency_full === "Full Sample, Nationwide") {
                        td.innerHTML = `<a href="${data[0].source_link}" target="_blank">Click for full list of agencies in current national sample.</a>`;
                    } else {
                        td.innerHTML = data.length > 0 ? `<a href="${data[0].source_link}" target="_blank">Click Here</a>` : '';
                    }
                    break;
                default:
                    td.textContent = '';
            }
        });
    }

    // Function to update table based on the selected filter
    function updateTable(data) {
        createStaticHeaders(); // Ensure headers are present
        populateDataRows(data); // Populate rows with data or leave empty
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

    function updateAgencyFilter(state) {
        let agencies = [...new Set(allData.filter(row => row.state_name === state).map(row => row.agency_name))];
    
        agencies.sort();
    
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
        boldSelectedAgency();
    }

    function boldSelectedAgency() {
        const items = document.querySelectorAll('.dropdown-item');
        items.forEach(item => {
            if (item.textContent === agencyBtn.textContent) {
                item.style.fontWeight = 'bold';
            } else {
                item.style.fontWeight = 'normal';
            }
        });
    }

    function filterData() {
        const selectedState = stateBtn.textContent;
        const selectedAgency = agencyBtn.textContent;
    
        if (selectedState !== "State" && selectedAgency !== "Agency") {
            const filteredData = allData.filter(row => row.state_name === selectedState && row.agency_name === selectedAgency);
            updateTable(filteredData);
            updateAgenciesNumBox(filteredData.length);
        } else {
            updateTable([]); // Show empty table with headers only
        }
    }

    function updateAgenciesNumBox(count) {
        agenciesNumBox.innerHTML = `Number of Agencies: <strong>${count}</strong>`;
    }

    // Toggle dropdown visibility with only one open at a time
    function closeAllDropdowns() {
        const dropdownMenus = document.querySelectorAll(".dropdown-menu");
        dropdownMenus.forEach(menu => menu.classList.remove('show'));
    }

    function toggleDropdown(button, dropdown) {
        button.addEventListener('click', function(event) {
            event.stopPropagation();
            closeAllDropdowns();
            dropdown.classList.toggle('show');
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

            boldSelectedAgency(); // Ensure selected agency is bolded
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
            option.style.fontWeight = 'bold';
        }

        option.addEventListener('click', function() {
            const items = dropdown.querySelectorAll('.dropdown-item');
            items.forEach(item => item.style.fontWeight = 'normal'); // Reset all to normal
            option.style.fontWeight = 'bold'; // Bold the selected one
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
