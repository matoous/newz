let openMenu = null;
toggleMenu = function(tag, ev){
    const menu = document.querySelector("#" + tag);
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

mobileMenuTrigger = function() {
  let nav = document.querySelector(".mobile-nav");
  nav.classList.toggle("open");
};

mobileMenuShowProfile = function() {
  let nav = document.querySelector(".mobile-profile");
  nav.classList.toggle("open");
};

mobileMenuShowSubscribed = function() {
  let nav = document.querySelector(".mobile-subscribed");
  nav.classList.toggle("open");
};

document.addEventListener("click", function(ev){
    if (openMenu && !openMenu.contains(ev.target)) {
        openMenu.classList.toggle('hidden');
        openMenu = null;
    }
});

document.addEventListener('scroll', function(){
    const logo = document.querySelector('.nav-logo.animated .logo');
    if(pageYOffset !== 0 && logo && !logo.classList.contains('smaller')){
        logo.classList.add('smaller');
    }
    else if(pageYOffset === 0 && logo && logo.classList.contains('smaller')){
        logo.classList.remove('smaller');
    }
});

handleUrlChange = function(){
    const url = document.querySelector('#url').value;
    if(url && url !== ''){
        document.querySelector('#summary').placeholder = 'Short description';
    } else {
        document.querySelector('#summary').placeholder = 'Summary or text';
    }
};

deleteById = function(id) {
    document.getElementById(id).outerHTML = '';
    return false;
};

generatePreview = function(){
    const md = document.querySelector('#text').value;
    document.querySelector('#preview').innerHTML = SnuOwnd.getParser().render(md);
};

closeModal = function(id) {
    const reportModal = document.getElementById(id);
    reportModal.style.display = "none";
    return false;
};

setReplyTo = function(id){
    document.querySelectorAll('.parent_comment_id').forEach(i => {
        i.value = id;
    })
};

cancelComment = function(id) {
  const ele = document.getElementById(id);
  ele.parentElement.style.display = "none";
  ele.outerHTML = "";
};

commentComment = function(id, route) {
    const nowId = '#c' + id + 'c';
    const commentDiv = document.querySelector("#c" + id + " .comment-comment");
    const submitUrl = route + "/comment";
    commentDiv.style.display = "block";
    commentDiv.innerHTML = `
<form method="post" action="${submitUrl}" id="${nowId}">
<textarea name="text" rows='6'></textarea>
<input class="parent_id" name="parent_id" hidden value="${id}">
<input name="csrf_token" value="${document.querySelector("#csrf_token").value}" type="hidden">
<button class="btn small" type="submit">Submit</button>
<button class="btn small" type="reset" onclick="return cancelComment('${nowId}')">Cancel</button>
</form>`;
    return false;
};

triggerFeedDescription = function(){
    document.querySelector('.feed').classList.toggle('hidden');
    document.querySelector('#description-trigger').innerHTML = document.querySelector('#description-trigger').innerHTML.toLowerCase().includes("hide") ? "Display feed details" : "Hide feed details";
};

  if ('serviceWorker' in navigator) {
    // navigator.serviceWorker
    //          .register('./static/scripts/service-worker.js')
    //          .then(function() { console.log('Service Worker Registered'); });
  }
