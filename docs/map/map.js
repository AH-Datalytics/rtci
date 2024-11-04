// Initialize the map and set its view to a starting location
const map = L.map('map').setView([37.7749, -95.7129], 4); // Centered on the U.S. with a zoom level of 4

// Add a tile layer to the map (OpenStreetMap tiles)
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
}).addTo(map);

d3.csv("../app_data/cities_coordinates.csv").then(data => {
    console.log("Data loaded:", data); // Log the entire dataset to ensure it’s loaded correctly
    
    data.forEach(city => {
        console.log(city); // Log each city row
        
        const lat = parseFloat(city.lat);  
        const lon = parseFloat(city.long); 
        
        // Check if latitude and longitude are valid numbers
        console.log(`Lat: ${lat}, Lon: ${lon}`);
        
        // Add a circle marker for each city with custom styling
        if (!isNaN(lat) && !isNaN(lon)) { // Only add marker if lat/lon are valid
            L.circleMarker([lat, lon], {
                radius: 10,              // Size of the circle marker
                color: NaN,         // Border color
                fillColor: "black",     // Fill color
                fillOpacity: 0.25       // 75% transparency
            }).addTo(map)
              .bindPopup(`<b>${city.agency_name}, ${city.state_name}</b>`);
        } else {
            console.warn(`Invalid coordinates for ${city.agency_name}, ${city.state_name}`);
        }
    });
}).catch(error => console.error("Error loading city data:", error));
