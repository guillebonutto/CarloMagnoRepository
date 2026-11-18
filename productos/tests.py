from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from .models import Categoria, Color, Producto, ProductoStock, Talle


class IngresoStockPorLectorTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_superuser(
            username='stock-admin',
            email='stock-admin@example.com',
            password='test-password',
        )
        self.client.force_login(self.user)
        self.producto = Producto.objects.create(
            codigo='001234',
            nombre='Producto de prueba',
            descripcion='Producto de prueba',
            precio=100,
            esta_activo=False,
        )
        self.color = Color.objects.create(nombre='Negro', hex_code='#000000')
        self.talle = Talle.objects.create(nombre='Mediano', abbreviation='M')
        self.url = reverse('admin:productos_productostock_recepcion')

    def test_scans_increment_selected_variant_without_activating_product(self):
        payload = {
            'codigo': self.producto.codigo,
            'color': self.color.pk,
            'talle': self.talle.pk,
        }

        response = self.client.post(self.url, payload)
        self.assertRedirects(response, self.url)
        response = self.client.post(self.url, payload)
        self.assertRedirects(response, self.url)

        stock = ProductoStock.objects.get(
            producto=self.producto,
            color=self.color,
            talle=self.talle,
        )
        self.assertEqual(stock.stock, 2)
        self.producto.refresh_from_db()
        self.assertFalse(self.producto.esta_activo)
        self.assertIn(self.color, self.producto.colores.all())

    def test_unknown_code_does_not_change_stock(self):
        response = self.client.post(self.url, {
            'codigo': '999999',
            'color': self.color.pk,
            'talle': self.talle.pk,
        })

        self.assertRedirects(response, self.url)
        self.assertFalse(ProductoStock.objects.exists())

    def test_category_parent_count_includes_nested_products(self):
        parent = Categoria.objects.create(nombre='Pantalones')
        child = Categoria.objects.create(nombre='Jeans', parent=parent)
        grandchild = Categoria.objects.create(nombre='Jean Lona', parent=child)
        self.producto.categoria = grandchild
        self.producto.save()

        response = self.client.get(reverse('categorias'))

        self.assertEqual(response.status_code, 200)
        categories = {category.pk: category for category in response.context['categories']}
        self.assertIn(parent.pk, categories)
        self.assertNotIn(child.pk, categories)
        self.assertNotIn(grandchild.pk, categories)
        self.assertEqual(categories[parent.pk].productos_totales, 1)
        self.assertNotContains(response, 'Jean Lona')
        self.assertContains(response, reverse('detalle_categoria', args=[parent.pk]))

        detail_response = self.client.get(
            reverse('detalle_categoria', args=[parent.pk])
        )
        self.assertEqual(detail_response.status_code, 200)
        self.assertContains(detail_response, 'Pantalones / Jeans / Jean Lona')
        self.assertContains(detail_response, self.producto.nombre)
        self.assertContains(detail_response, 'category-detail-header')
        self.assertContains(detail_response, 'category-product-card')
        self.assertNotContains(detail_response, '>Variantes<')
        self.assertEqual(len(detail_response.context['product_groups']), 1)
        self.assertEqual(
            detail_response.context['product_groups'][0]['productos'],
            [self.producto],
        )

    def test_unused_inicio_category_is_removed(self):
        response = self.client.get(reverse('categorias'))

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Categoria.objects.filter(nombre='Inicio').exists())
        self.assertNotIn(
            'Inicio',
            [category.nombre for category in response.context['categories']],
        )

    def test_admin_product_filter_includes_nested_subcategories(self):
        parent = Categoria.objects.create(nombre='Pantalones')
        child = Categoria.objects.create(nombre='Jeans', parent=parent)
        grandchild = Categoria.objects.create(nombre='Jean Lona', parent=child)
        self.producto.categoria = grandchild
        self.producto.save()

        response = self.client.get(reverse('admin_productos'), {'categoria': parent.pk})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.producto.nombre)

    def test_stock_groups_variants_by_product_initial_in_alphabetical_order(self):
        beta = Producto.objects.create(
            codigo='001235',
            nombre='Beta camisa',
            descripcion='Prueba',
            precio=100,
        )
        alfa = Producto.objects.create(
            codigo='001236',
            nombre='Árbol camisa',
            descripcion='Prueba',
            precio=100,
        )
        ProductoStock.objects.create(
            producto=beta,
            color=self.color,
            talle=self.talle,
            stock=2,
        )
        ProductoStock.objects.create(
            producto=alfa,
            color=self.color,
            talle=self.talle,
            stock=7,
        )

        response = self.client.get(reverse('stock'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [group['letter'] for group in response.context['letter_groups']],
            ['A', 'B'],
        )
        self.assertEqual(
            [item.producto.nombre for item in response.context['letter_groups'][0]['items']],
            ['Árbol camisa'],
        )
        self.assertContains(response, 'stock-letter-A')
        self.assertContains(response, 'stock-letter-B')

    def test_stock_search_matches_code_color_and_talle_and_accepts_sort(self):
        beta = Producto.objects.create(
            codigo='001237',
            nombre='Beta camisa',
            descripcion='Prueba',
            precio=100,
        )
        buzo = Producto.objects.create(
            codigo='001238',
            nombre='Buzo camisa',
            descripcion='Prueba',
            precio=100,
        )
        ProductoStock.objects.create(
            producto=self.producto,
            color=self.color,
            talle=self.talle,
            stock=2,
        )
        ProductoStock.objects.create(
            producto=beta,
            color=self.color,
            talle=self.talle,
            stock=7,
        )
        ProductoStock.objects.create(
            producto=buzo,
            color=self.color,
            talle=self.talle,
            stock=12,
        )

        response = self.client.get(reverse('stock'), {'orden': 'stock_desc'})
        beta_group = next(
            group for group in response.context['letter_groups']
            if group['letter'] == 'B'
        )
        self.assertEqual(
            [item.producto.nombre for item in beta_group['items']],
            ['Buzo camisa', 'Beta camisa'],
        )

        response = self.client.get(reverse('stock'), {
            'buscar': '001237',
            'orden': 'stock_desc',
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_stock_items'], 1)
        self.assertEqual(response.context['sort_by'], 'stock_desc')
        self.assertEqual(response.context['search_query'], '001237')
        self.assertEqual(
            response.context['letter_groups'][0]['items'][0].producto,
            beta,
        )

        response = self.client.get(reverse('stock'), {'buscar': 'Negro'})
        self.assertEqual(response.context['total_stock_items'], 3)

        response = self.client.get(reverse('stock'), {'buscar': 'Mediano'})
        self.assertEqual(response.context['total_stock_items'], 3)

    def test_stock_edit_page_sets_quantity_and_scans_matching_article_code(self):
        stock = ProductoStock.objects.create(
            producto=self.producto,
            color=self.color,
            talle=self.talle,
            stock=4,
        )
        edit_url = reverse('editar_stock', args=[stock.pk])

        page = self.client.get(edit_url)
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, self.producto.nombre)
        self.assertContains(page, 'Guardar stock')
        self.assertContains(page, 'La lectora procesa cada lectura válida')
        self.assertContains(page, 'data-stock-barcode')
        self.assertContains(page, 'requestSubmit()')
        self.assertEqual(page.content.count(b'<form'), 1)
        self.assertEqual(len(page.context['quantity_form'].fields), 1)
        self.assertNotContains(page, 'presioná Enter')

        response = self.client.post(edit_url, {
            'action': 'guardar',
            'stock': 9,
        })
        self.assertRedirects(response, edit_url)
        stock.refresh_from_db()
        self.assertEqual(stock.stock, 9)

        response = self.client.post(edit_url, {
            'action': 'escanear',
            'codigo': self.producto.codigo,
        })
        self.assertRedirects(response, edit_url)
        stock.refresh_from_db()
        self.assertEqual(stock.stock, 10)

        response = self.client.post(edit_url, {
            'action': 'escanear',
            'codigo': '999999',
        }, follow=True)
        stock.refresh_from_db()
        self.assertEqual(stock.stock, 10)
        self.assertContains(response, 'No se modificó el stock')

    def test_stock_list_edit_action_opens_custom_panel_editor(self):
        stock = ProductoStock.objects.create(
            producto=self.producto,
            color=self.color,
            talle=self.talle,
            stock=1,
        )

        response = self.client.get(reverse('stock'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            reverse('editar_stock', args=[stock.pk]),
        )
        self.assertNotContains(
            response,
            f'/admin/productos/productostock/{stock.pk}/change/',
        )
