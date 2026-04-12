/* main js file
   common ui things are here */


// dark mode

function initTheme() {
    var saved = localStorage.getItem('homevault-theme');
    if (saved === 'dark') {
        document.documentElement.setAttribute('data-theme', 'dark');
    }
    var toggles = document.querySelectorAll('.theme-checkbox');
    for (var i = 0; i < toggles.length; i++) {
        toggles[i].checked = (saved === 'dark');
    }
}

function toggleTheme() {
    var current = document.documentElement.getAttribute('data-theme');
    var newTheme;
    if (current === 'dark') {
        newTheme = 'light';
        document.documentElement.removeAttribute('data-theme');
    } else {
        newTheme = 'dark';
        document.documentElement.setAttribute('data-theme', 'dark');
    }
    localStorage.setItem('homevault-theme', newTheme);
    var toggles = document.querySelectorAll('.theme-checkbox');
    for (var i = 0; i < toggles.length; i++) {
        toggles[i].checked = (newTheme === 'dark');
    }
}


// three dot menus
// this was clipping near edges before
// now checking button position and opening up/down based on space

// keep only one open
var activeDropdown = null;

function toggleMenu(button) {
    // click same one again = close
    if (activeDropdown && activeDropdown._trigger === button) {
        closeActiveDropdown();
        return;
    }

    // close previous menu first
    closeActiveDropdown();

    var dropdown = button.nextElementSibling;

    // get button position
    var btnRect      = button.getBoundingClientRect();
    var dropdownWidth = 180;

    // fixed works better here than absolute
    dropdown.style.position = 'fixed';
    dropdown.style.width    = dropdownWidth + 'px';
    dropdown.style.zIndex   = '9999';

    // horizontal position
    var leftPos = btnRect.right - dropdownWidth;
    // little safety check
    if (leftPos < 8) leftPos = 8;
    dropdown.style.left = leftPos + 'px';

    // decide up or down
    var spaceBelow = window.innerHeight - btnRect.bottom;
    var spaceAbove = btnRect.top;
    var dropdownHeight = 160; // rough height

    if (spaceBelow >= dropdownHeight || spaceBelow >= spaceAbove) {
        // open down
        dropdown.style.top    = (btnRect.bottom + 4) + 'px';
        dropdown.style.bottom = 'auto';
    } else {
        // open up
        dropdown.style.top    = 'auto';
        dropdown.style.bottom = (window.innerHeight - btnRect.top + 4) + 'px';
    }

    dropdown.classList.add('open');
    dropdown._trigger = button;
    activeDropdown    = dropdown;
}

function closeActiveDropdown() {
    if (activeDropdown) {
        activeDropdown.classList.remove('open');
        // clear inline style after closing
        activeDropdown.style.position = '';
        activeDropdown.style.top      = '';
        activeDropdown.style.bottom   = '';
        activeDropdown.style.left     = '';
        activeDropdown.style.width    = '';
        activeDropdown._trigger       = null;
        activeDropdown                = null;
    }
}

// outside click closes it
document.addEventListener('click', function(e) {
    if (!e.target.closest('.menu-container')) {
        closeActiveDropdown();
    }
});

// scroll also closes it because menu is fixed
document.addEventListener('scroll', function() {
    closeActiveDropdown();
}, true);


// mobile sidebar

function openSidebar() {
    var sidebar = document.querySelector('.sidebar');
    var overlay = document.querySelector('.sidebar-overlay');
    if (sidebar) sidebar.classList.add('open');
    if (overlay) overlay.classList.add('active');
}

function closeSidebar() {
    var sidebar = document.querySelector('.sidebar');
    var overlay = document.querySelector('.sidebar-overlay');
    if (sidebar) sidebar.classList.remove('open');
    if (overlay) overlay.classList.remove('active');
}


// upload zone

function initUploadZone() {
    var zone      = document.querySelector('.upload-zone');
    var fileInput = document.getElementById('file-input');

    if (!zone || !fileInput) return;

    zone.addEventListener('click', function(e) {
        if (e.target.closest('.upload-btn') || e.target.closest('.upload-options')) return;
        fileInput.click();
    });

    zone.addEventListener('dragover', function(e) {
        e.preventDefault();
        zone.classList.add('drag-over');
    });

    zone.addEventListener('dragleave', function() {
        zone.classList.remove('drag-over');
    });

    zone.addEventListener('drop', function(e) {
        e.preventDefault();
        zone.classList.remove('drag-over');
        if (e.dataTransfer.files.length > 0) {
            fileInput.files = e.dataTransfer.files;
            updateFileName(fileInput);
        }
    });

    fileInput.addEventListener('change', function() {
        updateFileName(fileInput);
    });
}

function updateFileName(input) {
    var textEl = document.querySelector('.upload-text');
    if (!textEl || !input.files) return;
    if (input.files.length === 1) {
        textEl.textContent = input.files[0].name;
    } else if (input.files.length > 1) {
        textEl.textContent = input.files.length + ' files selected';
    }
}


// confirm helper

function confirmAction(message) {
    return confirm(message);
}


// grid/list toggle
// saved in local storage so view stays same next time

function initViewToggle() {
    var saved = localStorage.getItem('homevault-view') || 'list';
    applyView(saved, false);

    var listBtn = document.getElementById('viewList');
    var gridBtn = document.getElementById('viewGrid');

    if (listBtn) {
        listBtn.addEventListener('click', function() {
            applyView('list', true);
        });
    }

    if (gridBtn) {
        gridBtn.addEventListener('click', function() {
            applyView('grid', true);
        });
    }
}

function applyView(view, save) {
    var fileList   = document.getElementById('fileList');
    var listBtn    = document.getElementById('viewList');
    var gridBtn    = document.getElementById('viewGrid');
    var listHeader = document.getElementById('fileListHeader');

    if (!fileList) return;

    if (view === 'grid') {
        fileList.classList.add('grid-view');
        fileList.classList.remove('list-view');
        if (listHeader) listHeader.style.display = 'none';
        if (gridBtn)    gridBtn.classList.add('view-btn-active');
        if (listBtn)    listBtn.classList.remove('view-btn-active');
    } else {
        fileList.classList.add('list-view');
        fileList.classList.remove('grid-view');
        if (listHeader) listHeader.style.display = '';
        if (listBtn)    listBtn.classList.add('view-btn-active');
        if (gridBtn)    gridBtn.classList.remove('view-btn-active');
    }

    if (save) {
        localStorage.setItem('homevault-view', view);
    }
}


// preview modal

function handlePreview(button) {
    var fileId   = button.getAttribute('data-id');
    var fileType = button.getAttribute('data-type');
    var fileName = button.getAttribute('data-name');
    closeActiveDropdown();
    openPreview(fileId, fileType, fileName);
}

function openPreview(fileId, fileType, fileName) {
    var modal   = document.getElementById('previewModal');
    var content = document.getElementById('previewContent');
    var nameEl  = document.getElementById('previewFileName');

    if (!modal || !content) return;

    nameEl.textContent = fileName;
    var type = fileType.toLowerCase();

    if (type === 'photos') {
        content.innerHTML =
            '<img src="/preview/' + fileId + '" ' +
            'style="max-width:90vw; max-height:85vh; object-fit:contain; border-radius:6px;" ' +
            'alt="' + fileName + '">';

    } else if (type === 'videos') {
        content.innerHTML =
            '<video src="/preview/' + fileId + '" controls autoplay ' +
            'style="max-width:90vw; max-height:85vh; border-radius:6px;">' +
            'Your browser does not support video playback.' +
            '</video>';

    } else if (type === 'documents') {
        if (fileName.toLowerCase().endsWith('.pdf')) {
            content.innerHTML =
                '<iframe src="/preview/' + fileId + '" ' +
                'style="width:85vw; height:88vh; border:none; border-radius:6px;"></iframe>';
        } else {
            content.innerHTML = buildNoPreview(fileId, fileName, '&#128196;');
        }
    } else {
        content.innerHTML = buildNoPreview(fileId, fileName, '&#128230;');
    }

    modal.style.display = 'flex';
    document.body.style.overflow = 'hidden';
}

function buildNoPreview(fileId, fileName, icon) {
    return '<div style="text-align:center; color:white; padding:48px 32px;">' +
           '<div style="font-size:72px; margin-bottom:20px;">' + icon + '</div>' +
           '<div style="font-size:18px; font-weight:600; margin-bottom:10px;">' + fileName + '</div>' +
           '<div style="font-size:14px; opacity:0.65; margin-bottom:28px; max-width:300px; margin-left:auto; margin-right:auto;">' +
           'This file type cannot be previewed in the browser.</div>' +
           '<a href="/download/' + fileId + '" ' +
           'style="background:#2563eb; color:white; padding:11px 28px; ' +
           'border-radius:8px; text-decoration:none; font-size:14px; font-weight:500;">' +
           'Download to open' +
           '</a></div>';
}

function closePreview() {
    var modal   = document.getElementById('previewModal');
    var content = document.getElementById('previewContent');
    if (!modal) return;
    modal.style.display  = 'none';
    content.innerHTML    = '';
    document.body.style.overflow = '';
}


// init on page load

initTheme();

document.addEventListener('DOMContentLoaded', function() {
    initUploadZone();
    initViewToggle();

    var modal = document.getElementById('previewModal');
    if (modal) {
        modal.addEventListener('click', function(e) {
            if (e.target === modal) closePreview();
        });
    }

    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') closePreview();
    });
});
