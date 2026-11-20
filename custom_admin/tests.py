import re

from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse

from productos.models import Color, Marca, Producto, ProductoStock, Talle


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
