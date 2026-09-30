from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import Client, TestCase
from django.urls import reverse

from main.models import Project


class ProjectAjaxTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        users = get_user_model().objects
        cls.owner = users.create_superuser(username="owner", email="owner@example.com")
        cls.reader = users.create_user(username="reader")
        cls.staff = users.create_user(username="staff", is_staff=True)
        cls.editor = users.create_user(username="editor")
        cls.editor.groups.add(Group.objects.create(name="Editor"))
        cls.data = {
            "title": "AJAX Portfolio",
            "description": "An interactive portfolio",
            "tech_stack": "Django, JavaScript",
            "project_url": "https://example.com/project",
            "project_image_url": "",
        }
        cls.project = Project.objects.create(**cls.data)
        cls.create_url = reverse("main:create_project_ajax")
        cls.json_url = reverse("main:get_projects_json")
        cls.list_url = reverse("main:show_projects")

    def test_only_superuser_can_create_via_ajax(self):
        for user in (None, self.reader, self.staff, self.editor):
            with self.subTest(user=user):
                self.client.logout()
                if user:
                    self.client.force_login(user)
                response = self.client.post(self.create_url, self.data)
                self.assertEqual(response.status_code, 403)
                self.assertIn("message", response.json())
                self.assertEqual(Project.objects.count(), 1)
        self.client.force_login(self.owner)
        response = self.client.post(self.create_url, {
            **self.data, "title": "New project", "starred_by": [self.reader.pk],
        })
        self.assertEqual(response.status_code, 201)
        created = Project.objects.get(pk=response.json()["pk"])
        self.assertEqual(created.title, "New project")
        self.assertEqual(created.starred_by.count(), 0)
        self.assertEqual(Project.objects.count(), 2)

    def test_ajax_creation_only_accepts_post(self):
        self.client.force_login(self.owner)
        for method in ("get", "head", "put", "patch", "delete"):
            self.assertEqual(getattr(self.client, method)(self.create_url).status_code, 405)
        self.assertEqual(Project.objects.count(), 1)

    def test_invalid_ajax_forms_return_field_errors_without_saving(self):
        self.client.force_login(self.owner)
        for field, value in (
            ("title", "   "), ("title", "x" * 256),
            ("title", '<img src="x" onerror="alert(1)">'),
            ("description", ""), ("tech_stack", ""),
            ("project_url", "javascript:alert(1)"),
            ("project_image_url", "data:text/html,test"),
        ):
            with self.subTest(field=field, value=value):
                response = self.client.post(self.create_url, {**self.data, field: value})
                self.assertEqual(response.status_code, 400)
                self.assertIn(field, response.json()["errors"])
                self.assertEqual(Project.objects.count(), 1)

    def test_sanitization_applies_to_ajax_and_existing_create_and_edit(self):
        self.client.force_login(self.owner)
        for url in (
            self.create_url,
            reverse("main:create_project"),
            reverse("main:update_project", args=[self.project.pk]),
        ):
            with self.subTest(url=url):
                response = self.client.post(url, {
                    **self.data, "title": "Hello <b>world</b>",
                    "description": "<p>Details</p>", "tech_stack": "<b>Django</b>",
                })
                self.assertIn(response.status_code, (201, 302))
                saved = Project.objects.filter(title="Hello world").last()
                self.assertEqual(saved.description, "Details")
                self.assertEqual(saved.tech_stack, "Django")

    def test_ajax_csrf_header_is_required_and_validated(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.owner)
        self.assertEqual(client.post(self.create_url, self.data).status_code, 403)
        client.get(self.list_url)
        token = client.cookies["csrftoken"].value
        self.assertEqual(client.post(
            self.create_url, self.data, HTTP_X_CSRFTOKEN="invalid",
        ).status_code, 403)
        self.assertEqual(Project.objects.count(), 1)
        response = client.post(self.create_url, self.data, HTTP_X_CSRFTOKEN=token)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Project.objects.count(), 2)

    def test_existing_mutations_accept_csrf_header_and_keep_permissions(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.owner)
        client.get(self.list_url)
        token = client.cookies["csrftoken"].value
        for route in ("update_project", "toggle_star", "delete_project"):
            url = reverse("main:" + route, args=[self.project.pk])
            self.assertEqual(client.post(url, self.data).status_code, 403)
            self.assertEqual(client.post(
                url, self.data, HTTP_X_CSRFTOKEN=token,
            ).status_code, 302)
        self.assertFalse(Project.objects.filter(pk=self.project.pk).exists())

    def test_json_star_metadata_is_specific_to_logged_in_user(self):
        self.project.starred_by.add(self.reader)
        for user, expected in ((None, False), (self.reader, True), (self.owner, False)):
            with self.subTest(user=user):
                self.client.logout()
                if user:
                    self.client.force_login(user)
                response = self.client.get(self.json_url, {"title": "  portfolio  "})
                item = response.json()[0]
                self.assertEqual(item["pk"], str(self.project.pk))
                self.assertEqual(item["fields"]["is_starred"], expected)
                self.assertEqual(item["fields"]["star_count"], 1)
                self.assertEqual(item["fields"]["starred_by_names"], "reader")
                self.assertNotIn("starred_by", item["fields"])
                self.assertIn("no-store", response["Cache-Control"])
        self.assertEqual(self.client.get(self.json_url, {"title": "missing"}).json(), [])

    def test_modal_visibility_csrf_and_fallback_cards(self):
        for user in (None, self.reader, self.editor, self.owner):
            with self.subTest(user=user):
                self.client.logout()
                if user:
                    self.client.force_login(user)
                response = self.client.get(self.list_url)
                self.assertContains(response, self.project.title)
                self.assertContains(response, "js/projects.js")
                self.assertContains(response, "js/toast.js")
                self.assertContains(response, 'name="csrfmiddlewaretoken"')
                self.assertIn("csrftoken", response.cookies)
                if user == self.owner:
                    self.assertContains(response, 'id="project-form"')
                    self.assertContains(response, f'data-ajax-url="{self.create_url}"')
                else:
                    self.assertNotContains(response, 'id="project-form"')

    def test_stored_html_is_escaped_in_fallback_cards(self):
        self.project.title = '<img src="x" onerror="alert(1)">'
        self.project.save()
        response = self.client.get(self.list_url)
        self.assertNotContains(response, self.project.title)
        self.assertContains(response, "&lt;img")
        # JSON keeps the raw text; projects.js must escape it at the rendering boundary.
        self.assertEqual(self.client.get(self.json_url).json()[0]["fields"]["title"], self.project.title)


class AuthenticationRegressionTest(TestCase):
    def test_registration_login_csrf_rotation_session_and_logout_cookie(self):
        client = Client(enforce_csrf_checks=True)
        credentials = {"username": "newvisitor", "password": "Tutorial-05-example-pass"}
        client.get(reverse("main:register"))
        registration = {
            "username": credentials["username"],
            "password1": credentials["password"],
            "password2": credentials["password"],
        }
        self.assertEqual(client.post(reverse("main:register"), registration).status_code, 403)
        response = client.post(
            reverse("main:register"), registration,
            HTTP_X_CSRFTOKEN=client.cookies["csrftoken"].value,
        )
        self.assertRedirects(response, reverse("main:login"))
        old_token = client.cookies["csrftoken"].value
        response = client.post(reverse("main:login"), credentials, HTTP_X_CSRFTOKEN=old_token)
        self.assertRedirects(response, reverse("main:show_main"))
        self.assertIn("_auth_user_id", client.session)
        self.assertIn("last_login", response.cookies)
        self.assertNotEqual(client.cookies["csrftoken"].value, old_token)
        self.assertContains(client.get(reverse("main:show_main")), client.cookies["last_login"].value)
        response = client.get(reverse("main:logout"))
        self.assertRedirects(response, reverse("main:show_main"))
        self.assertNotIn("_auth_user_id", client.session)
        self.assertEqual(response.cookies["last_login"]["max-age"], 0)
