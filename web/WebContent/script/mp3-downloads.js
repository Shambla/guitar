/**
 * MP3 Downloads page — separate storefront from sheet-music catalog.
 * Data: mp3-downloads-data.json
 * Checkout: Stripe Payment Link → audio-purchase.html?track=…&paid=true
 * See DIRECT_AUDIO_SALES.md
 */

(function () {
	'use strict';

	const DATA_URL = 'mp3-downloads-data.json';
	const grid = document.getElementById('mp3-grid');
	const statusEl = document.getElementById('mp3-status');
	const searchInput = document.getElementById('mp3-search');

	let tracks = [];

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

	function matchesSearch(item, q) {
		if (!q) return true;
		const hay = [
			item.title,
			item.composer,
			item.id,
			(item.tags || []).join(' '),
			item.key || '',
			item.bpm != null ? String(item.bpm) : '',
		]
			.join(' ')
			.toLowerCase();
		return hay.indexOf(q) !== -1;
	}

	function render(list) {
		if (!grid) return;
		if (!list.length) {
			grid.innerHTML =
				'<p class="mp3-empty">No tracks match your search.</p>';
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
				if (item.bpm) metaBits.push(item.bpm + ' BPM');
				if (item.key) metaBits.push(item.key);
				if (item.tags && item.tags.length) {
					metaBits.push(item.tags.filter(function (t) {
						return t !== 'mp3';
					}).join(' · '));
				}

				let buyHtml;
				if (canBuy) {
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
					escapeHtml(page) +
					'">Track page</a>' +
					'</div>' +
					'</div>' +
					'</article>'
				);
			})
			.join('');
	}

	function applyFilter() {
		const q = (searchInput && searchInput.value ? searchInput.value : '')
			.trim()
			.toLowerCase();
		const filtered = tracks.filter(function (t) {
			return matchesSearch(t, q);
		});
		if (statusEl) {
			statusEl.textContent =
				filtered.length +
				' track' +
				(filtered.length === 1 ? '' : 's') +
				(q ? ' matching “' + q + '”' : '');
		}
		render(filtered);
	}

	if (searchInput) {
		searchInput.addEventListener('input', applyFilter);
	}

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
