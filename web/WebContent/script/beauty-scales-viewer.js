/**
 * In-page PDF viewer for free 12 Keys scales gift on mp3-downloads.html.
 * Uses Mozilla PDF.js — prev/next buttons + keyboard arrows.
 */
(function () {
	'use strict';

	var PDF_URL = 'img/12%20Keys%20Beautiful%20%26%20Print%20Friendly.pdf';
	var canvas = document.getElementById('pdf-canvas');
	var statusEl = document.getElementById('pdf-status');
	var pageLabel = document.getElementById('pdf-page-label');
	var prevBtn = document.getElementById('pdf-prev');
	var nextBtn = document.getElementById('pdf-next');
	var stage = document.getElementById('pdf-stage');

	if (!canvas || typeof pdfjsLib === 'undefined') {
		if (statusEl) {
			statusEl.className = 'mp3-pdf-status mp3-error';
			statusEl.textContent =
				'PDF viewer unavailable. Use Download PDF below (or above) instead.';
		}
		return;
	}

	pdfjsLib.GlobalWorkerOptions.workerSrc =
		'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';

	var pdfDoc = null;
	var pageNum = 1;
	var rendering = false;
	var pendingPage = null;

	function setStatus(msg, isError) {
		if (!statusEl) return;
		statusEl.className = 'mp3-pdf-status' + (isError ? ' mp3-error' : '');
		statusEl.textContent = msg || '';
	}

	function updateControls() {
		if (!pdfDoc) return;
		pageLabel.textContent = 'Page ' + pageNum + ' / ' + pdfDoc.numPages;
		prevBtn.disabled = pageNum <= 1;
		nextBtn.disabled = pageNum >= pdfDoc.numPages;
	}

	function renderPage(num) {
		rendering = true;
		return pdfDoc.getPage(num).then(function (page) {
			var unscaled = page.getViewport({ scale: 1 });
			var maxWidth = Math.min(
				(stage && stage.clientWidth ? stage.clientWidth - 24 : 860) || 860,
				900
			);
			var scale = Math.min(1.75, maxWidth / unscaled.width);
			var viewport = page.getViewport({ scale: scale });
			var ctx = canvas.getContext('2d');
			canvas.height = viewport.height;
			canvas.width = viewport.width;
			return page
				.render({ canvasContext: ctx, viewport: viewport })
				.promise.then(function () {
					rendering = false;
					pageNum = num;
					updateControls();
					setStatus('Free to view and download. Use ← → or the buttons to change pages.');
					if (pendingPage !== null) {
						var p = pendingPage;
						pendingPage = null;
						queueRender(p);
					}
				});
		});
	}

	function queueRender(num) {
		if (!pdfDoc || num < 1 || num > pdfDoc.numPages) return;
		if (rendering) {
			pendingPage = num;
			return;
		}
		renderPage(num).catch(function (err) {
			rendering = false;
			setStatus(err.message || String(err), true);
		});
	}

	function goPrev() {
		if (pageNum > 1) queueRender(pageNum - 1);
	}

	function goNext() {
		if (pdfDoc && pageNum < pdfDoc.numPages) queueRender(pageNum + 1);
	}

	prevBtn.addEventListener('click', goPrev);
	nextBtn.addEventListener('click', goNext);

	document.addEventListener('keydown', function (e) {
		var free = document.getElementById('free-scales');
		if (!free || !pdfDoc) return;
		var tag = (e.target && e.target.tagName) || '';
		if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') return;
		if (e.key === 'ArrowLeft') {
			e.preventDefault();
			goPrev();
		} else if (e.key === 'ArrowRight') {
			e.preventDefault();
			goNext();
		}
	});

	var resizeTimer = null;
	window.addEventListener('resize', function () {
		clearTimeout(resizeTimer);
		resizeTimer = setTimeout(function () {
			if (pdfDoc) queueRender(pageNum);
		}, 180);
	});

	pdfjsLib
		.getDocument(PDF_URL)
		.promise.then(function (doc) {
			pdfDoc = doc;
			queueRender(1);
		})
		.catch(function (err) {
			setStatus(
				'Could not load PDF viewer (' +
					(err.message || String(err)) +
					'). Use Download PDF instead.',
				true
			);
			prevBtn.disabled = true;
			nextBtn.disabled = true;
		});
})();
