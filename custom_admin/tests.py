import re

from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse


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
