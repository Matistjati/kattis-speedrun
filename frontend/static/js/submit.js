// Submit page: drag & drop file upload + infer shortname/language from filenames.

const EXT_LANGUAGE = {
    '.py': 'Python 3',
    '.cpp': 'C++',
    '.cc': 'C++',
    '.cxx': 'C++',
    '.cpp11': 'C++',
    '.rs': 'Rust',
};

const dropzone = document.getElementById('dropzone');
const fileInput = document.getElementById('files');
const fileList = document.getElementById('file-list');
const shortnameInput = document.getElementById('shortname');
const languageSelect = document.getElementById('language');

function extOf(filename) {
    const i = filename.lastIndexOf('.');
    return i === -1 ? '' : filename.slice(i).toLowerCase();
}

function inferFromFiles(files) {
    if (!files || !files.length) return;

    // Shortname from the first file's base name (Kattis shortnames are lowercase).
    const first = files[0].name;
    const base = first.replace(/\.[^.]+$/, '');
    if (base) shortnameInput.value = base.toLowerCase();

    // Language from the first recognised extension among the files.
    for (const f of files) {
        const lang = EXT_LANGUAGE[extOf(f.name)];
        if (lang) {
            languageSelect.value = lang;
            break;
        }
    }
}

function renderFileList(files) {
    fileList.textContent = files && files.length
        ? Array.from(files).map(f => f.name).join(', ')
        : '';
}

function handleFiles(files) {
    renderFileList(files);
    inferFromFiles(files);
}

fileInput.addEventListener('change', () => handleFiles(fileInput.files));

['dragenter', 'dragover'].forEach(evt =>
    dropzone.addEventListener(evt, (e) => {
        e.preventDefault();
        e.stopPropagation();
        dropzone.classList.add('dragover');
    })
);

['dragleave', 'drop'].forEach(evt =>
    dropzone.addEventListener(evt, (e) => {
        e.preventDefault();
        e.stopPropagation();
        dropzone.classList.remove('dragover');
    })
);

dropzone.addEventListener('drop', (e) => {
    const files = e.dataTransfer.files;
    // Reflect dropped files into the form's file input so they are submitted.
    fileInput.files = files;
    handleFiles(files);
});
