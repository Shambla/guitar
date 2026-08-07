// Catalog Page JavaScript

let catalogData = [];
let currentFilter = 'all';
let currentSort = 'default';

/**
 * Deep-link filters (e.g. ?filter=rap) are NOT live on production yet.
 * Set CATALOG_DEEP_LINKS_LIVE = true when ready for YouTube / public share URLs.
 * Until then, practice locally with: catalog.html?catalog_preview=1&filter=rap
 */
const CATALOG_DEEP_LINKS_LIVE = false;

/**
 * Direct MP3 sales (Stripe + hosted preview/full files). OFF by default so catalog
 * behavior stays unchanged until you set a real Payment Link and flip this to true.
 * Practice UI: catalog.html?catalog_preview=1  (shows "Listen / Buy" → audio-purchase.html)
 * See DIRECT_AUDIO_SALES.md
 */
const DIRECT_AUDIO_SALES_LIVE = false;

function catalogPreviewModeEnabled() {
    try {
        return new URLSearchParams(window.location.search).get('catalog_preview') === '1';
    } catch (e) {
        return false;
    }
}

function escapeHtmlAttr(s) {
    return String(s || '')
        .replace(/&/g, '&amp;')
        .replace(/"/g, '&quot;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;');
}

function paymentLinkConfigured(url) {
    return !!(url && !String(url).includes('YOUR_PAYMENT_LINK'));
}

function getDirectSale(item) {
    if (!item || !item.direct_sale || item.direct_sale.enabled === false) return null;
    return item.direct_sale;
}

/** Build CTA HTML for a catalog card — sheet music unchanged unless direct_sale applies. */
function buildCatalogCtaHtml(item) {
    const ds = getDirectSale(item);
    const smd = (item.sheet_music_direct_url || '').trim();
    const purchasePage = ds && (ds.purchase_page || `audio-purchase.html?track=${encodeURIComponent(item.id)}`);
    const showDirectUi =
        ds &&
        (DIRECT_AUDIO_SALES_LIVE || catalogPreviewModeEnabled()) &&
        purchasePage;

    if (showDirectUi) {
        const buyReady = DIRECT_AUDIO_SALES_LIVE && paymentLinkConfigured(ds.stripe_payment_link);
        let html =
            `<a class="link-button" href="${escapeHtmlAttr(purchasePage)}">Listen / Buy (direct)</a>`;
        if (smd) {
            html +=
                `<a class="link-button" href="${escapeHtmlAttr(smd)}" target="_blank" rel="noopener" style="margin-top:8px;opacity:0.85;font-size:0.9em;">Sheet Music Direct</a>`;
        }
        if (!buyReady && DIRECT_AUDIO_SALES_LIVE) {
            html +=
                `<p style="font-size:12px;margin:8px 0 0;opacity:0.7;">Stripe Payment Link not configured yet.</p>`;
        }
        return html;
    }

    // Default: existing sheet-music / listing behavior
    if (smd) {
        return `<a class="link-button" href="${escapeHtmlAttr(smd)}" target="_blank" rel="noopener">Open Listing</a>`;
    }

    // Direct-sale track without SMD and sales not live yet — soft placeholder (no broken link)
    if (ds && purchasePage) {
        return `<a class="link-button" href="${escapeHtmlAttr(purchasePage)}" style="opacity:0.9;">Preview page</a>`;
    }

    return `<span class="link-button" style="opacity:0.5;cursor:default;">Listing coming soon</span>`;
}

function catalogDeepLinksEnabled() {
    if (CATALOG_DEEP_LINKS_LIVE) return true;
    try {
        return new URLSearchParams(window.location.search).get('catalog_preview') === '1';
    } catch (e) {
        return false;
    }
}

/** Optional tags[] on catalog items — separate from category (e.g. tags: ["mp3","rap","hip hop"]). */
function getItemTags(item) {
    if (!item || !Array.isArray(item.tags)) return [];
    return item.tags
        .map((t) => (t || '').toString().trim())
        .filter(Boolean);
}

function getItemCategoriesList(item) {
    const cat = item && item.category;
    if (Array.isArray(cat)) {
        return cat.map((c) => (c || '').toString().trim()).filter(Boolean);
    }
    if (cat) return [(cat || '').toString().trim()];
    return [];
}

/** Text blob used by filterBy / data-category (category + tags + difficulty). */
function buildItemFilterText(item) {
    const parts = [
        ...getItemCategoriesList(item),
        ...getItemTags(item),
        (item.difficulty || '').toString().toLowerCase(),
    ];
    return normalizeSearchText(parts.join(' '));
}

function formatCategoryTagLabel(item) {
    const cats = getItemCategoriesList(item);
    const tags = getItemTags(item);
    const labelParts = [...cats];
    tags.forEach((t) => {
        if (!labelParts.some((c) => c.toLowerCase() === t.toLowerCase())) {
            labelParts.push(t);
        }
    });
    return labelParts.join(' · ') || '';
}

function isMp3AudioItem(item) {
    const cats = getItemCategoriesList(item).map((c) => c.toLowerCase());
    if (cats.some((c) => c.includes('mp3'))) return true;
    return getItemTags(item).some((t) => t.toLowerCase() === 'mp3');
}

/** Map short URL aliases → filter substring used by filterBy. */
function resolveDeepLinkFilter(raw) {
    const key = normalizeSearchText(raw).replace(/\s+/g, '-');
    const aliases = {
        rap: 'rap',
        'hip-hop': 'hip hop',
        hiphop: 'hip hop',
        'hip-hop-backing': 'hip hop',
        mp3: 'mp3',
        'mp3-audio': 'mp3',
        'rap-hip-hop': 'rap',
    };
    if (aliases[key]) return aliases[key];
    return normalizeSearchText(raw);
}

function applyDeepLinkFilterFromUrl() {
    if (!catalogDeepLinksEnabled()) return;

    let params;
    try {
        params = new URLSearchParams(window.location.search);
    } catch (e) {
        return;
    }

    const raw = params.get('filter') || params.get('tag');
    if (!raw) return;

    const filterKey = resolveDeepLinkFilter(raw);
    if (!filterKey || filterKey === 'all') return;

    filterBy(filterKey, null);

    // Highlight a matching filter button if present (including commented-out ones once enabled)
    document.querySelectorAll('.filter-btn').forEach((btn) => {
        const onclick = btn.getAttribute('onclick') || '';
        const match = onclick.match(/filterBy\(['"]([^'"]+)['"]/);
        if (match && normalizeSearchText(match[1]).includes(filterKey)) {
            btn.classList.add('active');
        } else if (onclick.includes("filterBy('all'") || onclick.includes('filterBy("all"')) {
            btn.classList.remove('active');
        }
    });
}

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
            applyDeepLinkFilterFromUrl();
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

            const filterText = buildItemFilterText(item);
            itemDiv.setAttribute('data-category', filterText);
            itemDiv.setAttribute('data-title', normalizeSearchText(item.title));
            itemDiv.setAttribute('data-composer', normalizeSearchText(item.composer));
            itemDiv.setAttribute('data-difficulty-rank', String(difficultyRank(item.difficulty)));
            itemDiv.setAttribute('data-price', String(parsePriceToNumber(item.price)));

            itemDiv.setAttribute(
                'data-search',
                normalizeSearchText(
                    `${item.title} ${item.composer} ${getItemCategoriesList(item).join(' ')} ${getItemTags(item).join(' ')} ${item.difficulty}`
                )
            );

            const difficultyClass = (item.difficulty || '').toString().toLowerCase();
            const categoryTagLabel = formatCategoryTagLabel(item);

            // Base path from current page location
            const basePath = window.location.pathname.substring(0, window.location.pathname.lastIndexOf('/') + 1);
            const isMp3Audio = isMp3AudioItem(item);
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
            const difficultyHtml = isMp3Audio ? '' : `<p class="difficulty ${difficultyClass}">${item.difficulty}</p>`;
            itemDiv.innerHTML = `
                <div class="preview-screen">
                    <img class="live-preview" src="${previewImageSrc}" alt="${imgAlt}"
                         onerror="handleImageError(this, '${previewImageSrc}', '${basePath}');">
                    <span class="preview-caption">${captionText}</span>
                </div>
                <div class="composer">${item.composer}</div>
                <h3>${item.title}</h3>
                <span class="category-tag">${categoryTagLabel}</span>
                ${difficultyHtml}
                <p class="price">${item.price}</p>
                ${buildCatalogCtaHtml(item)}
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

// Filter catalog by category or tag (substring match on data-category)
function filterBy(category, evt) {
    const needle = normalizeSearchText(category);
    currentFilter = needle || 'all';

    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.classList.remove('active');
    });

    if (evt && evt.target) {
        evt.target.classList.add('active');
    }

    const items = document.querySelectorAll('.catalog-item');
    items.forEach(item => {
        const itemCategory = normalizeSearchText(item.getAttribute('data-category') || '');
        if (currentFilter === 'all' || itemCategory.includes(currentFilter)) {
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

