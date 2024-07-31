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
    });

    byAgencyBtn.addEventListener("click", function() {
        fullSampleTable.style.display = "none";
        byAgencyTable.style.display = "table";
        byAgencyFilters.style.display = "block";
    });

    let currentPage = 1;
    const rowsPerPage = 10;

    d3.csv("../app_data/viz_data.csv").then(data => {
        console.log("Raw Data:", data);

        data.forEach(d => {
            d.date = new Date(d.date);
        });

        const crimeTypes = Array.from(new Set(data.map(d => d.crime_type)));
        crimeTypes.forEach(crimeType => {
            const option = document.createElement("option");
            option.value = crimeType;
            option.textContent = crimeType;
            crimeTypeFilter.appendChild(option);
        });

        function paginate(data, page, rowsPerPage) {
            const start = (page - 1) * rowsPerPage;
            const end = start + rowsPerPage;
            return data.slice(start, end);
        }

        function calculateYTDValues(filteredData) {
            const mostRecentDate = d3.max(filteredData, d => d.date);
            const mostRecentYear = mostRecentDate.getFullYear();
            const mostRecentMonth = mostRecentDate.getMonth() + 1;

            const ytdCurrentData = filteredData.filter(d => 
                d.date >= new Date(mostRecentYear, 0, 1) &&  // Start from January of the current year
                d.date < new Date(mostRecentYear, mostRecentMonth, 1)  // Include up to the next month
            );
            const ytdPreviousData = filteredData.filter(d => 
                d.date >= new Date(mostRecentYear - 1, 0, 1) &&  // Start from January of the previous year
                d.date < new Date(mostRecentYear - 1, mostRecentMonth, 1)  // Include up to the next month
            );

            const ytdCurrent = d3.sum(ytdCurrentData, d => d.count);
            const ytdPrevious = d3.sum(ytdPreviousData, d => d.count);
            const percentChange = ((ytdCurrent - ytdPrevious) / ytdPrevious) * 100;

            return {
                ytdCurrent,
                ytdPrevious,
                percentChange: percentChange.toFixed(2),
                dateThrough: d3.timeFormat("%B %Y")(mostRecentDate)
            };
        }

        function populateFullSampleTable() {
            const crimeType = crimeTypeFilter.value;
            let filteredData = crimeType === "all" ? data : data.filter(d => d.crime_type === crimeType);

            const agencyData = Array.from(
                d3.group(filteredData, d => d.agency_full),
                ([key, values]) => {
                    const ytdValues = calculateYTDValues(values);
                    return {
                        key,
                        values: {
                            ...ytdValues,
                            crimeType: values[0].crime_type
                        }
                    };
                }
            );

            agencyData.sort((a, b) => b.values.ytdCurrent - a.values.ytdCurrent);

            const paginatedData = paginate(agencyData, currentPage, rowsPerPage);

            const tableBody = document.getElementById("full-sample-table-body");
            tableBody.innerHTML = "";

            paginatedData.forEach(agency => {
                const row = tableBody.insertRow();
                row.insertCell(0).textContent = agency.key;
                row.insertCell(1).textContent = agency.values.crimeType;
                row.insertCell(2).textContent = agency.values.ytdCurrent;
                row.insertCell(3).textContent = agency.values.ytdPrevious;
                row.insertCell(4).textContent = agency.values.percentChange + '%';
                row.insertCell(5).textContent = agency.values.dateThrough;
            });

            document.getElementById("page-info").textContent = `Page ${currentPage} of ${Math.ceil(agencyData.length / rowsPerPage)}`;
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

        populateFullSampleTable();

    }).catch(error => {
        console.error("Error loading the CSV file:", error);
    });
});
