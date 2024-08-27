document.addEventListener("DOMContentLoaded", function() {
    const dataPath = "../app_data/sources.csv";
    const tableBody = document.getElementById("source-table-container");
    const agenciesNumBox = document.getElementById("agencies-num-box");

    let allData = [];
    let currentSortColumn = 'agency_full'; // Set default sort column
    let currentSortOrder = 'asc'; // Set default sort order
    let currentHeaderIndex = null; // To track the currently sorted column

    // Load data
    d3.csv(dataPath).then(data => {
        allData = data;  // Store all data for filtering
        displayNationalSample();  // Display rows where in_national_sample is TRUE on page load
        updateAgenciesNumBox(allData.filter(row => row.in_national_sample === "TRUE").length);
        sortTableByColumn(currentSortColumn, 0); // Default sort by "Agency" on load, assuming it's the first column
    }).catch(error => {
        console.error("Error loading the CSV data:", error);
    });

    function formatAndPopulateTable(data) {
        tableBody.innerHTML = "";  // Clear any existing content
    
        // Create a table element
        const table = document.createElement("table");
    
        // Create the table headers
        const headers = [
            { label: "Agency", key: "agency_full" },
            { label: "Population Covered", key: "population" },
            { label: "Source Type", key: "source_type" },
            { label: "Source Method", key: "source_method" },
            { label: "Most Recent Data", key: "most_recent_month" },
            { label: "Primary Link", key: "source_link" }
        ];

        const thead = document.createElement("thead");
        const headerRow = document.createElement("tr");

        headers.forEach((header, index) => {
            const th = document.createElement("th");

            // Wrap the header text in a <span> for better control
            const span = document.createElement("span");
            span.textContent = header.label;
            span.style.cursor = 'pointer'; // Set cursor to pointer only on the text

            // Add click event listener for sorting
            span.addEventListener('click', () => {
                sortTableByColumn(header.key, index); // Pass the index as well
            });

            th.appendChild(span); // Append the span to the header cell
            headerRow.appendChild(th);
        });
    
        thead.appendChild(headerRow);
        table.appendChild(thead);
    
        // Create the table body
        const tbody = document.createElement("tbody");
    
        data.forEach(row => {
            const tr = document.createElement("tr");

            headers.forEach(header => {
                const td = document.createElement("td");
                const value = row[header.key];
                
                if (header.key === "population") {
                    td.textContent = parseInt(value).toLocaleString(); // Format population with commas
                } else if (header.key === "source_link") {
                    td.innerHTML = `<a href="${value}" target="_blank">Click Here</a>`;
                } else {
                    td.textContent = value;
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

    function sortTableByColumn(columnKey, headerIndex) {
        if (currentSortColumn === columnKey) {
            // Toggle the sort order if the same column is clicked
            currentSortOrder = currentSortOrder === 'asc' ? 'desc' : 'asc';
        } else {
            // Set the new sort column and default to ascending order
            currentSortColumn = columnKey;
            currentSortOrder = 'asc';
        }
    
        // Sort the filtered data
        const filteredData = allData.filter(row => row.in_national_sample === "TRUE");
        filteredData.sort((a, b) => {
            let aValue = a[columnKey];
            let bValue = b[columnKey];
    
            if (columnKey === 'population') {
                aValue = parseInt(aValue);
                bValue = parseInt(bValue);
            } else {
                aValue = aValue.toLowerCase();
                bValue = bValue.toLowerCase();
            }
    
            if (aValue < bValue) return currentSortOrder === 'asc' ? -1 : 1;
            if (aValue > bValue) return currentSortOrder === 'asc' ? 1 : -1;
            return 0;
        });
    
        formatAndPopulateTable(filteredData);
        highlightSortedColumn(headerIndex);
    }
    
    // Initial load logic
    currentSortOrder = 'asc'; // Explicitly set sort order to ascending
    sortTableByColumn(currentSortColumn, 0); // Apply default sort to "Agency" column
    

    function highlightSortedColumn(headerIndex) {
        // Remove the highlight and arrow from all header cells
        document.querySelectorAll(".table-container th span").forEach(span => {
            span.classList.remove("sorted");
            span.innerHTML = span.textContent; // Remove any existing arrows
        });

        // Highlight the currently sorted column
        const sortedHeader = document.querySelectorAll(".table-container th span")[headerIndex];
        sortedHeader.classList.add("sorted");

        // Add the arrow based on the current sort order
        const arrow = currentSortOrder === 'asc' ? ' ▲' : ' ▼';
        sortedHeader.innerHTML += arrow;
    }
});
