var apiKey = "AIzaSyCNdFVx45bBA3_402O-UUREh9MmFL0vS0I";
var channelId = "UCBirLir8z4yrq3HEV5idxaA";

$(document).ready(function() {
	setTimeout(function() {$("#performer").addClass("active");}, 500);
	setTimeout(function() {$("#composer").addClass("active");}, 1200);
	setTimeout(function() {$("#teacher").addClass("active");}, 2000);
	
	randomizeBars();
	
	gapi.client.setApiKey(apiKey);
});

function randomizeBars() {
	$(".bar").each(function(i) {
		var boost = (i === 1 || i === 3 ? 2 : (i === 2 ?  4 : 0));
		var height = 5 + boost + Math.random() * (15 - boost) - (4 - boost);
		$(this).css("height", height + "px").css("margin-top", 20 - height + "px");
	});
	
	setTimeout(randomizeBars, 200);
}