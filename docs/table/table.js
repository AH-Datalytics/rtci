document.addEventListener("DOMContentLoaded", function() {
    const crimeTypeSelect = document.getElementById("crime-type-dropdown");
    const crimeTypeBtn = document.getElementById("crime-type-btn");

    let allData;
    let currentSortKey = "YTD";
    let currentSortOrder = "desc";

    d3.csv("../app_data/full_table_data.csv").then(data => {
        data.forEach(d => {
            d.YTD = +d.YTD;
            d.PrevYTD = +d.PrevYTD;
            d.Percent_Change = +d.Percent_Change;
            d.population = +d.population; // Add population parsing
            d.number_of_agencies = +d.number_of_agencies; // Add population parsing
        });

        allData = data;

        // Define crime types with master heading indicators
        const severityOrder = [
            { value: "Violent Crimes", isMaster: true },
            { value: "Murders", isMaster: false },
            { value: "Rapes", isMaster: false },
            { value: "Robberies", isMaster: false },
            { value: "Aggravated Assaults", isMaster: false },
            { value: "Property Crimes", isMaster: true },
            { value: "Burglaries", isMaster: false },
            { value: "Thefts", isMaster: false },
            { value: "Motor Vehicle Thefts", isMaster: false }
        ];

        // Populate the dropdown with the crime types
        severityOrder.forEach(crimeTypeObj => {
            const option = document.createElement("div");
            option.className = "dropdown-item";

            // Add specific styling class for master headings
            if (crimeTypeObj.isMaster) {
                option.classList.add("master-heading");
                // Specifically add a different class for "Property Crimes"
                if (crimeTypeObj.value === "Property Crimes") {
                    option.classList.add("second-master-heading");
                }
            }

            option.dataset.value = crimeTypeObj.value;
            option.textContent = crimeTypeObj.value;

            // Pre-select the default crime type
            if (crimeTypeObj.value === crimeTypeBtn.dataset.value) {
                option.classList.add("selected");
            }

            // Add click event listener for the dropdown item
            option.addEventListener('click', function() {
                crimeTypeBtn.textContent = crimeTypeObj.value;
                crimeTypeBtn.dataset.value = crimeTypeObj.value;
                crimeTypeSelect.classList.remove("show");
                populateFullSampleTable();
                setSelectedClass(crimeTypeSelect, crimeTypeObj.value);
            });

            crimeTypeSelect.appendChild(option);
        });

        setSelectedClass(crimeTypeSelect, crimeTypeBtn.dataset.value || "Murders");

        populateFullSampleTable();
        addSortingListeners(); // Add sorting listeners to column headers
        updateSortedColumnClass(currentSortKey); // Set default sort column and arrow on load
    }).catch(error => {
        console.error("Error loading the CSV file:", error);
    });

    // Agency Type Dropdown Setup
    const agencyTypeSelect = document.getElementById("agency-type-dropdown");
    const agencyTypeBtn = document.getElementById("agency-type-btn");

    const agencyTypeOrder = ["Individual Agencies", "National Samples", "State Samples"];

    // Populate agency type dropdown
    agencyTypeOrder.forEach(type => {
        const option = document.createElement("div");
        option.className = "dropdown-item";
        option.dataset.value = type;
        option.textContent = type;

        if (type === agencyTypeBtn.dataset.value || type === "Individual Agencies") {
            option.classList.add("selected");  // Default selection
            agencyTypeBtn.textContent = type;
            agencyTypeBtn.dataset.value = type;
        }

        option.addEventListener('click', () => {
            agencyTypeBtn.textContent = type;
            agencyTypeBtn.dataset.value = type;
            agencyTypeSelect.classList.remove("show");
            populateFullSampleTable();  // Update table based on filters
            setSelectedClass(agencyTypeSelect, type);
        });

        agencyTypeSelect.appendChild(option);
    });

    // Ensure dropdown toggles
    toggleDropdown(agencyTypeBtn, agencyTypeSelect);


function populateFullSampleTable() {
    const crimeType = crimeTypeBtn.dataset.value || "Murders";
    const agencyType = agencyTypeBtn.dataset.value || "Individual Agencies";

    let filteredData = allData.filter(d =>
        d.crime_type === crimeType && d.type === agencyType
    );

    filteredData = sortTable(filteredData);

    const tableBody = document.getElementById("full-sample-table-body");
    tableBody.innerHTML = "";

    const formatNumber = d3.format(",");

    filteredData.forEach(d => {
        const row = tableBody.insertRow();

        const [agency_name, state_name] = d.agency_full.split(", ").map(s => s.trim());

        row.insertCell(0).textContent = agency_name;
        row.insertCell(1).textContent = state_name;
        row.insertCell(2).textContent = isNaN(d.number_of_agencies) ? "Unknown" : formatNumber(d.number_of_agencies);
        row.insertCell(3).textContent = isNaN(d.population) ? "Unknown" : formatNumber(d.population);
        row.insertCell(4).textContent = d.crime_type;
        row.insertCell(5).textContent = formatNumber(d.YTD);
        row.insertCell(6).textContent = formatNumber(d.PrevYTD);

        const percentChangeCell = row.insertCell(7);
        percentChangeCell.textContent = isNaN(d.Percent_Change) ? "Undefined" : d.Percent_Change.toFixed(1) + '%';
        percentChangeCell.style.color = d.Percent_Change > 0 ? '#f28106' : (d.Percent_Change < 0 ? '#2d5ef9' : '#00333a');

        row.insertCell(8).textContent = `Jan - ${abbreviateMonth(d.Month_Through)}`;
    });
}


    // Function to abbreviate month names
    function abbreviateMonth(month) {
        const monthNames = {
            "January": "Jan",
            "February": "Feb",
            "March": "Mar",
            "April": "Apr",
            "May": "May",
            "June": "Jun",
            "July": "Jul",
            "August": "Aug",
            "September": "Sep",
            "October": "Oct",
            "November": "Nov",
            "December": "Dec"
        };
        return monthNames[month] || month;
    }
    
    function sortTable(data) {
        return data.slice().sort((a, b) => {
            let aValue = a[currentSortKey];
            let bValue = b[currentSortKey];
    
            // Handle sorting for state_name by splitting agency_full
        if (currentSortKey === "state_name") {
            const aState = a.agency_full.split(", ")[1]?.trim();
            const bState = b.agency_full.split(", ")[1]?.trim();
            return currentSortOrder === "asc" ? aState.localeCompare(bState) : bState.localeCompare(aState);
        }

            if (currentSortKey === "Percent_Change") {
                if (aValue === "Undefined" || isNaN(aValue)) return 1; // "Undefined" or NaN always at the bottom
                if (bValue === "Undefined" || isNaN(bValue)) return -1; // "Undefined" or NaN always at the bottom
                if ((aValue === "Undefined" || isNaN(aValue)) && (bValue === "Undefined" || isNaN(bValue))) return 0;
            }

            if (currentSortKey === "population") {
                if (aValue === "Unknown" || isNaN(aValue)) return 1; // "Unknown" or NaN always at the bottom
                if (bValue === "Unknown" || isNaN(bValue)) return -1; // "Unknown" or NaN always at the bottom
                if ((aValue === "Unknown" || isNaN(aValue)) && (bValue === "Unknown" || isNaN(bValue))) return 0;
                return currentSortOrder === "asc" ? aValue - bValue : bValue - aValue;
            }

            // Handle sorting for number_of_agencies, placing "Unknown" or NaN at the bottom
            if (currentSortKey === "number_of_agencies") {
                if (aValue === "Unknown" || isNaN(aValue)) return 1; 
                if (bValue === "Unknown" || isNaN(bValue)) return -1; 
                if ((aValue === "Unknown" || isNaN(aValue)) && (bValue === "Unknown" || isNaN(bValue))) return 0;
                return currentSortOrder === "asc" ? aValue - bValue : bValue - aValue;
            }
    
            if (currentSortKey === "YTD" || currentSortKey === "PrevYTD" || currentSortKey === "Percent_Change" || currentSortKey === "population") { // Add population sorting
                return currentSortOrder === "asc" ? aValue - bValue : bValue - aValue;
            } else {
                return currentSortOrder === "asc" ? aValue.localeCompare(bValue) : bValue.localeCompare(aValue);
            }
        });
    }

    function addSortingListeners() {
        document.querySelectorAll('th span.sortable').forEach((span) => {
            const keyMapping = {
                "Agency": "agency_full",
                "State": "state_name",   // Add the new state_name mapping
                "# of Agencies": "number_of_agencies",
                "Population Covered": "population", // Add population mapping
                "YTD": "YTD",
                "Previous YTD": "PrevYTD",
                "% Change": "Percent_Change"
            };

            const columnKey = keyMapping[span.textContent.trim()];
            if (columnKey) {
                span.dataset.key = columnKey;
                span.style.cursor = 'pointer';

                span.addEventListener('click', () => {
                    if (currentSortKey === columnKey) {
                        currentSortOrder = currentSortOrder === 'asc' ? 'desc' : 'asc';
                    } else {
                        currentSortKey = columnKey;
                        currentSortOrder = 'desc';
                    }
                    populateFullSampleTable();
                    updateSortedColumnClass(columnKey);
                });
            }
        });
    }

    function updateSortedColumnClass(columnKey) {
        document.querySelectorAll('th span.sortable').forEach(span => {
            span.classList.remove('sorted');
            span.querySelectorAll('.arrow').forEach(arrow => arrow.remove());
            span.style.color = '';
        });
    
        const sortedHeader = document.querySelector(`th span.sortable[data-key="${columnKey}"]`);
        if (sortedHeader) {
            sortedHeader.classList.add('sorted');
            sortedHeader.style.color = '#00333a';
            const arrow = document.createElement('span');
            arrow.classList.add('arrow');
            arrow.textContent = currentSortOrder === 'asc' ? ' ▲' : ' ▼';
            sortedHeader.appendChild(arrow);
        }
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

    function closeAllDropdowns() {
        const dropdownMenus = document.querySelectorAll(".dropdown-menu");
        dropdownMenus.forEach(menu => {
            menu.classList.remove("show");
        });
    }

    function setSelectedClass(dropdown, value) {
        dropdown.querySelectorAll(".dropdown-item").forEach(item => {
            item.classList.toggle("selected", item.dataset.value === value);
        });
    }

    toggleDropdown(crimeTypeBtn, crimeTypeSelect);

    function downloadCSV(data, filename) {
        if (!data || !data.length) {
            console.error("No data available for download.");
            return;
        }

        const headers = ["agency_full", "#_of_agencies", "population", "crime_type", "YTD", "PrevYTD", "Percent_Change", "YTD_Range", "Last Updated"];
        const csvData = [headers.join(",")];

        data.forEach(row => {
            const values = [
                `"${row.agency_full}"`,
                `${row.number_of_agencies}`, // Add population to download
                `${row.population}`, // Add population to download
                `"${row.crime_type}"`,
                `${row.YTD}`,
                `${row.PrevYTD}`,
                `${row.Percent_Change.toFixed(2)}%`,
                `"Jan - ${row.Month_Through}"`,
                `${row["Last Updated"]}`
            ];
            csvData.push(values.join(","));
        });

        const csvString = csvData.join("\n");
        const blob = new Blob([csvString], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement("a");
        link.href = URL.createObjectURL(blob);
        link.setAttribute("download", filename);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }

    document.getElementById("table-download").addEventListener("click", function() {
        const crimeType = crimeTypeBtn.dataset.value || "Murders";
        const agencyType = agencyTypeBtn.dataset.value || "Individual Agencies";
    
        let filteredData = allData.filter(d => 
            d.crime_type === crimeType && d.type === agencyType
        );
    
        filteredData = sortTable(filteredData);
        downloadCSV(filteredData, `${crimeType}_${agencyType}_YTD_Report.csv`);
    });
    


    document.getElementById("by-agency-btn").addEventListener('click', function() {
        navigateTo('by-agency.html');
    });

    function navigateTo(page) {
        window.location.href = page;
    }
});
