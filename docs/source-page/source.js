// Function to load and populate the source data table
function loadSourceData(stateFilter = null, agencyFilter = null) {
    d3.csv("../app_data/sources.csv").then(function(data) {
        const tableContainer = d3.select("#source-table-container");
        tableContainer.html(''); // Clear any existing table

        // Filter data based on state and agency
        let filteredData = data;
        if (stateFilter) {
            filteredData = filteredData.filter(d => d.state_name === stateFilter);
        }
        if (agencyFilter) {
            filteredData = filteredData.filter(d => d.agency_name === agencyFilter);
        }

        // Create the table element
        const table = tableContainer.append("table");
        const thead = table.append("thead");
        const tbody = table.append("tbody");
        
        // Define the columns with correct CSV column names
        const columns = [
            { display: "Agency", key: "agency_full" }, 
            { display: "Population", key: "population" }, 
            { display: "Number of Agencies", key: "agency_num" }, 
            { display: "Source Type", key: "source_type" }, 
            { display: "Source Method", key: "source_method" }, 
            { display: "Most Recent Data", key: "most_recent_month" }, 
            { display: "Link", key: "source_link" }
        ];

        // Append the header row
        thead.append("tr")
            .selectAll("th")
            .data(columns)
            .enter()
            .append("th")
            .text(function(column) { return column.display; });

        // Append rows to the table body
        const rows = tbody.selectAll("tr")
            .data(filteredData)
            .enter()
            .append("tr");

        // Append cells to each row
        rows.selectAll("td")
            .data(function(row) {
                return columns.map(function(column) {
                    if (column.key === "source_link") {
                        return `<a href="${row[column.key]}" target="_blank">Click here</a>`;
                    }
                    return row[column.key];
                });
            })
            .enter()
            .append("td")
            .html(function(d) { return d; });

        // Update the dropdowns
        populateDropdowns(data, stateFilter);
    });
}

// Populate state and agency dropdowns
function populateDropdowns(data, selectedState) {
    const stateDropdown = d3.select("#state-dropdown");
    const agencyDropdown = d3.select("#agency-dropdown");

    // Populate state dropdown
    let states = [...new Set(data.map(d => d.state_name))];

    // Sort states alphabetically, but place "Nationwide" at the top
    states = states.sort((a, b) => {
        if (a === "Nationwide") return -1;
        if (b === "Nationwide") return 1;
        return a.localeCompare(b);
    });

    stateDropdown.html('');
    stateDropdown.selectAll("div")
        .data(states)
        .enter()
        .append("div")
        .attr("class", "dropdown-item")
        .text(d => d)
        .on("click", function(event, d) {
            setFilterText(d, ''); // Clear agency filter
            loadSourceData(d); // Reload data with state filter
            closeDropdowns(); // Close dropdown after selection
        });

    // Populate agency dropdown based on selected state
    if (selectedState) {
        let agencies = [...new Set(data.filter(d => d.state_name === selectedState).map(d => d.agency_name))];

        // Sort agencies alphabetically
        agencies = agencies.sort((a, b) => a.localeCompare(b));

        agencyDropdown.html('');
        agencyDropdown.selectAll("div")
            .data(agencies)
            .enter()
            .append("div")
            .attr("class", "dropdown-item")
            .text(d => d)
            .on("click", function(event, d) {
                setFilterText(selectedState, d); // Update filter sentence
                loadSourceData(selectedState, d); // Reload data with both filters
                closeDropdowns(); // Close dropdown after selection
            });
    } else {
        agencyDropdown.html('<div class="dropdown-item">Select a state first</div>');
    }
}

// Function to update the filter sentence
function setFilterText(state, agency) {
    document.getElementById('state-btn').textContent = state || 'State';
    document.getElementById('agency-btn').textContent = agency || 'Agency';
}

// Function to close all dropdowns
function closeDropdowns() {
    d3.selectAll('.dropdown-menu').classed('show', false);
}

// Initial load actions
document.addEventListener('DOMContentLoaded', function() {
    loadSourceData(); // Load data without filters initially

    // Add event listeners to dropdown buttons to toggle dropdown visibility
    d3.select('#state-btn').on('click', function() {
        d3.select('#state-dropdown').classed('show', !d3.select('#state-dropdown').classed('show'));
    });
    
    d3.select('#agency-btn').on('click', function() {
        d3.select('#agency-dropdown').classed('show', !d3.select('#agency-dropdown').classed('show'));
    });

    // Close dropdowns if clicking outside
    document.addEventListener('click', function(event) {
        if (!event.target.closest('.dropdown-btn')) {
            closeDropdowns();
        }
    });
});
