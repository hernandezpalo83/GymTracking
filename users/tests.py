from django.test import TestCase, Client
from django.urls import reverse
from .models import User


def make_user(username='testuser', role=User.ROLE_ATHLETE, **kw):
    return User.objects.create_user(username=username, password='pass1234!', role=role, **kw)


def make_superuser(username='admin'):
    return User.objects.create_superuser(username=username, password='pass1234!')


class UserModelTest(TestCase):
    def test_create_athlete(self):
        u = make_user('athlete1', role=User.ROLE_ATHLETE)
        self.assertTrue(u.is_athlete)
        self.assertFalse(u.is_supervisor)
        self.assertFalse(u.is_superuser)

    def test_create_supervisor(self):
        u = make_user('sup1', role=User.ROLE_SUPERVISOR)
        self.assertTrue(u.is_supervisor)
        self.assertFalse(u.is_athlete)

    def test_dark_mode_default_false(self):
        u = make_user('dm_user')
        self.assertFalse(u.dark_mode)

    def test_supervised_by_relation(self):
        sup = make_user('sup', role=User.ROLE_SUPERVISOR)
        ath = make_user('ath', role=User.ROLE_ATHLETE)
        ath.supervised_by = sup
        ath.save()
        self.assertEqual(ath.supervised_by, sup)
        self.assertIn(ath, sup.athletes.all())

    def test_str_representation(self):
        u = make_user('javi', role=User.ROLE_ATHLETE, first_name='Javi', last_name='Test')
        self.assertIn('Javi', str(u))

    def test_get_role_label_superuser(self):
        u = make_superuser('su')
        self.assertEqual(u.get_role_label(), 'Superusuario')

    def test_get_role_label_athlete(self):
        u = make_user('ath', role=User.ROLE_ATHLETE)
        self.assertEqual(u.get_role_label(), 'Atleta')


class LoginViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = make_user()

    def test_login_page_loads(self):
        r = self.client.get(reverse('users:login'))
        self.assertEqual(r.status_code, 200)

    def test_login_success_redirects(self):
        r = self.client.post(reverse('users:login'), {
            'username': 'testuser', 'password': 'pass1234!'
        })
        self.assertRedirects(r, reverse('reports:dashboard'), fetch_redirect_response=False)

    def test_login_wrong_password(self):
        r = self.client.post(reverse('users:login'), {
            'username': 'testuser', 'password': 'wrongpass'
        })
        self.assertEqual(r.status_code, 200)

    def test_authenticated_redirected_from_login(self):
        self.client.login(username='testuser', password='pass1234!')
        r = self.client.get(reverse('users:login'))
        self.assertRedirects(r, reverse('reports:dashboard'), fetch_redirect_response=False)


class RegisterViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        # Enable registration for tests
        from config.models import SiteSettings
        settings = SiteSettings.get()
        settings.registration_enabled = True
        settings.save()

    def test_register_page_loads(self):
        r = self.client.get(reverse('users:register'))
        self.assertEqual(r.status_code, 200)

    def test_register_creates_user(self):
        r = self.client.post(reverse('users:register'), {
            'username': 'newuser',
            'first_name': 'New',
            'last_name': 'User',
            'email': 'new@test.com',
            'role': User.ROLE_ATHLETE,
            'password1': 'Str0ngP@ss!',
            'password2': 'Str0ngP@ss!',
        })
        self.assertTrue(User.objects.filter(username='newuser').exists())


class ProfileViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = make_user()

    def test_profile_requires_login(self):
        r = self.client.get(reverse('users:profile'))
        self.assertRedirects(r, f"{reverse('users:login')}?next={reverse('users:profile')}",
                             fetch_redirect_response=False)

    def test_profile_loads_when_authenticated(self):
        self.client.login(username='testuser', password='pass1234!')
        r = self.client.get(reverse('users:profile'))
        self.assertEqual(r.status_code, 200)


class AdminPanelTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.superuser = make_superuser()
        self.regular = make_user('regular')

    def test_admin_user_list_requires_superuser(self):
        self.client.login(username='regular', password='pass1234!')
        r = self.client.get(reverse('users:admin_user_list'))
        self.assertRedirects(r, reverse('reports:dashboard'), fetch_redirect_response=False)

    def test_admin_user_list_accessible_to_superuser(self):
        self.client.login(username='admin', password='pass1234!')
        r = self.client.get(reverse('users:admin_user_list'))
        self.assertEqual(r.status_code, 200)

    def test_admin_create_user(self):
        self.client.login(username='admin', password='pass1234!')
        r = self.client.post(reverse('users:admin_user_create'), {
            'username': 'created_user',
            'email': 'c@test.com',
            'role': User.ROLE_ATHLETE,
            'is_active': True,
            'password1': 'Str0ngP@ss!',
            'password2': 'Str0ngP@ss!',
        })
        self.assertTrue(User.objects.filter(username='created_user').exists())

    def test_toggle_active(self):
        self.client.login(username='admin', password='pass1234!')
        target = make_user('toggled')
        self.assertTrue(target.is_active)
        self.client.post(reverse('users:admin_user_toggle_active', args=[target.pk]))
        target.refresh_from_db()
        self.assertFalse(target.is_active)


class AthletesViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.supervisor = make_user('sup', role=User.ROLE_SUPERVISOR)
        self.athlete = make_user('ath', role=User.ROLE_ATHLETE)
        self.athlete.supervised_by = self.supervisor
        self.athlete.save()

    def test_athletes_view_requires_login(self):
        r = self.client.get(reverse('users:athletes'))
        self.assertEqual(r.status_code, 302)

    def test_athletes_view_for_supervisor(self):
        self.client.login(username='sup', password='pass1234!')
        r = self.client.get(reverse('users:athletes'))
        self.assertEqual(r.status_code, 200)

    def test_athlete_cannot_access_athletes_view(self):
        self.client.login(username='ath', password='pass1234!')
        r = self.client.get(reverse('users:athletes'))
        self.assertRedirects(r, reverse('reports:dashboard'), fetch_redirect_response=False)
