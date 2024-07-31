document.addEventListener("DOMContentLoaded", function() {
    const fullSampleBtn = document.getElementById("full-sample-btn");
    const byAgencyBtn = document.getElementById("by-agency-btn");
    const fullSampleTable = document.getElementById("full-sample-table");
    const byAgencyTable = document.getElementById("by-agency-table");
    const byAgencyFilters = document.getElementById("by-agency-filters");
    const crimeTypeFilter = document.getElementById("crime-type-filter");

    fullSampleBtn.addEventListener("click", function() {
        fullSampleTable.style.display = "table";
        byAgencyTable.style.display = "none";
        byAgencyFilters.style.display = "none";
        fullSampleBtn.classList.add("active");
        byAgencyBtn.classList.remove("active");
    });

    byAgencyBtn.addEventListener("click", function() {
        fullSampleTable.style.display = "none";
        byAgencyTable.style.display = "table";
        byAgencyFilters.style.display = "block";
        byAgencyBtn.classList.add("active");
        fullSampleBtn.classList.remove("active");
    });

    let currentPage = 1;
    const rowsPerPage = 10;
    let allData;

    d3.csv("../app_data/full_table_data.csv").then(data => {
        data.forEach(d => {
            d.YTD = +d.YTD;
            d.PrevYTD = +d.PrevYTD;
            d.Percent_Change = +d.Percent_Change;
        });

        allData = data;

        const crimeTypes = Array.from(new Set(data.map(d => d.crime_type)));
        crimeTypes.forEach(crimeType => {
            const option = document.createElement("option");
            option.value = crimeType;
            option.textContent = crimeType;
            crimeTypeFilter.appendChild(option);
        });

        // Set default crime type to Murders
        crimeTypeFilter.value = "Murders";

        function paginate(data, page, rowsPerPage) {
            const start = (page - 1) * rowsPerPage;
            const end = start + rowsPerPage;
            return data.slice(start, end);
        }

        function populateFullSampleTable(sortedData = null) {
            const crimeType = crimeTypeFilter.value;
            let filteredData = crimeType === "" ? data : data.filter(d => d.crime_type === crimeType);

            if (sortedData) {
                filteredData = sortedData;
            } else {
                filteredData.sort((a, b) => b.YTD - a.YTD); // Default sorting by YTD descending
            }

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

        function sortTable(data, key) {
            return data.slice().sort((a, b) => {
                if (key === "agency_full" || key === "crime_type") {
                    return a[key].localeCompare(b[key]);
                } else {
                    return b[key] - a[key];
                }
            });
        }

        document.getElementById("prev-page").addEventListener("click", () => {
            if (currentPage > 1) {
                currentPage--;
                populateFullSampleTable();
            }
        });

        document.getElementById("next-page").addEventListener("click", () => {
            if (currentPage * rowsPerPage < data.length) {
                currentPage++;
                populateFullSampleTable();
            }
        });

        crimeTypeFilter.addEventListener("change", () => {
            currentPage = 1;
            populateFullSampleTable();
        });

        const headers = document.querySelectorAll("th[data-sort]");
        headers.forEach(header => {
            header.addEventListener("click", () => {
                const key = header.getAttribute("data-sort");
                const sortedData = sortTable(allData.filter(d => d.crime_type === crimeTypeFilter.value), key);
                populateFullSampleTable(sortedData);
            });
        });

        // Default view: Murders sorted by YTD descending
        populateFullSampleTable();

    }).catch(error => {
        console.error("Error loading the CSV file:", error);
    });
});
