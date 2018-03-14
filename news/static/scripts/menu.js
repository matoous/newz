var openMenu = null;
toggleMenu = function(tag, ev){
    var menu = document.querySelector("#" + tag);
    if(menu){
        if(menu.classList.contains('hidden')){
            openMenu = menu;
        } else {
            openMenu = null;
        }
        menu.classList.toggle("hidden");
    }
    if(ev)
        ev.stopPropagation();
};

document.addEventListener("click", function(ev){
    if (openMenu && !openMenu.contains(ev.target)) {
        openMenu.classList.toggle('hidden');
        openMenu = null;
    }
});

document.addEventListener('scroll', function(){
    var logo = document.querySelector('.nav-logo .logo');
    if(pageYOffset !== 0 && logo && !logo.classList.contains('smaller')){
        logo.classList.add('smaller');
    }
    else if(pageYOffset === 0 && logo && logo.classList.contains('smaller')){
        logo.classList.remove('smaller');
    }
});