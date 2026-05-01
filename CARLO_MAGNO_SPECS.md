# Especificaciones del Proyecto: Carlo Magno - E-commerce Premium

Este documento resume la arquitectura, funcionalidades y estado actual del sitio web de Carlo Magno para facilitar el análisis por otras IA.

## 1. Visión General
**Carlo Magno** es un e-commerce de indumentaria masculina premium con un enfoque en diseño de alta gama (estética inspirada en Apple/Luxury) y una experiencia de usuario fluida y reactiva.

## 2. Stack Tecnológico
- **Backend:** Django 5.x (Python)
- **Base de Datos:** SQLite (Desarrollo), preparado para PostgreSQL.
- **Frontend:** HTML5 Semántico, CSS3 Vanilla (con variables :root y animaciones personalizadas), Bootstrap 5.
- **Interactividad:** JavaScript Vanilla (ES6+), AJAX/Fetch API para evitar recargas de página.
- **Integraciones:**
    - **Wavespeed AI:** Probador Virtual (VTON).
    - **Mercado Pago:** Procesamiento de pagos (Checkout Pro y API de tarjetas).

## 3. Funcionalidades Principales

### A. Catálogo y Navegación
- **Filtro 3D de Colores:** Selector de colores con estilo Apple Watch (carrusel 3D que escala y cambia opacidad al centrarse).
- **Filtrado en Tiempo Real (AJAX):** Al deslizar el carrusel de colores o seleccionar filtros, la grilla de productos se actualiza mediante Single Page Application (SPA) behavior sin recargar el navegador.
- **Buscador Inteligente:** Sticky search bar que se mantiene visible al hacer scroll.
- **Estructura de Datos:** Categorías, Marcas, Talles y Colores con relaciones dinámicas y conteo de stock.

### B. Probador Virtual (VTON)
- **Integración con IA:** Peticiones seguras al API de Wavespeed.
- **Optimización en Cliente:** Las fotos de los usuarios se comprimen y redimensionan automáticamente en el navegador (vía Canvas API) a un máximo de 1200px antes de subirse, ahorrando ancho de banda y evitando errores de servidor por archivos pesados.
- **Seguridad:** Validación de tipos MIME, límites de tamaño (15MB en código, 20MB en servidor) y requerimiento de inicio de sesión.

### C. Carrito de Compras
- **Mini-Cart Persistente:** Visualización del carrito en tiempo real en la barra de navegación.
- **Lógica de Stock:** Validación de stock disponible por combinación de color y talle antes de permitir la compra.
- **Checkout:** Proceso de pago integrado con Mercado Pago (soporta tarjetas, transferencia y dinero en cuenta).

### D. Autenticación y Perfil
- **Gestión de Cuentas:** Registro, inicio de sesión y cierre de sesión de clientes.
- **Recuperación de Contraseña:** Sistema seguro basado en tokens HMAC criptográficos (Django built-in) con plantillas de email HTML personalizadas.
- **Perfiles:** Gestión de datos personales y direcciones de envío múltiples.

### E. Panel de Administración (Custom)
- **Dashboard:** Métricas básicas y gestión total de la base de datos (Productos, Clientes, Pedidos, etc.) sin usar el admin nativo de Django, con una interfaz moderna y coherente.

## 4. Detalles de UX/UI Premium
- **Drag & Drop Global:** Soporte para arrastrar con el mouse todas las listas horizontales.
- **Máscaras de Desvanecimiento:** Efectos de gradiente en los bordes de los carruseles para indicar scroll.
- **Micro-interacciones:** Escalamiento suave de productos al pasar el mouse (hover), animaciones de carga (spinners) y notificaciones dinámicas.

## 5. Configuración de Seguridad
- **Upload Limits:** Protegido contra ataques de agotamiento de memoria.
- **Email Backend:** Configuración dinámica que usa la consola en desarrollo (`DEBUG=True`) y SMTP real en producción vía variables de entorno.
- **Protección CSRF:** Implementada en todos los formularios y llamadas a la API.

---
*Este documento fue generado automáticamente por Antigravity (IA Coding Assistant) para resumir el estado del repositorio.*
