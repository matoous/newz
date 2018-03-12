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