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

		// 🔹 Renderizar items del carrito
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
						<div class="cart-item-price">$${item.precio}</div>

						<div class="cart-item-quantity" data-item-id="${item.id}">
							<button class="quantity-btn" onclick="CartManager.changeQuantity(this, -1)">-</button>
							<span>${item.cantidad}</span>
							<button class="quantity-btn" onclick="CartManager.changeQuantity(this, 1)">+</button>
						</div>
					</div>
					<div class="cart-item-remove" onclick="CartManager.removeItem(${item.id})">
						<i class="fas fa-times"></i>
					</div>
				</div>
			`
			)
			.join("");

		// 🔹 Mostrar resumen del carrito (solo total + botón)
		cartSummary.innerHTML = `
			<div class="cart-total">
				<span>Total:</span>
				<span id="cartTotal">$${data.total.toFixed(2)}</span>
			</div>
			<button class="cart-checkout-btn" onclick="window.location.href='${window.CART_URLS.checkout}'">
				Comprar
			</button>
		`;
	},

	updateCartTotal() {
		const itemSubtotals = document.querySelectorAll(".cart-item-subtotal");
		let total = 0;
		itemSubtotals.forEach(sub => {
			const value = parseFloat(sub.textContent.replace("$", "").trim());
			if (!isNaN(value)) total += value;
		});
		document.getElementById("cartTotal").textContent = `$${total.toFixed(2)}`;
	},

	changeQuantity(button, delta) {
		const quantityContainer = button.closest(".cart-item-quantity");
		const span = quantityContainer.querySelector("span");
		const itemId = quantityContainer.dataset.itemId;
		let currentQuantity = parseInt(span.textContent);
		const newQuantity = currentQuantity + delta;

		if (newQuantity < 1) return; // Evita números negativos

		// 🔹 Actualizar visualmente al instante
		span.textContent = newQuantity;

		// 🔹 🔥 Actualizar subtotal visualmente al instante
		const itemElement = button.closest(".cart-item");
		const priceText = itemElement.querySelector(".cart-item-price").textContent.replace("$", "").trim();
		const price = parseFloat(priceText);
		const subtotalElement = itemElement.querySelector(".cart-item-subtotal");
		subtotalElement.textContent = `$${(price * newQuantity).toFixed(2)}`;

		// 🔹 Actualizar total general
		this.updateCartTotal();

		// 🔹 Llamar al backend
		this.updateQuantity(itemId, newQuantity);
	},



	async updateQuantity(itemId, newQuantity) {
		if (newQuantity < 1) return;

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

			if (response.ok) {
				await this.loadCart();
			} else {
			console.error("Error al actualizar cantidad");
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
