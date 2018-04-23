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
    var logo = document.querySelector('.nav-logo.animated .logo');
    if(pageYOffset !== 0 && logo && !logo.classList.contains('smaller')){
        logo.classList.add('smaller');
    }
    else if(pageYOffset === 0 && logo && logo.classList.contains('smaller')){
        logo.classList.remove('smaller');
    }
});

setReplyTo = function(id){
    document.querySelector('#parent_id').value = id;
    return false;
};

handleUrlChange = function(){
    const url = document.querySelector('#url').value;
    if(url && url !== ''){
        document.querySelector('#summary').placeholder = 'Short description';
    } else {
        document.querySelector('#summary').placeholder = 'Summary or text';
    }
};

generatePreview = function(){
    const md = document.querySelector('#summary').value;
    document.querySelector('#preview').innerHTML = SnuOwnd.getParser().render(md);
};

const report = function(id) {
    const reportModal = document.getElementById('report-modal');
    reportModal.style.display = "block";
    reportModal.onclick = function (ev) {
        if(ev.target === reportModal){
            reportModal.style.display = "none";
        }
    };
    return false;
};

const closeModal = function(id) {
    const reportModal = document.getElementById(id);
    reportModal.style.display = "none";
};