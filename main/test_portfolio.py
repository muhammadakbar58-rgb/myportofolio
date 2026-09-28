import uuid

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import Client, TestCase
from django.urls import reverse

from main.forms import ExperienceForm, SkillForm
from main.models import Experience, Skill


class PortfolioItemTests:
    @classmethod
    def setUpTestData(cls):
        users = get_user_model().objects
        cls.user = users.create_user(username="reader")
        cls.editor = users.create_user(username="editor")
        cls.editor.groups.add(Group.objects.create(name="Editor"))
        cls.owner = users.create_superuser(username="owner", email="owner@example.com")
        cls.staff = users.create_user(username="staff", is_staff=True)
        cls.item = cls.model.objects.create(**cls.data)
        cls.list_url = reverse(cls.list_name)
        cls.create_url = reverse(f"main:create_{cls.kind}")
        cls.edit_url = reverse(f"main:update_{cls.kind}", args=[cls.item.pk])
        cls.delete_url = reverse(f"main:delete_{cls.kind}", args=[cls.item.pk])
        cls.star_url = reverse(f"main:toggle_{cls.kind}_star", args=[cls.item.pk])

    def test_role_access_and_management_buttons(self):
        for user, can_edit, can_manage in (
            (None, False, False),
            (self.user, False, False),
            (self.staff, False, False),
            (self.editor, True, False),
            (self.owner, True, True),
        ):
            with self.subTest(user=user):
                self.client.logout()
                if user:
                    self.client.force_login(user)
                response = self.client.get(self.list_url)
                self.assertContains(response, str(self.item))
                for url, visible in (
                    (self.create_url, can_manage),
                    (self.edit_url, can_edit),
                    (self.delete_url, can_manage),
                ):
                    if visible:
                        self.assertContains(response, url)
                    else:
                        self.assertNotContains(response, url)
                for method, url, allowed in (
                    ("get", self.create_url, can_manage),
                    ("post", self.create_url, can_manage),
                    ("get", self.edit_url, can_edit),
                    ("post", self.edit_url, can_edit),
                    ("post", self.delete_url, can_manage),
                ):
                    if allowed:
                        continue
                    result = getattr(self.client, method)(url, self.data if method == "post" else {})
                    if user is None:
                        self.assertRedirects(
                            result, reverse("main:login") + "?next=" + url
                        )
                    else:
                        self.assertEqual(result.status_code, 403)
                self.item.refresh_from_db()
                self.assertEqual(getattr(self.item, self.title_field), self.data[self.title_field])
                self.assertEqual(self.model.objects.count(), 1)

    def test_owner_can_create_and_delete(self):
        self.client.force_login(self.owner)
        response = self.client.get(self.create_url)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["form"].is_bound)
        self.assertNotIn("starred_by", response.context["form"].fields)
        data = {**self.data, self.title_field: "New entry", "starred_by": [self.user.pk]}
        response = self.client.post(self.create_url, data, follow=True)
        self.assertRedirects(response, self.list_url)
        self.assertContains(response, "berhasil ditambahkan")
        created = self.model.objects.get(**{self.title_field: "New entry"})
        self.assertEqual(created.starred_by.count(), 0)
        self.assertEqual(created.description, self.data["description"])
        created.starred_by.add(self.user)
        response = self.client.post(
            reverse(f"main:delete_{self.kind}", args=[created.pk]), follow=True
        )
        self.assertRedirects(response, self.list_url)
        self.assertContains(response, "berhasil dihapus")
        self.assertFalse(self.model.objects.filter(pk=created.pk).exists())
        self.assertTrue(self.model.objects.filter(pk=self.item.pk).exists())

    def test_editor_and_owner_can_update_without_changing_stars(self):
        self.item.starred_by.add(self.user)
        for user in (self.editor, self.owner):
            with self.subTest(user=user):
                self.client.force_login(user)
                response = self.client.get(self.edit_url)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.context["form"].instance.pk, self.item.pk)
                self.assertContains(response, f'action="{self.edit_url}"')
                data = {**self.data, self.title_field: "Updated", "starred_by": [user.pk]}
                response = self.client.post(self.edit_url, data, follow=True)
                self.assertRedirects(response, self.list_url)
                self.assertContains(response, "berhasil diperbarui")
                self.item.refresh_from_db()
                self.assertEqual(getattr(self.item, self.title_field), "Updated")
                self.assertEqual(self.model.objects.count(), 1)
                self.assertEqual(list(self.item.starred_by.all()), [self.user])

    def test_removing_editor_membership_revokes_access(self):
        self.client.force_login(self.editor)
        self.editor.groups.clear()
        for method in ("get", "post"):
            self.assertEqual(
                getattr(self.client, method)(self.edit_url, self.data).status_code, 403
            )

    def test_invalid_create_and_update_preserve_data(self):
        self.client.force_login(self.owner)
        for url in (self.create_url, self.edit_url):
            for data in ({}, {**self.data, self.title_field: "x" * 256}):
                with self.subTest(url=url, data=data):
                    response = self.client.post(url, data)
                    self.assertEqual(response.status_code, 200)
                    self.assertTrue(response.context["form"].errors)
                    self.assertEqual(self.model.objects.count(), 1)
                    self.item.refresh_from_db()
                    self.assertEqual(getattr(self.item, self.title_field), self.data[self.title_field])

    def test_guests_are_sent_to_login_for_star(self):
        response = self.client.get(self.list_url)
        self.assertContains(response, "/login/?next=" + self.list_url)
        self.assertContains(response, '<span class="star-count">0</span>', html=True)
        self.assertRedirects(
            self.client.post(self.star_url),
            reverse("main:login") + "?next=" + self.star_url,
        )
        self.assertEqual(self.item.starred_by.count(), 0)

    def test_all_authenticated_roles_can_toggle_only_their_own_star(self):
        other = self.model.objects.create(**{**self.data, self.title_field: "Other entry"})
        other.starred_by.add(self.staff)
        self.item.starred_by.add(self.staff)
        self.item.starred_by.add(self.staff)
        self.assertEqual(self.item.starred_by.count(), 1)
        for user in (self.user, self.editor, self.owner):
            with self.subTest(user=user):
                self.client.force_login(user)
                response = self.client.post(self.star_url, {"user_id": self.staff.pk}, follow=True)
                self.assertRedirects(response, self.list_url)
                self.assertEqual(self.item.starred_by.count(), 2)
                self.assertTrue(self.item.starred_by.filter(pk=user.pk).exists())
                self.assertContains(response, 'aria-pressed="true"', count=1)
                self.assertContains(response, 'aria-pressed="false"', count=1)
                self.assertContains(response, "Unstar", count=1)
                self.assertContains(response, '<span class="star-count">2</span>', html=True)
                response = self.client.post(self.star_url, follow=True)
                self.assertRedirects(response, self.list_url)
                self.assertEqual(list(self.item.starred_by.all()), [self.staff])
                self.assertEqual(list(other.starred_by.all()), [self.staff])
                self.assertNotContains(response, "Unstar")
        self.client.logout()
        response = self.client.get(self.list_url)
        self.assertContains(response, '<span class="star-count">1</span>', count=2, html=True)

    def test_mutations_require_csrf_and_valid_token_works(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.owner)
        for url in (self.create_url, self.edit_url, self.delete_url, self.star_url):
            self.assertEqual(client.post(url, self.data).status_code, 403)
        self.assertEqual(self.model.objects.count(), 1)
        self.assertEqual(self.item.starred_by.count(), 0)
        client.get(self.list_url)
        token = client.cookies["csrftoken"].value
        for url in (self.create_url, self.edit_url, self.star_url, self.delete_url):
            response = client.post(url, {**self.data, "csrfmiddlewaretoken": token})
            self.assertRedirects(response, self.list_url)
        self.assertFalse(self.model.objects.filter(pk=self.item.pk).exists())
        self.assertEqual(self.model.objects.count(), 1)

    def test_methods_cannot_bypass_post_only_actions(self):
        self.client.force_login(self.owner)
        for url in (self.delete_url, self.star_url):
            for method in ("get", "head", "put", "patch", "delete"):
                self.assertEqual(getattr(self.client, method)(url).status_code, 405)
        for url in (self.create_url, self.edit_url):
            self.assertEqual(self.client.put(url, self.data).status_code, 405)
        self.assertTrue(self.model.objects.filter(pk=self.item.pk).exists())
        self.assertEqual(self.item.starred_by.count(), 0)

    def test_missing_items_return_404(self):
        self.client.force_login(self.owner)
        for action in (f"update_{self.kind}", f"delete_{self.kind}", f"toggle_{self.kind}_star"):
            url = reverse(f"main:{action}", args=[uuid.uuid4()])
            self.assertEqual(self.client.post(url, self.data).status_code, 404)
        self.assertEqual(self.model.objects.count(), 1)


class ExperienceActionsTest(PortfolioItemTests, TestCase):
    model = Experience
    kind = "experience"
    title_field = "title"
    list_name = "main:show_experience"
    data = {
        "title": "Research assistant",
        "description": "Research experience",
        "category": "research",
        "image": "img/research.png",
        "year": "2025 - Present",
    }

    def test_experience_form_handles_optional_fields_and_completion_date(self):
        form = ExperienceForm({
            **self.data, "image": "", "year": "", "thumbnail": "", "ended_at": "",
        })
        self.assertTrue(form.is_valid(), form.errors)
        item = form.save()
        self.assertTrue(item.is_ongoing)
        self.client.force_login(self.editor)
        url = reverse("main:update_experience", args=[item.pk])
        response = self.client.post(url, {
            **self.data, "ended_at": "2026-09-28T15:30",
            "thumbnail": "https://example.com/image.png",
        })
        self.assertRedirects(response, self.list_url)
        item.refresh_from_db()
        self.assertFalse(item.is_ongoing)
        self.assertEqual(item.ended_at.strftime("%Y-%m-%dT%H:%M"), "2026-09-28T15:30")
        response = self.client.get(url)
        self.assertContains(response, 'value="2026-09-28T15:30"')
        for invalid in ({"category": "invalid"}, {"ended_at": "invalid"}, {"thumbnail": "invalid"}):
            form = ExperienceForm({**self.data, **invalid})
            self.assertFalse(form.is_valid())


class SkillActionsTest(PortfolioItemTests, TestCase):
    model = Skill
    kind = "skill"
    title_field = "name"
    list_name = "main:show_skills"
    data = {
        "name": "Python",
        "description": "Building web applications",
        "image": "img/python.png",
    }

    def test_skill_form_requires_existing_model_fields(self):
        self.assertEqual(list(SkillForm().fields), ["name", "description", "image"])
        for field in self.data:
            form = SkillForm({**self.data, field: ""})
            self.assertFalse(form.is_valid())
            self.assertIn(field, form.errors)
