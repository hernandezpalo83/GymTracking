import json
from datetime import date, time

from django.test import TestCase, Client
from django.urls import reverse
from users.models import User
from exercises.models import Exercise
from plans.models import TrainingPlan
from .models import WorkoutSession, SessionExercise, ExerciseSet


def make_user(username='user', role=User.ROLE_ATHLETE):
    return User.objects.create_user(username=username, password='pass1234!', role=role)


def make_superuser(username='admin'):
    return User.objects.create_superuser(username=username, password='pass1234!')


def make_exercise(name='Squat', created_by=None):
    return Exercise.objects.create(name=name, created_by=created_by, is_public=True)


def make_plan(name='Plan', created_by=None, assigned_to=None):
    return TrainingPlan.objects.create(
        name=name,
        created_by=created_by,
        assigned_to=assigned_to or created_by,
    )


def make_session(user, plan=None, session_date=None, completed=False):
    return WorkoutSession.objects.create(
        user=user,
        plan=plan,
        date=session_date or date.today(),
        completed=completed,
    )


class WorkoutSessionModelTest(TestCase):
    def setUp(self):
        self.user = make_user()

    def test_create_session(self):
        session = make_session(self.user)
        self.assertEqual(session.user, self.user)
        self.assertFalse(session.completed)
        self.assertIsNone(session.plan)

    def test_session_str(self):
        session = make_session(self.user)
        self.assertIn(str(self.user), str(session))

    def test_session_without_plan(self):
        session = make_session(self.user, plan=None)
        self.assertIsNone(session.plan)

    def test_get_duration_minutes(self):
        session = make_session(self.user)
        session.start_time = time(9, 0)
        session.end_time = time(10, 30)
        session.save()
        self.assertEqual(session.get_duration_minutes(), 90)

    def test_get_duration_minutes_no_times(self):
        session = make_session(self.user)
        self.assertIsNone(session.get_duration_minutes())

    def test_get_mood_emoji(self):
        session = make_session(self.user)
        session.mood = 5
        self.assertEqual(session.get_mood_emoji(), '😄')

    def test_get_mood_emoji_none(self):
        session = make_session(self.user)
        self.assertEqual(session.get_mood_emoji(), '')

    def test_get_total_volume(self):
        superuser = make_superuser()
        exercise = make_exercise(created_by=superuser)
        session = make_session(self.user)
        se = SessionExercise.objects.create(session=session, exercise=exercise)
        ExerciseSet.objects.create(session_exercise=se, set_number=1, reps=10, weight=50)
        ExerciseSet.objects.create(session_exercise=se, set_number=2, reps=8, weight=60)
        self.assertEqual(session.get_total_volume(), 10 * 50 + 8 * 60)

    def test_session_ordering_most_recent_first(self):
        s1 = make_session(self.user, session_date=date(2025, 1, 1))
        s2 = make_session(self.user, session_date=date(2025, 6, 1))
        sessions = list(WorkoutSession.objects.all())
        self.assertEqual(sessions[0], s2)


class SessionExerciseModelTest(TestCase):
    def setUp(self):
        self.user = make_superuser()
        self.exercise = make_exercise(created_by=self.user)
        self.session = make_session(self.user)

    def test_create_session_exercise(self):
        se = SessionExercise.objects.create(session=self.session, exercise=self.exercise)
        self.assertEqual(se.session, self.session)
        self.assertEqual(se.exercise, self.exercise)

    def test_session_exercise_str(self):
        se = SessionExercise.objects.create(session=self.session, exercise=self.exercise)
        self.assertIn(self.exercise.name, str(se))


class ExerciseSetModelTest(TestCase):
    def setUp(self):
        self.user = make_superuser()
        self.exercise = make_exercise(created_by=self.user)
        self.session = make_session(self.user)
        self.se = SessionExercise.objects.create(session=self.session, exercise=self.exercise)

    def test_create_exercise_set(self):
        es = ExerciseSet.objects.create(
            session_exercise=self.se, set_number=1, reps=12, weight=80
        )
        self.assertEqual(es.reps, 12)
        self.assertEqual(float(es.weight), 80.0)
        self.assertTrue(es.completed)

    def test_exercise_set_str(self):
        es = ExerciseSet.objects.create(
            session_exercise=self.se, set_number=1, reps=5, weight=100
        )
        self.assertIn('1', str(es))
        self.assertIn('5', str(es))

    def test_exercise_set_ordering(self):
        ExerciseSet.objects.create(session_exercise=self.se, set_number=3, reps=5, weight=80)
        ExerciseSet.objects.create(session_exercise=self.se, set_number=1, reps=5, weight=80)
        sets = list(self.se.sets.all())
        self.assertEqual(sets[0].set_number, 1)


class SessionListViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = make_user()
        self.other = make_user('other')

    def test_list_requires_login(self):
        r = self.client.get(reverse('sessions:list'))
        self.assertNotEqual(r.status_code, 200)

    def test_list_accessible_when_authenticated(self):
        self.client.login(username='user', password='pass1234!')
        r = self.client.get(reverse('sessions:list'))
        self.assertEqual(r.status_code, 200)

    def test_user_sees_own_sessions(self):
        make_session(self.user)
        self.client.login(username='user', password='pass1234!')
        r = self.client.get(reverse('sessions:list'))
        self.assertEqual(len(r.context['sessions']), 1)

    def test_user_does_not_see_other_sessions(self):
        make_session(self.other)
        self.client.login(username='user', password='pass1234!')
        r = self.client.get(reverse('sessions:list'))
        self.assertEqual(len(r.context['sessions']), 0)


class SessionCreateViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = make_user()

    def test_create_requires_login(self):
        r = self.client.get(reverse('sessions:create'))
        self.assertNotEqual(r.status_code, 200)

    def test_create_accessible_when_authenticated(self):
        self.client.login(username='user', password='pass1234!')
        r = self.client.get(reverse('sessions:create'))
        self.assertEqual(r.status_code, 200)

    def test_user_can_create_session_without_plan(self):
        self.client.login(username='user', password='pass1234!')
        r = self.client.post(reverse('sessions:create'), {
            'date': str(date.today()),
        })
        self.assertTrue(WorkoutSession.objects.filter(user=self.user).exists())

    def test_session_created_with_correct_user(self):
        self.client.login(username='user', password='pass1234!')
        self.client.post(reverse('sessions:create'), {
            'date': str(date.today()),
        })
        session = WorkoutSession.objects.get(user=self.user)
        self.assertEqual(session.user, self.user)


class SessionDetailViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = make_user()
        self.other = make_user('other')
        self.session = make_session(self.user)

    def test_detail_requires_login(self):
        r = self.client.get(reverse('sessions:detail', args=[self.session.pk]))
        self.assertNotEqual(r.status_code, 200)

    def test_owner_can_view_detail(self):
        self.client.login(username='user', password='pass1234!')
        r = self.client.get(reverse('sessions:detail', args=[self.session.pk]))
        self.assertEqual(r.status_code, 200)


class SessionLogViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = make_user()
        self.other = make_user('other')
        self.session = make_session(self.user)

    def test_log_requires_login(self):
        r = self.client.get(reverse('sessions:log', args=[self.session.pk]))
        self.assertNotEqual(r.status_code, 200)

    def test_owner_can_access_log(self):
        self.client.login(username='user', password='pass1234!')
        r = self.client.get(reverse('sessions:log', args=[self.session.pk]))
        self.assertEqual(r.status_code, 200)

    def test_other_user_cannot_access_log(self):
        self.client.login(username='other', password='pass1234!')
        r = self.client.get(reverse('sessions:log', args=[self.session.pk]))
        self.assertEqual(r.status_code, 404)


class AddExerciseToSessionTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = make_superuser()
        self.exercise = make_exercise(created_by=self.user)
        self.session = make_session(self.user)

    def test_add_exercise_requires_login(self):
        r = self.client.post(reverse('sessions:add_exercise', args=[self.session.pk]), {
            'exercise': self.exercise.pk,
        })
        self.assertNotEqual(r.status_code, 200)

    def test_add_exercise_to_session(self):
        self.client.login(username='admin', password='pass1234!')
        r = self.client.post(reverse('sessions:add_exercise', args=[self.session.pk]), {
            'exercise': self.exercise.pk,
        })
        self.assertTrue(SessionExercise.objects.filter(session=self.session).exists())


class LogSetTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = make_superuser()
        self.exercise = make_exercise(created_by=self.user)
        self.session = make_session(self.user)
        self.se = SessionExercise.objects.create(session=self.session, exercise=self.exercise)

    def test_log_set_requires_login(self):
        r = self.client.post(
            reverse('sessions:log_set', args=[self.se.pk]),
            data=json.dumps({'reps': 10, 'weight': 50}),
            content_type='application/json',
        )
        self.assertNotEqual(r.status_code, 200)

    def test_log_set_creates_exercise_set(self):
        self.client.login(username='admin', password='pass1234!')
        r = self.client.post(
            reverse('sessions:log_set', args=[self.se.pk]),
            data=json.dumps({'reps': 10, 'weight': 50, 'set_number': 1}),
            content_type='application/json',
        )
        self.assertEqual(r.status_code, 200)
        data = json.loads(r.content)
        self.assertTrue(data['success'])
        self.assertTrue(ExerciseSet.objects.filter(session_exercise=self.se).exists())

    def test_log_set_updates_sets_completed(self):
        self.client.login(username='admin', password='pass1234!')
        self.client.post(
            reverse('sessions:log_set', args=[self.se.pk]),
            data=json.dumps({'reps': 10, 'weight': 50, 'set_number': 1}),
            content_type='application/json',
        )
        self.se.refresh_from_db()
        self.assertEqual(self.se.sets_completed, 1)


class CompleteSessionTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = make_user()
        self.other = make_user('other')
        self.session = make_session(self.user)

    def test_complete_requires_login(self):
        r = self.client.post(reverse('sessions:complete', args=[self.session.pk]))
        self.assertNotEqual(r.status_code, 200)

    def test_owner_can_complete_session(self):
        self.client.login(username='user', password='pass1234!')
        self.client.post(reverse('sessions:complete', args=[self.session.pk]))
        self.session.refresh_from_db()
        self.assertTrue(self.session.completed)

    def test_other_user_cannot_complete_session(self):
        self.client.login(username='other', password='pass1234!')
        r = self.client.post(reverse('sessions:complete', args=[self.session.pk]))
        self.assertEqual(r.status_code, 404)
