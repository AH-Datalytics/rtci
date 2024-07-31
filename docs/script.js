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
            closeAllDropdowns();  // Close all dropdowns before toggling the current one
            dropdown.classList.toggle("show");
        });
    
        document.addEventListener('click', function() {
            closeAllDropdowns();  // Close all dropdowns when clicking outside
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
    
        // Check if this option is the current selected option
        if (button.dataset.value === value) {
            option.classList.add('selected');
        }
    
        option.addEventListener('click', function() {
            // Remove the 'selected' class from all items
            const items = dropdown.querySelectorAll('.dropdown-item');
            items.forEach(item => item.classList.remove('selected'));
    
            // Add the 'selected' class to the clicked item
            option.classList.add('selected');
    
            // Update the button text and dataset value
            button.textContent = text;
            button.dataset.value = value;
            button.appendChild(document.createElement('i')).className = "fas fa-caret-down";
            dropdown.classList.remove("show");
    
            if (button === stateBtn) {
                updateAgencyFilter(allData, value);
            } else {
                renderChart();
            }
        });
        return option;
    }
    
    function createSearchableDropdown(dropdown, button, options) {
        const searchInput = document.createElement("input");
        searchInput.type = "text";
        searchInput.placeholder = "Search...";
        searchInput.className = "dropdown-search";
    
        // Clear previous options
        dropdown.innerHTML = "";
        dropdown.appendChild(searchInput);
    
        function filterOptions() {
            const filter = searchInput.value.toLowerCase();
            const filteredOptions = options.filter(option => option.toLowerCase().includes(filter));
    
            // Clear previous options
            const existingItems = dropdown.querySelectorAll(".dropdown-item");
            existingItems.forEach(item => item.remove());
    
            // Add filtered options
            filteredOptions.forEach(option => {
                const dropdownOption = createDropdownOption(option, option, dropdown, button);
                dropdown.appendChild(dropdownOption);
            });
        }
    
        searchInput.addEventListener("input", filterOptions);
    
        // Initial population of options
        options.forEach(option => {
            const dropdownOption = createDropdownOption(option, option, dropdown, button);
            dropdown.appendChild(dropdownOption);
        });
    }
    
    function updateFilters(data) {
        const crimeTypes = [...new Set(data.map(d => d.crime_type))].sort();
        const states = [...new Set(data.map(d => d.state_name))].sort();
        const agencies = [...new Set(data.map(d => d.agency_name))].sort();
    
        // Initialize crime type dropdown without search
        crimeTypeSelect.innerHTML = "";
        crimeTypes.forEach(crimeType => {
            const option = createDropdownOption(crimeType, crimeType, crimeTypeSelect, crimeTypeBtn);
            crimeTypeSelect.appendChild(option);
        });
    
        // Initialize searchable state and agency dropdowns
        createSearchableDropdown(stateSelect, stateBtn, states);
        createSearchableDropdown(agencySelect, agencyBtn, agencies);
    
        // Add options for the data type dropdown
        const dataTypes = [
            { value: "count", text: "Monthly Totals" },
            { value: "mvs_12mo", text: "12 Month Rolling Sum" }
        ];
    
        dataTypeDropdown.innerHTML = "";
        dataTypes.forEach(dataType => {
            const option = createDropdownOption(dataType.value, dataType.text, dataTypeDropdown, dataTypeBtn);
            dataTypeDropdown.appendChild(option);
        });
    
        // Set default values
        if (crimeTypes.includes("Murders")) {
            crimeTypeBtn.textContent = "Murders";
            crimeTypeBtn.dataset.value = "Murders";
        } else {
            crimeTypeBtn.textContent = crimeTypes[0];
            crimeTypeBtn.dataset.value = crimeTypes[0];
        }
    
        if (states.includes("Texas")) {
            stateBtn.textContent = "Texas";
            stateBtn.dataset.value = "Texas";
            updateAgencyFilter(data, "Texas");
        } else {
            stateBtn.textContent = states[0];
            stateBtn.dataset.value = states[0];
            updateAgencyFilter(data, states[0]);
        }
    
        // Set default value for data type
        dataTypeBtn.textContent = "Monthly Totals";
        dataTypeBtn.dataset.value = "count";
    
        // Set default value for agency (prefer "Houston" if available)
        if (agencies.includes("Houston")) {
            agencyBtn.textContent = "Houston";
            agencyBtn.dataset.value = "Houston";
        } else {
            agencyBtn.textContent = agencies[0];
            agencyBtn.dataset.value = agencies[0];
        }
    
        // Add 'selected' class to the default values
        const defaultCrimeTypeOption = crimeTypeSelect.querySelector(`[data-value="${crimeTypeBtn.dataset.value}"]`);
        if (defaultCrimeTypeOption) defaultCrimeTypeOption.classList.add('selected');
    
        const defaultStateOption = stateSelect.querySelector(`[data-value="${stateBtn.dataset.value}"]`);
        if (defaultStateOption) defaultStateOption.classList.add('selected');
    
        const defaultAgencyOption = agencySelect.querySelector(`[data-value="${agencyBtn.dataset.value}"]`);
        if (defaultAgencyOption) defaultAgencyOption.classList.add('selected');
    
        const defaultDataTypeOption = dataTypeDropdown.querySelector(`[data-value="${dataTypeBtn.dataset.value}"]`);
        if (defaultDataTypeOption) defaultDataTypeOption.classList.add('selected');
    }
    
    function updateAgencyFilter(data, selectedState) {
        const agencies = [...new Set(data.filter(d => d.state_name === selectedState).map(d => d.agency_name))].sort();
        createSearchableDropdown(agencySelect, agencyBtn, agencies);
    
        // Set default value to "Houston" if available, else the first agency in the list
        if (agencies.includes("Houston")) {
            agencyBtn.textContent = "Houston";
            agencyBtn.dataset.value = "Houston";
        } else {
            agencyBtn.textContent = agencies[0];
            agencyBtn.dataset.value = agencies[0];
        }
    
        // Add 'selected' class to the default value
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
        
        // Get the most recent year with data
        const mostRecentDate = d3.max(filteredData, d => d.date);
        const mostRecentYear = mostRecentDate.getFullYear();
        const mostRecentMonth = mostRecentDate.getMonth() + 1; // Months are zero-based

        // Filter data for the most recent year up to the most recent month
        const ytdData = filteredData.filter(d => 
            d.date.getFullYear() === mostRecentYear &&
            d.date.getMonth() + 1 <= mostRecentMonth
        );

        // Calculate the sum of offenses
        const ytdSum = d3.sum(ytdData, d => d.count);

        // Format the sum with commas
        const formattedYtdSum = d3.format(",")(ytdSum);

        // Get the selected crime type
        const selectedCrimeType = crimeTypeBtn.textContent;

        // Update KPI box 1 content
        kpiBox1.innerHTML = `
            <h2>Year to Date ${selectedCrimeType}</h2>
            <p>Jan '${mostRecentYear.toString().slice(-2)} through ${d3.timeFormat("%B")(mostRecentDate)} '${mostRecentYear.toString().slice(-2)}</p>
            <p><strong>${formattedYtdSum}</strong></p>
        `;
    }

    function updateKPIBox2(filteredData) {
        const kpiBox2 = document.getElementById("kpi-box2");
        
        // Get the most recent date
        const mostRecentDate = d3.max(filteredData, d => d.date);
        const mostRecentYear = mostRecentDate.getFullYear();
        const mostRecentMonth = mostRecentDate.getMonth() + 1; // Months are zero-based
    
        // Calculate the start and end dates for the previous year
        const startDatePrevYear = new Date(mostRecentYear - 1, 0, 1); // January 1st of previous year
        const endDatePrevYear = new Date(mostRecentYear - 1, mostRecentMonth, 0); // Last day of the most recent month of the previous year
    
        // Filter data for the previous year up to the same month
        const ytdDataPrevYear = filteredData.filter(d => 
            d.date >= startDatePrevYear && d.date <= endDatePrevYear
        );
    
        // Calculate the sum of offenses for the previous year
        const ytdSumPrevYear = d3.sum(ytdDataPrevYear, d => d.count);

        // Format the sum with commas
        const formattedYtdSumPrevYear = d3.format(",")(ytdSumPrevYear);
    
        // Get the selected crime type
        const selectedCrimeType = crimeTypeBtn.textContent;
    
        // Update KPI box 2 content
        kpiBox2.innerHTML = `
            <h2>Previous YTD ${selectedCrimeType}</h2>
            <p>Jan '${(mostRecentYear - 1).toString().slice(-2)} through ${d3.timeFormat("%B")(new Date(mostRecentYear - 1, mostRecentMonth - 1, 1))} '${(mostRecentYear - 1).toString().slice(-2)}</p>
            <p><strong>${formattedYtdSumPrevYear}</strong></p>
        `;
    }
    
    function updateKPIBox3(filteredData) {
        const kpiBox3 = document.getElementById("kpi-box3");
    
        // Get the most recent date
        const mostRecentDate = d3.max(filteredData, d => d.date);
        const mostRecentYear = mostRecentDate.getFullYear();
        const mostRecentMonth = mostRecentDate.getMonth() + 1; // Months are zero-based
    
        // Calculate the start and end dates for the current year
        const startDateCurrentYear = new Date(mostRecentYear, 0, 1); // January 1st of current year
        const endDateCurrentYear = new Date(mostRecentYear, mostRecentMonth, 0); // End of most recent month of current year
    
        // Calculate the start and end dates for the previous year
        const startDatePrevYear = new Date(mostRecentYear - 1, 0, 1); // January 1st of previous year
        const endDatePrevYear = new Date(mostRecentYear - 1, mostRecentMonth, 0); // End of most recent month of previous year
    
        // Filter data for the current year up to the most recent month
        const ytdDataCurrentYear = filteredData.filter(d => 
            d.date >= startDateCurrentYear && d.date <= endDateCurrentYear
        );
    
        // Filter data for the previous year up to the same month
        const ytdDataPrevYear = filteredData.filter(d => 
            d.date >= startDatePrevYear && d.date <= endDatePrevYear
        );
    
        // Calculate the sum of offenses for the current year and previous year
        const ytdSumCurrentYear = d3.sum(ytdDataCurrentYear, d => d.count);
        const ytdSumPrevYear = d3.sum(ytdDataPrevYear, d => d.count);
    
        // Calculate the percentage change
        const percentChange = ((ytdSumCurrentYear - ytdSumPrevYear) / ytdSumPrevYear) * 100;
    
        // Get the selected crime type
        const selectedCrimeType = crimeTypeBtn.textContent;
    
        // Update KPI box 3 content
        kpiBox3.innerHTML = `
            <h2>% Change in ${selectedCrimeType} YTD</h2>
            <p>Jan '${mostRecentYear.toString().slice(-2)} - ${d3.timeFormat("%B")(mostRecentDate)} '${mostRecentYear.toString().slice(-2)} vs. Jan '${(mostRecentYear - 1).toString().slice(-2)} - ${d3.timeFormat("%B")(new Date(mostRecentYear - 1, mostRecentMonth - 1, 1))} '${(mostRecentYear - 1).toString().slice(-2)}</p>
            <p><strong>${percentChange.toFixed(1)}%</strong></p>
        `;
    }
    
    function renderChart() {
        const filteredData = filterData(allData);
    
        // Update KPI boxes
        updateKPIBox1(filteredData);
        updateKPIBox2(filteredData);
        updateKPIBox3(filteredData);
    
        // Remove any existing SVG
        d3.select("#line-graph-container svg").remove();
    
        // Set up the SVG container dimensions
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
        
        // X-axis
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
    
        // Y-axis
        const yAxis = d3.axisLeft(y)
            .ticks(Math.min(d3.max(filteredData, d => d.value), 10))
            .tickFormat(d3.format(",d"));
    
        const yAxisGroup = svg.append("g")
            .call(yAxis);
    
        yAxisGroup.selectAll("path, line")
            .style("stroke", "#e0e0e0");
    
        yAxisGroup.selectAll("text")
            .style("font-family", "'Roboto Condensed', Arial, sans-serif")
            .style("fill", "#00333a")
            .attr("class", "axis-text");
    
        const labelFontSize = Math.max(Math.min(height * 0.05, 16), 10);
    
        const selectedCrimeType = crimeTypeBtn.textContent;
    
        // Function to calculate text width
        function getTextWidth(text, font) {
            const canvas = document.createElement('canvas');
            const context = canvas.getContext('2d');
            context.font = font;
            const metrics = context.measureText(text);
            return metrics.width;
        }

        // Calculate the width of the largest y-axis tick label
        const maxYValue = d3.max(filteredData, d => d.value);
        const maxYValueFormatted = d3.format(",d")(maxYValue);
        const font = `${labelFontSize}px 'Roboto Condensed', Arial, sans-serif`;
        const maxYLabelWidth = getTextWidth(maxYValueFormatted, font);

        svg.append("text")
            .attr("transform", "rotate(-90)")
            .attr("y", -margin.left - maxYLabelWidth + 40) // Adjust to increase distance from the y-axis
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
                .attr("fill", "#2d5ef9");
    
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
            svg.on("mousemove", function(event) {
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
        const sourceText = `${agencyFull}`;
    
        const sourceGroup = svg.append("g")
            .attr("transform", `translate(${width}, ${height + margin.bottom - 10})`)
            .attr("text-anchor", "end");
    
        const sourceTextElement = sourceGroup.append("text")
            .attr("class", "source-link")
            .style("font-family", "'Roboto Condensed', Arial, sans-serif")
            .style("fill", "#00333a");
    
        sourceTextElement.append("tspan")
            .text(sourceText);
    
        sourceTextElement.append("tspan")
            .attr("text-anchor", "start")
            .attr("dx", "0.2em")
            .attr("class", "source-link")
            .style("cursor", "pointer")
            .on("click", function() { window.open(stateUcrLink, "_blank"); })
            .text("source.");
    
        const population = filteredData[0].population;
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
            dataTypeDropdown.classList.remove("show"); // Close the dropdown
            renderChart();
        }
    });
    

    const dataTypeSelect = document.getElementById("data-type");
    dataTypeSelect.addEventListener('change', renderChart);


    // Tab functionality
    function openTab(event, tabName) {
        // Hide all tab contents
        var tabContents = document.getElementsByClassName('tab-content');
        for (var i = 0; i < tabContents.length; i++) {
            tabContents[i].style.display = 'none';
            tabContents[i].classList.remove('active');
        }
        // Remove active class from all tab links
        var tabLinks = document.getElementsByClassName('tab-link');
        for (var i = 0; i < tabLinks.length; i++) {
            tabLinks[i].classList.remove('active');
        }
        // Show the current tab content and add active class to the clicked tab link
        document.getElementById(tabName).style.display = 'block';
        document.getElementById(tabName).classList.add('active');
        event.currentTarget.classList.add('active');
    }

    // Initialize the dashboard tab as active
    if (document.getElementById('dashboard')) {
        document.getElementById('dashboard').style.display = 'block';
        document.getElementById('dashboard').classList.add('active');
    }

    // Event listeners for tabs
    var tabLinks = document.getElementsByClassName('tab-link');
    for (var i = 0; i < tabLinks.length; i++) {
        tabLinks[i].addEventListener('click', function(event) {
            var tabName = this.getAttribute('data-tab');
            openTab(event, tabName);
        });
    }
});

