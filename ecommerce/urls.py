"""
URL configuration for ecommerce project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.shortcuts import redirect
from django.conf import settings
from django.conf.urls.static import static
from products.views import producto_list, home, producto_detail
from contact.views import contact
from custom_admin import views as admin_views
from products import cart_views
from products import cliente_auth

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home, name='inicio'),
    path('productos/', producto_list, name='productos'),
    path('productos/<int:producto_id>/', producto_detail, name='producto_detail'),
    path('contacto/', contact, name='contact'),
    path('inicio/', lambda request: redirect('inicio')),

    path('panel/', admin_views.dashboard, name='dashboard'),
    path('panel/login/', admin_views.iniciar_sesion, name='login'),
    path('panel/logout/', admin_views.cerrar_sesion, name='logout'),
    
    # Productos
    path('panel/productos/', admin_views.productos, name='admin_productos'),
    path('panel/productos/agregar/', admin_views.agregar_producto, name='agregar_producto'),
    path('panel/productos/<int:pk>/editarar/', admin_views.editar_producto, name='editar_producto'),
    path('panel/productos/<int:pk>/eliminar/', admin_views.eliminar_producto, name='eliminar_producto'),
    
    # Categorías
    path('panel/categorias/', admin_views.categorias, name='categorias'),
    path('panel/categorias/agregar/', admin_views.agregar_categoria, name='agregar_categoria'),
    path('panel/categorias/<int:pk>/editarar/', admin_views.editar_categoria, name='editar_categoria'),
    path('panel/categorias/<int:pk>/eliminar/', admin_views.eliminar_categoria, name='eliminar_categoria'),
    
    # Colores
    path('panel/colores/', admin_views.colores, name='colores'),
    path('panel/colores/agregar/', admin_views.agregar_color, name='agregar_color'),
    path('panel/colores/<int:pk>/editarar/', admin_views.editar_color, name='editar_color'),
    path('panel/colores/<int:pk>/eliminar/', admin_views.eliminar_color, name='eliminar_color'),
    
    # Marcas
    path('panel/marcas/', admin_views.marcas, name='marcas'),
    path('panel/marcas/agregar/', admin_views.agregar_marca, name='agregar_marca'),
    path('panel/marcas/<int:pk>/editarar/', admin_views.editar_marca, name='editar_marca'),
    path('panel/marcas/<int:pk>/eliminar/', admin_views.eliminar_marca, name='eliminar_marca'),

    # Talles
    path('panel/talles/', admin_views.talles, name='talles'),
    path('panel/talles/agregar/', admin_views.agregar_talle, name='agregar_talle'),
    path('panel/talles/<int:pk>/editarar/', admin_views.editar_talle, name='editar_talle'),
    path('panel/talles/<int:pk>/eliminar/', admin_views.eliminar_talle, name='eliminar_talle'),

    # Clientes
    path('panel/clientes/', admin_views.clientes, name='clientes'),
    path('panel/clientes/agregar/', admin_views.agregar_cliente, name='agregar_cliente'),
    path('panel/clientes/<int:pk>/editarar/', admin_views.editar_cliente, name='editar_cliente'),
    path('panel/clientes/<int:pk>/eliminar/', admin_views.eliminar_cliente, name='eliminar_cliente'),

    # Direccioneses
    path('panel/direcciones/', admin_views.direcciones, name='direcciones'),
    path('panel/direcciones/agregar/', admin_views.agregar_direccion, name='agregar_direccion'),
    path('panel/direcciones/<int:pk>/editarar/', admin_views.editar_direccion, name='editar_direccion'),
    path('panel/direcciones/<int:pk>/eliminar/', admin_views.eliminar_direccion, name='eliminar_direccion'),

    # ========== AUTENTICACIÓN DE CLIENTES (NUEVO) ==========
    path('registro/', cliente_auth.registro_cliente, name='registro_cliente'),
    path('login/', cliente_auth.login_cliente, name='login_cliente'),
    path('logout/', cliente_auth.logout_cliente, name='logout_cliente'),
    path('perfil/', cliente_auth.perfil_cliente, name='perfil_cliente'),
    path('perfil/editar/', cliente_auth.editar_perfil, name='editar_perfil'),
    path('perfil/direccion/agregar/', cliente_auth.agregar_direccion, name='agregar_direccion'),
    path('perfil/direccion/<int:direccion_id>/editar/', cliente_auth.editar_direccion, name='editar_direccion'),
    path('perfil/direccion/<int:direccion_id>/eliminar/', cliente_auth.eliminar_direccion, name='eliminar_direccion'),
    
    # URLs del Carrito
    path('carrito/data/', cart_views.get_cart_data, name='cart_data'),
    path('carrito/agregar/', cart_views.agregar_al_carrito, name='agregar_al_carrito'),
    path('carrito/actualizar/', cart_views.actualizar_cantidad, name='actualizar_cantidad'),
    path('carrito/eliminar/', cart_views.eliminar_del_carrito, name='eliminar_del_carrito'),
    path('carrito/vaciar/', cart_views.vaciar_carrito, name='vaciar_carrito'),

    # Stock
    path('panel/stock/', admin_views.stock, name='stock'),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
