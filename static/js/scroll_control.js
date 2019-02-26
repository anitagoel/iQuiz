//Whenever the hash changes, scroll by the size of menu bar, so there is no overlap of body and menu bar
var shiftWindow = function() { scrollBy(0,-60) };
if (location.hash) shiftWindow();
window.addEventListener("hashchange", shiftWindow);

//Go to Top button
window.onscroll = function() {onScrollFunc()};
function onScrollFunc() 
{
	if (document.body.scrollTop > 100 || document.documentElement.scrollTop > 100)
	{document.getElementById("gotoTop").style.display="block";}
	else
	{document.getElementById("gotoTop").style.display="none";}
}
window.onscroll = function() {scrollFunction()};

function scrollFunction() {
    if (document.body.scrollTop > 20 || document.documentElement.scrollTop > 20) {
        document.getElementById("gotoTop").style.display = "block";
    } else {
        document.getElementById("gotoTop").style.display = "none";
    }
}
function gotoTopFunc() {
speed=50;
if (document.body.scrollTop > 0 || document.documentElement.scrollTop > 0) {
    document.body.scrollTop -= speed;
	document.documentElement.scrollTop -= speed;
	setTimeout(() => gotoTopFunc(), 5);
}
}

		
