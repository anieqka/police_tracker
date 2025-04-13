// Modified JavaScript for Flask

// Configuration
const ITEMS_PER_PAGE = 50;
const MAX_MAP_MARKERS = 300;
let currentPage = 1;
let allData = [];
let markersCluster = null;

// Initialize map
const map = L.map('map').setView([37.8, -96], 4);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
}).addTo(map);

// Initialize marker cluster group
markersCluster = L.markerClusterGroup({
    maxClusterRadius: 40,
    disableClusteringAtZoom: 8,
    spiderfyOnMaxZoom: true,
    showCoverageOnHover: false,
    zoomToBoundsOnClick: true
});
map.addLayer(markersCluster);

// File upload handling
document.getElementById('upload-btn').addEventListener('click', () => {
    document.getElementById('csv-file').click();
});

document.getElementById('csv-file').addEventListener('change', handleFileUpload);

async function handleFileUpload(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    document.getElementById('file-info').textContent = `Loading: ${file.name}`;
    document.getElementById('loading').style.display = 'block';
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        const response = await fetch('/upload', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (result.error) {
            throw new Error(result.error);
        }
        
        document.getElementById('file-info').textContent = `Loaded: ${result.filename}`;
        allData = result.data;
        document.getElementById('loading').style.display = 'none';
        document.getElementById('total-items').textContent = result.total;
        currentPage = 1;
        updateTableAndMap();
    } catch (error) {
        console.error('Error uploading file:', error);
        document.getElementById('loading').textContent = 'Error loading file. Please try again.';
        document.getElementById('file-info').textContent = '';
    }
}

// Rest of your JavaScript remains the same...
// (Include all the other functions from your original script)