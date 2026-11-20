/**
 * Camera Barcode Scanner Helper
 * Utiliza html5-qrcode para leer códigos de barras (EAN-13, CODE-128, UPC, etc.)
 * directamente desde la cámara trasera del celular o webcam.
 */

function setupCameraScanner({ triggerBtnId, inputElement, onDetected }) {
    const triggerBtn = document.getElementById(triggerBtnId);
    if (!triggerBtn || !inputElement) return;

    let html5QrCode = null;
    let modal = null;

    function createModal() {
        if (modal) return modal;

        modal = document.createElement('div');
        modal.className = 'camera-scanner-modal';
        modal.style.display = 'none';
        modal.innerHTML = `
            <div class="camera-scanner-dialog" role="dialog" aria-modal="true" aria-labelledby="camera-scanner-title">
                <div class="camera-scanner-header">
                    <h3 id="camera-scanner-title">📷 Escanear con cámara</h3>
                    <button type="button" class="camera-scanner-close" aria-label="Cerrar">&times;</button>
                </div>
                <div class="camera-scanner-body">
                    <div id="camera-reader-viewport"></div>
                    <div class="camera-scanner-status" id="camera-scanner-status">Iniciando cámara trasera...</div>
                </div>
                <div class="camera-scanner-footer">
                    <button type="button" class="btn btn-secondary camera-scanner-cancel-btn">Cancelar</button>
                </div>
            </div>
        `;

        document.body.appendChild(modal);

        modal.querySelector('.camera-scanner-close').addEventListener('click', stopScanner);
        modal.querySelector('.camera-scanner-cancel-btn').addEventListener('click', stopScanner);

        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                stopScanner();
            }
        });

        return modal;
    }

    async function startScanner() {
        createModal();
        modal.style.display = 'flex';
        const statusEl = document.getElementById('camera-scanner-status');
        statusEl.innerText = 'Apuntá la cámara al código de barras de la prenda...';

        try {
            if (typeof Html5Qrcode === 'undefined') {
                statusEl.innerText = 'Error: No se pudo cargar la librería de escaneo.';
                return;
            }

            if (!html5QrCode) {
                html5QrCode = new Html5Qrcode('camera-reader-viewport');
            }

            const config = {
                fps: 15,
                qrbox: { width: 280, height: 180 },
                aspectRatio: 1.0,
            };

            const qrCodeSuccessCallback = (decodedText, decodedResult) => {
                // Beep o retroalimentación háptica si el celular lo soporta
                if (navigator.vibrate) {
                    navigator.vibrate(100);
                }

                statusEl.innerText = `Código detectado: ${decodedText}`;

                // Detener scanner
                stopScanner();

                // Llenar el input
                inputElement.value = decodedText;

                // Invocar callback de envío
                if (typeof onDetected === 'function') {
                    onDetected(decodedText);
                }
            };

            // Intentar usar cámara trasera ('environment')
            await html5QrCode.start(
                { facingMode: 'environment' },
                config,
                qrCodeSuccessCallback,
                (errorMessage) => {
                    // Errores continuos de escaneo mientras busca código se ignoran
                }
            );
        } catch (err) {
            console.error('Error al iniciar la cámara:', err);
            statusEl.innerText = 'No se pudo acceder a la cámara. Verificá los permisos del navegador o la conexión HTTPS.';
        }
    }

    async function stopScanner() {
        if (html5QrCode && html5QrCode.isScanning) {
            try {
                await html5QrCode.stop();
            } catch (err) {
                console.error('Error al detener la cámara:', err);
            }
        }
        if (modal) {
            modal.style.display = 'none';
        }
    }

    triggerBtn.addEventListener('click', (e) => {
        e.preventDefault();
        startScanner();
    });
}
