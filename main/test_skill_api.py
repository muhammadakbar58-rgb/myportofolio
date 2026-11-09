"""Assignment 6: verify database integrity, input validation, and real CSRF."""
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.urls import reverse
from rest_framework.test import APIClient, APITestCase

from main.models import Skill


class SkillAssignmentAPITest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        users = get_user_model().objects
        cls.owner = users.create_superuser("skill-owner", "owner@example.com", "test-password")
        cls.reader = users.create_user("skill-reader", password="test-password")
        cls.editor = users.create_user("skill-editor", password="test-password")
        cls.editor.groups.add(Group.objects.create(name="Editor"))
        cls.payload = {"name": "Python", "description": "Web applications", "image": "img/pythonpic.png"}
        cls.skill = Skill.objects.create(**cls.payload)
        cls.skill.starred_by.add(cls.reader)
        cls.list_url = reverse("api:skill-list")
        cls.detail_url = reverse("api:skill-detail", args=[cls.skill.pk])
        cls.star_url = reverse("api:skill-star", args=[cls.skill.pk])

    def assert_original_database(self):
        self.assertEqual(Skill.objects.count(), 1)
        self.skill.refresh_from_db()
        for field, value in self.payload.items():
            self.assertEqual(getattr(self.skill, field), value)
        self.assertEqual(list(self.skill.starred_by.values_list("pk", flat=True)), [self.reader.pk])

    def test_every_forbidden_write_preserves_all_fields_rows_and_stars(self):
        for user in (None, self.reader, self.editor):
            self.client.force_authenticate(user)
            operations = [("post", self.list_url), ("delete", self.detail_url)]
            if user != self.editor:
                operations += [("put", self.detail_url), ("patch", self.detail_url)]
            for method, url in operations:
                with self.subTest(user=user, method=method):
                    response = getattr(self.client, method)(
                        url, {**self.payload, "name": "Forbidden", "starred_by": []}, format="json",
                    )
                    self.assertEqual(response.status_code, 403)
                    self.assert_original_database()

        self.client.force_authenticate(None)
        self.assertEqual(self.client.post(self.star_url).status_code, 403)
        self.assert_original_database()

    def test_all_skill_text_fields_are_cleaned_by_api_and_legacy_form(self):
        self.client.force_login(self.owner)
        tagged = {field: "<b>" + value + "</b>" for field, value in self.payload.items()}
        for url, kwargs in (
            (self.list_url, {"format": "json"}),
            (reverse("main:create_skill"), {}),
        ):
            with self.subTest(url=url):
                response = self.client.post(url, tagged, **kwargs)
                self.assertIn(response.status_code, (201, 302))
        self.assertEqual(Skill.objects.count(), 3)
        for item in Skill.objects.all():
            for field, value in self.payload.items():
                self.assertEqual(getattr(item, field), value)

    def test_empty_after_sanitization_cannot_create_or_overwrite_data(self):
        self.client.force_login(self.owner)
        for field in self.payload:
            for value in ("   ", "<b></b>", "<br>"):
                payload = {**self.payload, field: value}
                with self.subTest(field=field, value=value):
                    for method, url in (("post", self.list_url), ("patch", self.detail_url)):
                        response = getattr(self.client, method)(url, payload, format="json")
                        self.assertEqual(response.status_code, 400)
                        self.assertIn(field, response.data)
                        self.assert_original_database()
                    for url in (
                        reverse("main:create_skill"),
                        reverse("main:update_skill", args=[self.skill.pk]),
                    ):
                        response = self.client.post(url, payload)
                        self.assertEqual(response.status_code, 200)
                        self.assertIn(field, response.context["form"].errors)
                        self.assert_original_database()

    def test_real_session_csrf_for_reader_star_and_editor_patch(self):
        for user, method, url, payload in (
            (self.reader, "post", self.star_url, {}),
            (self.editor, "patch", self.detail_url, {"description": "Edited via API"}),
        ):
            with self.subTest(user=user.username):
                client = APIClient(enforce_csrf_checks=True)
                self.assertTrue(client.login(username=user.username, password="test-password"))
                page = client.get(reverse("main:show_skills"))
                self.assertEqual(page.status_code, 200)
                token = client.cookies["csrftoken"].value
                before = Skill.objects.values().get(pk=self.skill.pk)
                stars = set(self.skill.starred_by.values_list("pk", flat=True))
                response = getattr(client, method)(url, payload, format="json")
                self.assertEqual(response.status_code, 403)
                self.assertEqual(Skill.objects.values().get(pk=self.skill.pk), before)
                self.assertEqual(set(self.skill.starred_by.values_list("pk", flat=True)), stars)
                response = getattr(client, method)(
                    url, payload, format="json", HTTP_X_CSRFTOKEN=token,
                )
                self.assertEqual(response.status_code, 200)
                self.skill.refresh_from_db()
                if user == self.reader:
                    self.assertFalse(self.skill.starred_by.filter(pk=user.pk).exists())
                else:
                    self.assertEqual(self.skill.description, payload["description"])

    def test_browsable_api_and_modal_controls_for_each_role(self):
        for user in (None, self.reader, self.editor, self.owner):
            self.client.force_authenticate(None)
            self.client.logout()
            if user:
                self.client.force_login(user)
            with self.subTest(user=user):
                for url in (self.list_url, self.detail_url):
                    response = self.client.get(url, HTTP_ACCEPT="text/html")
                    self.assertEqual(response.status_code, 200)
                    self.assertIn("text/html", response["Content-Type"])
                page = self.client.get(reverse("main:show_skills"))
                self.assertIn("csrftoken", self.client.cookies)
                if user in (self.editor, self.owner):
                    self.assertContains(page, '<dialog id="skill-modal"')
                else:
                    self.assertNotContains(page, '<dialog id="skill-modal"')
                if user == self.owner:
                    self.assertContains(page, 'id="skill-create"')
                else:
                    self.assertNotContains(page, 'id="skill-create"')
