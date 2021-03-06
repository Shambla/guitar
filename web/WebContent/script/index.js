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
	setTimeout(function() {$("#performer").addClass("active");}, 500);
	setTimeout(function() {$("#composer").addClass("active");}, 1200);
	setTimeout(function() {$("#teacher").addClass("active");}, 2000);
	
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
		          scrollTop: target.offset().top
		        }, 1000);
		        return false;
		      }
		    }
		  });
		});
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
	} else {
		$("#backing").removeClass("scrolled");
	}
	
	var heroOpacity = 1 - ((distance - heights.bio / 2.75) / (heights.bio / 2.75));
	
	$("#hero").css("opacity", Math.max(0, Math.min(1, heroOpacity)));
	
	if(distance > heights.performances - 550) {
		$("#perform").addClass("active");
	}
	
	if(distance > heights.bio - 550) {
		$("#bio-pic").addClass("active");
	}
	
	if(distance > heights.contact - 550) {
		$("#contact-pic").addClass("active");
	}
}