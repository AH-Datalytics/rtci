document.addEventListener("DOMContentLoaded", function () {
    const dataPath = "../app_data/by_agency_table.csv";
    let allData = [];
    let selectedState = "State";
    let selectedAgency = "Agency";
    
    const currentYear = new Date().getFullYear();
    const yearLabels = { 
        twoPrev: currentYear - 2, 
        onePrev: currentYear - 1, 
        current: currentYear 
    };

    // Load data
    d3.csv(dataPath).then(data => {
        allData = data;
        console.log("Data loaded:", data);
        populateDropdowns(data);
        updateYearHeaders();
    }).catch(error => console.error("Error loading data:", error));

    function populateDropdowns(data) {
        const states = [...new Set(data.map(row => row.state_name))].sort();
        createSearchableDropdown("state-dropdown", "state-btn", states, true);
        createSearchableDropdown("agency-dropdown", "agency-btn", [], false);
    }

    function createSearchableDropdown(dropdownId, buttonId, options, isState) {
        const dropdown = document.getElementById(dropdownId);
        const button = document.getElementById(buttonId);

        const searchInput = document.createElement("input");
        searchInput.type = "text";
        searchInput.placeholder = "Search...";
        searchInput.className = "dropdown-search";

        dropdown.innerHTML = "";
        dropdown.appendChild(searchInput);

        function filterOptions() {
            const filter = searchInput.value.toLowerCase();
            const filteredOptions = options.filter(option => option.toLowerCase().includes(filter));
            const existingItems = dropdown.querySelectorAll(".dropdown-item");
            existingItems.forEach(item => item.remove());

            filteredOptions.forEach(option => {
                const item = document.createElement("div");
                item.className = "dropdown-item";
                item.textContent = option;
                item.addEventListener("click", () => {
                    button.textContent = option;
                    dropdown.classList.remove("show");

                    if (isState) {
                        selectedState = option;
                        updateAgencyDropdown(selectedState);
                    } else {
                        selectedAgency = option;
                    }
                    updateFilterSentence();
                    filterAndDisplayData();
                });
                dropdown.appendChild(item);
            });
        }

        searchInput.addEventListener("input", filterOptions);
        filterOptions();

        button.addEventListener("click", function (event) {
            event.stopPropagation();
            closeAllDropdowns();
            dropdown.classList.toggle("show");
        });

        document.addEventListener("click", closeAllDropdowns);
        dropdown.addEventListener("click", event => event.stopPropagation());
    }

    function updateAgencyDropdown(state) {
        const agencies = [...new Set(allData.filter(row => row.state_name === state).map(row => row.agency_name))].sort();
        createSearchableDropdown("agency-dropdown", "agency-btn", agencies, false);
    }

    function closeAllDropdowns() {
        const dropdownMenus = document.querySelectorAll(".dropdown-menu");
        dropdownMenus.forEach(menu => menu.classList.remove("show"));
    }

    function updateFilterSentence() {
        document.getElementById("filters-container").querySelector("span").textContent =
            `Show me the reported crime scorecard of`;
    }

    function filterAndDisplayData() {
        if (selectedState !== "State" && selectedAgency !== "Agency") {
            const filteredData = allData.filter(row =>
                row.state_name === selectedState && row.agency_name === selectedAgency
            );

            if (filteredData.length > 0) {
                console.log("Filtered data:", filteredData);
                const mostRecentMonth = getMostRecentMonth(filteredData);
                const crimeData = calculateAggregates(filteredData, mostRecentMonth);
                renderScorecard(crimeData);
            }
        }
    }

    function getMostRecentMonth(data) {
        const dates = data.map(row => new Date(row.date));
        const mostRecentDate = new Date(Math.max(...dates));
        return mostRecentDate.getMonth() + 1;
    }

    function calculateAggregates(data, endMonth) {
        const crimeTypes = [
            { type: "violent_crime", label: "Violent Crime", subtypes: ["murder", "rape", "robbery", "aggravated_assault"] },
            { type: "property_crime", label: "Property Crime", subtypes: ["burglary", "theft", "motor_vehicle_theft"] }
        ];

        const result = [];

        crimeTypes.forEach(({ type, label, subtypes }) => {
            const overallCounts = getYearlyCounts(data, type, endMonth, true);
            const typeResults = subtypes.map(crime => ({
                crime: formatCrimeType(crime),
                counts: getYearlyCounts(data, crime, endMonth, false),
                isOverall: false
            }));

            result.push({ crime: label, counts: overallCounts, isOverall: true });
            result.push(...typeResults);
        });

        return result;
    }

    function getYearlyCounts(data, crime, endMonth, isOverall) {
        const yearCounts = { twoPrev: 0, onePrev: 0, current: 0 };

        data.forEach(row => {
            const date = new Date(row.date);
            const year = date.getFullYear();
            const month = date.getMonth() + 1;

            if (month <= endMonth && month >= 1) { // Only consider months from January to endMonth
                if (year === yearLabels.twoPrev) yearCounts.twoPrev += parseInt(row[crime]) || 0;
                else if (year === yearLabels.onePrev) yearCounts.onePrev += parseInt(row[crime]) || 0;
                else if (year === yearLabels.current) yearCounts.current += parseInt(row[crime]) || 0;
            }
        });

        return yearCounts;
    }

    function calculatePercentChange(newVal, oldVal) {
        if (oldVal === 0) return newVal === 0 ? "0%" : "+100%";
        const change = (((newVal - oldVal) / oldVal) * 100).toFixed(1);
        return (change > 0 ? "+" : "") + change + "%";
    }

    function formatCrimeType(crime) {
        return crime.replace(/_/g, ' ').replace(/\b\w/g, char => char.toUpperCase());
    }

    function renderScorecard(data) {
        const tbody = document.getElementById("scorecard-body");
        tbody.innerHTML = "";

        data.forEach(item => {
            const { crime, counts, isOverall } = item;
            const fontWeight = isOverall ? "bold" : "normal";
            const fontSize = isOverall ? "1.2em" : "1em";

            const row = document.createElement("tr");
            row.innerHTML = `
                <td style="font-weight: ${fontWeight}; font-size: ${fontSize};">${crime}</td>
                <td>${counts.twoPrev}</td>
                <td>${counts.onePrev}</td>
                <td style="color: ${getColor(calculatePercentChange(counts.onePrev, counts.twoPrev))};">
                    ${calculatePercentChange(counts.onePrev, counts.twoPrev)}
                </td>
                <td>${counts.twoPrev}</td>
                <td>${counts.onePrev}</td>
                <td>${counts.current}</td>
                <td style="color: ${getColor(calculatePercentChange(counts.current, counts.twoPrev))};">
                    ${calculatePercentChange(counts.current, counts.twoPrev)}
                </td>
                <td style="color: ${getColor(calculatePercentChange(counts.current, counts.onePrev))};">
                    ${calculatePercentChange(counts.current, counts.onePrev)}
                </td>
            `;
            tbody.appendChild(row);
        });
    }

    function getColor(value) {
        return value.startsWith("+") ? "#f28106" : "#2d5ef9";
    }

    function updateYearHeaders() {
        document.querySelector("#scorecard-table thead tr:nth-child(2)").innerHTML = `
            <th style="background-color: #00333a; color: white;"></th>
            <th style="background-color: #00333a; color: white;">${yearLabels.twoPrev}</th>
            <th style="background-color: #00333a; color: white;">${yearLabels.onePrev}</th>
            <th style="background-color: #00333a; color: white;">% Change ${yearLabels.twoPrev}-${yearLabels.onePrev}</th>
            <th style="background-color: #00333a; color: white;">${yearLabels.twoPrev} (YTD)</th>
            <th style="background-color: #00333a; color: white;">${yearLabels.onePrev} (YTD)</th>
            <th style="background-color: #00333a; color: white;">${yearLabels.current} (YTD)</th>
            <th style="background-color: #00333a; color: white;">% Change ${yearLabels.twoPrev}-${yearLabels.current} (YTD)</th>
            <th style="background-color: #00333a; color: white;">% Change ${yearLabels.onePrev}-${yearLabels.current} (YTD)</th>
        `;
    }
});
