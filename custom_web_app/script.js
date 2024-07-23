document.addEventListener("DOMContentLoaded", function() {
    const crimeTypeSelect = document.getElementById("crime-type");
    const stateSelect = document.getElementById("state");
    const agencySelect = document.getElementById("agency");

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

        return data.filter(d => 
            d.crime_type === selectedCrimeType &&
            d.state_name === selectedState &&
            d.agency_name === selectedAgency
        );
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
            <h2>Year to Date ${selectedCrimeType} Offenses</h2>
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
        const endDatePrevYear = new Date(mostRecentYear - 1, mostRecentMonth - 1, 31); // End of most recent month of previous year
    
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
            <h2>Previous YTD ${selectedCrimeType} Offenses</h2>
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
            <p><strong>${percentChange.toFixed(2)}%</strong></p>
        `;
    }
    
    // Render the chart
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

        // Set up the scales
        const x = d3.scaleTime()
            .domain(d3.extent(filteredData, d => d.date))
            .range([0, width]);

        const y = d3.scaleLinear()
            .domain([0, d3.max(filteredData, d => d.count)])
            .nice()
            .range([height, 0]);

        // Add the X axis with only year labels
        svg.append("g")
            .attr("transform", `translate(0,${height})`)
            .call(d3.axisBottom(x).ticks(d3.timeYear).tickFormat(d3.timeFormat("%Y")).tickSizeOuter(0))
            .selectAll("path, line")
            .style("stroke", "#e0e0e0");

        // Style the X axis tick labels
        svg.selectAll(".x-axis text")
            .style("font-family", "'Roboto Condensed', Arial, sans-serif")
            .style("fill", "#00333a");

        // Add the Y axis with integer ticks only
        svg.append("g")
            .call(d3.axisLeft(y).ticks(d3.max(filteredData, d => d.count) < 10 ? d3.max(filteredData, d => d.count) : 10).tickFormat(d3.format("d")))
            .selectAll("path, line")
            .style("stroke", "#e0e0e0");

        // Style the Y axis tick labels
        svg.selectAll(".y-axis text")
            .style("font-family", "'Roboto Condensed', Arial, sans-serif")
            .style("fill", "#00333a");

        // Calculate dynamic font size for the Y-axis label
        const labelFontSize = Math.max(Math.min(height * 0.05, 16), 10);

        // Get the selected crime type
        const selectedCrimeType = crimeTypeSelect.options[crimeTypeSelect.selectedIndex].text;

        // Add the Y axis label
        svg.append("text")
            .attr("transform", "rotate(-90)")
            .attr("y", -margin.left + 25) // Adjusted margin for spacing
            .attr("x", -height / 2)
            .attr("dy", "1em")
            .style("text-anchor", "middle")
            .style("font-family", "'Roboto Condensed', Arial, sans-serif")
            .style("font-size", `${labelFontSize}px`)
            .attr("fill", "#00333a")
            .text(`Reported ${selectedCrimeType} Offenses`);

        // Style the tick labels correctly
        svg.selectAll(".tick text")
            .style("font-family", "'Roboto Condensed', Arial, sans-serif")
            .style("fill", "#00333a");

        // Calculate dynamic stroke-width and dot size
        const lineThickness = Math.max(Math.min(width * 0.005, 3.5), 2); // Example: scale between 2 and 3.5
        const dotSize = Math.max(Math.min(width * 0.005, 3.5), 2); // Example: scale between 3 and 5

        // Add the line
        const line = svg.append("path")
            .datum(filteredData)
            .attr("fill", "none")
            .attr("stroke", "#2d5ef9")
            .attr("stroke-width", lineThickness) // Thicker line
            .attr("d", d3.line()
                .curve(d3.curveCatmullRom.alpha(0.5)) // Smoother line
                .x(d => x(d.date))
                .y(d => y(d.count))
            );

        // Add tooltip
        const tooltip = d3.select("body").append("div")
            .attr("class", "tooltip")
            .style("opacity", 0)
            .style("font-family", "'Roboto Condensed', Arial, sans-serif");

        // Add dots at each data point
        const dots = svg.selectAll("circle")
            .data(filteredData)
            .enter().append("circle")
            .attr("cx", d => x(d.date))
            .attr("cy", d => y(d.count))
            .attr("r", dotSize) // Dynamic dot size
            .attr("fill", "#2d5ef9");

        dots.on("mouseover", function(event, d) {
            d3.select(this).attr("fill", "#f28106"); // Change dot color to orange on hover

            // Tooltip date display
            tooltip.transition()
                .duration(0) // Make tooltip appear immediately
                .style("opacity", .9);
            tooltip.html(`<strong>Agency:</strong> ${d.agency_name}<br><strong>Crime Type:</strong> ${d.crime_type}<br><strong>Offenses:</strong> ${d.count}<br><strong>Date:</strong> ${d3.timeFormat("%B %Y")(d.date)}`)
                .style("left", (event.pageX + 5) + "px")
                .style("top", (event.pageY - 28) + "px");
        })
        .on("mousemove", function(event, d) {
            tooltip.style("left", (event.pageX + 5) + "px")
                .style("top", (event.pageY - 28) + "px");
        })
        .on("mouseout", function(d) {
            d3.select(this).attr("fill", "#2d5ef9"); // Change dot color back to original
            tooltip.transition()
                .duration(500)
                .style("opacity", 0);
        });

        // Add source text in the bottom right corner
        const agencyFull = filteredData[0].agency_full;
        const stateUcrLink = filteredData[0].state_ucr_link;
        const sourceText = `${agencyFull}`;

        // Group the source text and link together for easier positioning
        const sourceGroup = svg.append("g")
            .attr("transform", `translate(${width}, ${height + margin.bottom - 10})`) // Increase the margin bottom value to add more padding
            .attr("text-anchor", "end");

        // Add text element for the source
        const sourceTextElement = sourceGroup.append("text")
            .style("font-family", "'Roboto Condensed', Arial, sans-serif")
            .style("font-size", "1.5vh") // Adjust as needed
            .style("fill", "#00333a");

        sourceTextElement.append("tspan")
            .text(sourceText);

        sourceTextElement.append("tspan")
            .attr("text-anchor", "start")
            .attr("dx", "0.2em") // Adjust spacing as needed
            .style("fill", "#2d5ef9") // Light blue color for the link
            .style("cursor", "pointer")
            .on("click", function() { window.open(stateUcrLink, "_blank"); })
            .text("source.");
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
});
