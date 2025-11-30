// Catalog Page JavaScript

let catalogData = [];
let currentFilter = 'all';

// Handle image loading errors - try fallback paths
function handleImageError(img, originalSrc, basePath) {
    img.onerror = null; // Prevent infinite loop
    
    // If we tried previews/, try img/previews/ instead
    if (originalSrc.includes('previews/') && !originalSrc.includes('img/previews/')) {
        const filename = originalSrc.split('/').pop();
        img.src = basePath + 'img/previews/' + filename;
        console.log('Trying fallback path:', img.src);
    } else {
        // Final fallback
        img.src = basePath + 'img/sheet.png';
        if (img.nextElementSibling) {
            img.nextElementSibling.textContent = 'Preview image not found';
        }
        console.error('Failed to load image:', originalSrc);
    }
}

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
    
    // TEST: Add a simple test div first to verify grid is visible
    const testDiv = document.createElement('div');
    testDiv.style.cssText = 'background: lime; color: black; padding: 20px; border: 5px solid red; font-size: 24px; font-weight: bold; grid-column: 1 / -1;';
    testDiv.textContent = '🧪 TEST: If you see this, the grid is visible!';
    grid.appendChild(testDiv);
    
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
            // Get base path from current page location to ensure images load correctly
            const basePath = window.location.pathname.substring(0, window.location.pathname.lastIndexOf('/') + 1);
            let previewImageSrc = item.preview_image || 'img/sheet.png';
            
            // Try previews/ folder first, then img/previews/, then fallback
            if (previewImageSrc.startsWith('img/previews/')) {
                // Try previews/ version first
                const filename = previewImageSrc.replace('img/previews/', '');
                previewImageSrc = 'previews/' + filename;
            }
            
            // Ensure path is relative to current page location
            if (!previewImageSrc.startsWith('/') && !previewImageSrc.startsWith('http')) {
                previewImageSrc = basePath + previewImageSrc;
            }
            let captionText = 'Preview image';

            // TEST: Add a simple colored div to verify items are visible
            const testDiv = index === 0 ? '<div style="background: red; color: white; padding: 10px; margin: 10px 0;">TEST: Item is visible!</div>' : '';
            
            itemDiv.innerHTML = `
                ${testDiv}
                <div class="preview-screen">
                    <img class="live-preview" src="${previewImageSrc}" alt="Preview of ${item.title}" 
                         onerror="handleImageError(this, '${previewImageSrc}', '${basePath}');">
                    <span class="preview-caption">${captionText}</span>
                </div>
                <div class="composer">${item.composer}</div>
                <h3>${item.title}</h3>
                <span class="category-tag">${item.category}</span>
                <p class="difficulty ${difficultyClass}">${item.difficulty}</p>
                <p class="price">${item.price}</p>
                <a class="link-button" href="${item.sheet_music_direct_url}" target="_blank" rel="noopener">Open Listing</a>
            `;
            
            // TEST: Force visibility
            itemDiv.style.display = 'block';
            itemDiv.style.visibility = 'visible';
            itemDiv.style.opacity = '1';
            
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
    
    // Force a visual test - add a red border and background to verify grid is visible
    if (grid.children.length > 0) {
        grid.style.border = '5px solid red';
        grid.style.minHeight = '200px';
        grid.style.backgroundColor = 'yellow';
        grid.style.padding = '20px';
        console.log('✅ Grid has', grid.children.length, 'children. RED BORDER + YELLOW BACKGROUND should be visible!');
        
        // Also check first item visibility
        const firstItem = grid.children[0];
        if (firstItem) {
            const firstItemStyle = window.getComputedStyle(firstItem);
            console.log('First item computed styles:');
            console.log('  display:', firstItemStyle.display);
            console.log('  visibility:', firstItemStyle.visibility);
            console.log('  opacity:', firstItemStyle.opacity);
            console.log('  width:', firstItemStyle.width);
            console.log('  height:', firstItemStyle.height);
        }
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

