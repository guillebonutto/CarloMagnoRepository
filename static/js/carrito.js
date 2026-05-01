/**
 * Carrito de Compras - Carlo Magno
 * Maneja la lógica de agregar, eliminar y actualizar productos mediante AJAX.
 */

// Función auxiliar para obtener el token CSRF de Django
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

/**
 * Agrega un producto al carrito mediante AJAX
 */
async function agregarAlCarrito(productoId, colorId, talleId, cantidad) {
    if (!window.CART_URLS || !window.CART_URLS.agregarAlCarrito) {
        console.error('URL de agregar al carrito no definida');
        throw new Error('Configuración del carrito faltante');
    }

    try {
        const response = await fetch(window.CART_URLS.agregarAlCarrito, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken'),
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: JSON.stringify({
                producto_id: productoId,
                color_id: colorId,
                talle_id: talleId,
                cantidad: cantidad
            })
        });

        const data = await response.json();

        if (data.success) {
            // Actualizar el contador del carrito en el navbar
            const badge = document.getElementById('cartBadge');
            if (badge) {
                badge.textContent = data.cantidad_total;
                badge.classList.add('pulse');
                setTimeout(() => badge.classList.remove('pulse'), 500);
            }

            // Notificar al usuario
            if (typeof mostrarNotificacion !== 'undefined') {
                mostrarNotificacion(data.message, 'success');
            } else {
                alert(data.message);
            }

            // Si estamos en una página que muestra el mini-cart, podríamos recargarlo
            if (typeof actualizarMiniCart === 'function') {
                actualizarMiniCart();
            }
            
            return data;
        } else {
            throw new Error(data.message || 'Error desconocido');
        }
    } catch (error) {
        console.error('Error en agregarAlCarrito:', error);
        throw error;
    }
}

/**
 * Notificación Toast básica (si no existe una global)
 */
function mostrarNotificacion(mensaje, tipo = 'success') {
    // Si ya existe una implementación global, esta función puede ser ignorada
    // Pero la definimos como fallback si es necesario.
    console.log(`[${tipo.toUpperCase()}] ${mensaje}`);
    
    // Implementación simple de Toast de Bootstrap
    const toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
        const container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'toast-container position-fixed bottom-0 end-0 p-3';
        container.style.zIndex = '1100';
        document.body.appendChild(container);
    }

    const toastId = 'toast-' + Date.now();
    const bgColor = tipo === 'success' ? 'bg-success' : 'bg-danger';
    
    const toastHTML = `
        <div id="${toastId}" class="toast align-items-center text-white ${bgColor} border-0" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="d-flex">
                <div class="toast-body">
                    ${mensaje}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        </div>
    `;

    document.getElementById('toast-container').insertAdjacentHTML('beforeend', toastHTML);
    const toastElement = document.getElementById(toastId);
    const toast = new bootstrap.Toast(toastElement, { delay: 3000 });
    toast.show();
    
    toastElement.addEventListener('hidden.bs.toast', () => {
        toastElement.remove();
    });
}
