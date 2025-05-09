const map = L.map('map').setView([37.7749, -95.7129], 4);

L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
    attribution: '&copy; OpenStreetMap contributors &copy; CARTO'
}).addTo(map);

// Region background layers
const regionColors = {
    "Midwest": getComputedStyle(document.documentElement).getPropertyValue('--midwest-color').trim(),
    "Northeast": getComputedStyle(document.documentElement).getPropertyValue('--northeast-color').trim(),
    "South": getComputedStyle(document.documentElement).getPropertyValue('--south-color').trim(),
    "West": getComputedStyle(document.documentElement).getPropertyValue('--west-color').trim()
};

function regionStyle(region) {
    return {
        fillColor: regionColors[region] || "#999999",
        weight: 1,
        color: "#ffffff",
        fillOpacity: 0.3
    };
}

const regionLayers = L.layerGroup().addTo(map);
const regions = ["midwest", "northeast", "south", "west"];

regions.forEach(region => {
    fetch(`../app_data/${region}_states.json`)
        .then(response => response.json())
        .then(geojsonData => {
            const layer = L.geoJson(geojsonData, {
                style: () => regionStyle(region.charAt(0).toUpperCase() + region.slice(1))
            });
            regionLayers.addLayer(layer);
        });
});

let allData = [];
let currentCrimeType = "Murders";
let markersLayer = L.layerGroup().addTo(map);

// Crime type groupings for custom dropdown structure
const crimeTypeGroups = {
    "Violent Crimes": ["Aggravated Assaults", "Murders", "Rapes", "Robberies"],
    "Property Crimes": ["Burglaries", "Thefts", "Motor Vehicle Thefts"]
};

// Load data
d3.csv("../app_data/ytd_map_data.csv").then(data => {
    allData = data;

    populateCrimeDropdown();
    updateMap();

    // Toggle dropdown menu
    d3.select("#crime-type-btn").on("click", () => {
        const menu = document.getElementById("crime-type-dropdown");
        menu.style.display = menu.style.display === "block" ? "none" : "block";
    });

    // Close dropdown if clicked outside
    document.addEventListener("click", function (e) {
        const wrapper = document.getElementById("crime-type-dropdown-wrapper");
        const menu = document.getElementById("crime-type-dropdown");
        if (!wrapper.contains(e.target)) {
            menu.style.display = "none";
        }
    });
});

function populateCrimeDropdown() {
    const dropdownMenu = d3.select("#crime-type-dropdown");
    dropdownMenu.html(""); // Clear previous items

    const severityOrder = [
        { value: "Violent Crimes", isMaster: true },
        { value: "Aggravated Assaults", isMaster: false },
        { value: "Murders", isMaster: false },
        { value: "Rapes", isMaster: false },
        { value: "Robberies", isMaster: false },
        { value: "Property Crimes", isMaster: true },
        { value: "Burglaries", isMaster: false },
        { value: "Thefts", isMaster: false },
        { value: "Motor Vehicle Thefts", isMaster: false }
    ];

    severityOrder.forEach(type => {
        const item = dropdownMenu.append("div")
            .attr("class", "dropdown-item")
            .attr("data-value", type.value)
            .text(type.value)
            .on("click", () => {
                currentCrimeType = type.value;
                d3.select("#crime-type-btn").text(type.value);
                document.getElementById("crime-type-dropdown").style.display = "none";
                updateDropdownSelection(type.value);
                updateMap();
            });

        if (type.value === currentCrimeType) {
            item.classed("selected", true);
        }

        if (type.isMaster) {
            item.classed("master-heading", true);
        }

        if (type.value === "Property Crimes") {
            item.classed("second-master-heading", true);
        }
    });
}



function updateMap() {
    markersLayer.clearLayers();

    const filtered = allData.filter(d =>
        d.crime_type === currentCrimeType &&
        d.Percent_Change !== "Undefined" &&
        d.Percent_Change !== "" &&
        !isNaN(+d.Percent_Change)
    );

    filtered.forEach(d => {
        const lat = +d.lat;
        const lon = +d.long;
        const change = +d.Percent_Change;
        if (isNaN(lat) || isNaN(lon) || isNaN(change)) return;

        const color = change > 0 ? "#f28106" : "#2d5ef9";
        const arrowSize = Math.min(20, Math.max(10, Math.abs(change)));
        const rotation = change > 0 ? 0 : 180;

        const svgIcon = L.divIcon({
            className: 'ytd-arrow-icon',
            html: `<svg width="${arrowSize}" height="${arrowSize}" viewBox="0 0 100 100" style="transform: rotate(${rotation}deg);">
                        <polygon points="50,0 100,100 0,100" fill="${color}" />
                   </svg>`,
            iconSize: [arrowSize, arrowSize],
            iconAnchor: [arrowSize / 2, arrowSize / 2]
        });

        const marker = L.marker([lat, lon], { icon: svgIcon });
        marker.bindPopup(`
            <b>${d.agency_name}, ${d.state_name}</b><br>
            ${d.crime_type}: ${change.toFixed(1)}% change YTD
        `);

        markersLayer.addLayer(marker);
    });
}

function updateDropdownSelection(selectedType) {
    d3.selectAll("#crime-type-dropdown .dropdown-item")
        .classed("selected", false)
        .style("font-weight", "normal");

    d3.select(`#crime-type-dropdown .dropdown-item[data-value="${selectedType}"]`)
        .classed("selected", true)
        .style("font-weight", "bold");
}
