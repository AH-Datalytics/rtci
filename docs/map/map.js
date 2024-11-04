// Initialize the map
const map = L.map('map').setView([37.7749, -122.4194], 5); // Adjust coordinates and zoom level as needed

// Add a tile layer to the map (OpenStreetMap tiles)
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
}).addTo(map);

// Add a marker (optional)
const marker = L.marker([37.7749, -122.4194]).addTo(map);
marker.bindPopup("<b>Sample Location</b><br>RTCI Participation Point.").openPopup();
