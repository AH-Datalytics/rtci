document.addEventListener("DOMContentLoaded", function() {
    const fullSampleBtn = document.getElementById("full-sample-btn");
    const byAgencyBtn = document.getElementById("by-agency-btn");
    const fullSampleTable = document.getElementById("full-sample-table");
    const filtersContainer = document.getElementById("filters-container");

    const crimeTypeSelect = document.getElementById("crime-type-dropdown");
    const sortKeySelect = document.getElementById("sort-key-dropdown");
    const sortOrderSelect = document.getElementById("sort-order-dropdown");

    const crimeTypeBtn = document.getElementById("crime-type-btn");
    const sortKeyBtn = document.getElementById("sort-key-btn");
    const sortOrderBtn = document.getElementById("sort-order-btn");

    if (!fullSampleBtn || !byAgencyBtn || !fullSampleTable || !crimeTypeSelect || !sortKeySelect || !sortOrderSelect || !crimeTypeBtn || !sortKeyBtn || !sortOrderBtn) {
        console.error("One or more elements could not be found.");
        return;
    }

    fullSampleBtn.addEventListener("click", function() {
        fullSampleTable.style.display = "table";
        if (filtersContainer) filtersContainer.style.display = "flex"; // Show the filters container
        fullSampleBtn.classList.add("active");
        byAgencyBtn.classList.remove("active");
    });

    byAgencyBtn.addEventListener("click", function() {
        window.location.href = "by-agency.html"; // Navigate to the new HTML page
    });

    let currentPage = 1;
    const rowsPerPage = 10;
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
                currentPage = 1;
                populateFullSampleTable();
                setSelectedClass(crimeTypeSelect, crimeType);
            });
            crimeTypeSelect.appendChild(option);
        });

        setSelectedClass(crimeTypeSelect, crimeTypeBtn.dataset.value || "Murders");

        function paginate(data, page, rowsPerPage) {
            const start = (page - 1) * rowsPerPage;
            const end = start + rowsPerPage;
            return data.slice(start, end);
        }

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
            const options = { month: 'short' };
            const monthName = new Intl.DateTimeFormat('en-US', options).format(date);
            return `Jan - ${monthName}`;
        }

        function populateFullSampleTable() {
            const crimeType = crimeTypeBtn.dataset.value || "Murders";
            let filteredData = allData.filter(d => d.crime_type === crimeType);

            filteredData = sortTable(filteredData);

            const paginatedData = paginate(filteredData, currentPage, rowsPerPage);

            const tableBody = document.getElementById("full-sample-table-body");
            tableBody.innerHTML = "";

            paginatedData.forEach(d => {
                const row = tableBody.insertRow();
                row.insertCell(0).textContent = d.agency_full;
                row.insertCell(1).textContent = d.crime_type;
                row.insertCell(2).textContent = d.YTD;
                row.insertCell(3).textContent = d.PrevYTD;
                row.insertCell(4).textContent = d.Percent_Change.toFixed(2) + '%';
                row.insertCell(5).textContent = d.Date_Through;
            });

            document.getElementById("page-info").textContent = `Page ${currentPage} of ${Math.ceil(filteredData.length / rowsPerPage)}`;
        }

        document.getElementById("prev-page").addEventListener("click", () => {
            if (currentPage > 1) {
                currentPage--;
                populateFullSampleTable();
            }
        });

        document.getElementById("next-page").addEventListener("click", () => {
            if (currentPage * rowsPerPage < allData.length) {
                currentPage++;
                populateFullSampleTable();
            }
        });

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

function navigateTo(page) {
    window.location.href = page;
}
