/**
 * MP3 Downloads page — storefront search/filter mirrors the sheet-music catalog:
 * search bar + obvious style buttons, combined, with ?filter= / ?q= deep links.
 * Data: mp3-downloads-data.json
 * Checkout: Stripe Payment Link → audio-purchase.html?track=…&paid=true
 *
 * Teacher / lesson-prep unlock: mp3-downloads.html?dev=… (sessionStorage; convenience only).
 */

(function () {
	'use strict';

	const MP3_DEV_SECRET = 'RichardHeartIsTheGoat';

	function mp3DevUnlocked() {
		try {
			const p = new URLSearchParams(window.location.search);
			if (p.get('dev') === MP3_DEV_SECRET) {
				try {
					sessionStorage.setItem('mp3_dev', '1');
				} catch (e) {
					/* ignore */
				}
				return true;
			}
			return sessionStorage.getItem('mp3_dev') === '1';
		} catch (e) {
			return false;
		}
	}

	const teacherMode = mp3DevUnlocked();

	const DATA_URL = 'mp3-downloads-data.json';
	const grid = document.getElementById('mp3-grid');
	const statusEl = document.getElementById('mp3-status');
	const searchInput = document.getElementById('mp3-search');
	const sortSelect = document.getElementById('mp3-sort');
	const filterBtns = document.querySelectorAll('.mp3-filter-btn');

	let tracks = [];
	let activeFilter = 'all';
	let currentSort = 'default';

	/** Same normalization as catalog.js — "hip-hop" matches "hip hop". */
	function normalizeSearchText(str) {
		return String(str || '')
			.toLowerCase()
			.replace(/[#♯]/g, ' sharp')
			.replace(/[♭]/g, ' flat')
			.replace(/[-_/.,()+]/g, ' ')
			.replace(/\s+/g, ' ')
			.trim();
	}

	const FILTER_NEEDLES = {
		all: [],
		rap: ['rap', 'hip hop', 'hiphop'],
		jazz: ['jazz'],
		bossa: ['bossa'],
		reggae: ['reggae'],
		ska: ['ska'],
		world: ['world'],
		choro: ['choro'],
		african: ['african'],
	};

	const URL_ALIASES = {
		'hip-hop': 'rap',
		hiphop: 'rap',
		'hip hop': 'rap',
		'bossa-nova': 'bossa',
		'bossa nova': 'bossa',
		'traditional-african': 'african',
	};

	function escapeHtml(s) {
		return String(s || '')
			.replace(/&/g, '&amp;')
			.replace(/</g, '&lt;')
			.replace(/>/g, '&gt;')
			.replace(/"/g, '&quot;');
	}

	function paymentLinkConfigured(url) {
		return !!(url && !String(url).includes('YOUR_PAYMENT_LINK'));
	}

	function purchaseHref(item) {
		const ds = item.direct_sale || {};
		if (ds.purchase_page) return ds.purchase_page;
		return 'audio-purchase.html?track=' + encodeURIComponent(item.id) + '&from=mp3';
	}

	function itemSearchBlob(item) {
		return normalizeSearchText(
			[
				item.title,
				item.composer,
				item.id,
				item.collection || '',
				(item.tags || []).join(' '),
				item.key || '',
				item.bpm != null ? String(item.bpm) : '',
			].join(' ')
		);
	}

	function itemFilterBlob(item) {
		return normalizeSearchText(
			[item.collection || '', (item.tags || []).join(' '), item.title, item.id].join(' ')
		);
	}

	function resolveFilter(raw) {
		const n = normalizeSearchText(raw);
		if (!n || n === 'all') return 'all';
		if (URL_ALIASES[n]) return URL_ALIASES[n];
		if (FILTER_NEEDLES[n]) return n;
		return n;
	}

	function matchesFilter(item) {
		if (activeFilter === 'all') return true;
		const blob = itemFilterBlob(item);
		const needles = FILTER_NEEDLES[activeFilter] || [activeFilter];
		return needles.some(function (n) {
			return blob.indexOf(n) !== -1;
		});
	}

	function matchesSearch(item, q) {
		if (!q) return true;
		const hay = itemSearchBlob(item);
		const words = normalizeSearchText(q).split(' ').filter(Boolean);
		return words.every(function (w) {
			return hay.indexOf(w) !== -1;
		});
	}

	function sortTracks(list) {
		const out = list.slice();
		function titleOf(t) {
			return normalizeSearchText(t.title || t.id);
		}
		if (currentSort === 'title_asc') {
			out.sort(function (a, b) {
				return titleOf(a).localeCompare(titleOf(b));
			});
		} else if (currentSort === 'title_desc') {
			out.sort(function (a, b) {
				return titleOf(b).localeCompare(titleOf(a));
			});
		} else if (currentSort === 'key_asc') {
			out.sort(function (a, b) {
				return normalizeSearchText(a.key || 'zzz').localeCompare(
					normalizeSearchText(b.key || 'zzz')
				);
			});
		} else if (currentSort === 'bpm_asc') {
			out.sort(function (a, b) {
				const av = a.bpm != null ? Number(a.bpm) : 9999;
				const bv = b.bpm != null ? Number(b.bpm) : 9999;
				return av - bv;
			});
		}
		return out;
	}

	function render(list) {
		if (!grid) return;
		if (!list.length) {
			grid.innerHTML =
				'<p class="mp3-empty">No tracks match. Try All Tracks, or a different keyword.</p>';
			return;
		}

		grid.innerHTML = list
			.map(function (item) {
				const ds = item.direct_sale || {};
				const preview = ds.preview_audio || '';
				const buyUrl = ds.stripe_payment_link || '';
				const canBuy = paymentLinkConfigured(buyUrl);
				const page = purchaseHref(item);
				const metaBits = [];
				if (item.collection) metaBits.push(String(item.collection));
				if (item.bpm) metaBits.push(item.bpm + ' BPM');
				if (item.key) metaBits.push(item.key);
				if (item.tags && item.tags.length) {
					metaBits.push(
						item.tags
							.filter(function (t) {
								return t !== 'mp3' && t !== item.collection;
							})
							.join(' · ')
					);
				}

				let buyHtml;
				const full = ds.full_audio || '';
				if (teacherMode && full) {
					buyHtml =
						'<a class="mp3-btn mp3-btn-buy" href="' +
						escapeHtml(full) +
						'" download>Download full (teacher)</a>';
				} else if (canBuy) {
					buyHtml =
						'<a class="mp3-btn mp3-btn-buy" href="' +
						escapeHtml(buyUrl) +
						'">Buy with Stripe — ' +
						escapeHtml(item.price || '') +
						'</a>';
				} else {
					buyHtml =
						'<a class="mp3-btn mp3-btn-buy mp3-btn-soft" href="' +
						escapeHtml(page) +
						'">Preview / buy page — ' +
						escapeHtml(item.price || '') +
						'</a>' +
						'<p class="mp3-stripe-hint">Stripe Payment Link not set yet — open the purchase page to test previews.</p>';
				}

				const trackPage =
					teacherMode
						? page + (page.indexOf('?') >= 0 ? '&' : '?') + 'dev=' + encodeURIComponent(MP3_DEV_SECRET)
						: page;

				return (
					'<article class="mp3-card" data-id="' +
					escapeHtml(item.id) +
					'">' +
					'<div class="mp3-card-art" aria-hidden="true">' +
					'<img src="img/mp3_logo.png" alt="">' +
					'</div>' +
					'<div class="mp3-card-body">' +
					'<h2 class="mp3-card-title">' +
					escapeHtml(item.title || item.id) +
					'</h2>' +
					'<p class="mp3-card-meta">' +
					escapeHtml(metaBits.join(' · ') || item.composer || '') +
					'</p>' +
					(preview
						? '<div class="mp3-preview-label">30s preview</div>' +
						  '<audio controls preload="none" src="' +
						  escapeHtml(preview) +
						  '"></audio>'
						: '<p class="mp3-stripe-hint">Preview file missing.</p>') +
					'<div class="mp3-card-actions">' +
					buyHtml +
					'<a class="mp3-btn mp3-btn-ghost" href="' +
					escapeHtml(trackPage) +
					'">Track page</a>' +
					'</div>' +
					'</div>' +
					'</article>'
				);
			})
			.join('');
	}

	function writeUrl() {
		try {
			const params = new URLSearchParams(window.location.search);
			if (activeFilter && activeFilter !== 'all') params.set('filter', activeFilter);
			else params.delete('filter');
			const q = searchInput && searchInput.value ? searchInput.value.trim() : '';
			if (q) params.set('q', q);
			else params.delete('q');
			const qs = params.toString();
			const next = window.location.pathname + (qs ? '?' + qs : '') + window.location.hash;
			window.history.replaceState({}, '', next);
		} catch (e) {
			/* ignore */
		}
	}

	function applyFilter() {
		const q = searchInput && searchInput.value ? searchInput.value : '';
		const filtered = sortTracks(
			tracks.filter(function (t) {
				return matchesFilter(t) && matchesSearch(t, q);
			})
		);
		if (statusEl) {
			const bits = [
				filtered.length + ' track' + (filtered.length === 1 ? '' : 's'),
			];
			if (teacherMode) bits.push('teacher unlock');
			if (activeFilter !== 'all') bits.push(activeFilter);
			if (q.trim()) bits.push('matching “' + q.trim() + '”');
			statusEl.textContent = bits.join(' · ');
		}
		render(filtered);
		writeUrl();
	}

	function setActiveButton(filterKey) {
		filterBtns.forEach(function (btn) {
			const key = resolveFilter(btn.getAttribute('data-filter') || 'all');
			btn.classList.toggle('active', key === filterKey);
		});
	}

	function readUrl() {
		try {
			const params = new URLSearchParams(window.location.search);
			const f = params.get('filter') || params.get('tag');
			if (f) {
				activeFilter = resolveFilter(f);
				setActiveButton(activeFilter);
			}
			const q = params.get('q') || params.get('search');
			if (q && searchInput) searchInput.value = q;
		} catch (e) {
			/* ignore */
		}
	}

	if (searchInput) {
		searchInput.addEventListener('input', applyFilter);
	}

	if (sortSelect) {
		sortSelect.addEventListener('change', function () {
			currentSort = sortSelect.value || 'default';
			applyFilter();
		});
	}

	filterBtns.forEach(function (btn) {
		btn.addEventListener('click', function () {
			activeFilter = resolveFilter(btn.getAttribute('data-filter') || 'all');
			setActiveButton(activeFilter);
			applyFilter();
		});
	});

	readUrl();

	fetch(DATA_URL)
		.then(function (r) {
			if (!r.ok) throw new Error('Could not load ' + DATA_URL);
			return r.json();
		})
		.then(function (data) {
			tracks = Array.isArray(data) ? data : [];
			applyFilter();
		})
		.catch(function (err) {
			if (grid) {
				grid.innerHTML =
					'<p class="mp3-empty mp3-error">' +
					escapeHtml(err.message || String(err)) +
					'</p>';
			}
			if (statusEl) statusEl.textContent = '';
		});
})();
