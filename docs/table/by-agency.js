document.addEventListener("DOMContentLoaded", function() {
    // Load data using D3
    d3.csv("../app_data/viz_data.csv").then(function(data) {
        console.log("Raw Data:", data);

        // Parse the date and numerical values
        data.forEach(d => {
            d.date = d3.timeParse("%Y-%m-%d")(d.date);
            d.count = +d.count;
            d.mvs_12mo = +d.mvs_12mo;
        });

        console.log("Parsed Data:", data);

        // Function to filter data based on crime type, state, and agency
        function filterData(data, crimeType, state, agency) {
            return data.filter(d => d.crime_type === crimeType && d.state_name === state && d.agency_name === agency);
        }

        // Function to populate state dropdown
        function populateStateDropdown(data) {
            const stateDropdown = d3.select("#state-dropdown");
            const states = Array.from(new Set(data.map(d => d.state_name))).sort();

            stateDropdown.selectAll("div")
                .data(states)
                .enter()
                .append("div")
                .attr("class", "dropdown-item")
                .attr("data-value", d => d)
                .text(d => d)
                .on("click", function() {
                    const selectedState = d3.select(this).attr("data-value");
                    d3.select("#state-btn").text(selectedState).append("i").attr("class", "fas fa-caret-down");
                    populateAgencyDropdown(data, selectedState);
                    updateByAgencyTable(data, selectedState, d3.select("#agency-btn").text());
                });
        }

        // Function to populate agency dropdown based on selected state
        function populateAgencyDropdown(data, selectedState) {
            const agencyDropdown = d3.select("#agency-dropdown");
            agencyDropdown.html(""); // Clear existing options

            const agencies = Array.from(new Set(data.filter(d => d.state_name === selectedState).map(d => d.agency_name))).sort();

            agencyDropdown.selectAll("div")
                .data(agencies)
                .enter()
                .append("div")
                .attr("class", "dropdown-item")
                .attr("data-value", d => d)
                .text(d => d)
                .on("click", function() {
                    const selectedAgency = d3.select(this).attr("data-value");
                    d3.select("#agency-btn").text(selectedAgency).append("i").attr("class", "fas fa-caret-down");
                    updateByAgencyTable(data, selectedState, selectedAgency);
                });
        }

        // Function to populate By Agency Table
        function updateByAgencyTable(data, selectedState, selectedAgency) {
            const tbody = d3.select("#by-agency-table tbody");
            tbody.html(""); // Clear existing table data

            // Transform data to wide format and sort by date
            const filteredData = filterData(data, defaultCrimeType, selectedState, selectedAgency);
            const groupedData = d3.group(filteredData, d => d.date);
            const wideData = Array.from(groupedData, ([key, values]) => {
                const row = { date: d3.timeFormat("%B %Y")(key), agency: values[0].agency_name };
                values.forEach(d => {
                    row[d.crime_type] = d.count;
                });
                return row;
            }).sort((a, b) => d3.descending(a.date, b.date));

            console.log("Wide Data:", wideData);

            // Define columns
            const columns = ["agency", "date", "Murder", "Rape", "Robbery", "Assault", "Burglary", "Theft", "Motor Vehicle Theft", "Arson"];

            // Append the data rows
            wideData.forEach(row => {
                const tr = tbody.append("tr");
                columns.forEach(col => {
                    tr.append("td").text(row[col] || 0);
                });
            });
        }

        // Populate the state dropdown
        populateStateDropdown(data);

        // Filter by default crime type, state, and agency to populate the By Agency table
        const defaultCrimeType = "Murder"; // Change to your default crime type
        const defaultState = "Texas"; // Set your default state
        const defaultAgency = "Houston"; // Set your default agency
        d3.select("#state-btn").text(defaultState).append("i").attr("class", "fas fa-caret-down");
        d3.select("#agency-btn").text(defaultAgency).append("i").attr("class", "fas fa-caret-down");
        populateAgencyDropdown(data, defaultState);
        updateByAgencyTable(data, defaultState, defaultAgency);
    }).catch(function(error) {
        console.error("Error loading the CSV file:", error);
    });
});
