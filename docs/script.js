document.addEventListener("DOMContentLoaded", function() {
    const crimeTypeSelect = document.getElementById("crime-type-dropdown");
    const stateSelect = document.getElementById("state-dropdown");
    const agencySelect = document.getElementById("agency-dropdown");
    const dataTypeDropdown = document.getElementById("data-type-dropdown");

    const crimeTypeBtn = document.getElementById("crime-type-btn");
    const stateBtn = document.getElementById("state-btn");
    const agencyBtn = document.getElementById("agency-btn");
    const dataTypeBtn = document.getElementById("data-type-btn");

    const downloadButton = document.getElementById("download-button");

    let allData = [];

    function closeAllDropdowns() {
        const dropdownMenus = document.querySelectorAll(".dropdown-menu");
        dropdownMenus.forEach(menu => {
            menu.classList.remove("show");
        });
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

    function createDropdownOption(value, text, dropdown, button) {
        const option = document.createElement("div");
        option.className = "dropdown-item";
        option.dataset.value = value;
        option.textContent = text;

        if (button.dataset.value === value) {
            option.classList.add('selected');
        }

        option.addEventListener('click', function() {
            const items = dropdown.querySelectorAll('.dropdown-item');
            items.forEach(item => item.classList.remove('selected'));
            option.classList.add('selected');
            button.textContent = text;
            button.dataset.value = value;
            button.appendChild(document.createElement('i')).className = "fas fa-caret-down";
            dropdown.classList.remove("show");

            if (button === stateBtn) {
                updateAgencyFilter(allData, value);
            } else {
                renderChart();
            }

            saveFilterValues();
        });
        return option;
    }

    function createSearchableDropdown(dropdown, button, options) {
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
                const dropdownOption = createDropdownOption(option, option, dropdown, button);
                dropdown.appendChild(dropdownOption);
            });
        }

        searchInput.addEventListener("input", filterOptions);

        options.forEach(option => {
            const dropdownOption = createDropdownOption(option, option, dropdown, button);
            dropdown.appendChild(dropdownOption);
        });
    }

    function updateFilters(data) {
        const severityOrder = ["Violent Crimes", "Murders", "Rapes", "Robberies", "Aggravated Assaults", "Property Crimes", "Burglaries", "Thefts", "Motor Vehicle Thefts"];
        const crimeTypes = severityOrder.filter(crimeType => data.some(d => d.crime_type === crimeType));
        const states = [...new Set(data.map(d => d.state_name))].sort();
        const agencies = [...new Set(data.map(d => d.agency_name))].sort();

        crimeTypeSelect.innerHTML = "";
        crimeTypes.forEach(crimeType => {
            const option = createDropdownOption(crimeType, crimeType, crimeTypeSelect, crimeTypeBtn);
            crimeTypeSelect.appendChild(option);
        });

        createSearchableDropdown(stateSelect, stateBtn, states);

        const dataTypes = [
            { value: "count", text: "Monthly Totals" },
            { value: "mvs_12mo", text: "12 Month Rolling Sum" }
        ];

        dataTypeDropdown.innerHTML = "";
        dataTypes.forEach(dataType => {
            const option = createDropdownOption(dataType.value, dataType.text, dataTypeDropdown, dataTypeBtn);
            dataTypeDropdown.appendChild(option);
        });

        const defaultFilters = {
            crimeType: "Murders",
            state: "Nationwide",
            agency: "Full Sample",
            dataType: "count"
        };

        retrieveFilterValues(defaultFilters);
    }

    function updateAgencyFilter(data, selectedState) {
        const agencies = [...new Set(data.filter(d => d.state_name === selectedState).map(d => d.agency_name))].sort();
        createSearchableDropdown(agencySelect, agencyBtn, agencies);

        const savedFilters = JSON.parse(sessionStorage.getItem('rtciFilters')) || {};
        const savedAgency = savedFilters.agency;

        if (agencies.includes(savedAgency)) {
            agencyBtn.textContent = savedAgency;
            agencyBtn.dataset.value = savedAgency;
        } else if (agencies.includes("Full Sample")) {
            agencyBtn.textContent = "Full Sample";
            agencyBtn.dataset.value = "Full Sample";
        } else if (agencies.length > 0) {
            agencyBtn.textContent = agencies[0];
            agencyBtn.dataset.value = agencies[0];
        }

        const defaultAgencyOption = agencySelect.querySelector(`[data-value="${agencyBtn.dataset.value}"]`);
        if (defaultAgencyOption) defaultAgencyOption.classList.add('selected');

        renderChart();
    }

    function filterData(data) {
        const selectedCrimeType = crimeTypeBtn.dataset.value;
        const selectedState = stateBtn.dataset.value;
        const selectedAgency = agencyBtn.dataset.value;
        const selectedDataType = dataTypeBtn.dataset.value;

        return data.filter(d =>
            d.crime_type === selectedCrimeType &&
            d.state_name === selectedState &&
            d.agency_name === selectedAgency
        ).map(d => ({
            ...d,
            value: d[selectedDataType]
        }));
    }

    function updateKPIBox1(filteredData) {
        const kpiBox1 = document.getElementById("kpi-box1");
    
        const mostRecentDate = d3.max(filteredData, d => d.date);
        const mostRecentYear = mostRecentDate ? mostRecentDate.getFullYear() : null;
        const mostRecentMonth = mostRecentDate ? mostRecentDate.getMonth() + 1 : null;
    
        const ytdData = filteredData.filter(d =>
            d.date.getFullYear() === mostRecentYear &&
            d.date.getMonth() + 1 <= mostRecentMonth
        );
    
        const ytdSum = d3.sum(ytdData, d => d.count);
        const formattedYtdSum = d3.format(",")(ytdSum);
    
        const selectedCrimeType = crimeTypeBtn.textContent;
    
        if (filteredData.length === 0 || filteredData.every(d => isNaN(d.value))) {
            kpiBox1.innerHTML = `
                <h2>Year to Date ${selectedCrimeType}</h2>
                <p>Missing data.</p>
            `;
            return;
        }
    
        kpiBox1.innerHTML = `
            <h2>Year to Date ${selectedCrimeType}</h2>
            <p>Jan '${mostRecentYear.toString().slice(-2)} through ${d3.timeFormat("%B")(mostRecentDate)} '${mostRecentYear.toString().slice(-2)}</p>
            <p><strong>${formattedYtdSum}</strong></p>
        `;
    }

    function updateKPIBox2(filteredData) {
        const kpiBox2 = document.getElementById("kpi-box2");
    
        const mostRecentDate = d3.max(filteredData, d => d.date);
        const mostRecentYear = mostRecentDate ? mostRecentDate.getFullYear() : null;
        const mostRecentMonth = mostRecentDate ? mostRecentDate.getMonth() + 1 : null;
    
        const startDatePrevYear = new Date(mostRecentYear - 1, 0, 1);
        const endDatePrevYear = new Date(mostRecentYear - 1, mostRecentMonth, 0);
    
        const ytdDataPrevYear = filteredData.filter(d =>
            d.date >= startDatePrevYear && d.date <= endDatePrevYear
        );
    
        const ytdSumPrevYear = d3.sum(ytdDataPrevYear, d => d.count);
        const formattedYtdSumPrevYear = d3.format(",")(ytdSumPrevYear);
    
        const selectedCrimeType = crimeTypeBtn.textContent;
    
        if (filteredData.length === 0 || filteredData.every(d => isNaN(d.value))) {
            kpiBox2.innerHTML = `
                <h2>Previous YTD ${selectedCrimeType}</h2>
                <p>Missing data.</p>
            `;
            return;
        }
    
        kpiBox2.innerHTML = `
            <h2>Previous YTD ${selectedCrimeType}</h2>
            <p>Jan '${(mostRecentYear - 1).toString().slice(-2)} through ${d3.timeFormat("%B")(new Date(mostRecentYear - 1, mostRecentMonth - 1, 1))} '${(mostRecentYear - 1).toString().slice(-2)}</p>
            <p><strong>${formattedYtdSumPrevYear}</strong></p>
        `;
    }
    

    function updateKPIBox3(filteredData) {
        const kpiBox3 = document.getElementById("kpi-box3");
    
        const mostRecentDate = d3.max(filteredData, d => d.date);
        const mostRecentYear = mostRecentDate ? mostRecentDate.getFullYear() : null;
        const mostRecentMonth = mostRecentDate ? mostRecentDate.getMonth() + 1 : null;
    
        const startDateCurrentYear = new Date(mostRecentYear, 0, 1);
        const endDateCurrentYear = new Date(mostRecentYear, mostRecentMonth, 0);
        const startDatePrevYear = new Date(mostRecentYear - 1, 0, 1);
        const endDatePrevYear = new Date(mostRecentYear - 1, mostRecentMonth, 0);
    
        const ytdDataCurrentYear = filteredData.filter(d =>
            d.date >= startDateCurrentYear && d.date <= endDateCurrentYear
        );
    
        const ytdDataPrevYear = filteredData.filter(d =>
            d.date >= startDatePrevYear && d.date <= endDatePrevYear
        );
    
        const ytdSumCurrentYear = d3.sum(ytdDataCurrentYear, d => d.count);
        const ytdSumPrevYear = d3.sum(ytdDataPrevYear, d => d.count);
    
        const percentChange = ((ytdSumCurrentYear - ytdSumPrevYear) / ytdSumPrevYear) * 100;
        const formattedPercentChange = isNaN(percentChange) ? "N/A" : `${percentChange.toFixed(1)}%`;
    
        const selectedCrimeType = crimeTypeBtn.textContent;
    
        if (filteredData.length === 0 || filteredData.every(d => isNaN(d.value))) {
            kpiBox3.innerHTML = `
                <h2>% Change in ${selectedCrimeType} YTD</h2>
                <p>Missing data.</p>
            `;
            return;
        }
    
        kpiBox3.innerHTML = `
            <h2>% Change in ${selectedCrimeType} YTD</h2>
            <p>Jan '${mostRecentYear.toString().slice(-2)} - ${d3.timeFormat("%B")(mostRecentDate)} '${mostRecentYear.toString().slice(-2)} vs. Jan '${(mostRecentYear - 1).toString().slice(-2)} - ${d3.timeFormat("%B")(new Date(mostRecentYear - 1, mostRecentMonth - 1, 1))} '${(mostRecentYear - 1).toString().slice(-2)}</p>
            <p><strong>${formattedPercentChange}</strong></p>
        `;
    }
    
    function abbreviateNumber(value) {
        if (value >= 1e6) {
            return (value / 1e6).toFixed(1) + "M";
        }
        if (value >= 100000) {
            return (value / 1e3).toFixed(0) + "K";
        }
        return d3.format(",")(value);
    }
    

    function renderChart() {
        const filteredData = filterData(allData);
    
        // Check if there are any valid values
        const hasValidValues = filteredData.some(d => !isNaN(d.value));
    
        // Clear existing content
        d3.select("#line-graph-container").html("");
    
        if (!hasValidValues) {
            // Display the message if no valid values are found
            d3.select("#line-graph-container").append("div")
                .attr("class", "no-data-message")
                .style("color", "#00333a")
                .text("Missing some or all data for the selected crime type.");

            // Update KPI boxes with "Missing data"
            updateKPIBox1([]);
            updateKPIBox2([]);
            updateKPIBox3([]);   
            
            return;
        }
    

        updateKPIBox1(filteredData);
        updateKPIBox2(filteredData);
        updateKPIBox3(filteredData);

        d3.select("#line-graph-container svg").remove();

        const margin = { top: 40, right: 30, bottom: 50, left: 70 };
        const container = document.getElementById('line-graph-container');
        const width = container.clientWidth - margin.left - margin.right;
        const height = container.clientHeight - margin.top - margin.bottom;

        const svg = d3.select("#line-graph-container").append("svg")
            .attr("width", width + margin.left + margin.right)
            .attr("height", height + margin.top + margin.bottom)
            .append("g")
            .attr("transform", `translate(${margin.left},${margin.top})`);

        const x = d3.scaleTime()
            .domain(d3.extent(filteredData, d => d.date))
            .range([0, width]);

        const y = d3.scaleLinear()
            .domain([0, d3.max(filteredData, d => d.value)])
            .nice()
            .range([height, 0]);

        const xAxis = d3.axisBottom(x)
            .ticks(d3.timeYear)
            .tickFormat(d3.timeFormat("%Y"))
            .tickSizeOuter(0);

        const xAxisGroup = svg.append("g")
            .attr("transform", `translate(0,${height})`)
            .call(xAxis);

        xAxisGroup.selectAll("path, line")
            .style("stroke", "#e0e0e0");

        xAxisGroup.selectAll("text")
            .style("font-family", "'Roboto Condensed', Arial, sans-serif")
            .style("fill", "#00333a")
            .attr("class", "axis-text");

        const yAxis = d3.axisLeft(y)
            .ticks(Math.min(d3.max(filteredData, d => d.value), 10))
            .tickFormat(abbreviateNumber);  // Use the updated abbreviateNumber function here

        const yAxisGroup = svg.append("g")
            .call(yAxis);

        yAxisGroup.selectAll("path, line")
            .style("stroke", "#e0e0e0");

        yAxisGroup.selectAll("text")
            .style("font-family", "'Roboto Condensed', Arial, sans-serif")
            .style("fill", "#00333a")
            .attr("class", "axis-text");

        const labelFontSize = Math.max(Math.min(height * 0.05, window.innerWidth * 0.02, 16), 14);

        const selectedCrimeType = crimeTypeBtn.textContent;

        function getTextWidth(text, font) {
            const canvas = document.createElement('canvas');
            const context = canvas.getContext('2d');
            context.font = font;
            const metrics = context.measureText(text);
            return metrics.width;
        }

        const maxYLabelWidth = Math.max(...yAxisGroup.selectAll(".tick text").nodes().map(node => node.getBBox().width));


        svg.append("text")
            .attr("transform", "rotate(-90)")
            .attr("y", -margin.left - maxYLabelWidth + 35)
            .attr("x", -height / 2)
            .attr("dy", "1em")
            .style("text-anchor", "middle")
            .style("font-family", "'Roboto Condensed', Arial, sans-serif")
            .style("font-size", `${labelFontSize}px`)
            .attr("fill", "#00333a")
            .text(`Reported ${selectedCrimeType}`);

        svg.selectAll(".tick text")
            .style("font-family", "'Roboto Condensed', Arial, sans-serif")
            .style("fill", "#00333a");

        const lineThickness = Math.max(Math.min(width * 0.003, 2.5), 1);
        const dotSize = Math.max(Math.min(width * 0.003, 2.5), 1);

        const line = svg.append("path")
            .datum(filteredData)
            .attr("fill", "none")
            .attr("stroke", "#2d5ef9")
            .attr("stroke-width", lineThickness)
            .attr("d", d3.line()
                .curve(d3.curveCatmullRom.alpha(0.5))
                .x(d => x(d.date))
                .y(d => y(d.value))
            );

        const selectedDataType = dataTypeBtn.dataset.value;

        const formatComma = d3.format(",");

        const tooltip = d3.select("body").append("div")
            .attr("class", "tooltip")
            .style("opacity", 0)
            .style("font-family", "'Roboto Condensed', Arial, sans-serif");

        if (selectedDataType === "count") {
            const dots = svg.selectAll("circle")
                .data(filteredData)
                .enter().append("circle")
                .attr("cx", d => x(d.date))
                .attr("cy", d => y(d.value))
                .attr("r", dotSize)
                .attr("fill", "#2d5ef9")
                .style("cursor", "pointer"); // Add this line to change cursor to pointer
                ;

            dots.on("mouseover", function(event, d) {
                d3.select(this).attr("fill", "#f28106");

                tooltip.transition()
                    .duration(0)
                    .style("opacity", .9);
                tooltip.html(`<strong>Agency:</strong> ${d.agency_name}<br><strong>Crime Type:</strong> ${d.crime_type}<br><strong>Total:</strong> ${formatComma(d.value)}<br><strong>Date:</strong> ${d3.timeFormat("%B %Y")(d.date)}`)
                    .style("left", (event.pageX + 5) + "px")
                    .style("top", (event.pageY - 28) + "px");
            })
            .on("mousemove", function(event, d) {
                tooltip.style("left", (event.pageX + 5) + "px")
                    .style("top", (event.pageY - 28) + "px");
            })
            .on("mouseout", function(d) {
                d3.select(this).attr("fill", "#2d5ef9");
                tooltip.transition()
                    .duration(500)
                    .style("opacity", 0);
            });
        } else {
            const path = svg.append("path")
                .datum(filteredData)
                .attr("fill", "none")
                .attr("stroke", "#2d5ef9")
                .attr("stroke-width", lineThickness)
                .attr("d", d3.line()
                    .curve(d3.curveCatmullRom.alpha(0.5))
                    .x(d => x(d.date))
                    .y(d => y(d.value))
                )    
                .style("cursor", "pointer"); // Add this line to change cursor to pointer
                ;
        
            path.on("mousemove", function(event) {
                const [mouseX, mouseY] = d3.pointer(event);
                const xDate = x.invert(mouseX);
                const closestData = filteredData.reduce((a, b) => {
                    return Math.abs(b.date - xDate) < Math.abs(a.date - xDate) ? b : a;
                });
                const xPos = x(closestData.date);
                const yPos = y(closestData.value);
        
                tooltip.transition()
                    .duration(0)
                    .style("opacity", .9);
                tooltip.html(`<strong>Agency:</strong> ${closestData.agency_name}<br><strong>Crime Type:</strong> ${closestData.crime_type}<br><strong>12 Month Sum:</strong> ${formatComma(closestData.value)}<br><strong>Through:</strong> ${d3.timeFormat("%B %Y")(closestData.date)}`)
                    .style("left", (event.pageX + 5) + "px")
                    .style("top", (event.pageY - 28) + "px");
            })
            .on("mouseout", function() {
                tooltip.transition()
                    .duration(500)
                    .style("opacity", 0);
            });
        }
        

        const agencyFull = filteredData[0].agency_full;
        const stateUcrLink = filteredData[0].state_ucr_link;
        let sourceText;

        // Check if the agency name ends with 's'
        if (agencyFull.endsWith("s")) {
            sourceText = `${agencyFull}' primary`;
        } else {
            sourceText = `${agencyFull}'s primary`;
        }

        const sourceGroup = svg.append("g")
            .attr("transform", `translate(${width}, ${height + margin.bottom - 10})`)
            .attr("text-anchor", "end");

        const sourceTextElement = sourceGroup.append("text")
            .attr("class", "source-link")
            .style("font-family", "'Roboto Condensed', Arial, sans-serif")
            .style("fill", "#00333a");

        sourceTextElement.append("tspan")
            .text(sourceText)
            .style("cursor", "text");

        sourceTextElement.append("tspan")
            .attr("text-anchor", "start")
            .attr("dx", "0.2em")
            .attr("class", "source-link")
            .style("cursor", "pointer")
            .on("click", function() { window.open(stateUcrLink, "_blank"); })
            .text("source.");


        const population = abbreviateNumber(filteredData[0].population);
        const agencyCount = filteredData[0].agency_count || "N/A";

        const captionGroup = svg.append("g")
            .attr("transform", `translate(0, ${height + margin.bottom - 10})`)
            .attr("text-anchor", "start")
            .attr("class", "caption-group");

        const captionTextElement = captionGroup.append("text")
            .style("font-family", "'Roboto Condensed', Arial, sans-serif")
            .style("fill", "#00333a");

        captionTextElement.append("tspan")
            .text("Population Covered* : ")
            .attr("x", 0);

        captionTextElement.append("tspan")
            .text(population)
            .attr("dx", "0.2em")
            .style("fill", "#f28106");

        captionTextElement.append("tspan")
            .text("Number of Agencies : ")
            .attr("dx", "3em");

        captionTextElement.append("tspan")
            .text(agencyCount)
            .attr("dx", "0.2em")
            .style("fill", "#f28106");
    }

    function downloadFilteredData(filteredData) {
        const selectedDataType = dataTypeBtn.dataset.value;
        const headers = ["agency_name", "state_name", "date", "crime_type", "number_of_agencies"];

        const dataColumn = selectedDataType === "count" ? "count" : "mvs_12mo";
        headers.push(dataColumn);

        const csvRows = [headers.join(",")];

        const hasAgencyCount = filteredData.length > 0 && filteredData[0].hasOwnProperty("number_of_agencies");

        filteredData.forEach(d => {
            const row = [
                d.agency_name,
                d.state_name,
                d3.timeFormat("%Y-%m-%d")(d.date),
                d.crime_type,
                hasAgencyCount ? d.number_of_agencies : "N/A",
                d.value
            ];
            csvRows.push(row.join(","));
        });

        const csvContent = "data:text/csv;charset=utf-8," + csvRows.join("\n");

        const encodedUri = encodeURI(csvContent);
        const link = document.createElement("a");
        link.setAttribute("href", encodedUri);
        link.setAttribute("download", "filtered_data.csv");

        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }

    function saveFilterValues() {
        const filters = {
            crimeType: crimeTypeBtn.dataset.value,
            state: stateBtn.dataset.value,
            agency: agencyBtn.dataset.value,
            dataType: dataTypeBtn.dataset.value
        };
        sessionStorage.setItem('rtciFilters', JSON.stringify(filters));
    }

    function retrieveFilterValues(defaultFilters) {
        const savedFilters = JSON.parse(sessionStorage.getItem('rtciFilters')) || defaultFilters;

        crimeTypeBtn.textContent = savedFilters.crimeType;
        crimeTypeBtn.dataset.value = savedFilters.crimeType;
        stateBtn.textContent = savedFilters.state;
        stateBtn.dataset.value = savedFilters.state;
        agencyBtn.textContent = savedFilters.agency;
        agencyBtn.dataset.value = savedFilters.agency;
        dataTypeBtn.textContent = savedFilters.dataType === "count" ? "Monthly Totals" : "12 Month Rolling Sum";
        dataTypeBtn.dataset.value = savedFilters.dataType;

        const crimeTypeOption = crimeTypeSelect.querySelector(`[data-value="${savedFilters.crimeType}"]`);
        if (crimeTypeOption) crimeTypeOption.classList.add('selected');
        const stateOption = stateSelect.querySelector(`[data-value="${savedFilters.state}"]`);
        if (stateOption) stateOption.classList.add('selected');
        const dataTypeOption = dataTypeDropdown.querySelector(`[data-value="${savedFilters.dataType}"]`);
        if (dataTypeOption) dataTypeOption.classList.add('selected');

        updateAgencyFilter(allData, savedFilters.state);
    }

    d3.csv("app_data/viz_data.csv").then(function(data) {
        data.forEach(d => {
            d.date = d3.timeParse("%Y-%m-%d")(d.date);
            d.count = +d.count;
            d.mvs_12mo = +d.mvs_12mo;
        });

        allData = data;
        updateFilters(allData);
        renderChart();
    }).catch(function(error) {
        console.error("Error loading the CSV file:", error);
    });

    window.addEventListener('resize', renderChart);

    toggleDropdown(crimeTypeBtn, crimeTypeSelect);
    toggleDropdown(stateBtn, stateSelect);
    toggleDropdown(agencyBtn, agencySelect);
    toggleDropdown(dataTypeBtn, dataTypeDropdown);

    downloadButton.addEventListener("click", function() {
        const filteredData = filterData(allData);
        downloadFilteredData(filteredData);
    });

    dataTypeDropdown.addEventListener('click', event => {
        const selectedItem = event.target.closest('.dropdown-item');
        if (selectedItem) {
            dataTypeBtn.textContent = selectedItem.textContent;
            dataTypeBtn.dataset.value = selectedItem.dataset.value;
            dataTypeDropdown.classList.remove("show");
            renderChart();
            saveFilterValues();
        }
    });

    const dataTypeSelect = document.getElementById("data-type");
    dataTypeSelect.addEventListener('change', renderChart);

    function openTab(event, tabName) {
        var tabContents = document.getElementsByClassName('tab-content');
        for (var i = 0; i < tabContents.length; i++) {
            tabContents[i].style.display = 'none';
            tabContents[i].classList.remove('active');
        }

        var tabLinks = document.getElementsByClassName('tab-link');
        for (var i = 0; i < tabLinks.length; i++) {
            tabLinks[i].classList.remove('active');
        }

        document.getElementById(tabName).style.display = 'block';
        document.getElementById(tabName).classList.add('active');
        event.currentTarget.classList.add('active');
    }

    if (document.getElementById('dashboard')) {
        document.getElementById('dashboard').style.display = 'block';
        document.getElementById('dashboard').classList.add('active');
    }

    var tabLinks = document.getElementsByClassName('tab-link');
    for (var i = 0; i < tabLinks.length; i++) {
        tabLinks[i].addEventListener('click', function(event) {
            var tabName = this.getAttribute('data-tab');
            openTab(event, tabName);
        });
    }
});
