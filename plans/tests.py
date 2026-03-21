from django.test import TestCase, Client
from django.urls import reverse
from users.models import User
from exercises.models import Exercise
from .models import TrainingPlan, PlanExercise


def make_user(username='user', role=User.ROLE_ATHLETE):
    return User.objects.create_user(username=username, password='pass1234!', role=role)


def make_superuser(username='admin'):
    return User.objects.create_superuser(username=username, password='pass1234!')


def make_plan(name='Plan Test', created_by=None, assigned_to=None,
              visibility='particular', is_active=True):
    return TrainingPlan.objects.create(
        name=name,
        created_by=created_by,
        assigned_to=assigned_to or created_by,
        visibility=visibility,
        is_active=is_active,
    )


class TrainingPlanModelTest(TestCase):
    def setUp(self):
        self.user = make_user('athlete', role=User.ROLE_ATHLETE)

    def test_create_plan(self):
        plan = make_plan('Mi Plan', self.user)
        self.assertEqual(plan.name, 'Mi Plan')
        self.assertTrue(plan.is_active)
        self.assertEqual(plan.visibility, 'particular')

    def test_plan_str(self):
        plan = make_plan('Fuerza', self.user)
        self.assertIn('Fuerza', str(plan))

    def test_get_exercises_by_day_empty(self):
        plan = make_plan('Empty Plan', self.user)
        result = plan.get_exercises_by_day()
        self.assertEqual(len(result), 7)
        for day_exercises in result.values():
            self.assertEqual(day_exercises, [])

    def test_visibility_choices(self):
        plan = make_plan('General', self.user, visibility='general')
        self.assertEqual(plan.visibility, 'general')

    def test_plan_ordering_by_created_at(self):
        p1 = make_plan('Plan 1', self.user)
        p2 = make_plan('Plan 2', self.user)
        plans = list(TrainingPlan.objects.all())
        self.assertEqual(plans[0], p2)  # Most recent first


class PlanExerciseModelTest(TestCase):
    def setUp(self):
        self.user = make_superuser()
        self.plan = make_plan('Plan', self.user)
        self.exercise = Exercise.objects.create(name='Squat', created_by=self.user)

    def test_create_plan_exercise(self):
        pe = PlanExercise.objects.create(
            plan=self.plan,
            exercise=self.exercise,
            day_of_week=0,
            sets=3,
            reps=10,
        )
        self.assertEqual(pe.sets, 3)
        self.assertEqual(pe.reps, 10)

    def test_plan_exercise_str(self):
        pe = PlanExercise.objects.create(
            plan=self.plan, exercise=self.exercise, day_of_week=0
        )
        self.assertIn('Squat', str(pe))


class PlanListViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.superuser = make_superuser()
        self.supervisor = make_user('sup', User.ROLE_SUPERVISOR)
        self.athlete = make_user('ath', User.ROLE_ATHLETE)
        self.athlete.supervised_by = self.supervisor
        self.athlete.save()

    def test_list_requires_login(self):
        r = self.client.get(reverse('plans:list'))
        self.assertNotEqual(r.status_code, 200)

    def test_athlete_sees_own_plans(self):
        plan = make_plan('My Plan', self.athlete, self.athlete, visibility='personal')
        self.client.login(username='ath', password='pass1234!')
        r = self.client.get(reverse('plans:list'))
        self.assertContains(r, 'My Plan')

    def test_athlete_sees_general_plans(self):
        general = make_plan('General Plan', self.superuser, visibility='general')
        self.client.login(username='ath', password='pass1234!')
        r = self.client.get(reverse('plans:list'))
        self.assertContains(r, 'General Plan')

    def test_athlete_does_not_see_other_private_plans(self):
        other = make_user('other_ath')
        private = make_plan('Private Plan', other, other, visibility='particular')
        self.client.login(username='ath', password='pass1234!')
        r = self.client.get(reverse('plans:list'))
        self.assertNotContains(r, 'Private Plan')

    def test_supervisor_sees_athlete_plans(self):
        plan = make_plan('Athlete Plan', self.supervisor, self.athlete)
        self.client.login(username='sup', password='pass1234!')
        r = self.client.get(reverse('plans:list'))
        self.assertContains(r, 'Athlete Plan')

    def test_superuser_sees_all_plans(self):
        p1 = make_plan('P1', self.athlete, self.athlete)
        p2 = make_plan('P2', self.supervisor, self.supervisor)
        self.client.login(username='admin', password='pass1234!')
        r = self.client.get(reverse('plans:list'))
        self.assertContains(r, 'P1')
        self.assertContains(r, 'P2')


class PlanCreateViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.athlete = make_user('ath', User.ROLE_ATHLETE)

    def test_create_requires_login(self):
        r = self.client.get(reverse('plans:create'))
        self.assertNotEqual(r.status_code, 200)

    def test_authenticated_can_access_create(self):
        self.client.login(username='ath', password='pass1234!')
        r = self.client.get(reverse('plans:create'))
        self.assertEqual(r.status_code, 200)

    def test_athlete_can_create_plan(self):
        self.client.login(username='ath', password='pass1234!')
        r = self.client.post(reverse('plans:create'), {
            'name': 'New Plan',
            'plan_type': 'weekly',
            'visibility': 'personal',
            'is_active': True,
        })
        self.assertTrue(TrainingPlan.objects.filter(name='New Plan').exists())


class PlanDeletePermissionTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.owner = make_user('owner')
        self.other = make_user('other')
        self.plan = make_plan('Owner Plan', self.owner, self.owner)

    def test_owner_can_access_delete(self):
        self.client.login(username='owner', password='pass1234!')
        r = self.client.get(reverse('plans:delete', args=[self.plan.pk]))
        self.assertEqual(r.status_code, 200)

    def test_non_owner_cannot_delete(self):
        self.client.login(username='other', password='pass1234!')
        r = self.client.get(reverse('plans:delete', args=[self.plan.pk]))
        self.assertEqual(r.status_code, 403)
