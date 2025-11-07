document.addEventListener("DOMContentLoaded", () => {
    // Toggle para Pedidos
	const togglePedido = document.getElementById("toggle-pedidos");
	const submenuPedido = document.getElementById("submenu-pedidos");

	if (togglePedido && submenuPedido) {
		togglePedido.addEventListener("click", (e) => {
			e.preventDefault();
			if (submenuPedido.style.display === "block") {
				submenuPedido.style.display = "none";
			} else {
				submenuPedido.style.display = "block";
			}
		});
	}

	// Toggle para Catálogo
	const toggleCatalogo = document.getElementById("toggle-catalogos");
	const submenuCatalogo = document.getElementById("submenu-catalogos");

	if (toggleCatalogo && submenuCatalogo) {
		toggleCatalogo.addEventListener("click", (e) => {
			e.preventDefault();
			if (submenuCatalogo.style.display === "block") {
				submenuCatalogo.style.display = "none";
			} else {
				submenuCatalogo.style.display = "block";
			}
		});
	}

	// Toggle para Clientes
	const toggleClientes = document.getElementById("toggle-clientes");
	const submenuClientes = document.getElementById("submenu-clientes");

	if (toggleClientes && submenuClientes) {
		toggleClientes.addEventListener("click", (e) => {
			e.preventDefault();
			if (submenuClientes.style.display === "block") {
				submenuClientes.style.display = "none";
			} else {
				submenuClientes.style.display = "block";
			}
		});
	}

	document.querySelectorAll('.color-box').forEach((box) => {
		const checkbox = box.previousElementSibling;

		// Inicializar estado visual según si ya está checkeado
		if (checkbox.checked) {
			box.classList.add('selected');
		}

		// Evento de clic
		box.addEventListener('click', () => {
			checkbox.checked = !checkbox.checked;
			box.classList.toggle('selected', checkbox.checked);
		});
	});
});

