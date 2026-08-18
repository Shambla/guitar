/**
 * In-page PDF viewers for free scale charts on mp3-downloads.html.
 * Uses Mozilla PDF.js — prev/next buttons + keyboard arrows (arrows follow the last chart used).
 */
(function () {
	'use strict';

	var VIEWERS = [
		{
			url: 'img/12%20Keys%20Beautiful%20%26%20Print%20Friendly.pdf',
			canvasId: 'pdf-canvas',
			statusId: 'pdf-status',
			pageLabelId: 'pdf-page-label',
			prevId: 'pdf-prev',
			nextId: 'pdf-next',
			stageId: 'pdf-stage',
			sectionId: 'free-scales'
		},
		{
			url: 'img/All%2012%20Harmonic%20minor%20Published.pdf',
			canvasId: 'pdf-canvas-harmonic',
			statusId: 'pdf-status-harmonic',
			pageLabelId: 'pdf-page-label-harmonic',
			prevId: 'pdf-prev-harmonic',
			nextId: 'pdf-next-harmonic',
			stageId: 'pdf-stage-harmonic',
			sectionId: 'free-scales-harmonic'
		}
	];

	function markViewerUnavailable(statusEl) {
		if (!statusEl) return;
		statusEl.className = 'mp3-pdf-status mp3-error';
		statusEl.textContent =
			'PDF viewer unavailable. Use Download PDF below (or above) instead.';
	}

	if (typeof pdfjsLib === 'undefined') {
		VIEWERS.forEach(function (cfg) {
			markViewerUnavailable(document.getElementById(cfg.statusId));
		});
		return;
	}

	pdfjsLib.GlobalWorkerOptions.workerSrc =
		'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';

	var lastViewer = null;

	function initPdfViewer(opts) {
		var canvas = document.getElementById(opts.canvasId);
		var statusEl = document.getElementById(opts.statusId);
		var pageLabel = document.getElementById(opts.pageLabelId);
		var prevBtn = document.getElementById(opts.prevId);
		var nextBtn = document.getElementById(opts.nextId);
		var stage = document.getElementById(opts.stageId);
		var section = document.getElementById(opts.sectionId);

		if (!canvas) {
			markViewerUnavailable(statusEl);
			return null;
		}

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

		var api = {
			goPrev: goPrev,
			goNext: goNext,
			section: section,
			ready: function () {
				return !!pdfDoc;
			}
		};

		function useThisViewer() {
			lastViewer = api;
		}

		prevBtn.addEventListener('click', function () {
			useThisViewer();
			goPrev();
		});
		nextBtn.addEventListener('click', function () {
			useThisViewer();
			goNext();
		});
		if (section) {
			section.addEventListener('mousedown', useThisViewer);
			section.addEventListener('focusin', useThisViewer);
		}

		var resizeTimer = null;
		window.addEventListener('resize', function () {
			clearTimeout(resizeTimer);
			resizeTimer = setTimeout(function () {
				if (pdfDoc) queueRender(pageNum);
			}, 180);
		});

		pdfjsLib
			.getDocument(opts.url)
			.promise.then(function (doc) {
				pdfDoc = doc;
				if (!lastViewer) lastViewer = api;
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

		return api;
	}

	document.addEventListener('keydown', function (e) {
		if (!lastViewer || !lastViewer.ready()) return;
		var tag = (e.target && e.target.tagName) || '';
		if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') return;
		if (e.key === 'ArrowLeft') {
			e.preventDefault();
			lastViewer.goPrev();
		} else if (e.key === 'ArrowRight') {
			e.preventDefault();
			lastViewer.goNext();
		}
	});

	VIEWERS.forEach(initPdfViewer);
})();
