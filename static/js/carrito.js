// Funciones del Carrito
const CartManager = {
	async loadCart() {
		try {
			const response = await fetch(window.CART_URLS.cartData);
			const data = await response.json();
			this.updateCartUI(data);
		} catch (error) {
			console.error("Error cargando carrito:", error);
		}
	},

	updateCartUI(data) {
		const cartItems = document.getElementById("cartItems");
		const cartBadge = document.getElementById("cartBadge");
		const cartTotal = document.getElementById("cartTotal");
		const cartSummary = document.getElementById("cartSummary");
		const emptyCart = document.getElementById("emptyCart");

		// Actualizar badge
		cartBadge.textContent = data.cantidad_total;

		if (data.items.length === 0) {
			emptyCart.style.display = "block";
			cartSummary.style.display = "none";
			return;
		}

		emptyCart.style.display = "none";
		cartSummary.style.display = "block";

		// Renderizar items
		cartItems.innerHTML = data.items
			.map(
				(item) => `
                    <div class="cart-item" data-item-id="${item.id}">
                        <img src="${item.imagen || "https://via.placeholder.com/80"}" 
                             alt="${item.nombre}" 
                             class="cart-item-image">
                        <div class="cart-item-details">
                            <div class="cart-item-name">${item.nombre}</div>
                            <div class="cart-item-description">
                                Talle: ${item.talle} | Color: ${item.color}
                            </div>
                            <div class="cart-item-price">${item.precio}</div>
                            <div class="cart-item-quantity">
                                <button class="quantity-btn" onclick="CartManager.updateQuantity(${
												item.id
											}, ${item.cantidad - 1})">-</button>
                                <span>${item.cantidad}</span>
                                <button class="quantity-btn" onclick="CartManager.updateQuantity(${
												item.id
											}, ${item.cantidad + 1})">+</button>
                            </div>
                        </div>
                        <div class="cart-item-remove" onclick="CartManager.removeItem(${item.id})">
                            <i class="fas fa-times"></i>
                        </div>
                    </div>
                `
			)
			.join("");

		// Actualizar total
		cartTotal.textContent = `${data.total}`;
	},

	async updateQuantity(itemId, newQuantity) {
		if (newQuantity < 1) {
			this.removeItem(itemId);
			return;
		}

		try {
			const response = await fetch(window.CART_URLS.actualizarCantidad, {
				method: "POST",
				headers: {
					"Content-Type": "application/json",
					"X-CSRFToken": this.getCookie("csrftoken"),
				},
				body: JSON.stringify({
					item_id: itemId,
					cantidad: newQuantity,
				}),
			});

			const data = await response.json();
			if (data.success) {
				this.loadCart();
			} else {
				alert(data.message);
			}
		} catch (error) {
			console.error("Error actualizando cantidad:", error);
		}
	},

	async removeItem(itemId) {
		try {
			const response = await fetch(window.CART_URLS.eliminarDelCarrito, {
				method: "POST",
				headers: {
					"Content-Type": "application/json",
					"X-CSRFToken": this.getCookie("csrftoken"),
				},
				body: JSON.stringify({
					item_id: itemId,
				}),
			});

			const data = await response.json();
			if (data.success) {
				this.loadCart();
			}
		} catch (error) {
			console.error("Error eliminando item:", error);
		}
	},

	getCookie(name) {
		let cookieValue = null;
		if (document.cookie && document.cookie !== "") {
			const cookies = document.cookie.split(";");
			for (let i = 0; i < cookies.length; i++) {
				const cookie = cookies[i].trim();
				if (cookie.substring(0, name.length + 1) === name + "=") {
					cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
					break;
				}
			}
		}
		return cookieValue;
	},
};

// Cargar carrito cuando la página carga
document.addEventListener("DOMContentLoaded", () => {
	CartManager.loadCart();

	// Recargar carrito cuando se pasa el mouse sobre el ícono
	const cartIcon = document.getElementById("cartIcon");
	cartIcon.addEventListener("mouseenter", () => {
		CartManager.loadCart();
	});
});

// Función global para agregar al carrito desde páginas de productos
async function agregarAlCarrito(productoId, colorId, talleId, cantidad = 1) {
	try {
		const response = await fetch(window.CART_URLS.agregarAlCarrito, {
			method: "POST",
			headers: {
				"Content-Type": "application/json",
				"X-CSRFToken": CartManager.getCookie("csrftoken"),
			},
			body: JSON.stringify({
				producto_id: productoId,
				color_id: colorId,
				talle_id: talleId,
				cantidad: cantidad,
			}),
		});

		const data = await response.json();
		if (data.success) {
			CartManager.loadCart();
			alert("✅ Producto agregado al carrito");
		} else {
			alert("❌ " + data.message);
		}
	} catch (error) {
		console.error("Error agregando al carrito:", error);
		alert("Error al agregar el producto");
	}
}
