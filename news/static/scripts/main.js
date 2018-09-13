function mobileMenuTrigger(e) {
    let nav = document.querySelector("body");
    nav.classList.toggle("open");
    e.stopPropagation();
}
function findClosest(ele, fn) {
    if (!ele) return undefined;
    return fn(ele) ? ele : findClosest(ele.parentElement, fn);
}

document.addEventListener("click", function (e) {
    let nav = document.querySelector("body");
    let target = findClosest(e.target, function (el) {
        return el.classList.contains("mobile-nav")
    });
    if (!target && nav.classList.contains("open")) {
        nav.classList.remove("open");
    }
});

window.addEventListener("resize", function () {
    let nav = document.querySelector("body");
    if (nav.classList.contains("open") && window.innerWidth > 720) {
        nav.classList.remove("open");
    }
});

function mobileMenuShowProfile(){
    let nav = document.querySelector(".mobile-profile");
    nav.classList.toggle("open");
}
function mobileMenuShowSubscribed(){
    let nav = document.querySelector(".mobile-subscribed");
    nav.classList.toggle("open");
}

handleUrlChange = function () {
    const url = document.querySelector('#url').value;
    if (url && url !== '') {
        document.querySelector('#summary').placeholder = 'Short description';
    } else {
        document.querySelector('#summary').placeholder = 'Summary or text';
    }
};

deleteById = function (id) {
    document.getElementById(id).outerHTML = '';
    return false;
};

setReplyTo = function (id) {
    document.querySelectorAll('.parent_comment_id').forEach(i => {
        i.value = id;
    })
};

cancelComment = function (id) {
    const ele = document.getElementById(id);
    ele.parentElement.style.display = "none";
    ele.outerHTML = "";
};

commentComment = function (id, route) {
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

if ('serviceWorker' in navigator) {
    // navigator.serviceWorker
    //          .register('./static/scripts/service-worker.js')
    //          .then(function() { console.log('Service Worker Registered'); });
}
