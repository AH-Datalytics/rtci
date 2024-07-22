// Set up dimensions and margins
const margin = {top: 20, right: 30, bottom: 50, left: 60},
      width = 1000 - margin.left - margin.right,
      height = 500 - margin.top - margin.bottom;

// Append SVG to the body
const svg = d3.select("svg")
    .attr("width", width + margin.left + margin.right)
    .attr("height", height + margin.top + margin.bottom)
    .append("g")
    .attr("transform", `translate(${margin.left},${margin.top})`);

// Define scales and axes
const x = d3.scaleTime().range([0, width]);
const y = d3.scaleLinear().range([height, 0]);

const xAxis = d3.axisBottom(x);
const yAxis = d3.axisLeft(y);

// Load data and create chart
/*d3.csv("data.csv").then(function(data) {
    // Parse the date and value
    const parseDate = d3.timeParse("%Y-%m");
    const formatDate = d3.timeFormat("%b %Y");*/

// Load data from the provided URL
//const dataUrl = "https://raw.githubusercontent.com/bhorwitz-ahd/Test/aeaa26fc51c7e2023afcc909d973f8ae5518897a/data.csv";
const dataUrl = "sample.csv"; //Need to figure out how to map to multiple columns



d3.csv(dataUrl).then(function(data) {
    // Parse the date and value
    const parseDate = d3.timeParse("%Y-%m");
    
    //var allGroup = ["Murder", "Rape", "Robbery"]

    data.forEach(d => {
        d.year = d.Year;
        d.month = d.Month;
        d.value = +d.Murder;//Need to figure out how to change columns in a filter
        d.agency = d.City_viz; 
        d.state = d.State_viz;
        d.crime = "Murder"
        d.date = parseDate(d.year + "-" + d.month);
        d.year = +d.year; // Parse year as number
        
        d.value = +d.value;
        
        
    });

    // Sort data by date
    //data.sort((a, b) => a.agency - b.agency);
    //data.sort((a, b) => a.state - b.state);
    //data.sort((a, b) => a.date - b.date);
    data.sort((a, b) => (a.date - b.date) || a.state.localeCompare(b.state) || a.agency.localeCompare(b.agency))
    
    

    // Create unique options for filters
    const agencies = [...new Set(data.map(d => d.agency))];
    const states = [...new Set(data.map(d => d.state))];
    const crimes = [...new Set(data.map(d => d.crime))];
    //const crimes = [...new Set(data.map(d => d.crime))];
    const years = [...new Set(data.map(d => d.year))].sort((a, b) => a - b);

  // Tooltip setup
  const tooltip = d3.select("body").append("div")
  .attr("class", "tooltip")
  .style("position", "absolute")
  .style("padding", "8px")
  .style("background", "lightsteelblue")
  .style("border-radius", "4px")
  .style("visibility", "hidden");

    d3.select("#agency-filter")
      .selectAll("option")
      .data(agencies)
      .enter().append("option")
      .text(d => d);

      d3.select("#state-filter")
      .selectAll("option")
      .data(states)
      .enter().append("option")
      .text(d => d);

    d3.select("#crime-filter")
      .selectAll("option")
      .data(crimes)
      .enter().append("option")
      .text(d => d);

      d3.select("#year-filter")
      .selectAll("option")
      .data(["all", ...years])
      .enter().append("option")
      .attr("value", d => d)
      .text(d => d === "all" ? "All Years" : d);

    function updateGraph() {
        const selectedStates = d3.select("#state-filter").property("value");
        const selectedAgency = d3.select("#agency-filter").property("value");
        const selectedCrime = d3.select("#crime-filter").property("value");
        const selectedYear = d3.select("#year-filter").property("value");

        const filteredData = data.filter(d => 
            (selectedStates === "" || d.state === selectedStates) &&
            (selectedAgency === "" || d.agency === selectedAgency) &&
            (selectedCrime === "" || d.crime === selectedCrime) &&
            (selectedYear === "all" || d.year === +selectedYear) // Handle 'all' year option
        );

        // Update the scales
        x.domain(d3.extent(filteredData, d => d.date));
        y.domain([0, d3.max(filteredData, d => d.value)]);

        // Define the line with smooth interpolation
        const line = d3.line()
            //.curve(d3.curveBasis)  // Use curveBasis for smooth lines
            //.curve(d3.curveBumpX)  // Use curveBumpX for smooth lines
            .curve(d3.curveCardinal.tension(.5))  // Use curveCardinal.tension for smooth lines
            .x(d => x(d.date))
            .y(d => y(d.value));

        svg.selectAll("*").remove(); // Clear previous content

               // Add Y-axis gridlines
        svg.append("g")
        .attr("class", "gridline")
        .attr("stroke", "lightgray") // line color
        .attr("stroke-dasharray","2,2") // make it dashed;;
        .call(d3.axisLeft(y)
            .tickSize(-width)
            .tickFormat("")
            //.tickColor("red")
            
        );
        
        svg.append("path")
            .data([filteredData])
            .attr("class", "line")
            .attr("d", line)            
            .style("fill", "none")
            .style("stroke", "steelblue")
            .style("stroke-width", "2px");

            // Add data points
            svg.selectAll(".dot")
            .data(filteredData)
            .enter().append("circle")
            .attr("class", "dot")
            .attr("cx", d => x(d.date))
            .attr("cy", d => y(d.value))
            .attr("r", 10)
            .style("fill", "transparent")
            .on("mouseover", function(event, d) {
                tooltip.style("visibility", "visible")
                    .html(`Agency: ${d.agency}<br>Date: ${d3.timeFormat("%b %Y")(d.date)}<br>Crime Count: ${d.value}<br>`)
                    .style("left", (event.pageX + 10) + "px")
                    .style("top", (event.pageY - 20) + "px");
            })
            .on("mousemove", function(event) {
                tooltip.style("left", (event.pageX + 10) + "px")
                    .style("top", (event.pageY - 20) + "px");
            })
            .on("mouseout", function() {
                tooltip.style("visibility", "hidden");
            });

            svg.append("g")
            .attr("class", "x-axis")
            .attr("transform", `translate(0,${height})`)
            
            .call(xAxis);

        svg.append("g")
            .attr("class", "y-axis")
            .call(yAxis
            );

        // Add x-axis label
        svg.append("text")
        .attr("class", "x-axis-label")
        .attr("x", width / 2)
        .attr("y", height + 15 + (margin.bottom / 2))
        .attr("text-anchor", "middle")
        .style("font-family", "Roboto")  // Apply Roboto font to Y-axis label
        .text("Date");

    // Add y-axis label
    svg.append("text")
        .attr("class", "y-axis-label")
        .attr("transform", `translate(${-margin.left / 2},${height / 2}) rotate(-90)`)
        .attr("text-anchor", "middle")
        .style("font-family", "Roboto")  // Apply Roboto font to Y-axis label
        .text("Crime Count");

        // Enable download data
        const downloadButton = d3.select("#download-data");
        downloadButton.on("click", function() {
            const csvContent = "data:text/csv;charset=utf-8," 
                + d3.csvFormat(filteredData, ["date", "state", "agency", "crime", "year", "value"]);

            const encodedUri = encodeURI(csvContent);
            const link = document.createElement("a");
            link.setAttribute("href", encodedUri);
            link.setAttribute("download", "filtered_data.csv");
            document.body.appendChild(link);
            link.click();
        });

        updateTable(filteredData);
        updateSummary(filteredData, selectedYear);

    }

    function updateTable(filteredData) {
        const tableContainer = d3.select("#data-table");
        tableContainer.selectAll("*").remove();

         // Create table and apply styles
         const table = tableContainer.append("table")
         .style("border-collapse", "collapse")
         .style("border", "2px black solid")
         .style("font-family", "Roboto");
        
        // Create table header
        const thead = table.append("thead").append("tr");
        ["Date", "State", "Agency", "Crime", "Year", "Value"].forEach(header => {
            thead.append("th").text(header)
                .style("border", "1px black solid")
                .style("padding", "5px")
                .style("background-color", "lightgray")
                .style("font-weight", "bold")
                .style("text-transform", "uppercase");
        });


         // Create table body
         const tbody = table.append("tbody");
         filteredData.forEach(d => {
             const row = tbody.append("tr");
             row.append("td").text(d3.timeFormat("%b %Y")(d.date))
                 .style("border", "1px black solid")
                 .style("padding", "5px")
                 .style("font-size", "16px")
                 .on("mouseover", function(){
                    d3.select(this).style("background-color", "powderblue");
                  })
                    .on("mouseout", function(){
                    d3.select(this).style("background-color", "white");
                  });
                  row.append("td").text(d.state)
                 .style("border", "1px black solid")
                 .style("padding", "5px")
                 .style("font-size", "16px")
                 .on("mouseover", function(){
                    d3.select(this).style("background-color", "powderblue");
                  })
                    .on("mouseout", function(){
                    d3.select(this).style("background-color", "white");
                  });
             row.append("td").text(d.agency)
                 .style("border", "1px black solid")
                 .style("padding", "5px")
                 .style("font-size", "16px")
                 .on("mouseover", function(){
                    d3.select(this).style("background-color", "powderblue");
                  })
                    .on("mouseout", function(){
                    d3.select(this).style("background-color", "white");
                  });
             row.append("td").text(d.crime)
                 .style("border", "1px black solid")
                 .style("padding", "5px")
                 .style("font-size", "16px")
                 .on("mouseover", function(){
                    d3.select(this).style("background-color", "powderblue");
                  })
                    .on("mouseout", function(){
                    d3.select(this).style("background-color", "white");
                  });
             row.append("td").text(d.year)
                 .style("border", "1px black solid")
                 .style("padding", "5px")
                 .style("font-size", "16px")
                 .on("mouseover", function(){
                    d3.select(this).style("background-color", "powderblue");
                  })
                    .on("mouseout", function(){
                    d3.select(this).style("background-color", "white");
                  });
             row.append("td").text(d.value)
                 .style("border", "1px black solid")
                 .style("padding", "5px")
                 .style("font-size", "16px")
                 .on("mouseover", function(){
                    d3.select(this).style("background-color", "powderblue");
                  })
                    .on("mouseout", function(){
                    d3.select(this).style("background-color", "white");
                  });
         });
     }

     // Calculate and update YTD, PYTD, and Percent Change
    function updateSummary(filteredData, selectedYear) {
        const currentYear = d3.max(filteredData, d => d.year);
        const previousYear = currentYear - 1;

        // Filter data for YTD and PYTD
        const ytdData = filteredData.filter(d => d.year === currentYear);
        const pytdData = filteredData.filter(d => d.year === previousYear);

        const ytdTotal = d3.sum(ytdData, d => d.value);
        const pytdTotal = d3.sum(pytdData, d => d.value);

        // Calculate percent change
        const percentChange = ((ytdTotal - pytdTotal) / pytdTotal) * 100;

        // Determine the date ranges
        const ytdRange = d3.extent(ytdData, d => d.date);
        const pytdRange = d3.extent(pytdData, d => d.date);

        // Format the date ranges
        const formatDate = d3.timeFormat("%b %Y");
        const ytdRangeText = `${formatDate(ytdRange[0])} - ${formatDate(ytdRange[1])}`;
        const pytdRangeText = `${formatDate(pytdRange[0])} - ${formatDate(pytdRange[1])}`;


        // Update text boxes
        
        d3.select("#ytd-value").text(`Total: ${ytdTotal}`);
        d3.select("#ytd-range").text(`${ytdRangeText}`);
        d3.select("#pytd-value").text(`Total: ${pytdTotal}`);
        d3.select("#pytd-range").text(`${pytdRangeText}`);
        d3.select("#percent-change").text(`${percentChange.toFixed(2)}%`);
        d3.select("#pct_chg-range").text(`${ytdRangeText}`);
    }


    // Initial render
    updateGraph();

    // Update graph on filter change
    d3.select("#state-filter").on("change", updateGraph);
    d3.select("#agency-filter").on("change", updateGraph);
    d3.select("#crime-filter").on("change", updateGraph);
    d3.select("#year-filter").on("change", updateGraph);

    // Toggle between graph and table
    d3.select("#toggle-graph").on("click", function() {
        d3.select("#line-graph").classed("hidden", false);
        d3.select("#data-table").classed("hidden", true);
        d3.select("#toggle-graph").classed("hidden", true);
        d3.select("#toggle-table").classed("hidden", false);
    });

    d3.select("#toggle-table").on("click", function() {
        d3.select("#line-graph").classed("hidden", true);
        d3.select("#data-table").classed("hidden", false);
        d3.select("#toggle-graph").classed("hidden", false);
        d3.select("#toggle-table").classed("hidden", true);
    });
    /*
    // Toggle table visibility
    const toggleTableButton = d3.select("#toggle-table");
    toggleTableButton.on("click", function() {
        const table = d3.select("#data-table");
        const isVisible = table.style("display") === "block";
        table.style("display", isVisible ? "none" : "block");
        toggleTableButton.text(isVisible ? "Show Table" : "Hide Table");
    });*/
});
