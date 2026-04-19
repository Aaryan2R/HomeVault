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
var previewClickTimer = null;

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
    var uploadBtn = document.getElementById('uploadBtn');

    if (!zone || !fileInput) return;

    zone.addEventListener('click', function(e) {
        if (e.target.closest('.upload-btn') ||
            e.target.closest('.upload-options')) return;
        fileInput.click();
    });

    zone.addEventListener('dragover', function(e) {
        e.preventDefault();
        if (e.dataTransfer.types.includes('Files')) {
            zone.classList.add('drag-over');
        }
    });

    zone.addEventListener('dragleave', function() {
        zone.classList.remove('drag-over');
    });

    zone.addEventListener('drop', function(e) {
        e.preventDefault();
        zone.classList.remove('drag-over');
        if (!e.dataTransfer.types.includes('Files')) return;
        if (e.dataTransfer.files.length === 0) return;
        fileInput.files = e.dataTransfer.files;
        updateFileName(fileInput);
    });

    fileInput.addEventListener('change', function() {
        updateFileName(fileInput);
    });

    if (uploadBtn) {
        uploadBtn.addEventListener('click', function() {
            if (!fileInput.files || fileInput.files.length === 0) {
                alert('Please choose at least one file first.');
                return;
            }
            startUpload(fileInput.files);
        });
    }
}

function startUpload(files) {
    var progressPanel = document.getElementById('progressPanel');
    var progressList  = document.getElementById('progressList');
    var shareCheck    = document.getElementById('shareCheck');
    var uploadBtn     = document.getElementById('uploadBtn');

    progressPanel.style.display = 'block';
    progressList.innerHTML      = '';

    uploadBtn.disabled    = true;
    uploadBtn.textContent = 'Uploading...';

    var completed = 0;
    var total     = files.length;

    for (var i = 0; i < files.length; i++) {
        uploadOneFile(files[i], shareCheck.checked, progressList,
            function() {
                completed++;
                if (completed === total) {
                    uploadBtn.disabled    = false;
                    uploadBtn.textContent = 'Upload Files';
                    setTimeout(function() {
                        window.location.reload();
                    }, 1500);
                }
            });
    }
}

function uploadOneFile(file, isShared, progressList, onDone) {
    var item = document.createElement('div');
    item.className = 'progress-item';
    item.innerHTML =
        '<div class="progress-item-name">' + file.name + '</div>' +
        '<div class="progress-bar-bg">' +
            '<div class="progress-bar-fill" id="bar-' + file.name.replace(/\W/g, '') + '"></div>' +
        '</div>' +
        '<div class="progress-status">' +
            '<span class="progress-pct">0%</span>' +
            '<span class="progress-state">Starting...</span>' +
        '</div>';
    progressList.appendChild(item);

    var bar   = item.querySelector('.progress-bar-fill');
    var pct   = item.querySelector('.progress-pct');
    var state = item.querySelector('.progress-state');

    var formData = new FormData();
    formData.append('file', file);
    formData.append('is_shared', isShared ? 'on' : '');

    var xhr = new XMLHttpRequest();

    xhr.upload.addEventListener('progress', function(e) {
        if (e.lengthComputable) {
            var percent = Math.round((e.loaded / e.total) * 100);
            bar.style.width   = percent + '%';
            pct.textContent   = percent + '%';
            state.textContent = 'Uploading...';
        }
    });

    xhr.addEventListener('load', function() {
        if (xhr.status === 200 || xhr.status === 302) {
            bar.style.width   = '100%';
            bar.classList.add('done');
            pct.textContent   = '100%';
            state.textContent = 'Done ✓';
        } else {
            bar.classList.add('error');
            state.textContent = 'Failed ✗';
        }
        onDone();
    });

    xhr.addEventListener('error', function() {
        bar.classList.add('error');
        state.textContent = 'Error ✗';
        onDone();
    });

    xhr.open('POST', '/upload');
    xhr.setRequestHeader('X-Requested-With', 'XMLHttpRequest');
    xhr.send(formData);
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
    var fileLists   = document.querySelectorAll('.file-list');
    var listBtn     = document.getElementById('viewList');
    var gridBtn     = document.getElementById('viewGrid');
    var listHeaders = document.querySelectorAll('.file-list-header');
    var i;

    if (!fileLists.length) return;

    if (view === 'grid') {
        for (i = 0; i < fileLists.length; i++) {
            fileLists[i].classList.add('grid-view');
            fileLists[i].classList.remove('list-view');
        }
        for (i = 0; i < listHeaders.length; i++) {
            listHeaders[i].style.display = 'none';
        }
        if (gridBtn) gridBtn.classList.add('view-btn-active');
        if (listBtn) listBtn.classList.remove('view-btn-active');
    } else {
        for (i = 0; i < fileLists.length; i++) {
            fileLists[i].classList.add('list-view');
            fileLists[i].classList.remove('grid-view');
        }
        for (i = 0; i < listHeaders.length; i++) {
            listHeaders[i].style.display = '';
        }
        if (listBtn) listBtn.classList.add('view-btn-active');
        if (gridBtn) gridBtn.classList.remove('view-btn-active');
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

function makeFileNameEditable(nameEl, fileId) {
    var currentName = nameEl.textContent.trim();
    var input = document.createElement('input');
    input.type = 'text';
    input.value = currentName;
    input.className = 'rename-input';
    input.style.cssText =
        'width:100%; padding:3px 6px; border:1px solid var(--accent);' +
        'border-radius:4px; font-size:14px; font-family:inherit;' +
        'background:var(--bg-card); color:var(--text-primary);';

    nameEl.replaceWith(input);
    input.focus();
    input.select();

    function saveRename() {
        var newName = input.value.trim();
        if (!newName || newName === currentName) {
            cancelRename();
            return;
        }

        var formData = new FormData();
        formData.append('name', newName);

        fetch('/rename/' + fileId, {
            method: 'POST',
            body: formData
        }).then(function(response) {
            if (response.ok) {
                var row = input.closest('.preview-trigger');
                if (row) row.setAttribute('data-name', newName);

                var newDiv = document.createElement('div');
                newDiv.className = 'file-name';
                newDiv.title = newName;
                newDiv.textContent = newName;
                newDiv.addEventListener('dblclick', function(e) {
                    if (previewClickTimer) {
                        clearTimeout(previewClickTimer);
                        previewClickTimer = null;
                    }
                    closePreview();
                    e.stopPropagation();
                    makeFileNameEditable(newDiv, fileId);
                });
                input.replaceWith(newDiv);
            } else {
                cancelRename();
            }
        });
    }

    function cancelRename() {
        var div = document.createElement('div');
        div.className = 'file-name';
        div.title = currentName;
        div.textContent = currentName;
        div.addEventListener('dblclick', function(e) {
            if (previewClickTimer) {
                clearTimeout(previewClickTimer);
                previewClickTimer = null;
            }
            closePreview();
            e.stopPropagation();
            makeFileNameEditable(div, fileId);
        });
        input.replaceWith(div);
    }

    input.addEventListener('keydown', function(e) {
        if (e.key === 'Enter') saveRename();
        if (e.key === 'Escape') cancelRename();
    });

    input.addEventListener('blur', saveRename);
}

function initRename() {
    document.querySelectorAll('.preview-trigger').forEach(function(row) {
        var nameEl = row.querySelector('.file-name');
        var fileId = row.getAttribute('data-id');

        if (!nameEl || !fileId) return;

        nameEl.addEventListener('dblclick', function(e) {
            if (previewClickTimer) {
                clearTimeout(previewClickTimer);
                previewClickTimer = null;
            }
            closePreview();
            e.stopPropagation();
            makeFileNameEditable(nameEl, fileId);
        });

        nameEl.title = 'Double-click to rename';
    });
}


// init on page load

initTheme();

document.addEventListener('DOMContentLoaded', function() {
    initUploadZone();
    initViewToggle();
    initRename();

    document.querySelectorAll('.preview-trigger').forEach(function(row) {
        row.addEventListener('click', function(e) {
            if (e.target.closest('a')) return;
            if (e.target.closest('button')) return;
            if (e.target.closest('form')) return;
            if (e.target.closest('.rename-input')) return;

            var fileId   = row.getAttribute('data-id');
            var fileType = row.getAttribute('data-type');
            var fileName = row.getAttribute('data-name');

            if (previewClickTimer) {
                clearTimeout(previewClickTimer);
            }

            previewClickTimer = setTimeout(function() {
                openPreview(fileId, fileType, fileName);
                previewClickTimer = null;
            }, 400);
        });

        row.addEventListener('dblclick', function(e) {
            if (e.target.closest('.file-name') && previewClickTimer) {
                clearTimeout(previewClickTimer);
                previewClickTimer = null;
            }
        });

        row.style.cursor = 'pointer';
    });

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
