function filter_toggle(event) {
    var group = event.target.closest(".filter-group ");
    var options = group.querySelector(".filter-group-options");
    if (options.style.display == "none") {
        options.style.display = "block";
        event.target.innerHTML = "Hide";
    } else {
        options.style.display = "none";
        event.target.innerHTML = "Show";
    }
    return false;
}

document.querySelectorAll('.filters .filter-group .filter-group-title a.filter-group-toggle-options').forEach((link) => {
  link.style.display = 'inline';
  link.onclick = filter_toggle;
  link.href = "#";
});

document.querySelectorAll('.filters .filter-group .filter-group-options').forEach((area) => {
  area.style.display = 'none';
});



