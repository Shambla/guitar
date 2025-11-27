// Catalog Page JavaScript

let catalogData = [];
let currentFilter = 'all';

// Load catalog when page loads
document.addEventListener('DOMContentLoaded', function() {
    loadCatalog();
});

// Load catalog from JSON file
function loadCatalog() {
    fetch('catalog-data.json')
        .then(response => {
            if (!response.ok) {
                throw new Error('Catalog data not found');
            }
            return response.json();
        })
        .then(data => {
            catalogData = data;
            displayCatalog(catalogData);
        })
        .catch(error => {
            console.error('Error loading catalog:', error);
            document.getElementById('catalog-grid').innerHTML = 
                '<p class="no-results">Catalog coming soon! Check back later or visit <a href="https://www.sheetmusicdirect.com/en-US/Search.aspx?query=Brian%2BStreckfus" target="_blank">Sheet Music Direct</a> to browse available pieces.</p>';
        });
}

// Display catalog items
function displayCatalog(items) {
    const grid = document.getElementById('catalog-grid');
    
    if (items.length === 0) {
        grid.innerHTML = '<p class="no-results">No pieces match your search. Try a different filter or search term.</p>';
        return;
    }
    
    grid.innerHTML = '';
    
    items.forEach(item => {
        const itemDiv = document.createElement('div');
        itemDiv.className = 'catalog-item';
        itemDiv.setAttribute('data-category', `${item.category} ${item.difficulty.toLowerCase()}`);
        itemDiv.setAttribute('data-search', `${item.title} ${item.composer} ${item.category} ${item.difficulty}`.toLowerCase());
        
        // Difficulty class for color coding
        const difficultyClass = item.difficulty.toLowerCase();
        
        const previewTarget = item.preview_url || item.sheet_music_direct_url;
        const encodedPreview = encodeURIComponent(previewTarget);
        let previewImageSrc = `https://image.thum.io/get/width/600/crop/600/${encodedPreview}`;
        let captionText = 'Snapshot of the live listing (auto-refreshes periodically)';

        if (item.preview_image) {
            previewImageSrc = item.preview_image;
            captionText = 'Preview image (replace with your own screenshot)';
        } else if (previewImageSrc.startsWith('https://image.thum.io')) {
            captionText = 'Snapshot of the live listing (auto-refreshes periodically)';
        }

        if (!previewImageSrc) {
            previewImageSrc = 'img/sheet.png';
            captionText = 'Preview image (replace with your own screenshot)';
        }

        itemDiv.innerHTML = `
            <div class="preview-screen">
                <img class="live-preview" src="${previewImageSrc}" alt="Preview of ${item.title}" data-source="${previewTarget}">
                <span class="preview-caption">${captionText}</span>
            </div>
            <div class="composer">${item.composer}</div>
            <h3>${item.title}</h3>
            <span class="category-tag">${item.category}</span>
            <p class="difficulty ${difficultyClass}">${item.difficulty}</p>
            <p class="price">${item.price}</p>
            <a class="link-button" href="${item.sheet_music_direct_url}" target="_blank" rel="noopener">Open Listing</a>
        `;
        
        grid.appendChild(itemDiv);
    });
}

// Filter catalog by category
function filterBy(category) {
    currentFilter = category;
    
    // Update active button
    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    event.target.classList.add('active');
    
    // Filter items
    const items = document.querySelectorAll('.catalog-item');
    items.forEach(item => {
        const itemCategory = item.getAttribute('data-category');
        if (category === 'all' || itemCategory.includes(category)) {
            item.style.display = 'flex';
        } else {
            item.style.display = 'none';
        }
    });
    
    // Check if any items are visible
    const visibleItems = Array.from(items).filter(item => item.style.display !== 'none');
    if (visibleItems.length === 0) {
        document.getElementById('catalog-grid').innerHTML = '<p class="no-results">No pieces found in this category.</p>';
    }
}

// Search catalog
function searchCatalog() {
    const searchTerm = document.getElementById('search-bar').value.toLowerCase();
    const items = document.querySelectorAll('.catalog-item');
    let visibleCount = 0;
    
    items.forEach(item => {
        const searchData = item.getAttribute('data-search');
        if (searchData.includes(searchTerm)) {
            item.style.display = 'flex';
            visibleCount++;
        } else {
            item.style.display = 'none';
        }
    });
    
    // Show "no results" message if nothing matches
    if (visibleCount === 0 && searchTerm !== '') {
        const grid = document.getElementById('catalog-grid');
        const noResults = grid.querySelector('.no-results');
        if (!noResults) {
            const msg = document.createElement('p');
            msg.className = 'no-results';
            msg.textContent = `No pieces found matching "${searchTerm}". Try a different search term.`;
            grid.appendChild(msg);
        }
    } else {
        // Remove "no results" message if it exists
        const noResults = document.querySelector('.no-results');
        if (noResults) {
            noResults.remove();
        }
    }
}

// Fallback image handler for live previews
document.addEventListener('error', function(event) {
    const target = event.target;
    if (target.classList && target.classList.contains('live-preview')) {
        target.src = 'img/sheet.png';
        target.nextElementSibling.textContent = 'Preview unavailable (open listing to view score)';
    }
}, true);

