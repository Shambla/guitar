// Catalog Page JavaScript

let catalogData = [];
let currentFilter = 'all';

// Load catalog when page loads
document.addEventListener('DOMContentLoaded', function() {
    loadCatalog();
});

// Load catalog from JSON file
function loadCatalog() {
    console.log('Loading catalog...');
    // Use simple relative path - catalog-data.json is in same directory as catalog.html
    fetch('catalog-data.json')
        .then(response => {
            console.log('Fetch response:', response.status, response.statusText);
            if (!response.ok) {
                throw new Error(`Catalog data not found: ${response.status} ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('Catalog data loaded:', data.length, 'items');
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
    console.log('Displaying catalog:', items.length, 'items');
    const grid = document.getElementById('catalog-grid');
    
    if (!grid) {
        console.error('Catalog grid element not found!');
        return;
    }
    
    if (items.length === 0) {
        grid.innerHTML = '<p class="no-results">No pieces match your search. Try a different filter or search term.</p>';
        return;
    }
    
    grid.innerHTML = '';
    console.log('Grid cleared, creating', items.length, 'items...');
    
    let itemsCreated = 0;
    items.forEach((item, index) => {
        try {
            const itemDiv = document.createElement('div');
            itemDiv.className = 'catalog-item';
            itemDiv.setAttribute('data-category', `${item.category} ${item.difficulty.toLowerCase()}`);
            itemDiv.setAttribute('data-search', `${item.title} ${item.composer} ${item.category} ${item.difficulty}`.toLowerCase());
            
            // Difficulty class for color coding
            const difficultyClass = item.difficulty.toLowerCase();
            
            // Use manual preview images only (no thum.io)
            let previewImageSrc = item.preview_image || 'img/sheet.png';
            let captionText = 'Preview image';

            itemDiv.innerHTML = `
                <div class="preview-screen">
                    <img class="live-preview" src="${previewImageSrc}" alt="Preview of ${item.title}">
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
            itemsCreated++;
            if (index === 0) {
                console.log('First item created and appended:', item.title);
            }
        } catch (error) {
            console.error('Error creating item', index, ':', error);
        }
    });
    
    console.log('Items created:', itemsCreated, 'of', items.length);
    console.log('Grid children count:', grid.children.length);
    console.log('Grid computed style display:', window.getComputedStyle(grid).display);
    
    // Force a visual test - add a red border to verify grid is visible
    if (grid.children.length > 0) {
        grid.style.border = '3px solid red';
        grid.style.minHeight = '200px';
        console.log('✅ Grid has', grid.children.length, 'children. If you see a red border, items are there but may be hidden by CSS.');
    } else {
        console.error('❌ Grid has NO children! Items were not appended.');
    }
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

