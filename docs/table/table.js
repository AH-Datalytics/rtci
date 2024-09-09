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
        });

        allData = data;

        const severityOrder = ["Violent Crimes", "Murders", "Rapes", "Robberies", "Aggravated Assaults", "Property Crimes", "Burglaries", "Thefts", "Motor Vehicle Thefts"];
        const crimeTypes = severityOrder.filter(crimeType => data.some(d => d.crime_type === crimeType));

        crimeTypes.forEach(crimeType => {
            const option = document.createElement("div");
            option.className = "dropdown-item";
            option.dataset.value = crimeType;
            option.textContent = crimeType;
            if (crimeType === crimeTypeBtn.dataset.value) {
                option.classList.add("selected");
            }
            option.addEventListener('click', function() {
                crimeTypeBtn.textContent = crimeType;
                crimeTypeBtn.dataset.value = crimeType;
                crimeTypeSelect.classList.remove("show");
                populateFullSampleTable();
                setSelectedClass(crimeTypeSelect, crimeType);
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

    function populateFullSampleTable() {
        const crimeType = crimeTypeBtn.dataset.value || "Murders";
        let filteredData = allData.filter(d => d.crime_type === crimeType);
    
        filteredData = sortTable(filteredData);
    
        const tableBody = document.getElementById("full-sample-table-body");
        tableBody.innerHTML = "";
    
        const formatNumber = d3.format(","); // Formatter for numbers with commas
    
        filteredData.forEach(d => {
            const row = tableBody.insertRow();
            
            const cell0 = row.insertCell(0);
            cell0.textContent = d.agency_full;
            
            const cell1 = row.insertCell(1); // Add Population column
            cell1.textContent = formatNumber(d.population);
            
            const cell2 = row.insertCell(2);
            cell2.textContent = d.crime_type;
            
            const cell3 = row.insertCell(3);
            cell3.textContent = formatNumber(d.YTD);
            
            const cell4 = row.insertCell(4);
            cell4.textContent = formatNumber(d.PrevYTD);
            
            const cell5 = row.insertCell(5);
            if (isNaN(d.Percent_Change) || d.Percent_Change === "Undefined") {  
                cell5.textContent = "Undefined";
                cell5.style.color = '#f28106';  // Use orange color for undefined indicating a positive situation
            } else {
                cell5.textContent = d.Percent_Change.toFixed(1) + '%';
                if (d.Percent_Change > 0) {
                    cell5.style.color = '#f28106';  // Positive change
                } else if (d.Percent_Change < 0) {
                    cell5.style.color = '#2d5ef9';  // Negative change
                } else {
                    cell5.style.color = '#00333a';  // No change
                }
            }
    
            const cell6 = row.insertCell(6);

            const startMonth = "January"; // Replace with the actual start month if it's not fixed
            const endMonth = d.Month_Through;
            const dateThrough = new Date(d.Date_Through); // Parse the date string
            const year = dateThrough.getFullYear(); // Extract the year from the date

            cell6.textContent = `${abbreviateMonth(startMonth)} - ${abbreviateMonth(endMonth)}`;
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
    
            if (currentSortKey === "Percent_Change") {
                if (aValue === "Undefined" || isNaN(aValue)) return 1; // "Undefined" or NaN always at the bottom
                if (bValue === "Undefined" || isNaN(bValue)) return -1; // "Undefined" or NaN always at the bottom
                if ((aValue === "Undefined" || isNaN(aValue)) && (bValue === "Undefined" || isNaN(bValue))) return 0;
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

        const headers = ["agency_full", "population", "crime_type", "YTD", "PrevYTD", "Percent_Change", "YTD_Range", "Last Updated"];
        const csvData = [headers.join(",")];

        data.forEach(row => {
            const values = [
                `"${row.agency_full}"`,
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
        let filteredData = allData.filter(d => d.crime_type === crimeType);
        filteredData = sortTable(filteredData);
        downloadCSV(filteredData, `${crimeType}_YTD_Report.csv`);
    });

    document.getElementById("by-agency-btn").addEventListener('click', function() {
        navigateTo('by-agency.html');
    });

    function navigateTo(page) {
        window.location.href = page;
    }
});
