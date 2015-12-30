var apiKey = "AIzaSyCNdFVx45bBA3_402O-UUREh9MmFL0vS0I";
var channelId = "UCBirLir8z4yrq3HEV5idxaA";
var playlistId = "PLHk58iPhFqsZSl02DYiEHnWL4IYgKekIR";

var res;

var thumbColumns = 4;
var thumbRows = 3;

var heights = {};

$(document).ready(function() {
	setTimeout(function() {$("#performer").addClass("active");}, 500);
	setTimeout(function() {$("#composer").addClass("active");}, 1200);
	setTimeout(function() {$("#teacher").addClass("active");}, 2000);
	
	randomizeBars();
	
	heights.bio = $("#bio").offset().top;
	heights.performances = $("#performances").offset().top;
	
	window.addEventListener("scroll", scrolled);
	
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
	
	setTimeout(randomizeBars, 200);
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
			
			$("#thumbs").html(thumbHtml);
		});
	});
}

function showVideo(id) {
	$("#featured").html("<iframe id='ytplayer' type='text/html' width='636' height='360' src='https://www.youtube.com/embed/" + id + "?fs=1&rel=0&showinfo=1&autohide=1&color=white' frameborder='0' allowfullscreen>");
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
}