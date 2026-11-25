import json
import re
from datetime import datetime, timezone as dt_timezone
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from productos.models import Color, Estilo, Marca, Pedido, Producto, ProductoStock, Talle, Tipo


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class PanelPasswordTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.admin = user_model.objects.create_user(
            username='panel-admin',
            email='admin@example.com',
            password='Old-Complex-Password-739!',
            is_staff=True,
        )
        self.customer = user_model.objects.create_user(
            username='customer',
            email='customer@example.com',
            password='Old-Complex-Password-739!',
        )

    def test_staff_can_change_password_without_losing_session(self):
        self.client.force_login(self.admin)
        page = self.client.get(reverse('cambiar_contrasena'))
        self.assertEqual(page.status_code, 200)

        response = self.client.post(reverse('cambiar_contrasena'), {
            'old_password': 'Old-Complex-Password-739!',
            'new_password1': 'New-Complex-Password-739!',
            'new_password2': 'New-Complex-Password-739!',
        })

        self.assertRedirects(response, reverse('cambiar_contrasena'))
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.check_password('New-Complex-Password-739!'))
        self.assertEqual(int(self.client.session['_auth_user_id']), self.admin.pk)

    def test_non_staff_cannot_use_panel_password_change(self):
        self.client.force_login(self.customer)
        response = self.client.get(reverse('cambiar_contrasena'))

        self.assertRedirects(response, reverse('inicio'))

    def test_reset_request_sends_email_only_to_staff_accounts(self):
        login_page = self.client.get(reverse('login'))
        self.assertContains(login_page, reverse('panel_password_reset'))

        response = self.client.post(reverse('panel_password_reset'), {
            'email': self.customer.email,
        })

        self.assertRedirects(response, reverse('panel_password_reset_done'))
        self.assertEqual(len(mail.outbox), 0)

        response = self.client.post(reverse('panel_password_reset'), {
            'email': self.admin.email,
        })

        self.assertRedirects(response, reverse('panel_password_reset_done'))
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('/panel/recuperar-contrasena/', mail.outbox[0].body)

    def test_staff_can_complete_email_password_reset(self):
        self.client.post(reverse('panel_password_reset'), {'email': self.admin.email})
        reset_url = re.search(
            r'http://testserver(/panel/recuperar-contrasena/[^/\s]+/[^/\s]+/)',
            mail.outbox[0].body,
        ).group(1)

        response = self.client.get(reset_url)
        self.assertEqual(response.status_code, 302)
        reset_url = response.url
        response = self.client.get(reset_url)
        self.assertEqual(response.status_code, 200)
        response = self.client.post(reset_url, {
            'new_password1': 'Reset-Complex-Password-739!',
            'new_password2': 'Reset-Complex-Password-739!',
        })

        self.assertRedirects(response, reverse('panel_password_reset_complete'))
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.check_password('Reset-Complex-Password-739!'))


class PanelProductEditTests(TestCase):
    def setUp(self):
        self.admin = get_user_model().objects.create_user(
            username='product-admin',
            password='Test-Password-739!',
            is_staff=True,
        )
        self.original_brand = Marca.objects.create(nombre='Marca anterior')
        self.updated_brand = Marca.objects.create(nombre='Marca nueva')
        self.product = Producto.objects.create(
            codigo='TEST-PANEL-001',
            nombre='Producto de prueba',
            descripcion='Descripción original',
            precio='100.00',
            marca=self.original_brand,
        )
        self.client.force_login(self.admin)

    def test_edit_form_preserves_barcode_and_saves_brand(self):
        response = self.client.get(
            reverse('editar_producto', args=[self.product.pk]),
        )

        self.assertContains(response, 'name="codigo"')

        response = self.client.post(
            reverse('editar_producto', args=[self.product.pk]),
            {
                'codigo': self.product.codigo,
                'nombre': self.product.nombre,
                'descripcion': self.product.descripcion,
                'precio': str(self.product.precio),
                'categoria': '',
                'marca': str(self.updated_brand.pk),
                'talles': [],
                'esta_activo': 'on',
            },
        )

        self.assertRedirects(response, reverse('admin_productos'))
        self.product.refresh_from_db()
        self.assertEqual(self.product.codigo, 'TEST-PANEL-001')
        self.assertEqual(self.product.marca, self.updated_brand)

    def test_product_create_and_edit_form_save_a_single_style(self):
        first_style = Estilo.objects.create(nombre='Estilo de prueba A')
        second_style = Estilo.objects.create(nombre='Estilo de prueba B')
        first_type = Tipo.objects.create(nombre='Tela de prueba A')
        second_type = Tipo.objects.create(nombre='Tela de prueba B')
        response = self.client.post(
            reverse('agregar_producto'),
            {
                'codigo': 'TEST-PANEL-STYLE-001',
                'nombre': 'Producto con estilo',
                'descripcion': 'Producto de prueba',
                'precio': '100.00',
                'categoria': '',
                'marca': str(self.original_brand.pk),
                'estilo': str(first_style.pk),
                'tipo': str(first_type.pk),
                'talles': [],
                'colores': [],
                'esta_activo': 'on',
            },
        )

        self.assertRedirects(response, reverse('admin_productos'))
        product = Producto.objects.get(codigo='TEST-PANEL-STYLE-001')
        self.assertEqual(product.estilo, first_style)
        self.assertEqual(product.tipo, first_type)

        response = self.client.post(
            reverse('editar_producto', args=[product.pk]),
            {
                'codigo': product.codigo,
                'nombre': product.nombre,
                'descripcion': product.descripcion,
                'precio': str(product.precio),
                'categoria': '',
                'marca': str(self.original_brand.pk),
                'estilo': str(second_style.pk),
                'tipo': str(second_type.pk),
                'talles': [],
                'colores': [],
                'esta_activo': 'on',
            },
        )

        self.assertRedirects(response, reverse('admin_productos'))
        product.refresh_from_db()
        self.assertEqual(product.estilo, second_style)
        self.assertEqual(product.tipo, second_type)

    def test_talles_render_as_abbreviation_badges_in_product_form(self):
        Talle.objects.create(nombre='Mediano', abbreviation='M')

        response = self.client.get(
            reverse('editar_producto', args=[self.product.pk]),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'class="size-option"')
        self.assertContains(response, '>M</span>')

    def test_edit_form_keeps_an_assigned_inactive_style_available(self):
        style = Estilo.objects.create(
            nombre='Estilo inactivo',
            esta_activo=False,
        )
        self.product.estilo = style
        self.product.save(update_fields=['estilo'])

        response = self.client.get(
            reverse('editar_producto', args=[self.product.pk]),
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            str(response.context['form']['estilo'].value()),
            str(style.pk),
        )

    def test_styles_can_be_managed_from_the_panel(self):
        response = self.client.post(reverse('agregar_estilo'), {
            'nombre': 'Estilo de prueba nuevo',
            'order': '1',
            'esta_activo': 'on',
        })

        self.assertRedirects(response, reverse('estilos'))
        self.assertTrue(Estilo.objects.filter(nombre='Estilo de prueba nuevo').exists())
        self.assertContains(
            self.client.get(reverse('estilos')),
            'Estilo de prueba nuevo',
        )

    def test_fabric_types_can_be_managed_from_the_panel(self):
        response = self.client.post(reverse('agregar_tipo'), {
            'nombre': 'Tela de prueba',
            'order': '1',
            'esta_activo': 'on',
        })

        self.assertRedirects(response, reverse('tipos'))
        self.assertTrue(Tipo.objects.filter(nombre='Tela de prueba').exists())
        self.assertContains(self.client.get(reverse('tipos')), 'Tela de prueba')

    def test_product_list_search_finds_product_by_code_without_stock(self):
        product = Producto.objects.get(codigo='001067')
        response = self.client.get(
            reverse('admin_productos'),
            {'buscar': '001067'},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, product.nombre)
        self.assertEqual(list(response.context['productos']), [product])
        self.assertFalse(product.stock_items.exists())

    def test_saving_product_creates_missing_color_size_stock_variants_at_zero(self):
        first_color = Color.objects.create(nombre='Rojo', hex_code='#FF0000')
        second_color = Color.objects.create(nombre='Azul', hex_code='#0000FF')
        size = Talle.objects.create(
            nombre='Mediano',
            abbreviation='M',
        )
        second_size = Talle.objects.create(
            nombre='Grande',
            abbreviation='L',
        )
        response = self.client.post(
            reverse('editar_producto', args=[self.product.pk]),
            {
                'codigo': self.product.codigo,
                'nombre': self.product.nombre,
                'descripcion': self.product.descripcion,
                'precio': str(self.product.precio),
                'categoria': '',
                'marca': str(self.original_brand.pk),
                'talles': [str(size.pk), str(second_size.pk)],
                'colores': [str(first_color.pk), str(second_color.pk)],
                'esta_activo': 'on',
            },
        )

        self.assertRedirects(response, reverse('admin_productos'))
        variants = ProductoStock.objects.filter(producto=self.product)
        self.assertEqual(variants.count(), 4)
        self.assertSetEqual(
            set(variants.values_list('color_id', flat=True)),
            {first_color.pk, second_color.pk},
        )
        self.assertSetEqual(
            set(variants.values_list('talle_id', flat=True)),
            {size.pk, second_size.pk},
        )
        self.assertSetEqual(set(variants.values_list('stock', flat=True)), {0})

    def test_staff_can_receive_stock_from_custom_panel_and_keep_variant_selection(self):
        color = Color.objects.create(nombre='Verde', hex_code='#00FF00')
        size = Talle.objects.create(nombre='Mediano', abbreviation='M')
        self.product.esta_activo = False
        self.product.save(update_fields=['esta_activo'])
        receive_url = reverse('recibir_stock')

        page = self.client.get(receive_url)

        self.assertEqual(page.status_code, 200)
        self.assertContains(page, 'Recibir stock con lector')
        self.assertContains(page, '/static/css/stock.')
        self.assertEqual(page.context['form']['codigo'].field.widget.attrs['autofocus'], True)

        response = self.client.post(receive_url, {
            'codigo': self.product.codigo,
            'color': color.pk,
            'talle': size.pk,
        })

        self.assertRedirects(response, receive_url)
        stock = ProductoStock.objects.get(
            producto=self.product,
            color=color,
            talle=size,
        )
        self.assertEqual(stock.stock, 1)
        self.product.refresh_from_db()
        self.assertTrue(self.product.esta_activo)

        page = self.client.get(receive_url)
        self.assertEqual(str(page.context['form']['color'].value()), str(color.pk))
        self.assertEqual(str(page.context['form']['talle'].value()), str(size.pk))


class PanelReceiveStockModificationTests(TestCase):
    def setUp(self):
        self.admin = get_user_model().objects.create_user(
            username='receive-stock-admin',
            password='Test-Password-739!',
            is_staff=True,
        )
        self.client.force_login(self.admin)
        self.marca_vieja = Marca.objects.create(nombre='Marca vieja')
        self.marca_nueva = Marca.objects.create(nombre='Marca nueva')
        self.color_viejo = Color.objects.create(nombre='Azul', hex_code='#0000FF')
        self.color_nuevo = Color.objects.create(nombre='Rojo', hex_code='#FF0000')
        self.talle_viejo = Talle.objects.create(nombre='Chico', abbreviation='S')
        self.talle_nuevo = Talle.objects.create(nombre='Grande', abbreviation='L')
        self.producto = Producto.objects.create(
            codigo='MOD-001',
            nombre='Camisa de prueba',
            descripcion='Descripción de prueba',
            precio='100.00',
            marca=self.marca_vieja,
        )
        self.stock = ProductoStock.objects.create(
            producto=self.producto,
            color=self.color_viejo,
            talle=self.talle_viejo,
            stock=7,
        )
        self.receive_url = reverse('recibir_stock')
        self.modify_url = reverse('api_modificar_stock')

    def _payload(self, **overrides):
        payload = {
            'codigo': self.producto.codigo,
            'color': self.color_viejo.pk,
            'talle': self.talle_viejo.pk,
            'marca': self.marca_vieja.pk,
            'stock_id': self.stock.pk,
        }
        payload.update(overrides)
        return payload

    def test_receive_stock_page_exposes_modify_button_and_brand_field(self):
        page = self.client.get(self.receive_url)

        self.assertEqual(page.status_code, 200)
        self.assertContains(page, 'id="btn-modify-stock"')
        self.assertContains(page, 'Modificar')
        self.assertContains(page, 'name="marca"')
        self.assertContains(page, self.modify_url)

    def test_modify_updates_brand_without_creating_brand_or_changing_stock(self):
        marcas_iniciales = Marca.objects.count()
        response = self.client.post(
            self.modify_url,
            self._payload(marca=self.marca_nueva.pk),
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'], data)
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.marca, self.marca_nueva)
        self.assertEqual(Marca.objects.count(), marcas_iniciales)
        self.stock.refresh_from_db()
        self.assertEqual(self.stock.stock, 7)

    def test_modify_moves_wrong_variant_to_correct_color_and_size(self):
        response = self.client.post(
            self.modify_url,
            self._payload(
                color=self.color_nuevo.pk,
                talle=self.talle_nuevo.pk,
            ),
        )

        data = response.json()
        self.assertTrue(data['success'], data)
        # Se reutiliza la misma variante: cambia color/talle, no se crea otra.
        self.stock.refresh_from_db()
        self.assertEqual(self.stock.color_id, self.color_nuevo.pk)
        self.assertEqual(self.stock.talle_id, self.talle_nuevo.pk)
        self.assertEqual(self.stock.stock, 7)
        self.assertFalse(
            ProductoStock.objects.filter(
                producto=self.producto,
                color=self.color_viejo,
                talle=self.talle_viejo,
            ).exists()
        )
        self.assertEqual(len(data['stocks']), 1)

    def test_modify_merges_stock_when_correct_variant_already_exists(self):
        destino = ProductoStock.objects.create(
            producto=self.producto,
            color=self.color_nuevo,
            talle=self.talle_nuevo,
            stock=3,
        )

        response = self.client.post(
            self.modify_url,
            self._payload(
                color=self.color_nuevo.pk,
                talle=self.talle_nuevo.pk,
            ),
        )

        data = response.json()
        self.assertTrue(data['success'])
        self.assertFalse(ProductoStock.objects.filter(pk=self.stock.pk).exists())
        destino.refresh_from_db()
        self.assertEqual(destino.stock, 10)
        self.assertEqual(ProductoStock.objects.filter(producto=self.producto).count(), 1)

    def test_ajax_lookup_includes_brand_and_variant_id(self):
        response = self.client.get(
            self.receive_url,
            {'buscar_codigo': self.producto.codigo},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )

        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['producto']['marca_id'], self.marca_vieja.pk)
        self.assertEqual(data['stocks'][0]['id'], self.stock.pk)

    def test_receiving_stock_also_saves_selected_brand(self):
        response = self.client.post(
            self.receive_url,
            {
                'codigo': self.producto.codigo,
                'color': self.color_viejo.pk,
                'talle': self.talle_viejo.pk,
                'marca': self.marca_nueva.pk,
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )

        data = response.json()
        self.assertTrue(data['success'])
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.marca, self.marca_nueva)
        self.assertEqual(data['producto']['marca_id'], self.marca_nueva.pk)


class PanelDashboardMetricsTests(TestCase):
    def setUp(self):
        self.admin = get_user_model().objects.create_user(
            username='dashboard-admin',
            password='Test-Password-739!',
            is_staff=True,
        )
        self.client.force_login(self.admin)
        self.año_actual = timezone.now().year

    def _crear_pedido(self, total, estado='pagado', anio=None, mes=1, dia=10):
        pedido = Pedido.objects.create(
            email='cliente@example.com',
            nombre_completo='Cliente de prueba',
            direccion='Calle de prueba 123',
            total=Decimal(total),
            estado_pago=estado,
        )
        if anio is not None:
            Pedido.objects.filter(pk=pedido.pk).update(
                fecha_creacion=datetime(anio, mes, dia, tzinfo=dt_timezone.utc),
            )
        return pedido

    def test_dashboard_groups_sales_by_month_and_year_in_one_aggregation(self):
        self._crear_pedido('100.00', anio=self.año_actual, mes=3)
        self._crear_pedido('50.00', anio=self.año_actual, mes=3)
        self._crear_pedido('25.00', anio=self.año_actual - 1, mes=3)
        self._crear_pedido(
            '999.00',
            estado='pendiente',
            anio=self.año_actual,
            mes=4,
        )

        response = self.client.get(reverse('dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['ventas_totales'], Decimal('175.00'))
        self.assertEqual(response.context['cantidad_pedidos'], 3)

        actual = json.loads(response.context['forecast_actual_json'])
        anterior = json.loads(response.context['tendencia_año_anterior_json'])
        self.assertEqual(actual[2], 150.0)
        self.assertEqual(anterior[2], 25.0)
        self.assertEqual(actual[3], 0.0)

