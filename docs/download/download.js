document.addEventListener("DOMContentLoaded", function() {
    const dataPath = "../app_data/final_sample.csv";  // Updated path
    let allData = [];

    // Load data
    d3.csv(dataPath).then(data => {
        allData = data;  // Store all data for downloading
        console.log('Data successfully loaded and stored.');

        // Enable the download button now that the data is ready
        document.querySelector('.download-button').disabled = false;
    }).catch(error => {
        console.error("Error loading the CSV data:", error);
    });

    // Function to convert data to CSV and trigger download
    function downloadCSV(data, filename) {
        if (!data || !data.length) {
            console.error("No data available for download.");
            return;
        }

        const csvData = d3.csvFormat(data);
        const blob = new Blob([csvData], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement("a");
        link.href = URL.createObjectURL(blob);
        link.setAttribute("download", filename);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }

    // Event listener for download button
    document.querySelector('.download-button').addEventListener("click", function() {
        if (allData.length > 0) {
            downloadCSV(allData, 'final_sample.csv');
        } else {
            console.error('Data is not loaded yet. Unable to download.');
        }
    });
});
