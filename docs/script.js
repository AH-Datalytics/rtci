document.addEventListener("DOMContentLoaded", function() {
    // Define elements for dropdowns and buttons
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
    let filtersChanged = false; // Flag to track filter changes

    // Function to close all dropdowns
    function closeAllDropdowns() {
        const dropdownMenus = document.querySelectorAll(".dropdown-menu");
        dropdownMenus.forEach(menu => {
            menu.classList.remove("show");
        });
    }

    // Function to toggle dropdowns
    function toggleDropdown(button, dropdown) {
        button.addEventListener('click', function(event) {
            event.stopPropagation();
            closeAllDropdowns(); // Close all dropdowns before toggling the current one
            dropdown.classList.toggle("show");
    
            // Close the download dropdown menu if it's open
            const downloadMenu = document.querySelector("#download-button .dropdown-menu");
            if (downloadMenu && downloadMenu.style.display === "block") {
                downloadMenu.style.display = "none";
            }
        });
    
        document.addEventListener('click', function() {
            closeAllDropdowns();
        });
    
        dropdown.addEventListener('click', function(event) {
            event.stopPropagation();
        });
    }
    
    // Helper functions (createDropdownOption, createSearchableDropdown, etc.)
    function createDropdownOption(value, text, dropdown, button, isMasterHeading = false) {
        const option = document.createElement("div");
        option.className = "dropdown-item";
        option.dataset.value = value;
        option.textContent = text;
    
        // Apply the special class for master headings
        if (isMasterHeading) {
            option.classList.add("master-heading");
        }
    
        if (button.dataset.value === value) {
            option.classList.add('selected');
        }
    
        option.addEventListener('click', function() {
            if (button.dataset.value !== value) {
                filtersChanged = true; // Set the flag to true when a filter is changed
            }
    
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

    // Define functions for handling data filtering and rendering
    function updateFilters(data) {
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
        const crimeTypes = severityOrder.filter(crimeType => data.some(d => d.crime_type === crimeType));
    
        let states = [...new Set(data.map(d => d.state_name))];
    
        // Remove "Nationwide" from the list if it exists
        const nationwideIndex = states.indexOf("Nationwide");
        if (nationwideIndex > -1) {
            states.splice(nationwideIndex, 1);  // Remove "Nationwide" from its original position
        }
    
        // Sort the remaining states alphabetically
        states.sort();
    
        // Add "Nationwide" back at the beginning of the list
        states.unshift("Nationwide");
    
        // Create the dropdown with the ordered list
        createSearchableDropdown(stateSelect, stateBtn, states);
    
        crimeTypeSelect.innerHTML = "";
        severityOrder.forEach((crimeType, index) => {
            const option = createDropdownOption(crimeType.value, crimeType.value, crimeTypeSelect, crimeTypeBtn, crimeType.isMaster);
            
            // Add a specific class for the second master heading "Property Crimes"
            if (crimeType.value === "Property Crimes") {
                option.classList.add("second-master-heading");
            }

            crimeTypeSelect.appendChild(option);
    });
    
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
            dataType: "mvs_12mo"
        };
    
        retrieveFilterValues(defaultFilters);
    }

    function updateAgencyFilter(data, selectedState) {
        let agencies = [...new Set(data.filter(d => d.state_name === selectedState).map(d => d.agency_name))];
    
        // Define the desired order for Nationwide agencies
        const nationwideAgencyOrder = [
            "Full Sample", 
            "Agencies of 1M+", 
            "Agencies of 250K - 1M", 
            "Agencies of 100K - 250K", 
            "Agencies of < 100K"
        ];
    
        // Define region names
        const regionNames = ["Midwest", "Northeast", "Other", "South", "West"];
    
        // Separate regional agencies from others
        let regionalAgencies = agencies.filter(agency => regionNames.includes(agency)).sort();
        agencies = agencies.filter(agency => !regionNames.includes(agency));
    
        // Sort agencies based on the custom order
        agencies.sort((a, b) => {
            const indexA = nationwideAgencyOrder.indexOf(a);
            const indexB = nationwideAgencyOrder.indexOf(b);
    
            if (indexA !== -1 && indexB !== -1) return indexA - indexB;
            if (indexA !== -1) return -1;
            if (indexB !== -1) return 1;
            return a.localeCompare(b);
        });
    
        // Clear previous options
        agencySelect.innerHTML = "";
    
        // Add search input field
        const searchInput = document.createElement("input");
        searchInput.type = "text";
        searchInput.placeholder = "Search...";
        searchInput.className = "dropdown-search";
        agencySelect.appendChild(searchInput);
    
        searchInput.addEventListener("input", function() {
            const filter = searchInput.value.toLowerCase();
            const items = agencySelect.querySelectorAll(".dropdown-item");
            items.forEach(item => {
                const text = item.textContent.toLowerCase();
                item.style.display = text.includes(filter) ? "" : "none";
            });
        });
    
        // Append agencies and add "Population Groups" sublabel after "Full Sample"
        if (selectedState === "Nationwide") {
            // Keep existing Nationwide logic
            agencies.forEach(agency => {
                const dropdownOption = createDropdownOption(agency, agency, agencySelect, agencyBtn);
                agencySelect.appendChild(dropdownOption);
        
                if (agency === "Full Sample") {
                    const populationGroupLabel = document.createElement("div");
                    populationGroupLabel.textContent = "Population Groups";
                    populationGroupLabel.classList.add("master-heading");
                    populationGroupLabel.style.pointerEvents = "none";
                    agencySelect.appendChild(populationGroupLabel);
                }
            });
        } else {
            // For state-specific (not Nationwide)
            // Handle "Full Sample" first if present
            const fullSampleIndex = agencies.indexOf("Full Sample");
            if (fullSampleIndex !== -1) {
                const fullSampleOption = createDropdownOption("Full Sample", "Full Sample", agencySelect, agencyBtn);
                agencySelect.appendChild(fullSampleOption);
                agencies.splice(fullSampleIndex, 1); // Remove "Full Sample" from agencies list
            }
        
            // Separate cities and counties
            const cities = agencies.filter(a => !a.includes("County") && !a.includes("Parish")).sort((a, b) => a.localeCompare(b));
            const counties = agencies.filter(a => a.includes("County") || a.includes("Parish")).sort((a, b) => a.localeCompare(b));
        
            // Add "Cities" subheader if there are cities
            if (cities.length > 0) {
                const citiesLabel = document.createElement("div");
                citiesLabel.textContent = "Cities";
                citiesLabel.classList.add("master-heading");
                citiesLabel.style.pointerEvents = "none";
                agencySelect.appendChild(citiesLabel);
        
                cities.forEach(city => {
                    const cityOption = createDropdownOption(city, city, agencySelect, agencyBtn);
                    agencySelect.appendChild(cityOption);
                });
            }
        
            // Add "Counties" subheader if there are counties
            if (counties.length > 0) {
                const countiesLabel = document.createElement("div");
                countiesLabel.textContent = "Counties";
                countiesLabel.classList.add("master-heading");
                countiesLabel.style.pointerEvents = "none";
                agencySelect.appendChild(countiesLabel);
        
                counties.forEach(county => {
                    const countyOption = createDropdownOption(county, county, agencySelect, agencyBtn);
                    agencySelect.appendChild(countyOption);
                });
            }
        }
        
    
        // If Nationwide, add "Regions" heading and append regional agencies
        if (selectedState === "Nationwide" && regionalAgencies.length > 0) {
            const regionsLabel = document.createElement("div");
            regionsLabel.textContent = "Regions";
            regionsLabel.classList.add("master-heading");
            regionsLabel.style.pointerEvents = "none"; // Prevent interactions
            agencySelect.appendChild(regionsLabel);
    
            regionalAgencies.forEach(region => {
                const dropdownOption = createDropdownOption(region, region, agencySelect, agencyBtn);
                agencySelect.appendChild(dropdownOption);
            });
        }
    
        const savedFilters = JSON.parse(sessionStorage.getItem('rtciFilters')) || {};
        const savedAgency = savedFilters.agency;

        // Ensure that the saved agency selection works for both population groups and regions
        if ([...agencies, ...regionalAgencies].includes(savedAgency)) {
            agencyBtn.textContent = savedAgency;
            agencyBtn.dataset.value = savedAgency;
        } else if (agencySelect.querySelector('[data-value="Full Sample"]')) {  // ✅ If Full Sample exists, select it
            agencyBtn.textContent = "Full Sample";
            agencyBtn.dataset.value = "Full Sample";
        } else if (agencies.length > 0) {  // Otherwise fallback to first agency
            agencyBtn.textContent = agencies[0];
            agencyBtn.dataset.value = agencies[0];
        }


        // Find the matching dropdown option and mark it as selected
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
    
        // Log the ytdData to inspect for invalid entries
        console.log('YTD Data:', ytdData);
    
        // Check for missing or invalid data
        const expectedMonths = new Set(Array.from({ length: mostRecentMonth }, (_, i) => i + 1));
        const availableMonths = new Set();
    
        ytdData.forEach(d => {
            if (d.count !== null && d.count !== undefined && !isNaN(d.count)) {
                availableMonths.add(d.date.getMonth() + 1);
            }
        });
    
        const missingMonths = [...expectedMonths].filter(month => !availableMonths.has(month));
    
        console.log('Expected Months:', expectedMonths);
        console.log('Available Months:', availableMonths);
        console.log('Missing Months:', missingMonths);
    
        // If any month is missing or has invalid data, display "Missing data"
        if (missingMonths.length > 0) {
            kpiBox1.innerHTML = `
                <h2>Year to Date ${crimeTypeBtn.textContent}</h2>
                <p>Missing data.</p>
            `;
            return;
        }
    
        const ytdSum = d3.sum(ytdData, d => d.count);
        const formattedYtdSum = d3.format(",")(ytdSum);
    
        if (filteredData.length === 0 || filteredData.every(d => isNaN(d.value))) {
            kpiBox1.innerHTML = `
                <h2>Year to Date ${crimeTypeBtn.textContent}</h2>
                <p>Missing data.</p>
            `;
            return;
        }
    
        kpiBox1.innerHTML = `
            <h2>Year to Date ${crimeTypeBtn.textContent}</h2>
            <p>Jan - ${d3.timeFormat("%b")(mostRecentDate)} ${mostRecentYear}</p>
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
    
        // Log the ytdDataPrevYear to inspect for invalid entries
        console.log('Previous YTD Data:', ytdDataPrevYear);
    
        // Check for missing or invalid data
        const expectedMonthsPrevYear = new Set(Array.from({ length: mostRecentMonth }, (_, i) => i + 1));
        const availableMonthsPrevYear = new Set();
    
        ytdDataPrevYear.forEach(d => {
            if (d.count !== null && d.count !== undefined && !isNaN(d.count)) {
                availableMonthsPrevYear.add(d.date.getMonth() + 1);
            }
        });
    
        const missingMonthsPrevYear = [...expectedMonthsPrevYear].filter(month => !availableMonthsPrevYear.has(month));
    
        console.log('Expected Months Prev Year:', expectedMonthsPrevYear);
        console.log('Available Months Prev Year:', availableMonthsPrevYear);
        console.log('Missing Months Prev Year:', missingMonthsPrevYear);
    
        // If any month is missing or has invalid data, display "Missing data"
        if (missingMonthsPrevYear.length > 0) {
            kpiBox2.innerHTML = `
                <h2>Previous YTD ${crimeTypeBtn.textContent}</h2>
                <p>Missing data.</p>
            `;
            return;
        }
    
        const ytdSumPrevYear = d3.sum(ytdDataPrevYear, d => d.count);
        const formattedYtdSumPrevYear = d3.format(",")(ytdSumPrevYear);
    
        if (ytdDataPrevYear.length === 0 || ytdDataPrevYear.every(d => isNaN(d.value))) {
            kpiBox2.innerHTML = `
                <h2>Previous YTD ${crimeTypeBtn.textContent}</h2>
                <p>Missing data.</p>
            `;
            return;
        }
    
        kpiBox2.innerHTML = `
            <h2>Previous YTD ${crimeTypeBtn.textContent}</h2>
            <p>Jan - ${d3.timeFormat("%b")(endDatePrevYear)} ${mostRecentYear - 1}</p>
            <p><strong>${formattedYtdSumPrevYear}</strong></p>
        `;

    }
    

    function updateKPIBox3() {
        const kpiBox1 = document.getElementById("kpi-box1");
        const kpiBox2 = document.getElementById("kpi-box2");
        const kpiBox3 = document.getElementById("kpi-box3");
    
        // Check if either KPI Box 1 or KPI Box 2 contains "Missing data"
        if (kpiBox1.textContent.includes("Missing data") || kpiBox2.textContent.includes("Missing data")) {
            kpiBox3.innerHTML = `
                <h2>% Change in ${crimeTypeBtn.textContent} YTD</h2>
                <p>Missing data.</p>
            `;
            return;
        }
    
        // Extract the numeric value from the <strong> elements
        const ytdSumCurrentYear = parseFloat(kpiBox1.querySelector('strong').textContent.replace(/,/g, ''));
        const ytdSumPrevYear = parseFloat(kpiBox2.querySelector('strong').textContent.replace(/,/g, ''));
    
        // Debugging: Log extracted values to ensure correctness
        console.log('YTD Sum Current Year:', ytdSumCurrentYear);
        console.log('YTD Sum Previous Year:', ytdSumPrevYear);
    
        // Verify if extracted values are numbers
        if (isNaN(ytdSumCurrentYear) || isNaN(ytdSumPrevYear)) {
            kpiBox3.innerHTML = `
                <h2>% Change in ${crimeTypeBtn.textContent} YTD</h2>
                <p>Error in data extraction.</p>
            `;
            return;
        }
    
        // Calculate the percentage change with a check for division by zero
        let percentChange;
        if (ytdSumPrevYear === 0 && ytdSumCurrentYear > 0) {
            percentChange = "Undefined."; // Handle division by zero case
        } else {
            percentChange = ((ytdSumCurrentYear - ytdSumPrevYear) / ytdSumPrevYear) * 100;
        }
    
        console.log('Calculated Percent Change:', percentChange);
    
        let formattedPercentChange;
        if (isNaN(percentChange)) {
            formattedPercentChange = "Undefined.";
        } else if (percentChange > 0) {
            formattedPercentChange = `+${percentChange.toFixed(1)}%`; // Add plus sign for positive change
        } else {
            formattedPercentChange = `${percentChange.toFixed(1)}%`;
        }
    
        // Extract and format the date ranges from KPI Box 1 and KPI Box 2
        let dateRangeCurrentYear = kpiBox1.querySelector('p:nth-of-type(1)').textContent;
        let dateRangePrevYear = kpiBox2.querySelector('p:nth-of-type(1)').textContent;
    
        // Replace "through" with "-"
        dateRangeCurrentYear = dateRangeCurrentYear.replace("through", "-");
        dateRangePrevYear = dateRangePrevYear.replace("through", "-");
    
        // Update KPI Box 3 with the calculated percent change and formatted date range
        kpiBox3.innerHTML = `
            <h2>% Change in ${crimeTypeBtn.textContent} YTD</h2>
            <p><strong>${formattedPercentChange}</strong></p>
        `;
    }


    
    
    
    
    function abbreviateNumber(value) {
        if (value >= 1e6) {
            return (value / 1e6).toFixed(1) + "M";
        }
        if (value >= 1e4) {
            return (value / 1e3).toFixed(0) + "K";
        }
        return d3.format(",")(value);
    }

    function abbreviateNumberForCaption(value) {
        if (value >= 1e6) {
            return (value / 1e6).toFixed(2) + "M";
        }
        if (value >= 1e4) {
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
    
        // Ensure the download button is functional
        ensureDownloadButtonIsFunctional();

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

        // Append the logo image to the SVG
        svg.append("image")
            .attr("xlink:href", "images/rtci_full_logo.png")
            .attr("x", -margin.left + 80)
            .attr("y", -margin.top - 3)
            .attr("width", 60)
            .attr("height", 60)
            .attr("opacity", 0.5);

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
            .tickFormat(abbreviateNumber);

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
        const chosenDataType = dataTypeBtn.textContent;


        function getTextWidth(text, font) {
            const canvas = document.createElement('canvas');
            const context = canvas.getContext('2d');
            context.font = font;
            const metrics = context.measureText(text);
            return metrics.width;
        }

        const maxYLabelWidth = Math.max(...yAxisGroup.selectAll(".tick text").nodes().map(node => node.getBBox().width));

        const yAxisLabel = svg.append("text")
            .attr("transform", "rotate(-90)")
            .attr("y", -margin.left - maxYLabelWidth + 35)
            .attr("x", -height / 2)
            .attr("dy", "1em")
            .style("text-anchor", "middle")
            .style("font-family", "'Roboto Condensed', Arial, sans-serif")
            .style("font-size", `${labelFontSize}px`)
            .attr("fill", "#00333a");

            // Determine the label based on the selected data type
            let dataTypeLabel;
            if (chosenDataType === "Monthly Totals") {
                dataTypeLabel = "Per Month";
            } else if (chosenDataType === "12 Month Rolling Sum") {
                dataTypeLabel = "Rolling Over 12 Months";
            }

            // Append the crime type 
            yAxisLabel.append("tspan")
                .text(`Reported ${selectedCrimeType} `);

            // Append the data type
            yAxisLabel.append("tspan")
                .text(`${dataTypeLabel}`);


        svg.selectAll(".tick text")
            .style("font-family", "'Roboto Condensed', Arial, sans-serif")
            .style("fill", "#00333a");

        const lineThickness = Math.max(Math.min(width * 0.005, 2.5), 1);
        const dotSize = Math.max(Math.min(width * 0.005, 2.5), 1);

        // Define the line function
        const line = d3.line()
            .curve(d3.curveCatmullRom.alpha(0.5))
            .x(d => x(d.date))
            .y(d => y(d.value));

        // Filtered data to remove any NA values and create segments
        const filteredSegments = [];
        let currentSegment = [];

        filteredData.forEach((d, i) => {
            if (!isNaN(d.value)) {
                currentSegment.push(d);
            } else if (currentSegment.length > 0) {
                filteredSegments.push(currentSegment);
                currentSegment = [];
            }
        });

        if (currentSegment.length > 0) {
            filteredSegments.push(currentSegment);
        }

        // Append multiple paths to represent the line with breaks for NA values
        svg.selectAll(".line-segment")
            .data(filteredSegments)
            .enter().append("path")
            .attr("class", "line-segment")
            .attr("fill", "none")
            .attr("stroke", "#2d5ef9")
            .attr("stroke-width", lineThickness)
            .attr("d", line)
            .each(function(d, i) {
                if (filtersChanged) {
                    const totalLength = this.getTotalLength();
                    d3.select(this)
                        .attr("stroke-dasharray", totalLength + " " + totalLength)
                        .attr("stroke-dashoffset", totalLength)
                        .transition()
                        .delay(i * 1500) // Stagger the animations based on the segment index
                        .duration(1000)
                        .ease(d3.easeLinear)
                        .attr("stroke-dashoffset", 0);
                }
            });

        // Tooltip logic
        const tooltip = d3.select("body").append("div")
            .attr("class", "tooltip")
            .style("opacity", 0)
            .style("font-family", "'Roboto Condensed', Arial, sans-serif");

        // Conditional rendering based on selected data type
        const selectedDataType = dataTypeBtn.dataset.value;

        if (selectedDataType === "count") {
            const dots = svg.selectAll("circle")
                .data(filteredData.filter(d => !isNaN(d.value)))
                .enter().append("circle")
                .attr("cx", d => x(d.date))
                .attr("cy", d => y(d.value))
                .attr("r", dotSize)
                .attr("fill", "#2d5ef9")
                .style("cursor", "pointer");

                if (filtersChanged) {
                    const totalSegments = filteredSegments.length;
                    const totalAnimationTime = ((totalSegments - 1) * 1500) + 1000;
                
                    dots.attr("r", 0)
                        .transition()
                        .delay(totalAnimationTime) // Delay until after all line segments are drawn
                        .duration(100)
                        .ease(d3.easeLinear)
                        .attr("r", dotSize);
                }
                

            dots.on("mouseover", function(event, d) {
                    d3.select(this).attr("fill", "#f28106");

                    tooltip.transition()
                        .duration(0)
                        .style("opacity", .9);
                    tooltip.html(`<strong>Agency:</strong> ${d.agency_abbr}<br><strong>Crime Type:</strong> ${d.crime_type}<br><strong>Total:</strong> ${d3.format(",")(d.value)}<br><strong>Date:</strong> ${d3.timeFormat("%B %Y")(d.date)}`)
                        .style("left", (event.pageX + 5) + "px")
                        .style("top", (event.pageY - 28) + "px");
                })
                .on("mousemove", function(event) {
                    tooltip.style("left", (event.pageX + 5) + "px")
                        .style("top", (event.pageY - 28) + "px");
                })
                .on("mouseout", function() {
                    d3.select(this).attr("fill", "#2d5ef9");
                    tooltip.transition()
                        .duration(500)
                        .style("opacity", 0);
                });
        } else {
            svg.selectAll(".line-segment")
                .style("cursor", "pointer")
                .on("mousemove", function(event, d) {
                    const [mouseX] = d3.pointer(event);
                    const xDate = x.invert(mouseX);
                    const closestData = filteredData.reduce((a, b) => {
                        return Math.abs(b.date - xDate) < Math.abs(a.date - xDate) ? b : a;
                    });

                    tooltip.transition()
                        .duration(0)
                        .style("opacity", .9);
                    tooltip.html(`<strong>Agency:</strong> ${closestData.agency_abbr}<br><strong>Crime Type:</strong> ${closestData.crime_type}<br><strong>12 Month Sum:</strong> ${d3.format(",")(closestData.value)}<br><strong>Through:</strong> ${d3.timeFormat("%B %Y")(closestData.date)}`)
                        .style("left", (event.pageX + 5) + "px")
                        .style("top", (event.pageY - 28) + "px");
                })
                .on("mouseout", function() {
                    tooltip.transition()
                        .duration(500)
                        .style("opacity", 0);
                });
        }

        filtersChanged = false;

        appendSourceAndCaption(svg, width, height, filteredData, margin);
    }

    function appendSourceAndCaption(svg, width, height, filteredData, margin) {
        const agencyFull = filteredData[0].agency_full;
        const stateUcrLink = filteredData[0].state_ucr_link;
        let sourceText, linkText;
    
        // Function to handle the apostrophe logic
        function getApostropheText(name) {
            if (name.endsWith('s')) {
                return `${name}'`;  // Use single apostrophe if name ends with 's'
            } else {
                return `${name}'s`; // Otherwise, use 's for names not ending in 's'
            }
        }
    
        // Check if state is "Nationwide" or agency is "Full Sample"
        if (filteredData[0].state_name === "Nationwide" || filteredData[0].agency_name === "Full Sample") {
            sourceText = `${getApostropheText(agencyFull)} composite`;  // Apostrophe logic for "composite agencies"
            linkText = "agencies";  // Use "agencies" as the hyperlink text
        } else {
            // Default text when it's not "Nationwide" or "Full Sample"
            sourceText = `${getApostropheText(agencyFull)} primary`;  // Apostrophe logic for "primary source"
            linkText = "source";  // Use "source" as the hyperlink text
        }
    
        const sourceGroup = svg.append("g")
            .attr("transform", `translate(${width}, ${height + margin.bottom - 10})`)
            .attr("text-anchor", "end");
    
        const sourceTextElement = sourceGroup.append("text")
            .attr("class", "source-link")
            .style("font-family", "'Roboto Condensed', Arial, sans-serif")
            .style("fill", "#00333a");
    
        // Append the first part of the source text
        sourceTextElement.append("tspan")
            .text(sourceText)  // No space added here
            .style("cursor", "text");
    
        // Append the hyperlinked text (either "agencies" or "source")
        sourceTextElement.append("tspan")
            .attr("text-anchor", "start")
            .attr("dx", "0.2em")  // Adds a slight space between the two words
            .attr("class", "source-link")
            .style("cursor", "pointer")
            .on("click", function() { window.open(stateUcrLink, "_blank"); })
            .text(linkText + ".");  // Append the period here
    
        const population = abbreviateNumberForCaption(filteredData[0].population);
        const agencyCount = filteredData[0].number_of_agencies || "N/A";
    
        const captionGroup = svg.append("g")
            .attr("transform", `translate(0, ${height + margin.bottom - 10})`)
            .attr("text-anchor", "start")
            .attr("class", "caption-group");
    
        const captionTextElement = captionGroup.append("text")
            .style("font-family", "'Roboto Condensed', Arial, sans-serif")
            .style("fill", "#00333a");
    
        captionTextElement.append("tspan")
            .text("Population Covered: ")
            .attr("x", 0);
    
        captionTextElement.append("tspan")
            .text(population)
            .attr("dx", "0em")
            .style("fill", "#f28106")
            .style("font-weight", "bold");
    
        captionTextElement.append("tspan")
            .text("Number of Agencies: ")
            .attr("dx", "1.5em");
    
        captionTextElement.append("tspan")
            .text(agencyCount)
            .attr("dx", "0em")
            .style("fill", "#f28106")
            .style("font-weight", "bold");
    
        // Adjust caption for mobile
        function adjustCaptionForMobile() {
            const isMobile = window.innerWidth <= 600; // Adjust for screens 600px or less
    
            if (isMobile) {
                captionGroup.attr("transform", `translate(-60, ${height + margin.bottom - 10})`);
                sourceGroup.attr("transform", `translate(${width + 20}, ${height + margin.bottom - 10})`);
            } else {
                captionGroup.attr("transform", `translate(0, ${height + margin.bottom - 10})`);
                sourceGroup.attr("transform", `translate(${width}, ${height + margin.bottom - 10})`);
            }
        }
    
        adjustCaptionForMobile();
        window.addEventListener('resize', adjustCaptionForMobile);
    }
    
    
    
    

    function downloadFilteredData(filteredData) {
        const selectedDataType = dataTypeBtn.dataset.value;
        const headers = ["agency_name", "state_name", "date", "crime_type", "number_of_agencies", "population_covered_fbi"];
    
        const dataColumn = selectedDataType === "count" ? "monthly_total" : "12mo_rolling_sum";
        headers.push(dataColumn, "Last Updated"); // Add "Last Updated" at the end
    
        const csvRows = [headers.join(",")];
    
        const hasAgencyCount = filteredData.length > 0 && filteredData[0].hasOwnProperty("number_of_agencies");
    
        filteredData.forEach(d => {
            const row = [
                d.agency_name,
                d.state_name,
                d3.timeFormat("%B %Y")(d.date),
                d.crime_type,
                hasAgencyCount ? d.number_of_agencies : "N/A",
                d.population || "N/A",  // Adding population to the row
                d.value,
                d["Last Updated"] // Move "Last Updated" to the end
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
        
        filtersChanged = true; // Ensure animation on first render
        renderChart();
    }).catch(function(error) {
        console.error("Error loading the CSV file:", error);
    });

    window.addEventListener('resize', renderChart);

    toggleDropdown(crimeTypeBtn, crimeTypeSelect);
    toggleDropdown(stateBtn, stateSelect);
    toggleDropdown(agencyBtn, agencySelect);
    toggleDropdown(dataTypeBtn, dataTypeDropdown);

    // Create the dropdown menu for the download button
    const downloadMenu = document.createElement("div");
    downloadMenu.className = "dropdown-menu";
    downloadMenu.style.position = "absolute";
    downloadMenu.style.top = "100%";
    downloadMenu.style.right = "0";
    downloadMenu.style.minWidth = "150px"; // Adjust as needed
    downloadMenu.style.display = "none";
    downloadMenu.style.zIndex = "1000";

    const downloadDataOption = document.createElement("div");
    downloadDataOption.className = "dropdown-item";
    downloadDataOption.textContent = "Filtered Data";
    downloadDataOption.addEventListener("click", function() {
        const filteredData = filterData(allData);
        downloadFilteredData(filteredData);
        setTimeout(() => {
            downloadMenu.style.display = "none"; // Close the dropdown after click
        }, 100); // Adding a slight delay
    });

    const downloadImageOption = document.createElement("div");
    downloadImageOption.className = "dropdown-item";
    downloadImageOption.textContent = "Graph";
    downloadImageOption.addEventListener("click", function() {
        downloadGraphAsImage();
        setTimeout(() => {
            downloadMenu.style.display = "none"; // Close the dropdown after click
        }, 100); // Adding a slight delay
    });

    downloadMenu.appendChild(downloadDataOption);
    downloadMenu.appendChild(downloadImageOption);
    downloadButton.appendChild(downloadMenu);

    // Toggle the dropdown menu on download button click
    downloadButton.addEventListener("click", function(event) {
        event.stopPropagation();
        const isMenuVisible = downloadMenu.style.display === "block";
        closeAllDropdowns();
        downloadMenu.style.display = isMenuVisible ? "none" : "block";
    });

    // Global event listener to close the dropdown menu when clicking outside
    document.addEventListener("click", function(event) {
        // Check if the click was outside the download button or the dropdown menu
        if (!downloadButton.contains(event.target) && !downloadMenu.contains(event.target)) {
            downloadMenu.style.display = "none"; // Close the dropdown menu
        }
    });

    // Function to ensure the button doesn't get re-added
    function ensureDownloadButtonIsFunctional() {
        const existingButton = document.getElementById("download-button");
        if (!existingButton) {
            const container = document.querySelector("#line-graph-container");
            container.appendChild(downloadButton);
        }
    }

    dataTypeDropdown.addEventListener('click', event => {
        const selectedItem = event.target.closest('.dropdown-item');
        if (selectedItem && dataTypeBtn.dataset.value !== selectedItem.dataset.value) {
            filtersChanged = true; // Set the flag to true when data type is changed
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


function downloadGraphAsImage() {
    const graphContainer = document.getElementById("line-graph-container");
    const downloadButton = document.getElementById("download-button");

    // Calculate the dynamic margins based on the graph's dimensions and positioning
    const graphBoundingBox = graphContainer.getBoundingClientRect();
    const svgElement = graphContainer.querySelector("svg");
    const svgBoundingBox = svgElement.getBoundingClientRect();

    // Calculate the margin differences
    const marginLeft = svgBoundingBox.left - graphBoundingBox.left + 80;  // Adjust if needed based on your graph
    const marginTop = svgBoundingBox.top - graphBoundingBox.top + 12;     // Adjust if needed based on your graph

    // Create an image element for the logo
    const logoImage = document.createElement("img");
    logoImage.src = "images/rtci_full_logo.png"; // Path to your logo
    logoImage.style.position = "absolute";
    logoImage.style.top = `${marginTop}px`; // Position based on dynamic margin calculation
    logoImage.style.left = `${marginLeft}px`; // Position based on dynamic margin calculation
    logoImage.style.width = "90px"; // Adjust size relative to container width
    logoImage.style.height = "auto"; // Maintain aspect ratio
    logoImage.style.opacity = "0.5"; // Opacity as in your SVG

    // Append the logo image to the graph container temporarily
    graphContainer.appendChild(logoImage);

    // Temporarily hide the download button
    downloadButton.style.display = "none";

    // Wait for fonts to be ready before capturing
    document.fonts.ready.then(function() {
        html2canvas(graphContainer, {
            useCORS: true,
            backgroundColor: "#ffffff", // Ensure white background
            logging: true, // Enable logging for debugging purposes
            scale: 2 // Increase scale for higher resolution
        }).then(canvas => {
            // Convert canvas to PNG format
            const imgURI = canvas.toDataURL("image/png");

            const link = document.createElement("a");
            link.setAttribute("href", imgURI);
            link.setAttribute("download", "graph_screenshot.png");
            link.click();

            // Restore the download button and remove the logo image after the image is captured
            downloadButton.style.display = "";
            graphContainer.removeChild(logoImage);
        }).catch(error => {
            console.error("Error capturing the graph as a screenshot:", error);
            // Restore the download button and remove the logo image in case of an error
            downloadButton.style.display = "";
            graphContainer.removeChild(logoImage);
        });
    });
}
