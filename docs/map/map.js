// Initialize the map and set its view to a starting location
const map = L.map('map').setView([37.7749, -95.7129], 4); // Centered on the U.S. with a zoom level of 4

// Add a tile layer to the map (OpenStreetMap tiles)
L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors, &copy; <a href="https://carto.com/attributions">CARTO</a>'
}).addTo(map);


// Get region colors from CSS variables
const regionColors = {
    "Midwest": getComputedStyle(document.documentElement).getPropertyValue('--midwest-color').trim(),
    "Northeast": getComputedStyle(document.documentElement).getPropertyValue('--northeast-color').trim(),
    "South": getComputedStyle(document.documentElement).getPropertyValue('--south-color').trim(),
    "West": getComputedStyle(document.documentElement).getPropertyValue('--west-color').trim()
};



// Function to style regions
function regionStyle(region) {
    return {
        fillColor: regionColors[region] || "#999999", // Default grey if region not found
        weight: 1,
        color: "#ffffff", // White border
        fillOpacity: 0.3, // Subtle transparency
    };
}

// Create a single group layer for all regions
const regionLayers = L.layerGroup().addTo(map); // Ensure it is added BEFORE markers

// Load and add each region layer
const regions = ["midwest", "northeast", "south", "west"];

regions.forEach(region => {
    fetch(`../app_data/${region}_states.json`)
        .then(response => response.json())
        .then(geojsonData => {
            const regionLayer = L.geoJson(geojsonData, {
                style: () => regionStyle(region.charAt(0).toUpperCase() + region.slice(1))
            });
            regionLayers.addLayer(regionLayer); // Add each region to the background layer
        })
        .catch(error => console.error(`Error loading ${region} region data:`, error));
});




// Store markers for easy access when updating size
const markers = [];
let includedCount = 0; // Count for included in the sample
let excludedCount = 0; // Count for excluded from the sample
let includedPopulation = 0; // Total population for included agencies
let excludedPopulation = 0; // Total population for excluded agencies

// Function to calculate radius based on population and zoom level
function getRadius(population, zoom) {
    const baseRadius = !isNaN(population) ? Math.sqrt(population) / 75 : 5;  // Default size if population is missing
    const zoomFactor = Math.max(1, (zoom / 5)); // Adjust this factor to control size scaling
    return baseRadius * zoomFactor;
}

/* 
// OPTIONAL: Add a global grey overlay for non-RTCI countries
fetch("../app_data/non_rtci_countries.geo.json") // Path to the filtered non-RTCI countries file
    .then(response => response.json())
    .then(nonRtciCountriesData => {
        // Style for non-RTCI countries to appear greyed out
        function nonRtciCountryStyle() {
            return {
                fillColor: "#c0c0c0",
                weight: 0,
                color: "blue",
                fillOpacity: 0.4
            };
        }

        // Add the non-RTCI countries layer to the map
        L.geoJson(nonRtciCountriesData, { style: nonRtciCountryStyle, interactive: false }).addTo(map);
    })
    .catch(error => console.error("Error loading non-RTCI countries data:", error));
*/

/*
// OPTIONAL: Add a greyed-out overlay for non-RTCI U.S. states
fetch("../app_data/non_rtci_states.json")
    .then(response => response.json())
    .then(nonRtciStatesData => {
        // Style for non-RTCI states within the U.S.
        function nonRtciStateStyle() {
            return {
                fillColor: "#c0c0c0",
                weight: 0,
                color: null,
                fillOpacity: 0.5
            };
        }

        // Add the non-RTCI states layer on top of the world countries layer
        L.geoJson(nonRtciStatesData, { style: nonRtciStateStyle, interactive: false }).addTo(map);
    })
    .catch(error => console.error("Error loading non-RTCI states data:", error));
*/

// Load city coordinates with population and sample data and add markers
d3.csv("../app_data/cities_coordinates.csv").then(data => {
    data.forEach(city => {
        const lat = parseFloat(city.lat);  
        const lon = parseFloat(city.long);  
        const population = parseInt(city.population);
        const isNationalSample = city.national_sample === "TRUE"; // Check sample status

          // Increment the counters based on sample status
          if (isNationalSample) {
            includedCount++;
            includedPopulation += (!isNaN(population) ? population : 0); // Add only valid population
        } else {
            excludedCount++;
            excludedPopulation += (!isNaN(population) ? population : 0); // Add only valid population
        }

        // Determine initial marker color based on sample status
        const fillColor = isNationalSample ? "#2d5ef9" : "#f28106";

        // Calculate initial radius based on the current zoom level
        const radius = getRadius(population, map.getZoom());

        if (!isNaN(lat) && !isNaN(lon)) {
            let marker;
        
            if (city.is_county === "TRUE") { // Draw a triangle for counties
                const size = radius; // Adjust this to control triangle size, you can tweak it later
        
                // Calculate coordinates for triangle vertices
                const triangleCoords = [
                    [lat + size / 100, lon],                   // Top vertex
                    [lat - size / 200, lon - size / 200],      // Bottom left vertex
                    [lat - size / 200, lon + size / 200]       // Bottom right vertex
                ];
        
                marker = L.polygon(triangleCoords, {
                    color: null,
                    fillColor: fillColor,
                    fillOpacity: 0.6,
                    weight: 0
                }).addTo(map);
            } else { // Draw a circle for cities
                marker = L.circleMarker([lat, lon], {
                    radius: radius,
                    color: null,
                    fillColor: fillColor,
                    fillOpacity: 0.6
                }).addTo(map);
            }
        
            // Format population with commas if available
            const formattedPopulation = !isNaN(population) ? population.toLocaleString() : "Data not available";
        
            // Bind popup for both types
            marker.bindPopup(`
                <b>${city.agency_name}, ${city.state_name}</b><br>
                Population: ${formattedPopulation}<br>
                Source Method: <a href="${city.state_ucr_link}" target="_blank"> ${city.source_method}</a>
            `);
        
            // Hover and click interactions (same as before)
            marker.on('mouseover', function () {
                markers.forEach(({ marker }) => {
                    if (marker.isClicked) {
                        marker.isClicked = false;
                        marker.setStyle({ fillColor: fillColor });
                        marker.closePopup();
                    }
                });
                if (!this.isClicked) {
                    this.setStyle({ fillColor: "#00333a" });
                    this.openPopup();
                }
            });
        
            marker.on('mouseout', function () {
                if (!this.isClicked) {
                    this.setStyle({ fillColor: fillColor });
                    this.closePopup();
                }
            });
        
            marker.on('click', function (e) {
                markers.forEach(({ marker }) => {
                    if (marker.isClicked) {
                        marker.isClicked = false;
                        marker.setStyle({ fillColor: fillColor });
                        marker.closePopup();
                    }
                });
                this.isClicked = true;
                this.setStyle({ fillColor: "#00333a" });
                this.openPopup();
            });
        
            map.on('click', function (e) {
                if (!e.originalEvent.target.classList.contains('leaflet-popup-content')) {
                    markers.forEach(({ marker }) => {
                        if (marker.isClicked) {
                            marker.isClicked = false;
                            marker.closePopup();
                            marker.setStyle({ fillColor: fillColor });
                        }
                    });
                }
            });
        
            // Save marker for resizing and reference (only circles are resizable, but we can store all for consistency)
            markers.push({ marker, population, isCounty: city.is_county === "TRUE" });
        }
        
    });
    
    // Update the legend after data is processed
    updateLegend();
}).catch(error => console.error("Error loading city data:", error));

// Listen for zoom changes and resize markers accordingly
map.on('zoomend', () => {
    const zoom = map.getZoom();
    markers.forEach(({ marker, population }) => {
        const newRadius = getRadius(population, zoom);
        marker.setRadius(newRadius);
    });
});

// Function to update the legend dynamically
// Function to update the legend dynamically
function updateLegend() {
    const legend = L.control({ position: 'topright' });

    legend.onAdd = function () {
        const div = L.DomUtil.create('div', 'info legend');

        // Format populations to two decimals and add "M"
        const formattedIncludedPopulation = (includedPopulation / 1_000_000).toFixed(2) + "M";
        const formattedExcludedPopulation = (excludedPopulation / 1_000_000).toFixed(2) + "M";

        // First key: National sample status
        div.innerHTML += `<h4>Included in National & State Samples?</h4>`;
        div.innerHTML += `<i style="background: #2d5ef9"></i> Yes, has complete data <span>(${includedCount})</span>.<br>`;
        div.innerHTML += `<i style="background: #f28106"></i> No, incomplete data <span>(${excludedCount})</span>.<br>`;
        div.innerHTML += `<p style="padding-bottom: 0px; margin-bottom: 0px; font-size: 12px;">*Markers sized by population.</p>`;
        div.innerHTML += `<p style="margin-top: 0px; padding-top: 0px; padding-bottom: 0px; margin-bottom: 0px; font-size: 12px;">**National sample covers ${formattedIncludedPopulation} total population.</p>`;

        // Add a divider for separation
        div.innerHTML += `<hr style="border: 0; height: 1px; background: #ccc; margin: 8px 0;">`;

        // NEW Section: Type
div.innerHTML += `<h4>Agency Type</h4>`;

div.innerHTML += `<div style="display: flex; align-items: center; margin-left: 2px; gap: 2.5px;">
    <i style="
        display: inline-block;
        width: 14px;
        height: 14px;
        background: black;
        border-radius: 50%;
        flex-shrink: 0;
    "></i> 
    <span>City</span>
</div>`;

div.innerHTML += `<div style="display: flex; align-items: center; margin-left: 2px; gap: 1px;">
    <i style="
        width: 0; 
        height: 0; 
        border-left: 8px solid transparent;
        border-right: 8px solid transparent;
        border-bottom: 14px solid black;
        display: inline-block;
        flex-shrink: 0;
    "></i> 
    <span>County</span>
</div>`;


        // Add a divider for separation
        div.innerHTML += `<hr style="border: 0; height: 1px; background: #ccc; margin: 8px 0;">`;

        // Second key: Region colors from CSS
        div.innerHTML += `<h4>FBI Regions</h4>`;
        div.innerHTML += `<i style="background: var(--midwest-color); opacity: 0.4; border: 1px solid var(--midwest-color);"></i> Midwest<br>`;
        div.innerHTML += `<i style="background: var(--northeast-color); opacity: 0.4; border: 1px solid var(--northeast-color);"></i> Northeast<br>`;
        div.innerHTML += `<i style="background: var(--south-color); opacity: 0.4; border: 1px solid var(--south-color);"></i> South<br>`;
        div.innerHTML += `<i style="background: var(--west-color); opacity: 0.4; border: 1px solid var(--west-color);"></i> West<br>`;

        return div;
    };

    legend.addTo(map);
}
