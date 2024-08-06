document.addEventListener("DOMContentLoaded", function() {
    const dataPath = "../app_data/by_agency_table.csv";
    const tableBody = document.getElementById("by-agency-table-body");
    const agencyBtn = document.getElementById("agency-btn");
    const stateBtn = document.getElementById("state-btn");
    const agencyDropdown = document.getElementById("agency-dropdown");
    const stateDropdown = document.getElementById("state-dropdown");

    let allData = [];
    let filteredAgencies = [];

    // Default filter values
    const defaultFilters = {
        state: "New York",
        agency: "New York City"
    };

    // Load data
    d3.csv(dataPath).then(data => {
        allData = data;  // Store all data for filtering
        retrieveFilterValues(defaultFilters);
        const initialData = data.filter(row => row.agency_name === agencyBtn.textContent && row.state_name === stateBtn.textContent);
        initialData.sort((a, b) => new Date(b.date) - new Date(a.date));
        formatAndPopulateTable(initialData);
        populateFilters(data);
    }).catch(error => {
        console.error("Error loading the CSV data:", error);
    });

    function formatAndPopulateTable(data) {
        tableBody.innerHTML = "";

        const formatNumber = d3.format(","); // Formatter for numbers with commas

        data.forEach(row => {
            const tr = document.createElement("tr");

            ["month_year", "agency_name", "state_name", "murder", "rape", "robbery", "aggravated_assault", "burglary", "theft", "motor_vehicle_theft"].forEach(col => {
                const td = document.createElement("td");
                if (["aggravated_assault", "burglary", "motor_vehicle_theft", "murder", "rape", "robbery", "theft"].includes(col)) {
                    td.textContent = formatNumber(row[col]); // Format with commas
                } else {
                    td.textContent = row[col];
                }
                tr.appendChild(td);
            });

            tableBody.appendChild(tr);
        });
    }

    function populateFilters(data) {
        const states = [...new Set(data.map(row => row.state_name))].sort();

        createSearchableDropdown(stateDropdown, stateBtn, states);
    }

    function updateAgencyFilter(state) {
        const agencies = [...new Set(allData.filter(row => row.state_name === state).map(row => row.agency_name))].sort();
        createSearchableDropdown(agencyDropdown, agencyBtn, agencies);

        const savedFilters = JSON.parse(sessionStorage.getItem('byAgencyTableFilters'));
        const savedAgency = savedFilters ? savedFilters.agency : null;

        // Default to the saved agency or the default agency for the first time
        if (agencies.length > 0) {
            agencyBtn.textContent = agencies.includes(savedAgency) ? savedAgency : (state === defaultFilters.state ? defaultFilters.agency : agencies[0]);
            filterData();
        } else {
            agencyBtn.textContent = "Agency";
        }

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
            filteredData.sort((a, b) => new Date(b.date) - new Date(a.date));
            formatAndPopulateTable(filteredData);
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
});
