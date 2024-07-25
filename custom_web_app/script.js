document.addEventListener("DOMContentLoaded", function() {
    const crimeTypeSelect = document.getElementById("crime-type");
    const stateSelect = document.getElementById("state");
    const agencySelect = document.getElementById("agency");
    const downloadButton = document.getElementById("download-button");

    let allData = [];

    // Define a date parser
    const parseDate = d3.timeParse("%Y-%m-%d");

    function updateFilters(data) {
        const crimeTypes = [...new Set(data.map(d => d.crime_type))];
        const states = [...new Set(data.map(d => d.state_name))];

        // Clear previous options
        crimeTypeSelect.innerHTML = "";
        stateSelect.innerHTML = "";
        agencySelect.innerHTML = "";

        crimeTypes.forEach(crimeType => {
            const option = document.createElement("option");
            option.value = crimeType;
            option.text = crimeType;
            crimeTypeSelect.appendChild(option);
        });

        states.forEach(state => {
            const option = document.createElement("option");
            option.value = state;
            option.text = state;
            stateSelect.appendChild(option);
        });

        // Set default values
        crimeTypeSelect.value = crimeTypes[0];
        stateSelect.value = states[0];

        updateAgencyFilter(data, states[0]);
    }

    function updateAgencyFilter(data, selectedState) {
        const agencies = [...new Set(data.filter(d => d.state_name === selectedState).map(d => d.agency_name))];
        
        // Clear previous options
        agencySelect.innerHTML = "";

        agencies.forEach(agency => {
            const option = document.createElement("option");
            option.value = agency;
            option.text = agency;
            agencySelect.appendChild(option);
        });

        // Set default value
        agencySelect.value = agencies[0];
    }

    function filterData(data) {
        const selectedCrimeType = crimeTypeSelect.value;
        const selectedState = stateSelect.value;
        const selectedAgency = agencySelect.value;
        const selectedDataType = document.getElementById("data-type").value;


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

        // Get the selected crime type
        const selectedCrimeType = crimeTypeSelect.options[crimeTypeSelect.selectedIndex].text;

        // Update KPI box 1 content
        kpiBox1.innerHTML = `
            <h2>Year to Date ${selectedCrimeType}</h2>
            <p>Jan '${mostRecentYear.toString().slice(-2)} through ${d3.timeFormat("%B")(mostRecentDate)} '${mostRecentYear.toString().slice(-2)}</p>
            <p><strong>${ytdSum}</strong></p>
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
    
        // Get the selected crime type
        const selectedCrimeType = crimeTypeSelect.options[crimeTypeSelect.selectedIndex].text;
    
        // Update KPI box 2 content
        kpiBox2.innerHTML = `
            <h2>Previous YTD ${selectedCrimeType}</h2>
            <p>Jan '${(mostRecentYear - 1).toString().slice(-2)} through ${d3.timeFormat("%B")(new Date(mostRecentYear - 1, mostRecentMonth - 1, 1))} '${(mostRecentYear - 1).toString().slice(-2)}</p>
            <p><strong>${ytdSumPrevYear}</strong></p>
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
        const selectedCrimeType = crimeTypeSelect.options[crimeTypeSelect.selectedIndex].text;
    
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
        
        svg.append("g")
            .attr("transform", `translate(0,${height})`)
            .call(d3.axisBottom(x).ticks(d3.timeYear).tickFormat(d3.timeFormat("%Y")).tickSizeOuter(0))
            .selectAll("path, line")
            .style("stroke", "#e0e0e0");
        
        svg.selectAll(".x-axis text")
            .style("font-family", "'Roboto Condensed', Arial, sans-serif")
            .style("fill", "#00333a");
        
        svg.append("g")
            .call(d3.axisLeft(y).ticks(Math.min(d3.max(filteredData, d => d.value), 10)).tickFormat(d3.format("d"))) // Ensure proper number of ticks
            .selectAll("path, line")
            .style("stroke", "#e0e0e0");
        
        svg.selectAll(".y-axis text")
            .style("font-family", "'Roboto Condensed', Arial, sans-serif")
            .style("fill", "#00333a");
        
    
        const labelFontSize = Math.max(Math.min(height * 0.05, 16), 10);
        const selectedCrimeType = crimeTypeSelect.options[crimeTypeSelect.selectedIndex].text;
    
        svg.append("text")
            .attr("transform", "rotate(-90)")
            .attr("y", -margin.left + 25)
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
    
        const lineThickness = Math.max(Math.min(width * 0.005, 3.5), 2);
        const dotSize = Math.max(Math.min(width * 0.005, 3.5), 2);
    
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
    
        const tooltip = d3.select("body").append("div")
            .attr("class", "tooltip")
            .style("opacity", 0)
            .style("font-family", "'Roboto Condensed', Arial, sans-serif");
    
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
            tooltip.html(`<strong>Agency:</strong> ${d.agency_name}<br><strong>Crime Type:</strong> ${d.crime_type}<br><strong>Total:</strong> ${d.value}<br><strong>Date:</strong> ${d3.timeFormat("%B %Y")(d.date)}`)
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
    
        const agencyFull = filteredData[0].agency_full;
        const stateUcrLink = filteredData[0].state_ucr_link;
        const sourceText = `${agencyFull}`;
    
        const sourceGroup = svg.append("g")
            .attr("transform", `translate(${width}, ${height + margin.bottom - 10})`)
            .attr("text-anchor", "end");
    
        const sourceTextElement = sourceGroup.append("text")
            .attr("class", "source-link")
            .style("font-family", "'Roboto Condensed', Arial, sans-serif")
            .style("font-size", "1.5vh")
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
    
        // Add new caption group for population and number of agencies
        const population = filteredData[0].population;
        const agencyCount = filteredData[0].agency_count || "N/A";
    
        const captionGroup = svg.append("g")
            .attr("transform", `translate(0, ${height + margin.bottom - 10})`) // Adjust vertical position
            .attr("text-anchor", "start");
    
        const captionTextElement = captionGroup.append("text")
            .style("font-family", "'Roboto Condensed', Arial, sans-serif")
            .style("font-size", "1.5vh")
            .style("fill", "#00333a");
    
        captionTextElement.append("tspan")
            .text("Population* Covered: ")
            .attr("x", 0);
    
        captionTextElement.append("tspan")
            .text(population)
            .attr("dx", "0.2em")
            .style("fill", "#f28106");
    
        captionTextElement.append("tspan")
            .text("Number of Agencies: ")
            .attr("dx", "3em"); // Increase spacing
    
        captionTextElement.append("tspan")
            .text(agencyCount)
            .attr("dx", "0.2em")
            .style("fill", "#f28106");
    }
    
    
    
    
    

    function downloadFilteredData(filteredData) {
        const selectedDataType = document.getElementById("data-type").value;
        const headers = ["agency_name", "state_name", "date", "crime_type", "number_of_agencies"];
        
        // Rename the 'value' column based on the selected data type
        const dataColumn = selectedDataType === "count" ? "count" : "12mo_rolling_sum";
        headers.push(dataColumn);
    
        const csvRows = [headers.join(",")];
    
        // Check if the number_of_agencies column exists in the data
        const hasAgencyCount = filteredData.length > 0 && filteredData[0].hasOwnProperty("number_of_agencies");
    
        // Add data rows
        filteredData.forEach(d => {
            const row = [
                d.agency_name,
                d.state_name,
                d3.timeFormat("%Y-%m-%d")(d.date),
                d.crime_type,
                hasAgencyCount ? d.number_of_agencies : "N/A", // Use the number_of_agencies column if it exists, otherwise "N/A"
                d.value
            ];
            csvRows.push(row.join(","));
        });
    
        // Create CSV content
        const csvContent = "data:text/csv;charset=utf-8," + csvRows.join("\n");
    
        // Create a downloadable link
        const encodedUri = encodeURI(csvContent);
        const link = document.createElement("a");
        link.setAttribute("href", encodedUri);
        link.setAttribute("download", "filtered_data.csv");
    
        // Append to the document and trigger the download
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }
    
    
    

    // Load data and initialize filters and chart
    d3.csv("data/viz_data.csv").then(function(data) {
        data.forEach(d => {
            d.date = parseDate(d.date); // Use d3.timeParse to parse dates
            d.count = +d.count;
        });

        allData = data;
        updateFilters(allData);
        renderChart();
    }).catch(function(error) {
        console.error("Error loading the CSV file:", error);
    });

    // Re-render on window resize
    window.addEventListener('resize', renderChart);

    // Update chart when filters change
    crimeTypeSelect.addEventListener('change', renderChart);
    stateSelect.addEventListener('change', function() {
        updateAgencyFilter(allData, stateSelect.value);
        renderChart();
    });
    agencySelect.addEventListener('change', renderChart);

    // Add event listener to download button
    downloadButton.addEventListener("click", function() {
        const filteredData = filterData(allData);
        downloadFilteredData(filteredData);
    });

    const dataTypeSelect = document.getElementById("data-type");
    dataTypeSelect.addEventListener('change', renderChart);

});
