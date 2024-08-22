document.addEventListener("DOMContentLoaded", function() {
    const dataPath = "../app_data/sources.csv";
    const tableBody = document.getElementById("source-table-body");
    const agencyBtn = document.getElementById("agency-btn");
    const stateBtn = document.getElementById("state-btn");
    const agencyDropdown = document.getElementById("agency-dropdown");
    const stateDropdown = document.getElementById("state-dropdown");

    let allData = [];

    // Load data
    d3.csv(dataPath).then(data => {
        allData = data;
        populateFilters(data);
        filterData(); // Load the initial data based on the default filter values
    }).catch(error => {
        console.error("Error loading the CSV data:", error);
    });

    function formatAndPopulateTable(data) {
        tableBody.innerHTML = "";  // Clear any existing content
    
        if (data.length === 0) {
            tableBody.innerHTML = "<tr><td>No data available</td></tr>";
            return;
        }
    
        const firstRow = data[0];
    
        const rows = [
            { label: "Agency", value: firstRow.agency_full },
            { label: "Population Covered", value: parseInt(firstRow.population).toLocaleString() },
            { label: "Source Type", value: firstRow.source_type },
            { label: "Source Method", value: firstRow.source_method },
            { label: "Most Recent Data", value: firstRow.most_recent_month },
            { label: "Primary Link", value: `<a href="${firstRow.source_link}" target="_blank">Click Here</a>` }
        ];
    
        rows.forEach(row => {
            const tr = document.createElement("tr");
            const th = document.createElement("th");
            th.textContent = row.label;
            const td = document.createElement("td");
            td.innerHTML = row.value;
            tr.appendChild(th);
            tr.appendChild(td);
            tableBody.appendChild(tr);
        });
    }
    
    function populateFilters(data) {
        let states = [...new Set(data.map(row => row.state_name))];
    
        states.sort();
    
        createSearchableDropdown(stateDropdown, stateBtn, states);
    }

    function filterData() {
        const selectedState = stateBtn.textContent;
        const selectedAgency = agencyBtn.textContent;
    
        const filteredData = allData.filter(row => row.state_name === selectedState && row.agency_name === selectedAgency);
        formatAndPopulateTable(filteredData);
    }

    // Dropdown toggle and search functionality
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
    }

    function createDropdownOption(value, text, dropdown, button) {
        const option = document.createElement("div");
        option.className = "dropdown-item";
        option.dataset.value = value;
        option.textContent = text;

        option.addEventListener('click', function() {
            const items = dropdown.querySelectorAll('.dropdown-item');
            items.forEach(item => item.classList.remove('selected'));
            option.classList.add('selected');
            button.textContent = text;
            dropdown.classList.remove("show");
            filterData();
        });

        return option;
    }
});
