// Function to load and populate the source data table
function loadSourceData(stateFilter = null, agencyFilter = null) {
    d3.csv("../app_data/sources.csv").then(function(data) {
        const tableContainer = d3.select("#source-table-container");
        tableContainer.html(''); // Clear any existing table

        // Filter data based on state and agency
        let filteredData = data;
        if (stateFilter) {
            filteredData = filteredData.filter(d => d.state === stateFilter);
        }
        if (agencyFilter) {
            filteredData = filteredData.filter(d => d.agency_full === agencyFilter);
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
    const states = [...new Set(data.map(d => d.state))];
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
        });

    // Populate agency dropdown based on selected state
    if (selectedState) {
        const agencies = [...new Set(data.filter(d => d.state === selectedState).map(d => d.agency_full))];
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

// Initial load actions
document.addEventListener('DOMContentLoaded', function() {
    loadSourceData(); // Load data without filters initially
});
