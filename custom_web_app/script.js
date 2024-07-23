document.addEventListener("DOMContentLoaded", function() {
    const crimeTypeSelect = document.getElementById("crime-type");
    const stateSelect = document.getElementById("state");
    const agencySelect = document.getElementById("agency");

    let allData = [];

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

    function renderChart() {
        const filteredData = filterData(allData);

        // Remove any existing SVG
        d3.select("#line-graph-container svg").remove();

        // Set up the SVG container dimensions
        const margin = { top: 20, right: 20, bottom: 30, left: 70 };
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

        // Add the Y axis with integer ticks only
        svg.append("g")
            .call(d3.axisLeft(y).ticks(d3.max(filteredData, d => d.count) < 10 ? d3.max(filteredData, d => d.count) : 10).tickFormat(d3.format("d")))
            .selectAll("path, line")
            .style("stroke", "#e0e0e0");

        // Calculate dynamic font size for the Y-axis label
        const labelFontSize = Math.max(Math.min(height * 0.05, 16), 10);

        // Add the Y axis label
        svg.append("text")
            .attr("transform", "rotate(-90)")
            .attr("y", -margin.left + 20) // Adjusted margin for spacing
            .attr("x", -height / 2)
            .attr("dy", "1em")
            .style("text-anchor", "middle")
            .style("font-family", "'Roboto Condensed', Arial, sans-serif")
            .style("font-size", `${labelFontSize}px`)
            .text("Offenses");

        // Add the line
        const line = svg.append("path")
            .datum(filteredData)
            .attr("fill", "none")
            .attr("stroke", "steelblue")
            .attr("stroke-width", 2.5) // Thicker line
            .attr("d", d3.line()
                .x(d => x(d.date))
                .y(d => y(d.count))
            );

        // Add dots at each data point
        svg.selectAll("dot")
            .data(filteredData)
            .enter().append("circle")
            .attr("cx", d => x(d.date))
            .attr("cy", d => y(d.count))
            .attr("r", 3)
            .attr("fill", "steelblue");

        // Add tooltip
        const tooltip = d3.select("body").append("div")
            .attr("class", "tooltip")
            .style("opacity", 0)
            .style("font-family", "'Roboto Condensed', Arial, sans-serif");

        svg.selectAll("circle")
            .on("mouseover", function(event, d) {
                tooltip.transition()
                    .duration(200)
                    .style("opacity", .9);
                tooltip.html(`<strong>Agency:</strong> ${d.agency_name}<br><strong>Crime Type:</strong> ${d.crime_type}<br><strong>Offenses:</strong> ${d.count}<br><strong>Date:</strong> ${d3.timeFormat("%B %Y")(d.date)}`)
                    .style("left", (event.pageX + 5) + "px")
                    .style("top", (event.pageY - 28) + "px");
            })
            .on("mouseout", function(d) {
                tooltip.transition()
                    .duration(500)
                    .style("opacity", 0);
            });
    }

    // Load data and initialize filters and chart
    d3.csv("data/viz_data.csv").then(function(data) {
        data.forEach(d => {
            d.date = new Date(d.date);
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
