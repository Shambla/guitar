var apiKey = "AIzaSyCNdFVx45bBA3_402O-UUREh9MmFL0vS0I";
var channelId = "UCBirLir8z4yrq3HEV5idxaA";
var playlistId = "PLHk58iPhFqsZSl02DYiEHnWL4IYgKekIR";

var res;

var barTimeout;
var playing = true;

var thumbColumns = 4;
var thumbRows = 3;

var heights = {};

var e1 = "brianstreckfus";
var e2 = "\u0040";
var e3 = "gma";
var e4 = "il.com";

(function(i,s,o,g,r,a,m){i['GoogleAnalyticsObject']=r;i[r]=i[r]||function(){
(i[r].q=i[r].q||[]).push(arguments)},i[r].l=1*new Date();a=s.createElement(o),
m=s.getElementsByTagName(o)[0];a.async=1;a.src=g;m.parentNode.insertBefore(a,m)
})(window,document,'script','//www.google-analytics.com/analytics.js','ga');

ga('create', 'UA-71877195-1', 'auto');
ga('send', 'pageview');


$(document).ready(function() {
	setTimeout(function() {$("#teacher").addClass("active");}, 500);
	setTimeout(function() {$("#arranger").addClass("active");}, 1200);
	setTimeout(function() {$("#performer").addClass("active");}, 2000);
	setTimeout(function() {$("#content-creator").addClass("active");}, 2800);
	setTimeout(function() {$("#producer").addClass("active");}, 2800);
	
	setTimeout(function() {$("#addy").html(e1 + e2 + e3 + e4)}, 3000);
	
	randomizeBars();
	
	heights.bio = $("#bio").offset().top;
	heights.performances = $("#performances").offset().top;
	heights.contact = $("#contact").offset().top;
	
	window.addEventListener("scroll", scrolled);
	
	$("#music").on("click", function() {
		if(playing) {
			pause();
		} else {
			play();
		}
	});
	
	$("#featured").on("click", function() {
		pause();
	});
	
	$(function() {
		  $('a[href*=#]:not([href=#])').click(function() {
		    if (location.pathname.replace(/^\//,'') == this.pathname.replace(/^\//,'') && location.hostname == this.hostname) {
		      var target = $(this.hash);
		      target = target.length ? target : $('[name=' + this.hash.slice(1) +']');
		      if (target.length) {
		        $('html,body').animate({
		          scrollTop: target.offset().top - 80 // Account for fixed nav
		        }, 600); // Faster scroll animation
		        return false;
		      }
		    }
		  });
		});
	
	// Initialize modern scroll animations
	initScrollAnimations();
	
	// Add animation classes to elements
	setupAnimationClasses();
});

function randomizeBars() {
	$(".bar").each(function(i) {
		var boost = (i === 1 || i === 3 ? 2 : (i === 2 ?  4 : 0));
		var height = 5 + boost + Math.random() * (15 - boost) - (4 - boost);
		$(this).css("height", height + "px").css("margin-top", 20 - height + "px");
	});
	
	barTimeout = setTimeout(randomizeBars, 200);
}

function pause() {
	$("audio")[0].pause();
	$("#paused").show();
	clearTimeout(barTimeout);
		
	$(".bar").each(function(i) {
		$(this).css("height", "0px").css("margin-top", "20px");
	});
	
	playing = false;
}

function play() {
	$("audio")[0].play();
	$("#paused").hide();
	
	randomizeBars();
	
	playing = true;
}

function loadYoutube() {
	gapi.client.setApiKey(apiKey);
	
	gapi.client.load('youtube', 'v3', function() {
		var request = gapi.client.youtube.playlistItems.list({
			playlistId: playlistId,
			maxResults: 50,
			part: "contentDetails"
		});
		
		request.execute(function(response) {
			var thumbHtml = "";
			
			$.each(response.items, function(i) {
				if(i === 0) {
					showVideo(this.contentDetails.videoId);
				} else if(i <= thumbColumns * thumbRows) {
					if(i % thumbColumns === 1) {
						thumbHtml += "<div class='row'>";
					}
					
					thumbHtml += "<a href='javascript:showVideo(\"" + this.contentDetails.videoId + "\")'><img src='http://img.youtube.com/vi/" + this.contentDetails.videoId + "/mqdefault.jpg'/></a>";
					
					if(i % thumbColumns === 0) {
						thumbHtml += "</div>";
					}
				}
			});
			
			thumbHtml += "<a id='external' href='https://www.youtube.com/user/WoodenBoxEngineer'>View All Videos <i class='fa fa-external-link'></i></a>";
			
			$("#thumbs").html(thumbHtml);
		});
	});
}

function showVideo(id) {
	var videoHeight;
	
	if($(window).width() >= 1570) {
		videoHeight = 40 * (thumbRows - 1) + 90 * thumbRows; 
	} else if($(window).width() >= 1250) {
		videoHeight = 20 * (thumbRows - 1) + 73 * thumbRows;
	} else {
		videoHeight = 20 * (thumbRows - 1) + 54 * thumbRows;
	}
	
	$("#featured").html("<iframe id='ytplayer' type='text/html' width='" + (1.7666 * videoHeight) + "' height='" + videoHeight + "' src='https://www.youtube.com/embed/" + id + "?fs=1&rel=0&showinfo=1&autohide=1&color=white' frameborder='0' allowfullscreen>");
	$("#ytplayer").iframeTracker({
		blurCallback: function() {
			pause();
		}
	})
}

function scrolled() {
	var distance = window.pageYOffset || document.documentElement.scrollTop;
	
	if(distance > 20) {
		$("#backing").addClass("scrolled");
		$("nav").addClass("scrolled");
	} else {
		$("#backing").removeClass("scrolled");
		$("nav").removeClass("scrolled");
	}
	
	var heroOpacity = 1 - ((distance - heights.bio / 2.75) / (heights.bio / 2.75));
	
	$("#hero").css("opacity", Math.max(0, Math.min(1, heroOpacity)));
	
	// Subtle parallax effect for hero
	if(distance < heights.bio) {
		$("#hero").css("transform", "translateY(" + (distance * 0.2) + "px)");
	}
	
	if(distance > heights.performances - 550) {
		$("#perform").addClass("active");
	}
	
	if(distance > heights.bio - 550) {
		$("#bio-pic").addClass("active");
		$("#desk-pic").addClass("active");
	}
	
	if(distance > heights.contact - 550) {
		$("#contact-pic").addClass("active");
	}
}

// Modern Intersection Observer for scroll animations
function initScrollAnimations() {
	// Helper function to check if element is in viewport
	function isInViewport(el) {
		const rect = el.getBoundingClientRect();
		return (
			rect.top >= 0 &&
			rect.left >= 0 &&
			rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
			rect.right <= (window.innerWidth || document.documentElement.clientWidth)
		);
	}
	
	// Animate elements already in viewport immediately
	function animateVisibleElements() {
		document.querySelectorAll('.fade-in-up, .fade-in-left, .fade-in-right, .fade-in, .scale-in').forEach(function(el) {
			if (isInViewport(el)) {
				el.classList.add('animate');
			}
		});
	}
	
	// Animate visible elements on page load
	setTimeout(animateVisibleElements, 100);
	
	// Check if Intersection Observer is supported
	if ('IntersectionObserver' in window) {
		const observerOptions = {
			root: null,
			rootMargin: '0px 0px -50px 0px',
			threshold: 0.15
		};
		
		const observer = new IntersectionObserver(function(entries) {
			entries.forEach(function(entry) {
				if (entry.isIntersecting) {
					entry.target.classList.add('animate');
				}
			});
		}, observerOptions);
		
		// Observe all elements with animation classes
		document.querySelectorAll('.fade-in-up, .fade-in-left, .fade-in-right, .fade-in, .scale-in').forEach(function(el) {
			// Only observe if not already animated
			if (!el.classList.contains('animate')) {
				observer.observe(el);
			}
		});
		
		// Observe sections (but exclude left/right halves and contact details)
		document.querySelectorAll('.content > div:not(.left-half):not(.right-half):not(#bio-right):not(#performance-details):not(#contact-details)').forEach(function(el) {
			if (!el.classList.contains('animate')) {
				observer.observe(el);
			}
		});
		
		// Observe list items with staggered delays (only those with fade-in-up class)
		document.querySelectorAll('ol li.fade-in-up, ul li.fade-in-up').forEach(function(el, index) {
			el.style.transitionDelay = (index * 0.1) + 's';
			if (!el.classList.contains('animate')) {
				observer.observe(el);
			}
		});
		
		// Observe footer
		const footer = document.querySelector('footer');
		if (footer && !footer.classList.contains('animate')) {
			observer.observe(footer);
		}
	} else {
		// Fallback for older browsers - animate immediately
		document.querySelectorAll('.fade-in-up, .fade-in-left, .fade-in-right, .fade-in, .scale-in').forEach(function(el) {
			el.classList.add('animate');
		});
	}
}

// Add animation classes to elements
function setupAnimationClasses() {
	// Ensure contact items animate properly
	$('.contact.fade-in-up').each(function(index) {
		$(this).addClass('animate-delay-' + Math.min(index + 1, 5));
	});
	
	// Make sure contact section is visible immediately
	$('#contact-details').css('opacity', '1');
	$('.contacts').css('opacity', '1');
	
	// Animate contact items that are already visible
	setTimeout(function() {
		$('.contact.fade-in-up').each(function() {
			const el = this;
			const rect = el.getBoundingClientRect();
			if (rect.top < window.innerHeight && rect.bottom > 0) {
				$(el).addClass('animate');
			}
		});
	}, 200);
}