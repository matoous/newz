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

generatePreview = function(){
    const md = document.querySelector('#summary').value;
    document.querySelector('#preview').innerHTML = SnuOwnd.getParser().render(md);
};

reportComment = function(id) {
    const reportModal = document.getElementById('report-modal');
    reportModal.style.display = "block";
    reportModal.onclick = function (ev) {
        if(ev.target === reportModal){
            reportModal.style.display = "none";
        }
    };
    console.log(id);
    document.getElementById("report_comment_id").value = id;
    return false;
};

closeModal = function(id) {
    const reportModal = document.getElementById(id);
    reportModal.style.display = "none";
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

commentComment = function(id) {
    const nowId = '#c' + id + 'c';
    const commentDiv = document.querySelector("#c" + id + " .comment-comment");
    const submitUrl = window.location.pathname + "/comment";
    commentDiv.style.display = "block";
    commentDiv.innerHTML = `
<form method="post" action="${submitUrl}" id="${nowId}">
<textarea name="text" rows='6'></textarea>
<input class="parent_id" name="parent_id" hidden value="${id}">
<input name="csrf_token" value="${document.querySelector("#csrf_token").value}" type="hidden">
<button class="small" type="submit">Submit</button>
<button class="small" type="reset" onclick="return cancelComment('${nowId}')">Cancel</button>
</form>`;
    return false;
};