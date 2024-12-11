// Initialize the map and set its view to a starting location
const map = L.map('map').setView([37.7749, -95.7129], 4); // Centered on the U.S. with a zoom level of 4

// Add a tile layer to the map (OpenStreetMap tiles)
L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors, &copy; <a href="https://carto.com/attributions">CARTO</a>'
}).addTo(map);


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
            const marker = L.circleMarker([lat, lon], {
                radius: radius,
                color: null,
                fillColor: fillColor,
                fillOpacity: 0.6
            }).addTo(map);

            // Format population with commas if available
            const formattedPopulation = !isNaN(population) ? population.toLocaleString() : "Data not available";

            marker.bindPopup(`<b>${city.agency_name}, ${city.state_name}</b><br>Population: ${formattedPopulation}`);

            // Show popup and change color to dark grey on hover
            marker.on('mouseover', function () {
                this.openPopup();
                this.setStyle({ fillColor: "#00333a" }); // Change on hover
            });

            // Reset color to original on mouse out
            marker.on('mouseout', function () {
                this.closePopup();
                this.setStyle({ fillColor: fillColor }); // Reset to initial color
            });

            // Save the marker for resizing
            markers.push({ marker, population });
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
function updateLegend() {
    const legend = L.control({ position: 'topright' });

    legend.onAdd = function () {
        const div = L.DomUtil.create('div', 'info legend');

        // Format populations to two decimals and add "M"
        const formattedIncludedPopulation = (includedPopulation / 1_000_000).toFixed(2) + "M";
        const formattedExcludedPopulation = (excludedPopulation / 1_000_000).toFixed(2) + "M";
    
        // Add color legend for national sample status with italic counts and total population
        div.innerHTML += `<h4>Included in National & State Samples?</h4>`;
        div.innerHTML += `<i style="background: #2d5ef9"></i> Yes, has complete data <span>(${includedCount})</span>.<br>`;
        div.innerHTML += `<i style="background: #f28106"></i> No, incomplete data <span>(${excludedCount})</span>.<br>`;
    
        // Add a sentence about size
        div.innerHTML += `<p style="padding-bottom: 0px; margin-bottom: 0px; font-size: 12px;">*Markers sized by population.</p>`;
        div.innerHTML += `<p style="margin-top: 0px; padding-top: 0px; padding-bottom: 0px; margin-bottom: 0px; font-size: 12px;">**National sample covers ${formattedIncludedPopulation} total population.</p>`;
        
    
        return div;
    };
    

    legend.addTo(map);
}