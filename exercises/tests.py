from django.test import TestCase, Client
from django.urls import reverse
from users.models import User
from .models import Exercise, MuscleGroup


def make_user(username='user', role=User.ROLE_ATHLETE):
    return User.objects.create_user(username=username, password='pass1234!', role=role)


def make_superuser(username='admin'):
    return User.objects.create_superuser(username=username, password='pass1234!')


def make_exercise(name='Press banca', created_by=None, is_public=True):
    ex = Exercise.objects.create(name=name, created_by=created_by, is_public=is_public)
    return ex


class MuscleGroupModelTest(TestCase):
    def test_create_muscle_group(self):
        mg = MuscleGroup.objects.create(name='chest')
        self.assertEqual(str(mg), 'Pecho')

    def test_unique_muscle_group(self):
        MuscleGroup.objects.create(name='back')
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            MuscleGroup.objects.create(name='back')


class ExerciseModelTest(TestCase):
    def setUp(self):
        self.user = make_superuser()

    def test_create_exercise(self):
        ex = make_exercise('Sentadilla', self.user)
        self.assertEqual(ex.name, 'Sentadilla')
        self.assertEqual(ex.exercise_type, 'strength')
        self.assertTrue(ex.is_public)

    def test_exercise_str(self):
        ex = make_exercise('Dominadas', self.user)
        self.assertEqual(str(ex), 'Dominadas')

    def test_exercise_muscle_group_relation(self):
        mg = MuscleGroup.objects.create(name='back')
        ex = make_exercise('Remo', self.user)
        ex.muscle_groups.add(mg)
        self.assertIn(mg, ex.muscle_groups.all())

    def test_exercise_ordering_by_name(self):
        make_exercise('Z exercise', self.user)
        make_exercise('A exercise', self.user)
        exercises = list(Exercise.objects.all())
        self.assertEqual(exercises[0].name, 'A exercise')


class ExerciseListViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = make_user()
        self.superuser = make_superuser()

    def test_list_requires_login(self):
        r = self.client.get(reverse('exercises:list'))
        self.assertNotEqual(r.status_code, 200)

    def test_list_accessible_when_authenticated(self):
        self.client.login(username='user', password='pass1234!')
        r = self.client.get(reverse('exercises:list'))
        self.assertEqual(r.status_code, 200)

    def test_list_shows_public_exercises(self):
        make_exercise('Public ex', self.superuser, is_public=True)
        self.client.login(username='user', password='pass1234!')
        r = self.client.get(reverse('exercises:list'))
        self.assertContains(r, 'Public ex')

    def test_list_hides_private_other_user_exercises(self):
        other = make_user('other')
        make_exercise('Private ex', other, is_public=False)
        self.client.login(username='user', password='pass1234!')
        r = self.client.get(reverse('exercises:list'))
        self.assertNotContains(r, 'Private ex')


class ExerciseCreateViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = make_user()
        self.superuser = make_superuser()

    def test_create_blocked_for_regular_user(self):
        self.client.login(username='user', password='pass1234!')
        r = self.client.get(reverse('exercises:create'))
        self.assertRedirects(r, reverse('exercises:list'), fetch_redirect_response=False)

    def test_create_accessible_for_superuser(self):
        self.client.login(username='admin', password='pass1234!')
        r = self.client.get(reverse('exercises:create'))
        self.assertEqual(r.status_code, 200)

    def test_superuser_can_create_exercise(self):
        self.client.login(username='admin', password='pass1234!')
        r = self.client.post(reverse('exercises:create'), {
            'name': 'New Exercise',
            'description': 'A test exercise',
            'exercise_type': 'strength',
            'is_public': True,
            'muscle_groups': [],
            'met_value': 5.0,
            'rest_time': 60,
        }, follow=True)
        self.assertTrue(Exercise.objects.filter(name='New Exercise').exists())


class ExerciseDeleteViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = make_user()
        self.superuser = make_superuser()
        self.ex = make_exercise('Del Ex', self.superuser)

    def test_delete_blocked_for_regular_user(self):
        self.client.login(username='user', password='pass1234!')
        r = self.client.get(reverse('exercises:delete', args=[self.ex.pk]))
        self.assertRedirects(r, reverse('exercises:list'), fetch_redirect_response=False)

    def test_delete_accessible_for_superuser(self):
        self.client.login(username='admin', password='pass1234!')
        r = self.client.get(reverse('exercises:delete', args=[self.ex.pk]))
        self.assertEqual(r.status_code, 200)

    def test_superuser_can_delete(self):
        self.client.login(username='admin', password='pass1234!')
        self.client.post(reverse('exercises:delete', args=[self.ex.pk]))
        self.assertFalse(Exercise.objects.filter(pk=self.ex.pk).exists())
