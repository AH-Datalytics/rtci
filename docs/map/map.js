// Initialize the map and set its view to a starting location
const map = L.map('map').setView([37.7749, -95.7129], 4); // Centered on the U.S. with a zoom level of 4

// Add a tile layer to the map (OpenStreetMap tiles)
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
}).addTo(map);

// Store markers for easy access when updating size
const markers = [];

// Function to calculate radius based on population and zoom level
function getRadius(population, zoom) {
    const baseRadius = !isNaN(population) ? Math.sqrt(population) / 75 : 5;  // Default size if population is missing
    const zoomFactor = Math.max(1, (zoom / 5)); // Adjust this factor to control size scaling
    return baseRadius * zoomFactor;
}

// Load city coordinates with population and sample data and add markers
d3.csv("../app_data/cities_coordinates.csv").then(data => {
    data.forEach(city => {
        const lat = parseFloat(city.lat);  
        const lon = parseFloat(city.long);  
        const population = parseInt(city.population);
        const isNationalSample = city.national_sample === "TRUE"; // Check sample status

        // Determine initial marker color based on sample status
        const fillColor = isNationalSample ? "#2d5ef9" : "#f28106";

        // Calculate initial radius based on the current zoom level
        const radius = getRadius(population, map.getZoom());

        if (!isNaN(lat) && !isNaN(lon)) {
            const marker = L.circleMarker([lat, lon], {
                radius: radius,
                color: null,
                fillColor: fillColor,
                fillOpacity: 0.75
            }).addTo(map);

            // Format population with commas if available
            const formattedPopulation = !isNaN(population) ? population.toLocaleString() : "Data not available";

            marker.bindPopup(`<b>${city.agency_name}, ${city.state_name}</b><br>Population: ${formattedPopulation}`);

            // Show popup and change color to orange on hover
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
}).catch(error => console.error("Error loading city data:", error));

// Listen for zoom changes and resize markers accordingly
map.on('zoomend', () => {
    const zoom = map.getZoom();
    markers.forEach(({ marker, population }) => {
        const newRadius = getRadius(population, zoom);
        marker.setRadius(newRadius);
    });
});

// Add a legend to the map
const legend = L.control({ position: 'topright' });

legend.onAdd = function () {
    const div = L.DomUtil.create('div', 'info legend');
    div.innerHTML += `<h4>National and State Samples</h4>`;
    div.innerHTML += `<i style="background: #2d5ef9"></i> Included<br>`;
    div.innerHTML += `<i style="background: #f28106"></i> Excluded<br>`;
    return div;
};

legend.addTo(map);
