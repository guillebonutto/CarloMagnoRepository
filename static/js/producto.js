const dropArea = document.getElementById('drop-area');
const fileInput = document.getElementById('file-input');
const originalPreview = document.getElementById('original-preview');
const resizedPreview = document.getElementById('resized-preview');
const originalSize = document.getElementById('original-size');
const resizedSize = document.getElementById('resized-size');
const downloadBtn = document.getElementById('download-btn');
const errorMessage = document.getElementById('error-message');
const loadingMessage = document.getElementById('loading-message');

// Prevenir comportamiento por defecto del drag and drop
['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
    dropArea.addEventListener(eventName, preventDefaults, false);
    document.body.addEventListener(eventName, preventDefaults, false);
});

function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
}

// Efectos visuales durante el drag
['dragenter', 'dragover'].forEach(eventName => {
    dropArea.addEventListener(eventName, highlight, false);
});

['dragleave', 'drop'].forEach(eventName => {
    dropArea.addEventListener(eventName, unhighlight, false);
});

function highlight(e) {
    dropArea.classList.add('dragover');
}

function unhighlight(e) {
    dropArea.classList.remove('dragover');
}

// Manejar la subida de archivos
dropArea.addEventListener('drop', handleDrop, false);
dropArea.addEventListener('click', () => fileInput.click());
fileInput.addEventListener('change', handleFiles);

function handleDrop(e) {
    const dt = e.dataTransfer;
    const files = dt.files;
    handleFiles({ target: { files } });
}

function handleFiles(e) {
    const file = e.target.files[0];
    if (!file) return;

    if (!file.type.startsWith('image/')) {
        showError('Por favor, selecciona un archivo de imagen válido.');
        return;
    }

    showLoading(true);
    showError('');

    // Crear URL temporal para la imagen original
    const objectUrl = URL.createObjectURL(file);

    // Mostrar imagen original con máxima calidad
    const img = new Image();
    img.onload = function () {
        originalPreview.src = objectUrl;
        originalSize.textContent = `Tamaño original: ${img.width}x${img.height}px`;
        // Guardar nombre original para usarlo en la descarga
        img.name = file.name;
        resizeImage(img);
        // Liberar memoria
        URL.revokeObjectURL(objectUrl);
    };
    img.src = objectUrl;
}

function resizeImage(img) {
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');

    // Aplicar configuración para mejor calidad desde el inicio
    ctx.imageSmoothingEnabled = true;
    ctx.imageSmoothingQuality = 'high';

    // Calcular el ratio de aspecto original
    const ratio = img.width / img.height;

    // Determinar las nuevas dimensiones manteniendo proporción
    let newWidth = 300;
    let newHeight = 300;

    if (ratio > 1) {
        // Imagen más ancha que alta
        newHeight = 300 / ratio;
    } else {
        // Imagen más alta que ancha
        newWidth = 300 * ratio;
    }

    // Redondear dimensiones para evitar problemas de píxeles
    newWidth = Math.round(newWidth);
    newHeight = Math.round(newHeight);

    // Establecer dimensiones del canvas según la proporción
    canvas.width = 300;
    canvas.height = 300;

    // Fondo blanco (opcional)
    ctx.fillStyle = '#FFFFFF';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // Centrar la imagen en el canvas
    const x = Math.round((300 - newWidth) / 2);
    const y = Math.round((300 - newHeight) / 2);

    // Dibujar la imagen redimensionada
    ctx.drawImage(img, x, y, newWidth, newHeight);

    // Convertir a PNG para mejor calidad
    const resizedDataUrl = canvas.toDataURL('image/png');
    resizedPreview.src = resizedDataUrl;
    resizedSize.textContent = `Tamaño ajustado: ${newWidth}x${newHeight}px`;

    // Habilitar botón de descarga con nombre original
    downloadBtn.disabled = false;
    downloadBtn.onclick = () => {
        const link = document.createElement('a');
        const baseName = img.name ? img.name.replace(/\.[^/.]+$/, '') : 'imagen';
        link.download = `${baseName}-redimensionada.png`;
        link.href = resizedDataUrl;
        link.click();
    };

    showLoading(false);
}

function downloadImage(dataUrl, originalName) {
    const link = document.createElement('a');
    // Usar el nombre original si está disponible
    const baseName = originalName ? originalName.replace(/\.[^/.]+$/, '') : 'imagen';
    link.download = `${baseName}-redimensionada.png`;
    link.href = dataUrl;
    link.click();
}

function showError(message) {
    errorMessage.textContent = message;
    errorMessage.style.display = message ? 'block' : 'none';
}

function showLoading(show) {
    loadingMessage.style.display = show ? 'block' : 'none';
    downloadBtn.disabled = show;
}