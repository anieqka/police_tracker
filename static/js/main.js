// Configuration
const ITEMS_PER_PAGE = 50;
const MAX_MAP_MARKERS = 300;
let currentPage = 1;
let allData = [];
let markersCluster = null;


// Initialize map
function initMap() {
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
    return map;
}

const map = initMap();

// File upload handling
document.getElementById('upload-btn')?.addEventListener('click', () => {
    document.getElementById('csv-file').click();
});

document.getElementById('csv-file')?.addEventListener('change', handleFileUpload);

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
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const result = await response.json();
        
        document.getElementById('file-info').textContent = `Loaded: ${file.name}`;
        allData = result.data || [];
        document.getElementById('loading').style.display = 'none';
        document.getElementById('total-items').textContent = allData.length;
        currentPage = 1;
        updateTableAndMap();
    } catch (error) {
        console.error('Error uploading file:', error);
        document.getElementById('loading').textContent = 'Error loading file. Please try again.';
        document.getElementById('file-info').textContent = '';
    }
}

// Function to load data (called from data.html)
async function loadComparisonData() {
    try {
        const response = await fetch('/api/comparison');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        
        // Update the chart if the function exists
        if (typeof updateChart === 'function') {
            updateChart(data.tech_distribution);
        }
        
        // Populate tables if elements exist
        const atlasStats = document.getElementById('atlas-stats');
        if (atlasStats) {
            atlasStats.innerHTML = `
                <p>Agencies: ${data.total_agencies?.atlas || 'N/A'}</p>
                <p>Top Tech: ${Object.keys(data.tech_distribution?.atlas || {})[0] || 'N/A'}</p>
            `;
        }
    } catch (error) {
        console.error("Error loading data:", error);
    }
}

// Initialize based on current page
document.addEventListener('DOMContentLoaded', function() {
    // Initialize elements that exist on both pages
    initFlowerCursor();
    initHeartAnimation();
    
    // Page-specific initialization
    if (window.location.pathname.endsWith('data.html')) {
        loadComparisonData();
    } else {
        // Main page initialization
        initVerification();
    }
});

function initFlowerCursor() {
    const flowers = [];
    const flowerCount = 12;
    const flowerColors = ['#ff69b4', '#ffb6c1', '#db7093', '#ff85a2', '#ff9ebb'];
    const flowerSizes = [18, 20, 22, 24, 26];
    
    // Create flower elements
    for (let i = 0; i < flowerCount; i++) {
        const flower = document.createElement('div');
        flower.className = 'flower-trail';
        const size = flowerSizes[Math.floor(Math.random() * flowerSizes.length)];
        const color = flowerColors[Math.floor(Math.random() * flowerColors.length)];
        
        flower.innerHTML = `
            <svg width="${size}" height="${size}" style="color: ${color}">
                <use href="#flower"></use>
            </svg>
        `;
        
        flower.style.opacity = 0;
        flower.style.transition = `opacity ${0.2 + i*0.05}s, transform ${0.2 + i*0.03}s`;
        document.body.appendChild(flower);
        flowers.push({
            element: flower,
            size: size,
            delay: i * 50
        });
    }
    
    let mouseX = 0;
    let mouseY = 0;
    let lastPositions = [];
    const positionHistoryLength = 5;
    
    // Track mouse movement
    document.addEventListener('mousemove', (e) => {
        mouseX = e.clientX;
        mouseY = e.clientY;
        
        // Store recent positions for smoother trail
        lastPositions.unshift({x: mouseX, y: mouseY});
        if (lastPositions.length > positionHistoryLength) {
            lastPositions.pop();
        }
        
        updateFlowerTrail();
    });
    
    function updateFlowerTrail() {
        flowers.forEach((flower, index) => {
            const posIndex = Math.min(index, lastPositions.length - 1);
            if (posIndex >= 0) {
                const {x, y} = lastPositions[posIndex];
                
                // Calculate delay-based movement
                setTimeout(() => {
                    flower.element.style.left = `${x}px`;
                    flower.element.style.top = `${y}px`;
                    flower.element.style.opacity = 0.8 - (index * 0.06);
                    flower.element.style.transform = `
                        translate(-50%, -50%) 
                        rotate(${index * 15}deg) 
                        scale(${0.7 + (index * 0.03)})
                    `;
                }, flower.delay);
            }
        });
    }
    
    // Hide flowers when mouse stops
    let mouseStopTimer;
    document.addEventListener('mousemove', () => {
        clearTimeout(mouseStopTimer);
        flowers.forEach(flower => {
            flower.element.style.opacity = 0.8;
        });
        mouseStopTimer = setTimeout(() => {
            flowers.forEach(flower => {
                flower.element.style.opacity = 0;
            });
        }, 300);
    });
}

// Make heartPattern global
const heartPattern = [
    [0,0,1,1,0,0,1,1,0,0],
    [0,1,1,1,1,1,1,1,1,0],
    [1,1,1,1,1,1,1,1,1,1],
    [1,1,1,1,1,1,1,1,1,1],
    [1,1,1,1,1,1,1,1,1,1],
    [0,1,1,1,1,1,1,1,1,0],
    [0,0,1,1,1,1,1,1,0,0],
    [0,0,0,1,1,1,1,0,0,0],
    [0,0,0,0,1,1,0,0,0,0]
];

// Make hearts array global
let hearts = [];

// Initialize everything when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    initializeHearts();
    setupVerificationButton();
    // Other initialization code...
});

function initializeHearts() {
    hearts = [
        document.getElementById('heart1'),
        document.getElementById('heart2'),
        document.getElementById('heart3')
    ];

    hearts.forEach(heart => {
        heart.innerHTML = '';
        heart.style.width = '50px';
        heart.style.height = '50px';
        heart.style.position = 'relative';
        
        heartPattern.forEach((row, rowIndex) => {
            row.forEach((pixel, colIndex) => {
                if (pixel === 1) {
                    const pixelElement = document.createElement('div');
                    pixelElement.classList.add('pixel');
                    pixelElement.style.position = 'absolute';
                    pixelElement.style.width = '5px';
                    pixelElement.style.height = '5px';
                    pixelElement.style.left = `${colIndex * 5}px`;
                    pixelElement.style.top = `${rowIndex * 5}px`;
                    pixelElement.style.backgroundColor = 'var(--primary-pink)';
                    heart.appendChild(pixelElement);
                }
            });
        });
        heart.style.opacity = '0';
    });
}

function setupVerificationButton() {
    document.getElementById('verify-btn').addEventListener('click', function() {
        const loadingScreen = document.getElementById('loading-screen');
        const verifyBtn = document.getElementById('verify-btn');
        const verificationMessage = document.getElementById('verification-message');
        const uploadBtn = document.getElementById('upload-btn');
        const imageContainer = document.querySelector('.image-container');
        
        loadingScreen.classList.add('active');
        document.getElementById('loading-text').textContent = "LOADING...";
        
        // Start heart animation
        const heartAnimation = animateHearts();
        
        setTimeout(() => {
            document.getElementById('loading-text').textContent = "VERIFIED!";
            
            // Show all hearts at full opacity
            hearts.forEach(heart => {
                heart.style.opacity = '1';
                heart.style.transform = 'scale(1)';
            });
            
            setTimeout(() => {
                clearInterval(heartAnimation);
                loadingScreen.classList.remove('active');
                imageContainer.classList.add('active');
                verificationMessage.style.display = 'block';
                uploadBtn.style.display = 'inline-block';
                verifyBtn.style.display = 'none';
            }, 500);
        }, 3000);
    });
}

function animateHearts() {
    let step = 0;
    return setInterval(() => {
        hearts.forEach((heart, index) => {
            if (index < step) {
                heart.style.opacity = '1';
                heart.style.transform = 'scale(1)';
            } else {
                heart.style.opacity = '0';
                heart.style.transform = 'scale(0.5)';
            }
        });
        
        step = (step + 1) % (hearts.length + 1);
        
        if (step === 0) {
            setTimeout(() => {
                step = 1;
            }, 300);
        }
    }, 500);
}
// Rest of your table and map update functions remain the same
// (updateTableAndMap, updateTable, updateMap, etc.)