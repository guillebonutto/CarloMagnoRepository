 const form = document.getElementById('contactForm');
    const mensajeExito = document.getElementById('mensajeExito');

    form.addEventListener('submit', function (event) {
        event.preventDefault(); // Evita que se envíe el formulario y recargue la página

        // Aquí podrías agregar validaciones adicionales si quieres

        // Mostrar mensaje de éxito
        mensajeExito.style.display = 'block';

        // Limpiar formulario
        form.reset();
    });