// Preview del talle en tiempo real
const abbreviationInput = document.querySelector('input[name="abbreviation"]');
const sizePreview = document.getElementById("size-preview");

if (abbreviationInput) {
	abbreviationInput.addEventListener("input", function () {
		const value = this.value.trim().toUpperCase();
		sizePreview.textContent = value || "?";
	});

	// Establecer valor inicial si existe
	if (abbreviationInput.value) {
		sizePreview.textContent = abbreviationInput.value.toUpperCase();
	}
}
