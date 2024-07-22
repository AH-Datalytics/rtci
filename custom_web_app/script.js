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
        const margin = { top: 20, right: 20, bottom: 30, left: 40 };
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
            .range([height, 0]);

        // Add the X axis
        svg.append("g")
            .attr("transform", `translate(0,${height})`)
            .call(d3.axisBottom(x).ticks(width / 80).tickSizeOuter(0));

        // Add the Y axis
        svg.append("g")
            .call(d3.axisLeft(y).ticks(height / 40));

        // Add the line
        svg.append("path")
            .datum(filteredData)
            .attr("fill", "none")
            .attr("stroke", "steelblue")
            .attr("stroke-width", 1.5)
            .attr("d", d3.line()
                .x(d => x(d.date))
                .y(d => y(d.count))
            );
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
