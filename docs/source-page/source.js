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
        filterData();  // Automatically filter data based on initial dropdown values
    }).catch(error => {
        console.error("Error loading the CSV data:", error);
    });

    function formatAndPopulateTable(data) {
        const tableBody = document.getElementById("source-table-body");
        tableBody.innerHTML = "";  // Clear any existing content
    
        data.forEach(row => {
            const headers = [
                "Agency",
                "Population Covered",
                "Source Type",
                "Source Method",
                "Most Recent Data",
                "Primary Link"
            ];
            
            const columns = [
                row.agency_full,
                parseInt(row.population).toLocaleString(),
                row.source_type,
                row.source_method,
                row.most_recent_month,
                `<a href="${row.source_link}" target="_blank">Click Here</a>`
            ];
    
            // For each header/data pair, create a new row
            headers.forEach((header, index) => {
                const tr = document.createElement("tr");
    
                const th = document.createElement("td");
                th.textContent = header;
                th.style.fontWeight = "bold"; // Ensure headers are bold
                th.style.backgroundColor = "#00333a"; // Background color to match header style
                th.style.color = "white"; // White text for headers
                tr.appendChild(th);
    
                const td = document.createElement("td");
                td.innerHTML = columns[index];
                tr.appendChild(td);
    
                tableBody.appendChild(tr);
            });
        });
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
