document.addEventListener("DOMContentLoaded", function() {
    const dataPath = "../app_data/sources.csv";
    const tableBody = document.getElementById("source-table-container");
    const agenciesNumBox = document.getElementById("agencies-num-box");

    let allData = [];

    // Load data
    d3.csv(dataPath).then(data => {
        allData = data;  // Store all data for filtering
        displayNationalSample();  // Display rows where in_national_sample is TRUE on page load
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

    // Function to display the National Full Sample
    function displayNationalSample() {
        const filteredData = allData.filter(row => row.in_national_sample === "TRUE");
        formatAndPopulateTable(filteredData);
        updateAgenciesNumBox(filteredData.length);
    }

    function updateAgenciesNumBox(count) {
        agenciesNumBox.innerHTML = `Number of Agencies: <strong>${count}</strong>`;
    }
});
