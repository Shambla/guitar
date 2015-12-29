var apiKey = "AIzaSyCNdFVx45bBA3_402O-UUREh9MmFL0vS0I";
var channelId = "UCBirLir8z4yrq3HEV5idxaA";

var res;

var heights = {};

$(document).ready(function() {
	setTimeout(function() {$("#performer").addClass("active");}, 500);
	setTimeout(function() {$("#composer").addClass("active");}, 1200);
	setTimeout(function() {$("#teacher").addClass("active");}, 2000);
	
	randomizeBars();
	
	heights.bio = $("#bio").offset().top;
	
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
		var request = gapi.client.youtube.channelSections.list({
			channelId: channelId,
			part: "contentDetails"
		});
		
		request.execute(function(response) {
			res = response;
		});
	});
}

function scrolled() {
	var distance = window.pageYOffset || document.documentElement.scrollTop;
	
	if(distance > 20) {
		$("#backing").addClass("scrolled");
	} else {
		$("#backing").removeClass("scrolled");
	}
	
	var heroOpacity = 1 - ((distance - heights.bio / 2.2) / (heights.bio / 2.2));
	
	$("#hero").css("opacity", Math.max(0, Math.min(1, heroOpacity)));
}