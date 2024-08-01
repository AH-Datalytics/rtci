document.addEventListener("DOMContentLoaded", function() {
    const crimeTypeSelect = document.getElementById("crime-type-dropdown");
    const sortKeySelect = document.getElementById("sort-key-dropdown");
    const sortOrderSelect = document.getElementById("sort-order-dropdown");

    const crimeTypeBtn = document.getElementById("crime-type-btn");
    const sortKeyBtn = document.getElementById("sort-key-btn");
    const sortOrderBtn = document.getElementById("sort-order-btn");

    let allData;
    let currentSortKey = "YTD";
    let currentSortOrder = "desc";

    d3.csv("../app_data/full_table_data.csv").then(data => {
        data.forEach(d => {
            d.YTD = +d.YTD;
            d.PrevYTD = +d.PrevYTD;
            d.Percent_Change = +d.Percent_Change;
            d.Date_Through = formatDateThrough(d.Date_Through);
        });

        allData = data;

        const crimeTypes = Array.from(new Set(data.map(d => d.crime_type)));
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

        function sortTable(data) {
            return data.slice().sort((a, b) => {
                if (currentSortKey === "agency_full" || currentSortKey === "crime_type") {
                    return currentSortOrder === "asc" ? a[currentSortKey].localeCompare(b[currentSortKey]) : b[currentSortKey].localeCompare(a[currentSortKey]);
                } else {
                    return currentSortOrder === "asc" ? a[currentSortKey] - b[currentSortKey] : b[currentSortKey] - a[currentSortKey];
                }
            });
        }

        function formatDateThrough(dateString) {
            const date = new Date(dateString);
            const options = { month: 'long' };
            const monthName = new Intl.DateTimeFormat('en-US', options).format(date);
            return `January - ${monthName}`;
        }

        function populateFullSampleTable() {
            const crimeType = crimeTypeBtn.dataset.value || "Murders";
            let filteredData = allData.filter(d => d.crime_type === crimeType);

            filteredData = sortTable(filteredData);

            const tableBody = document.getElementById("full-sample-table-body");
            tableBody.innerHTML = "";

            filteredData.forEach(d => {
                const row = tableBody.insertRow();
                
                const cell0 = row.insertCell(0);
                cell0.textContent = d.agency_full;
                if (currentSortKey === "agency_full") cell0.classList.add('bold');
                
                const cell1 = row.insertCell(1);
                cell1.textContent = d.crime_type;
                if (currentSortKey === "crime_type") cell1.classList.add('bold');
                
                const cell2 = row.insertCell(2);
                cell2.textContent = d.YTD;
                if (currentSortKey === "YTD") cell2.classList.add('bold');
                
                const cell3 = row.insertCell(3);
                cell3.textContent = d.PrevYTD;
                if (currentSortKey === "PrevYTD") cell3.classList.add('bold');
                
                const cell4 = row.insertCell(4);
                cell4.textContent = d.Percent_Change.toFixed(1) + '%';
                cell4.style.color = d.Percent_Change >= 0 ? '#f28106' : '#2d5ef9';
                if (currentSortKey === "Percent_Change") cell4.classList.add('bold');
                
                const cell5 = row.insertCell(5);
                cell5.textContent = d.Date_Through;
                if (currentSortKey === "Date_Through") cell5.classList.add('bold');
            });
        }

        sortKeySelect.querySelectorAll(".dropdown-item").forEach(item => {
            if (item.dataset.value === currentSortKey) {
                item.classList.add("selected");
            }
            item.addEventListener("click", function() {
                currentSortKey = this.dataset.value;
                sortKeyBtn.textContent = this.textContent;
                sortKeySelect.classList.remove("show");
                populateFullSampleTable();
                setSelectedClass(sortKeySelect, currentSortKey);
            });
        });

        sortOrderSelect.querySelectorAll(".dropdown-item").forEach(item => {
            if (item.dataset.value === currentSortOrder) {
                item.classList.add("selected");
            }
            item.addEventListener("click", function() {
                currentSortOrder = this.dataset.value;
                sortOrderBtn.textContent = this.textContent;
                sortOrderSelect.classList.remove("show");
                populateFullSampleTable();
                setSelectedClass(sortOrderSelect, currentSortOrder);
            });
        });

        populateFullSampleTable();
    }).catch(error => {
        console.error("Error loading the CSV file:", error);
    });

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
    toggleDropdown(sortKeyBtn, sortKeySelect);
    toggleDropdown(sortOrderBtn, sortOrderSelect);
});
