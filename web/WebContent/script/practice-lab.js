/**
 * 2026-11-02 — Improv Practice is the first screen of mp3-downloads.html.
 * The same markup still lives on practice-lab.html. Reads mp3-downloads-data.json.
 * Scrolling past this screen reaches the old Browse MP3s list.
 *
 * A sell-side store list made people scroll, press play, then scroll again
 * to a scale PDF. This page keeps one track and the matching chart together.
 *
 * Key pages for "12 Keys Beautiful & Print Friendly.pdf" were read off the
 * page titles (circle of fifths, major with its relative minor). Pages 13–24
 * repeat 1–12, so this lab uses 1–12.
 *
 * Harmonic-minor pages are only auto-jumped when a page title actually read
 * as that key. The rest say so and leave the arrows in charge.
 *
 * Rebrand stays a comment: the live page is still "MP3 Downloads". This lab
 * is titled "Free improvisation practice" so the free chart and preview lead,
 * and buying the MP3 is the way to keep the jam.
 */
(function () {
	'use strict';

	var DATA_URL = 'mp3-downloads-data.json';
	var BEAUTY_URL = 'img/12%20Keys%20Beautiful%20%26%20Print%20Friendly.pdf';
	var HARMONIC_URL = 'img/All%2012%20Harmonic%20minor%20Published.pdf';
	var DEV_SECRET = 'RichardHeartIsTheGoat';

	var GENRE_LABELS = {
		ambient: 'Ambient',
		country: 'Country',
		egypt: 'Egypt',
		reggae: 'Reggae',
		rap: 'Rap / hip hop',
		asian: 'Asian',
		'60s-rock': '60s rock',
		'shoegaze-reggae': 'Shoegaze reggae',
		bossa: 'Bossa nova',
		irish: 'Irish',
		'funk-disco': 'Funk / disco',
		synth: 'Synth',
		'lo-fi': 'Lo-fi',
		metal: 'Metal',
		'chill-indian': 'Chill Indian',
		'edm-metal': 'EDM metal',
		lydian: 'Lydian',
		calypso: 'Calypso',
		suno: 'Suno backing',
	};

	/* page: PDF page. pairs: [root, mode] that live on that chart. */
	var BEAUTY_PAGES = [
		{ page: 1, label: 'C major / A minor', pairs: [['C', 'major'], ['A', 'minor']] },
		{ page: 2, label: 'G major / E minor', pairs: [['G', 'major'], ['E', 'minor']] },
		{ page: 3, label: 'D major / B minor', pairs: [['D', 'major'], ['B', 'minor']] },
		{ page: 4, label: 'A major / F# minor', pairs: [['A', 'major'], ['F#', 'minor']] },
		{ page: 5, label: 'E major / C# minor', pairs: [['E', 'major'], ['C#', 'minor']] },
		{ page: 6, label: 'B major / G# minor', pairs: [['B', 'major'], ['G#', 'minor']] },
		{
			page: 7,
			label: 'F# major / D# minor (also Gb major / Eb minor)',
			pairs: [['F#', 'major'], ['Gb', 'major'], ['D#', 'minor'], ['Eb', 'minor']],
		},
		{
			page: 8,
			label: 'C# major / A# minor (also Db major / Bb minor)',
			pairs: [['C#', 'major'], ['Db', 'major'], ['A#', 'minor'], ['Bb', 'minor']],
		},
		{ page: 9, label: 'Ab major / F minor', pairs: [['Ab', 'major'], ['G#', 'major'], ['F', 'minor']] },
		{ page: 10, label: 'Eb major / C minor', pairs: [['Eb', 'major'], ['D#', 'major'], ['C', 'minor']] },
		{ page: 11, label: 'Bb major / G minor', pairs: [['Bb', 'major'], ['A#', 'major'], ['G', 'minor']] },
		{ page: 12, label: 'F major / D minor', pairs: [['F', 'major'], ['D', 'minor']] },
	];

	/*
	 * Harmonic PDF image pages. sure:true means that page's title actually read
	 * as the key. sure:false is only the circle-of-fifths seat between two sure
	 * neighbors (B then G# → F# and C#). F harmonic minor and C harmonic minor
	 * are left unmapped so a bad guess doesn't open the wrong chart.
	 */
	var HARMONIC_PAGES = [
		{ page: 1, roots: ['A'], sure: true },
		{ page: 3, roots: ['B'], sure: true },
		{ page: 4, roots: ['F#'], sure: false },
		{ page: 5, roots: ['C#'], sure: false },
		{ page: 6, roots: ['G#', 'Ab'], sure: true },
		{ page: 7, roots: ['Eb', 'D#'], sure: true },
		{ page: 8, roots: ['A#', 'Bb'], sure: true },
		{ page: 9, roots: ['D'], sure: true },
		{ page: 10, roots: ['G'], sure: true },
		{ page: 12, roots: ['E'], sure: true },
	];

	var keySelect = document.getElementById('lab-key');
	var genreSelect = document.getElementById('lab-genre');
	var nextBtn = document.getElementById('lab-next');
	var prevBtn = document.getElementById('lab-prev');
	var titleEl = document.getElementById('lab-title');
	var blurbEl = document.getElementById('lab-blurb');
	var badgesEl = document.getElementById('lab-badges');
	var actionsEl = document.getElementById('lab-actions');
	var audioEl = document.getElementById('lab-audio');
	var emptyEl = document.getElementById('lab-empty');
	var chartLiveEl = document.getElementById('lab-chart-live');
	var chartTitle = document.getElementById('lab-chart-title');
	var chartNote = document.getElementById('lab-chart-note');
	var pdfLabel = document.getElementById('lab-pdf-label');
	var pdfPrev = document.getElementById('lab-pdf-prev');
	var pdfNext = document.getElementById('lab-pdf-next');
	var pdfDownload = document.getElementById('lab-pdf-download');
	var pdfCanvas = document.getElementById('lab-pdf-canvas');

	var tracks = [];
	var visible = [];
	var currentIndex = 0;
	var teacherMode = false;

	var pdfDocs = {};
	var pdfState = { which: 'beauty', page: 1, rendering: false, pending: null };

	function teacherUnlocked() {
		try {
			var p = new URLSearchParams(window.location.search);
			if (p.get('dev') === DEV_SECRET) {
				try { sessionStorage.setItem('mp3_dev', '1'); } catch (e) { /* ignore */ }
				return true;
			}
			return sessionStorage.getItem('mp3_dev') === '1';
		} catch (e) {
			return false;
		}
	}

	function escapeHtml(s) {
		return String(s || '')
			.replace(/&/g, '&amp;')
			.replace(/</g, '&lt;')
			.replace(/>/g, '&gt;')
			.replace(/"/g, '&quot;');
	}

	function canonRoot(token) {
		var t = String(token || '').trim();
		t = t.replace(/^[^A-Ga-g]+/, '');
		t = t.replace(/sharp/ig, '#').replace(/flat/ig, 'b');
		t = t.replace(/\s+/g, '');
		t = t.replace('♯', '#').replace('♭', 'b');
		var m = t.match(/^([A-Ga-g])(#|b)?/);
		if (!m) return '';
		var name = m[1].toUpperCase() + (m[2] || '');
		if (name === 'Cb') return 'B';
		if (name === 'Fb') return 'E';
		if (name === 'E#') return 'F';
		if (name === 'B#') return 'C';
		return name;
	}

	function parseKeyText(text) {
		var raw = String(text || '').replace(/[–—]/g, ' ').trim();
		if (!raw) return null;
		/* Parenthetical asides ("F minor (C Phrygian)") stay out of the label. */
		var main = raw.replace(/\([^)]*\)/g, ' ');
		var modeMatch = main.match(/(harmonic\s+minor|harmonic|dorian|phrygian|lydian|mixolydian|pentatonic|penta|minor|major)/i);
		if (!modeMatch) return null;
		var modeWord = modeMatch[1].toLowerCase().replace(/\s+/g, ' ');
		var mode = 'major';
		if (modeWord.indexOf('harmonic') !== -1) mode = 'harmonic';
		else if (modeWord === 'dorian') mode = 'dorian';
		else if (modeWord === 'phrygian') mode = 'phrygian';
		else if (modeWord === 'lydian') mode = 'lydian';
		else if (modeWord === 'mixolydian') mode = 'mixolydian';
		else if (modeWord.indexOf('penta') !== -1) mode = 'pentatonic';
		else if (modeWord === 'minor') mode = 'minor';
		/* Root is a standalone note next to the mode, not a letter inside another word. */
		var before = main.slice(0, modeMatch.index);
		var roots = before.match(/(?:^|[^A-Za-z])([A-Ga-g])\s*(#|♯|b|♭|sharp|flat)?/g);
		if (!roots || !roots.length) return null;
		var root = canonRoot(roots[roots.length - 1]);
		if (!root) return null;
		var labelMode = {
			major: 'major',
			minor: 'minor',
			harmonic: 'harmonic minor',
			dorian: 'dorian',
			phrygian: 'phrygian',
			lydian: 'lydian',
			mixolydian: 'mixolydian',
			pentatonic: 'pentatonic',
		}[mode];
		return {
			root: root,
			mode: mode,
			label: root + ' ' + labelMode,
		};
	}

	function keyOf(item) {
		/* The title (and the file id) win over the stored key field.
		   Several tracks are named for a sharp or a mode while `key` still says "C minor". */
		return parseKeyText(item.title || '')
			|| parseKeyText(String(item.id || '').replace(/-/g, ' '))
			|| parseKeyText(item.key || '');
	}

	function genreOf(item) {
		var c = item.collection || '';
		if (c && GENRE_LABELS[c]) return c;
		var tags = item.tags || [];
		for (var i = 0; i < tags.length; i++) {
			var t = String(tags[i]).toLowerCase();
			if (t === 'hip hop' || t === 'hip-hop') return 'rap';
			if (GENRE_LABELS[t]) return t;
		}
		return c || 'other';
	}

	function genreLabel(id) {
		return GENRE_LABELS[id] || id;
	}

	function sameKey(a, b) {
		return a && b && a.root === b.root && a.mode === b.mode;
	}

	function findBeauty(root, mode) {
		for (var i = 0; i < BEAUTY_PAGES.length; i++) {
			var page = BEAUTY_PAGES[i];
			for (var j = 0; j < page.pairs.length; j++) {
				if (page.pairs[j][0] === root && page.pairs[j][1] === mode) return page;
			}
		}
		return null;
	}

	function findHarmonic(root) {
		for (var i = 0; i < HARMONIC_PAGES.length; i++) {
			if (HARMONIC_PAGES[i].roots.indexOf(root) !== -1) return HARMONIC_PAGES[i];
		}
		return null;
	}

	function chartFor(key) {
		if (!key) {
			return {
				which: 'beauty',
				page: 1,
				title: 'Scale chart',
				note: 'This track’s name doesn’t include a key, so the chart stays on C major / A minor. Use the page arrows if you know the key.',
			};
		}
		if (key.mode === 'harmonic') {
			var h = findHarmonic(key.root);
			if (!h) {
				return {
					which: 'harmonic',
					page: 1,
					title: key.label,
					note: 'No harmonic-minor page is mapped for ' + key.label + ' yet. Start at page 1 and nudge with the arrows.',
				};
			}
			return {
				which: 'harmonic',
				page: h.page,
				title: key.label,
				note: h.sure
					? 'Harmonic minor chart, page ' + h.page + ', for ' + key.label + '.'
					: 'Best guess: harmonic minor page ' + h.page + ' for ' + key.label + '. The neon title on that page was hard to read — arrows nudge it.',
			};
		}
		var modeForChart = key.mode === 'minor' || key.mode === 'major' ? key.mode : 'major';
		if (key.mode === 'dorian' || key.mode === 'phrygian') modeForChart = 'minor';
		var page = findBeauty(key.root, modeForChart);
		if (!page && modeForChart === 'minor') page = findBeauty(key.root, 'major');
		if (!page) {
			return {
				which: 'beauty',
				page: 1,
				title: key.label,
				note: 'No chart page is mapped for ' + key.label + ' yet.',
			};
		}
		var extra = '';
		if (key.mode === 'lydian' || key.mode === 'pentatonic' || key.mode === 'dorian' || key.mode === 'phrygian' || key.mode === 'mixolydian') {
			extra = ' ' + key.label + ' is not its own page in this PDF, so this is the closest major/minor chart (' + page.label + ').';
		} else {
			extra = ' This page is ' + page.label + '.';
		}
		return {
			which: 'beauty',
			page: page.page,
			title: key.label,
			note: 'Free chart for ' + key.label + '.' + extra,
		};
	}

	function paymentReady(url) {
		return !!(url && String(url).indexOf('YOUR_PAYMENT_LINK') === -1);
	}

	function selectionOn() {
		return !!((keySelect && keySelect.value) || (genreSelect && genreSelect.value));
	}

	function showIdle() {
		visible = [];
		titleEl.textContent = 'No track yet';
		blurbEl.textContent = '';
		badgesEl.innerHTML = '';
		actionsEl.innerHTML = '';
		audioEl.removeAttribute('src');
		if (emptyEl) {
			emptyEl.hidden = false;
			var idleCopy = emptyEl.querySelector('p');
			if (idleCopy) idleCopy.textContent = 'Select a key or genre';
		}
		if (chartLiveEl) chartLiveEl.hidden = true;
		if (nextBtn) nextBtn.disabled = true;
		if (prevBtn) prevBtn.disabled = true;
	}

	function showTrack(index) {
		if (!selectionOn()) {
			showIdle();
			return;
		}
		if (emptyEl) emptyEl.hidden = true;
		if (chartLiveEl) chartLiveEl.hidden = false;
		if (!visible.length) {
			titleEl.textContent = 'Nothing matches';
			blurbEl.textContent = 'Try another key or genre.';
			badgesEl.innerHTML = '';
			actionsEl.innerHTML = '';
			audioEl.removeAttribute('src');
			if (emptyEl) {
				emptyEl.hidden = false;
				var emptyCopy = emptyEl.querySelector('p');
				if (emptyCopy) emptyCopy.textContent = 'Nothing matches that key or genre';
			}
			if (chartLiveEl) chartLiveEl.hidden = true;
			if (nextBtn) nextBtn.disabled = true;
			if (prevBtn) prevBtn.disabled = true;
			writeUrl();
			return;
		}
		var emptyCopy = emptyEl && emptyEl.querySelector('p');
		if (emptyCopy) emptyCopy.textContent = 'Select a key or genre';
		if (index < 0) index = visible.length - 1;
		if (index >= visible.length) index = 0;
		currentIndex = index;
		var item = visible[index];
		var key = keyOf(item);
		var genre = genreOf(item);
		titleEl.textContent = item.title || item.id;
		var bits = [];
		if (item.bpm) bits.push(item.bpm + ' BPM');
		if (item.composer) bits.push(item.composer);
		blurbEl.textContent = bits.join(' · ');
		badgesEl.innerHTML =
			'<span class="lab-badge">' + escapeHtml(key ? key.label : 'Key not in the name') + '</span>' +
			'<span class="lab-badge">' + escapeHtml(genreLabel(genre)) + '</span>' +
			'<span class="lab-badge">Jam ' + (index + 1) + ' of ' + visible.length + '</span>';

		var ds = item.direct_sale || {};
		var preview = ds.preview_audio || '';
		if (preview) {
			audioEl.src = preview;
		} else {
			audioEl.removeAttribute('src');
		}

		var buy = ds.stripe_payment_link || '';
		var page = ds.purchase_page || ('audio-purchase.html?track=' + encodeURIComponent(item.id) + '&from=mp3');
		var html = '';
		if (teacherMode && ds.full_audio) {
			html += '<a class="lab-buy" href="' + escapeHtml(ds.full_audio) + '" download>Download full (teacher)</a>';
		} else if (paymentReady(buy)) {
			html += '<a class="lab-buy" href="' + escapeHtml(buy) + '">Keep this track — ' + escapeHtml(item.price || '') + '</a>';
		}
		html += '<a href="' + escapeHtml(page) + '">Track page</a>';
		actionsEl.innerHTML = html;
		if (nextBtn) nextBtn.disabled = visible.length < 2;
		if (prevBtn) prevBtn.disabled = visible.length < 2;

		var chart = chartFor(key);
		chartTitle.textContent = chart.title;
		chartNote.textContent = chart.note + ' · ' + (index + 1) + ' of ' + visible.length;
		showPdf(chart.which, chart.page);
		writeUrl();
	}

	function applyFilter(keepId) {
		if (!selectionOn()) {
			showIdle();
			writeUrl();
			return;
		}
		var wantKey = keySelect.value;
		var wantGenre = genreSelect.value;
		visible = tracks.filter(function (item) {
			var key = keyOf(item);
			if (wantKey === '__none') {
				if (key) return false;
			} else if (wantKey) {
				if (!key || key.label !== wantKey) return false;
			}
			if (wantGenre && genreOf(item) !== wantGenre) return false;
			return true;
		});
		var start = 0;
		if (keepId) {
			for (var i = 0; i < visible.length; i++) {
				if (visible[i].id === keepId) { start = i; break; }
			}
		}
		showTrack(start);
	}

	function fillSelects() {
		var keys = {};
		var genres = {};
		var unknown = 0;
		tracks.forEach(function (item) {
			var key = keyOf(item);
			if (key) keys[key.label] = true;
			else unknown += 1;
			genres[genreOf(item)] = true;
		});
		var keyNames = Object.keys(keys).sort();
		keySelect.innerHTML = '<option value="">Select a key</option>' +
			(unknown ? '<option value="__none">Key not in the name (' + unknown + ')</option>' : '') +
			keyNames.map(function (name) {
				return '<option value="' + escapeHtml(name) + '">' + escapeHtml(name) + '</option>';
			}).join('');
		var genreNames = Object.keys(genres).sort(function (a, b) {
			return genreLabel(a).localeCompare(genreLabel(b));
		});
		genreSelect.innerHTML = '<option value="">Select a genre</option>' +
			genreNames.map(function (id) {
				return '<option value="' + escapeHtml(id) + '">' + escapeHtml(genreLabel(id)) + '</option>';
			}).join('');
	}

	function writeUrl() {
		try {
			var params = new URLSearchParams(window.location.search);
			if (keySelect.value) params.set('key', keySelect.value);
			else params.delete('key');
			if (genreSelect.value) params.set('style', genreSelect.value);
			else params.delete('style');
			params.delete('q');
			var qs = params.toString();
			window.history.replaceState({}, '', window.location.pathname + (qs ? '?' + qs : ''));
		} catch (e) { /* ignore */ }
	}

	function readUrl() {
		try {
			var params = new URLSearchParams(window.location.search);
			if (params.get('key')) keySelect.value = params.get('key');
			if (params.get('style')) genreSelect.value = params.get('style');
		} catch (e) { /* ignore */ }
	}

	function contentBounds(canvas) {
		var w = canvas.width;
		var h = canvas.height;
		if (!w || !h) return null;
		var data = canvas.getContext('2d').getImageData(0, 0, w, h).data;
		var minX = w;
		var minY = h;
		var maxX = 0;
		var maxY = 0;
		var step = Math.max(1, Math.floor(Math.min(w, h) / 400));
		for (var y = 0; y < h; y += step) {
			for (var x = 0; x < w; x += step) {
				var i = (y * w + x) * 4;
				var r = data[i];
				var g = data[i + 1];
				var b = data[i + 2];
				var a = data[i + 3];
				if (a < 20) continue;
				var hi = r > g ? (r > b ? r : b) : (g > b ? g : b);
				var lo = r < g ? (r < b ? r : b) : (g < b ? g : b);
				if (lo > 186 && (hi - lo) < 36) continue;
				if (x < minX) minX = x;
				if (y < minY) minY = y;
				if (x > maxX) maxX = x;
				if (y > maxY) maxY = y;
			}
		}
		if (maxX <= minX || maxY <= minY) return null;
		var bleed = 4;
		var x0 = Math.max(0, minX - bleed);
		var y0 = Math.max(0, minY - bleed);
		var x1 = Math.max(x0 + 1, Math.min(w, maxX + 1 + bleed));
		var y1 = Math.max(y0 + 1, Math.min(h, maxY + 1 + bleed));
		return { x: x0 / w, y: y0 / h, w: (x1 - x0) / w, h: (y1 - y0) / h };
	}

	function focusFrame(box, pageW, pageH, paneW, paneH) {
		// Note names live in the middle of these charts. The script caption
		// along the bottom goes first, then a little of the staff at the top,
		// so the fretboard can fill a wide screen instead of sitting small.
		var topTrim = 0.04;
		var bottomTrim = 0.12;
		var y = box.y + box.h * topTrim;
		var h = box.h * (1 - topTrim - bottomTrim);
		var bw = box.w * pageW;
		var bh = h * pageH;
		var paneAspect = paneW / Math.max(1, paneH);
		var aspect = bw / Math.max(1, bh);
		if (aspect < paneAspect) {
			var keep = (bw / paneAspect) / bh;
			if (keep < 0.79) keep = 0.79;
			var cut = h * (1 - keep);
			y += cut * 0.35;
			h -= cut;
		}
		var limit = box.y + box.h;
		if (y + h > limit) h = limit - y;
		return { x: box.x, y: y, w: box.w, h: Math.max(0.25, h) };
	}

	function renderPdfPage(which, num) {
		var doc = pdfDocs[which];
		if (!doc) return;
		if (num < 1) num = 1;
		if (num > doc.numPages) num = doc.numPages;
		if (pdfState.rendering) {
			pdfState.pending = { which: which, page: num };
			return;
		}
		pdfState.rendering = true;
		pdfState.which = which;
		doc.getPage(num).then(function (page) {
			var unscaled = page.getViewport({ scale: 1 });
			var wrap = pdfCanvas.parentNode;
			var paneW = Math.max(160, (wrap && wrap.clientWidth) || 640);
			var paneH = Math.max(160, (wrap && wrap.clientHeight) || 360);
			var dpr = Math.min(2, window.devicePixelRatio || 1);
			var probe = document.createElement('canvas');
			var probeScale = Math.min(1, 640 / unscaled.width);
			var probeView = page.getViewport({ scale: probeScale });
			probe.width = Math.max(1, Math.floor(probeView.width));
			probe.height = Math.max(1, Math.floor(probeView.height));
			return page.render({ canvasContext: probe.getContext('2d'), viewport: probeView }).promise.then(function () {
				var box = contentBounds(probe) || { x: 0, y: 0, w: 1, h: 1 };
				var frame = focusFrame(box, unscaled.width, unscaled.height, paneW, paneH);
				var contentW = Math.max(1, unscaled.width * frame.w);
				var contentH = Math.max(1, unscaled.height * frame.h);
				var displayScale = Math.min(paneW / contentW, paneH / contentH);
				var full = page.getViewport({ scale: displayScale * dpr });
				var off = document.createElement('canvas');
				off.width = Math.max(1, Math.floor(full.width));
				off.height = Math.max(1, Math.floor(full.height));
				return page.render({ canvasContext: off.getContext('2d'), viewport: full }).promise.then(function () {
					var sx = Math.floor(frame.x * off.width);
					var sy = Math.floor(frame.y * off.height);
					var sw = Math.max(1, Math.ceil(frame.w * off.width));
					var sh = Math.max(1, Math.ceil(frame.h * off.height));
					if (sx + sw > off.width) sw = off.width - sx;
					if (sy + sh > off.height) sh = off.height - sy;
					pdfCanvas.width = sw;
					pdfCanvas.height = sh;
					pdfCanvas.style.width = Math.round(sw / dpr) + 'px';
					pdfCanvas.style.height = Math.round(sh / dpr) + 'px';
					pdfCanvas.getContext('2d').drawImage(off, sx, sy, sw, sh, 0, 0, sw, sh);
					pdfState.page = num;
					pdfState.rendering = false;
					pdfLabel.textContent = 'Page ' + num + ' / ' + doc.numPages;
					pdfPrev.disabled = num <= 1;
					pdfNext.disabled = num >= doc.numPages;
					pdfDownload.href = which === 'harmonic' ? HARMONIC_URL : BEAUTY_URL;
					pdfDownload.setAttribute('download', which === 'harmonic'
						? 'All 12 Harmonic minor Published.pdf'
						: '12 Keys Beautiful & Print Friendly.pdf');
					if (pdfState.pending) {
						var next = pdfState.pending;
						pdfState.pending = null;
						renderPdfPage(next.which, next.page);
					}
				});
			});
		}).catch(function () {
			pdfState.rendering = false;
			chartNote.textContent = 'The chart viewer could not draw that page. Use Download this PDF.';
		});
	}

	function showPdf(which, page) {
		if (!pdfDocs[which]) {
			pdfLabel.textContent = 'Loading chart…';
			pdfState.which = which;
			pdfState.page = page;
			return;
		}
		requestAnimationFrame(function () {
			renderPdfPage(which, page);
		});
	}

	function loadPdfs() {
		if (typeof pdfjsLib === 'undefined') {
			chartNote.textContent = 'Chart viewer did not load. The download link still works.';
			return;
		}
		pdfjsLib.GlobalWorkerOptions.workerSrc =
			'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';
		function load(which, url) {
			return pdfjsLib.getDocument(url).promise.then(function (doc) {
				pdfDocs[which] = doc;
			});
		}
		Promise.all([load('beauty', BEAUTY_URL), load('harmonic', HARMONIC_URL)]).then(function () {
			if (selectionOn() && chartLiveEl && !chartLiveEl.hidden) {
				showPdf(pdfState.which || 'beauty', pdfState.page || 1);
			}
		}).catch(function () {
			chartNote.textContent = 'Could not open the PDF. Use Download this PDF.';
		});
	}

	keySelect.addEventListener('change', function () { applyFilter(); });
	genreSelect.addEventListener('change', function () { applyFilter(); });
	nextBtn.addEventListener('click', function () { showTrack(currentIndex + 1); });
	prevBtn.addEventListener('click', function () { showTrack(currentIndex - 1); });
	var resizeTimer = null;
	function rerenderChartSoon() {
		clearTimeout(resizeTimer);
		resizeTimer = setTimeout(function () {
			if (chartLiveEl && !chartLiveEl.hidden && pdfDocs[pdfState.which]) {
				renderPdfPage(pdfState.which, pdfState.page);
			}
		}, 120);
	}
	window.addEventListener('resize', rerenderChartSoon);
	if (window.ResizeObserver && pdfCanvas.parentNode) {
		new ResizeObserver(rerenderChartSoon).observe(pdfCanvas.parentNode);
	}
	pdfPrev.addEventListener('click', function () {
		renderPdfPage(pdfState.which, pdfState.page - 1);
	});
	pdfNext.addEventListener('click', function () {
		renderPdfPage(pdfState.which, pdfState.page + 1);
	});
	document.addEventListener('keydown', function (e) {
		var tag = (e.target && e.target.tagName) || '';
		if (tag === 'INPUT' || tag === 'SELECT' || tag === 'TEXTAREA') return;
		if (e.key === 'n' || e.key === 'N') showTrack(currentIndex + 1);
		if (e.key === 'p' || e.key === 'P') showTrack(currentIndex - 1);
	});

	teacherMode = teacherUnlocked();
	loadPdfs();

	fetch(DATA_URL)
		.then(function (r) {
			if (!r.ok) throw new Error('Could not load tracks');
			return r.json();
		})
		.then(function (data) {
			tracks = Array.isArray(data) ? data : [];
			fillSelects();
			readUrl();
			applyFilter();
		})
		.catch(function (err) {
			titleEl.textContent = err.message || String(err);
		});
})();
