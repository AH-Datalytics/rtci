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

// Load city coordinates with population data and add markers
d3.csv("../app_data/cities_coordinates.csv").then(data => {
    data.forEach(city => {
        const lat = parseFloat(city.lat);  
        const lon = parseFloat(city.long);  
        const population = parseInt(city.population);

        // Calculate initial radius based on the current zoom level
        const radius = getRadius(population, map.getZoom());

        if (!isNaN(lat) && !isNaN(lon)) {
            const marker = L.circleMarker([lat, lon], {
                radius: radius,
                color: null,
                fillColor: "black",
                fillOpacity: 0.5
            }).addTo(map);

            // Format population with commas if available
            const formattedPopulation = !isNaN(population) ? population.toLocaleString() : "Data not available";

            marker.bindPopup(`<b>${city.agency_name}, ${city.state_name}</b><br>Population: ${formattedPopulation}`);

            // Show popup and change color to orange on hover
            marker.on('mouseover', function () {
                this.openPopup();
                this.setStyle({ fillColor: "#f28106" }); // Change to orange on hover
            });

            // Reset color to black when no longer hovering
            marker.on('mouseout', function () {
                this.closePopup();
                this.setStyle({ fillColor: "black" }); // Reset to black
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
