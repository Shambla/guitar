// Catalog Page JavaScript

let catalogData = [];
let currentFilter = 'all';
let currentSort = 'default';

function parsePriceToNumber(priceStr) {
    const cleaned = (priceStr || '')
        .toString()
        .replace(/[^0-9.]/g, '');
    const n = parseFloat(cleaned);
    return Number.isFinite(n) ? n : NaN;
}

function difficultyRank(difficultyStr) {
    const d = (difficultyStr || '').toString().toLowerCase().trim();
    if (d === 'beginner') return 1;
    if (d === 'intermediate') return 2;
    if (d === 'advanced') return 3;
    return 99;
}

// Normalize text for consistent searching (e.g., "film-score" matches "film score")
function normalizeSearchText(str) {
    return (str || '')
        .toString()
        .toLowerCase()
        .replace(/[-_]/g, ' ')
        .replace(/\s+/g, ' ')
        .trim();
}

// Handle image loading errors - try fallback paths
function handleImageError(img, originalSrc, basePath) {
    img.onerror = null; // Prevent infinite loop

    // If we tried previews/, try img/previews/ instead
    if (originalSrc.includes('previews/') && !originalSrc.includes('img/previews/')) {
        const filename = originalSrc.split('/').pop();
        img.src = basePath + 'img/previews/' + filename;
    } else if (originalSrc.includes('mp3_logo')) {
        // MP3 logo failed; keep trying same path (no sheet-music fallback for audio items)
        img.src = basePath + 'img/mp3_logo.png';
        if (img.nextElementSibling) {
            img.nextElementSibling.textContent = 'MP3 audio file';
        }
    } else {
        // Final fallback for sheet music previews
        img.src = basePath + 'img/sheet.png';
        if (img.nextElementSibling) {
            img.nextElementSibling.textContent = 'Preview image not found';
        }
        console.error('Failed to load image:', originalSrc);
    }
}

/**
 * FIX: If nav is position:fixed and its height changes (mobile / scrolled / fonts),
 * it can cover the search bar + controls. This syncs body padding-top to the nav height.
 */
function syncCatalogPageOffsetForFixedNav() {
    const body = document.body;
    if (!body || !body.classList.contains('catalog-page')) return;

    const nav = document.querySelector('nav');
    if (!nav) return;

    const navHeight = Math.ceil(nav.getBoundingClientRect().height);
    const buffer = 16;

    body.style.paddingTop = `${navHeight + buffer}px`;
}

// Load catalog when page loads
document.addEventListener('DOMContentLoaded', function () {
    // Prevent fixed nav from overlapping content
    syncCatalogPageOffsetForFixedNav();

    // Recalculate after fonts/layout settle
    window.setTimeout(syncCatalogPageOffsetForFixedNav, 50);
    window.setTimeout(syncCatalogPageOffsetForFixedNav, 250);

    // Recalculate on resize/orientation changes
    window.addEventListener('resize', syncCatalogPageOffsetForFixedNav);

    // Your page toggles nav.scrolled; recalculating after scroll helps too
    window.addEventListener('scroll', function () {
        window.requestAnimationFrame(syncCatalogPageOffsetForFixedNav);
    });

    // Wire search input automatically (so HTML doesn't need inline onkeyup)
    const sb = document.getElementById('search-bar');
    if (sb) {
        sb.addEventListener('input', function () {
            searchCatalog();
        });
    } else {
        console.warn('Search bar (#search-bar) not found in DOM. Search UI may be missing or ID mismatch.');
    }

    loadCatalog();
});

// Load catalog from JSON file
function loadCatalog() {
    fetch('catalog-data.json')
        .then(response => {
            if (!response.ok) {
                throw new Error(`Catalog data not found: ${response.status} ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            catalogData = data;
            displayCatalog(catalogData);
            sortCatalog();
        })
        .catch(error => {
            console.error('Error loading catalog:', error);
            const grid = document.getElementById('catalog-grid');
            if (grid) {
                grid.innerHTML =
                    '<p class="no-results">Catalog coming soon! Check back later or visit <a href="https://www.sheetmusicdirect.com/en-US/Search.aspx?query=Brian%2BStreckfus" target="_blank" rel="noopener">Sheet Music Direct</a> to browse available pieces.</p>';
            }
        });
}

// Display catalog items
function displayCatalog(items) {
    const grid = document.getElementById('catalog-grid');

    if (!grid) {
        console.error('Catalog grid element not found!');
        return;
    }

    if (!Array.isArray(items) || items.length === 0) {
        grid.innerHTML = '<p class="no-results">No pieces match your search. Try a different filter or search term.</p>';
        return;
    }

    grid.innerHTML = '';

    items.forEach((item, index) => {
        try {
            const itemDiv = document.createElement('div');
            itemDiv.className = 'catalog-item';

            itemDiv.setAttribute('data-category', `${item.category} ${(item.difficulty || '').toString().toLowerCase()}`);
            itemDiv.setAttribute('data-title', normalizeSearchText(item.title));
            itemDiv.setAttribute('data-composer', normalizeSearchText(item.composer));
            itemDiv.setAttribute('data-difficulty-rank', String(difficultyRank(item.difficulty)));
            itemDiv.setAttribute('data-price', String(parsePriceToNumber(item.price)));

            itemDiv.setAttribute(
                'data-search',
                normalizeSearchText(`${item.title} ${item.composer} ${item.category} ${item.difficulty}`)
            );

            const difficultyClass = (item.difficulty || '').toString().toLowerCase();

            // Base path from current page location
            const basePath = window.location.pathname.substring(0, window.location.pathname.lastIndexOf('/') + 1);
            const isMp3Audio = (item.category || '').toString().toLowerCase().includes('mp3');
            let previewImageSrc = isMp3Audio ? 'img/mp3_logo.png' : (item.preview_image || 'img/sheet.png');

            /*
             * PREVIEWS FOLDER STRUCTURE (sloppy, but documented):
             *
             * We have TWO previews folders:
             * 1. /previews/ - 183 items (27.8 MB) - Different filenames than JSON
             * 2. /img/previews/ - 57 items - Matches JSON filenames
             *
             * MP3 audio items always use img/mp3_logo.png so users see it's an audio file, not sheet music.
             */
            if (!isMp3Audio && previewImageSrc.startsWith('img/previews/')) {
                const filename = previewImageSrc.replace('img/previews/', '');
                previewImageSrc = 'previews/' + filename;
            }

            if (!previewImageSrc.startsWith('/') && !previewImageSrc.startsWith('http')) {
                previewImageSrc = basePath + previewImageSrc;
            }

            const captionText = isMp3Audio ? 'MP3 audio file' : 'Preview image';

            const imgAlt = isMp3Audio ? `MP3 audio: ${item.title}` : `Preview of ${item.title}`;
            itemDiv.innerHTML = `
                <div class="preview-screen">
                    <img class="live-preview" src="${previewImageSrc}" alt="${imgAlt}"
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

            itemDiv.style.display = 'flex';
            itemDiv.style.visibility = 'visible';
            itemDiv.style.opacity = '1';

            grid.appendChild(itemDiv);
        } catch (error) {
            console.error('Error creating item', index, ':', error);
        }
    });

    if (grid.children.length > 0) {
        grid.style.display = 'grid';
        grid.style.visibility = 'visible';
        grid.style.opacity = '1';
    }
}

// Sort visible catalog items based on the dropdown selection
function sortCatalog() {
    const grid = document.getElementById('catalog-grid');
    if (!grid) return;

    const select = document.getElementById('sort-select');
    const selected = select ? select.value : 'default';
    currentSort = selected || 'default';

    const nodes = Array.from(grid.children).filter(
        el => el.classList && el.classList.contains('catalog-item')
    );
    if (nodes.length <= 1) return;

    // Keep hidden items after visible items
    const byDisplay = (el) => (el.style && el.style.display === 'none') ? 1 : 0;

    const cmpText = (a, b) => (a || '').localeCompare((b || ''), undefined, { sensitivity: 'base' });
    const cmpNum = (a, b) => {
        const na = Number(a), nb = Number(b);
        const aBad = !Number.isFinite(na);
        const bBad = !Number.isFinite(nb);
        if (aBad && bBad) return 0;
        if (aBad) return 1;
        if (bBad) return -1;
        return na - nb;
    };

    const comparator = (aEl, bEl) => {
        const d = byDisplay(aEl) - byDisplay(bEl);
        if (d !== 0) return d;

        if (currentSort === 'title_asc') return cmpText(aEl.dataset.title, bEl.dataset.title);
        if (currentSort === 'title_desc') return cmpText(bEl.dataset.title, aEl.dataset.title);

        if (currentSort === 'composer_asc') return cmpText(aEl.dataset.composer, bEl.dataset.composer);
        if (currentSort === 'composer_desc') return cmpText(bEl.dataset.composer, aEl.dataset.composer);

        if (currentSort === 'difficulty_asc') return cmpNum(aEl.dataset.difficultyRank, bEl.dataset.difficultyRank);
        if (currentSort === 'difficulty_desc') return cmpNum(bEl.dataset.difficultyRank, aEl.dataset.difficultyRank);

        if (currentSort === 'price_asc') return cmpNum(aEl.dataset.price, bEl.dataset.price);
        if (currentSort === 'price_desc') return cmpNum(bEl.dataset.price, aEl.dataset.price);

        return 0;
    };

    nodes.sort(comparator);
    nodes.forEach(n => grid.appendChild(n));
}

// Filter catalog by category
function filterBy(category, evt) {
    currentFilter = category;

    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.classList.remove('active');
    });

    if (evt && evt.target) {
        evt.target.classList.add('active');
    }

    const items = document.querySelectorAll('.catalog-item');
    items.forEach(item => {
        const itemCategory = item.getAttribute('data-category') || '';
        if (category === 'all' || itemCategory.includes(category)) {
            item.style.display = 'flex';
        } else {
            item.style.display = 'none';
        }
    });

    sortCatalog();

    // Show/hide a no-results message WITHOUT deleting the items
    const grid = document.getElementById('catalog-grid');
    if (!grid) return;

    const visibleItems = Array.from(items).filter(item => item.style.display !== 'none');
    let noResults = grid.querySelector('.no-results');

    if (visibleItems.length === 0) {
        if (!noResults) {
            noResults = document.createElement('p');
            noResults.className = 'no-results';
            noResults.textContent = 'No pieces found in this category.';
            grid.appendChild(noResults);
        }
    } else {
        if (noResults) noResults.remove();
    }
}

// Search catalog
function searchCatalog() {
    const sb = document.getElementById('search-bar');
    if (!sb) return;

    const searchTerm = normalizeSearchText(sb.value);
    const items = document.querySelectorAll('.catalog-item');
    let visibleCount = 0;

    items.forEach(item => {
        const searchData = item.getAttribute('data-search') || '';
        if (searchData.includes(searchTerm)) {
            item.style.display = 'flex';
            visibleCount++;
        } else {
            item.style.display = 'none';
        }
    });

    const grid = document.getElementById('catalog-grid');
    if (!grid) return;

    const existing = grid.querySelector('.no-results');

    if (visibleCount === 0 && searchTerm !== '') {
        if (!existing) {
            const msg = document.createElement('p');
            msg.className = 'no-results';
            msg.textContent = `No pieces found matching "${sb.value}". Try a different search term.`;
            grid.appendChild(msg);
        }
    } else {
        if (existing) existing.remove();
    }

    sortCatalog();
}

// Fallback image handler for live previews
document.addEventListener('error', function (event) {
    const target = event.target;
    if (target.classList && target.classList.contains('live-preview')) {
        const isMp3 = (target.src || '').includes('mp3_logo');
        target.src = isMp3 ? 'img/mp3_logo.png' : 'img/sheet.png';
        if (target.nextElementSibling) {
            target.nextElementSibling.textContent = isMp3 ? 'MP3 audio file' : 'Preview unavailable (open listing to view score)';
        }
    }
}, true);

