from django.templatetags.static import static
import uuid

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from main.forms import ProjectForm
from main.models import Experience, Project, Skill


class MainTest(TestCase):
    def setUp(self):
        self.experience = Experience.objects.create(
            title="Asisten Dosen PBP",
            description="Membantu mahasiswa memahami pengembangan web.",
            category="part-time",
        )

    def test_main_url_is_accessible(self):
        response = self.client.get(reverse("main:show_main"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "index.html")
        self.assertNotContains(response, self.experience.title)
        self.assertContains(response, f'href="{reverse("main:show_experience")}"')

    def test_nonexistent_page_returns_404(self):
        response = self.client.get("/halaman-yang-tidak-ada/")

        self.assertEqual(response.status_code, 404)

    def test_experience_model(self):
        self.assertEqual(str(self.experience), "Asisten Dosen PBP")
        self.assertEqual(self.experience.category, "part-time")
        self.assertTrue(self.experience.is_ongoing)

    def test_experience_page(self):
        response = self.client.get(reverse("main:show_experience"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "experience.html")
        self.assertContains(response, self.experience.title)
        self.assertContains(response, self.experience.description)
        self.assertNotContains(response, "Part-Time")
        self.assertNotContains(response, 'class="experience-category"')
        self.assertNotContains(response, 'class="experience-status"')
        self.assertNotContains(response, "Sedang berlangsung")
        self.assertContains(response, f'href="{reverse("main:show_main")}"')

    def test_experience_optional_fields_default_to_empty(self):
        self.experience.refresh_from_db()
        self.assertEqual(self.experience.image, "")
        self.assertEqual(self.experience.year, "")
        self.experience.full_clean()

        response = self.client.get(reverse("main:show_experience"))

        self.assertContains(response, self.experience.title)
        self.assertNotContains(response, 'class="experience-image"')
        self.assertNotContains(response, 'class="experience-year"')

    def test_experience_image_and_year(self):
        for year, image_path in (
            ("2025 - Present", "img/ongoing-experience.png"),
            ("2024 - 2025", "img/completed-experience.png"),
            ("2024", "img/single-year-experience.png"),
        ):
            with self.subTest(year=year):
                self.experience.image = image_path
                self.experience.year = year
                self.experience.full_clean()
                self.experience.save()
                self.experience.refresh_from_db()
                self.assertEqual(self.experience.image, image_path)
                self.assertEqual(self.experience.year, year)

                response = self.client.get(reverse("main:show_experience"))

                self.assertContains(
                    response,
                    f'<img class="experience-image" src="{static(image_path)}" '
                    f'alt="{self.experience.title}" width="96" height="96" loading="lazy">',
                    html=True,
                )
                self.assertContains(
                    response, f'<p class="experience-year">{year}</p>', html=True
                )
                self.assertContains(response, self.experience.title)
                self.assertContains(response, self.experience.description)
                self.assertNotContains(response, "Part-Time")

    def test_empty_experience_page(self):
        Experience.objects.all().delete()
        response = self.client.get(reverse("main:show_experience"))

        self.assertContains(response, "Belum ada pengalaman yang ditambahkan.")

    def test_completed_experience(self):
        self.experience.ended_at = timezone.now()
        self.experience.save()
        response = self.client.get(reverse("main:show_experience"))

        self.assertFalse(self.experience.is_ongoing)
        self.assertNotContains(response, "Selesai")
        self.assertNotContains(response, "Sedang berlangsung")


class SkillsTest(TestCase):
    def test_skills_url_and_template(self):
        self.assertEqual(reverse("main:show_skills"), "/skills/")
        response = self.client.get("/skills/")

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "skills.html")

    def test_skills_from_database_appear_in_html(self):
        skills = [
            Skill.objects.create(
                name="Analisis Data",
                description="Mengolah data menjadi informasi yang berguna.",
                image="img/analysis.png",
            ),
            Skill.objects.create(
                name="Desain Antarmuka",
                description="Membuat antarmuka yang mudah digunakan.",
                image="img/design.png",
            ),
        ]
        response = self.client.get(reverse("main:show_skills"))

        self.assertCountEqual(response.context["skill_list"], skills)
        for skill in skills:
            self.assertContains(response, skill.name)
            self.assertContains(response, skill.description)
            self.assertContains(response, f'src="{static(skill.image)}"')
        self.assertNotContains(response, "Belum ada skill yang ditambahkan.")

    def test_empty_skills_page(self):
        response = self.client.get(reverse("main:show_skills"))

        self.assertContains(response, "Belum ada skill yang ditambahkan.")
        self.assertNotContains(response, 'class="skill-image"')

    def test_skills_link_in_portfolio_navbars(self):
        for page in ("main:show_main", "main:show_experience", "main:show_skills"):
            with self.subTest(page=page):
                response = self.client.get(reverse(page))
                self.assertContains(
                    response,
                    f'<a href="{reverse("main:show_skills")}">Skills</a>',
                    html=True,
                )

class ProjectCRUDTest(TestCase):
    def setUp(self):
        self.admin = get_user_model().objects.create_superuser(
            username="owner", email="owner@example.com", password="test-password"
        )
        self.client.force_login(self.admin)
        self.data = {
            "title": "Portfolio Django",
            "description": "Website portfolio dengan CRUD.",
            "tech_stack": "Django, Python",
            "project_url": "https://example.com/project",
            "project_image_url": "https://example.com/image.png",
        }
        self.project = Project.objects.create(**self.data)
        self.list_url = reverse("main:show_projects")
        self.create_url = reverse("main:create_project")
        self.update_url = reverse("main:update_project", args=[self.project.pk])
        self.delete_url = reverse("main:delete_project", args=[self.project.pk])
        self.json_url = reverse("main:get_projects_json")

    def test_form_exposes_all_editable_fields(self):
        expected = [
            field.name for field in Project._meta.fields
            if field.editable and not field.primary_key
        ]
        self.assertEqual(list(ProjectForm().fields), expected)
        self.assertEqual(len(expected), 5)
        self.assertNotIn("id", ProjectForm().fields)

    def test_all_pages_inherit_base_and_link_projects(self):
        for url in (
            reverse("main:show_main"), reverse("main:show_experience"),
            reverse("main:show_skills"), self.list_url,
            self.create_url, self.update_url,
        ):
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)
                self.assertTemplateUsed(response, "base.html")
                self.assertContains(response, "<!DOCTYPE html>", count=1)
                self.assertContains(response, 'class="site-header"', count=1)
                self.assertContains(response, f'href="{self.list_url}">Projects</a>')

    def test_list_renders_project_data_and_actions_without_javascript(self):
        response = self.client.get(self.list_url)
        self.assertContains(response, self.project.title)
        self.assertContains(response, f'href="{self.update_url}"')
        self.assertContains(response, f'action="{self.delete_url}"')
        self.assertContains(response, 'src="/static/js/projects.js"')
        self.assertNotContains(response, "<template")
        self.assertNotContains(response, "data-json-url")
        self.assertContains(response, f'src="{self.data["project_image_url"]}"')
        self.assertContains(response, f'href="{self.data["project_url"]}"')
        projects = response.context["project_list"]
        self.assertEqual(len(projects), 1)
        self.assertEqual(projects[0].pk, self.project.pk)
        for field, value in self.data.items():
            self.assertEqual(getattr(projects[0], field), value)
        self.assertEqual(Project.objects.count(), 1)
        self.assertContains(response, "Muhammad Akbar Rinaldy")
        self.assertContains(response, "csrfmiddlewaretoken")

    def test_create_get_is_empty_and_post_persists_all_fields(self):
        response = self.client.get(self.create_url)
        self.assertFalse(response.context["form"].is_bound)
        self.assertIsNone(response.context["form"].initial.get("title"))
        data = {**self.data, "title": "New Project"}
        response = self.client.post(self.create_url, data, follow=True)
        self.assertRedirects(response, self.list_url)
        created = Project.objects.get(title=data["title"])
        for field, value in data.items():
            self.assertEqual(getattr(created, field), value)
        self.assertContains(response, "Proyek baru berhasil ditambahkan!")
        self.assertEqual(Project.objects.count(), 2)

    def test_empty_post_displays_validation_errors(self):
        response = self.client.post(self.create_url, {})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["form"].is_bound)
        for field in ("title", "description", "tech_stack"):
            self.assertIn(field, response.context["form"].errors)
        self.assertEqual(Project.objects.count(), 1)

    def test_invalid_create_does_not_save(self):
        for invalid in (
            {"title": ""}, {"title": "x" * 256}, {"description": ""},
            {"tech_stack": ""}, {"project_url": "not a url"},
            {"project_image_url": "not a url"},
        ):
            with self.subTest(invalid=invalid):
                response = self.client.post(self.create_url, {**self.data, **invalid})
                self.assertEqual(response.status_code, 200)
                self.assertTrue(response.context["form"].errors)
                self.assertEqual(Project.objects.count(), 1)

    def test_optional_urls_can_be_blank(self):
        data = {**self.data, "project_url": "", "project_image_url": ""}
        self.assertTrue(ProjectForm(data).is_valid())
        response = self.client.post(self.create_url, data)
        self.assertRedirects(response, self.list_url)
        self.assertTrue(Project.objects.filter(project_url="", project_image_url="").exists())

    def test_update_get_prefills_every_field_and_correct_action(self):
        response = self.client.get(self.update_url)
        for field, value in self.data.items():
            self.assertEqual(response.context["form"].initial[field], value)
        self.assertContains(response, f'action="{self.update_url}"')
        self.assertContains(response, "Simpan Perubahan")

    def test_update_saves_same_record_and_json_reflects_changes(self):
        data = {
            "title": "Updated Portfolio",
            "description": "Updated description",
            "tech_stack": "Django, JavaScript",
            "project_url": "",
            "project_image_url": "https://example.com/new.png",
        }
        response = self.client.post(self.update_url, data, follow=True)
        self.assertRedirects(response, self.list_url)
        self.assertContains(response, "Proyek berhasil diperbarui!")
        self.project.refresh_from_db()
        for field, value in data.items():
            self.assertEqual(getattr(self.project, field), value)
        self.assertEqual(Project.objects.count(), 1)
        self.assertEqual(
            {key: value for key, value in self.client.get(self.json_url).json()[0]["fields"].items()
             if key in data}, data,
        )

    def test_invalid_update_preserves_database_and_submitted_values(self):
        data = {**self.data, "title": "Unsaved title", "project_url": "invalid"}
        response = self.client.post(self.update_url, data)
        self.assertEqual(response.status_code, 200)
        self.assertIn("project_url", response.context["form"].errors)
        self.assertEqual(response.context["form"]["title"].value(), data["title"])
        self.project.refresh_from_db()
        self.assertEqual(self.project.title, self.data["title"])

    def test_delete_only_accepts_post(self):
        for method in ("get", "head", "put", "delete"):
            with self.subTest(method=method):
                response = getattr(self.client, method)(self.delete_url)
                self.assertEqual(response.status_code, 405)
                self.assertTrue(Project.objects.filter(pk=self.project.pk).exists())
        response = self.client.post(self.delete_url, follow=True)
        self.assertRedirects(response, self.list_url)
        self.assertContains(response, "Project berhasil dihapus!")
        self.assertFalse(Project.objects.filter(pk=self.project.pk).exists())
        self.assertEqual(self.client.get(self.json_url).json(), [])

    def test_unknown_project_returns_404(self):
        unknown_id = uuid.uuid4()
        update_url = reverse("main:update_project", args=[unknown_id])
        delete_url = reverse("main:delete_project", args=[unknown_id])
        self.assertEqual(self.client.get(update_url).status_code, 404)
        self.assertEqual(self.client.post(update_url, self.data).status_code, 404)
        self.assertEqual(self.client.post(delete_url).status_code, 404)

    def test_json_returns_every_record_and_field(self):
        other = Project.objects.create(**{**self.data, "title": "Another project"})
        response = self.client.get(self.json_url)
        self.assertEqual(response["Content-Type"], "application/json")
        data = {item["pk"]: item for item in response.json()}
        self.assertEqual(set(data), {str(self.project.pk), str(other.pk)})
        self.assertEqual(
            {key: value for key, value in data[str(self.project.pk)]["fields"].items()
             if key in self.data}, self.data,
        )
        self.assertEqual(data[str(self.project.pk)]["model"], "main.project")

    def test_search_filters_both_html_and_json(self):
        Project.objects.create(**{**self.data, "title": "Other project"})
        response = self.client.get(self.list_url, {"title": "  PORTFOLIO  "})
        self.assertContains(response, self.project.title)
        self.assertNotContains(response, "Other project")
        data = self.client.get(self.json_url, {"title": "  PORTFOLIO  "}).json()
        self.assertEqual([item["pk"] for item in data], [str(self.project.pk)])
        self.assertEqual(self.client.get(self.json_url, {"title": "missing"}).json(), [])
        self.assertContains(
            self.client.get(self.list_url, {"title": "missing"}),
            "Tidak ada proyek dengan nama tersebut.",
        )

    def test_empty_list(self):
        Project.objects.all().delete()
        self.assertEqual(self.client.get(self.json_url).json(), [])
        self.assertContains(self.client.get(self.list_url), "Belum ada proyek yang ditambahkan.")

    def test_mutations_require_csrf_and_accept_valid_token(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.admin)
        for url in (self.create_url, self.update_url, self.delete_url):
            with self.subTest(url=url):
                self.assertEqual(client.post(url, self.data).status_code, 403)
        self.assertEqual(Project.objects.count(), 1)
        client.get(self.create_url)
        token = client.cookies["csrftoken"].value
        response = client.post(self.create_url, {**self.data, "csrfmiddlewaretoken": token})
        self.assertRedirects(response, self.list_url)
        response = client.post(self.update_url, {
            **self.data, "title": "CSRF updated", "csrfmiddlewaretoken": token,
        })
        self.assertRedirects(response, self.list_url)
        response = client.post(self.delete_url, {"csrfmiddlewaretoken": token})
        self.assertRedirects(response, self.list_url)
        self.assertFalse(Project.objects.filter(pk=self.project.pk).exists())


class ProjectAccessTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(
            username="visitor", password="test-password"
        )
        cls.staff = get_user_model().objects.create_user(
            username="staff", password="test-password", is_staff=True
        )
        cls.editor = get_user_model().objects.create_user(username="editor")
        cls.editor.groups.add(Group.objects.create(name="Editor"))
        cls.owner = get_user_model().objects.create_superuser(
            username="owner", email="owner@example.com", password="test-password"
        )
        cls.data = {
            "title": "Original project",
            "description": "Original description",
            "tech_stack": "Django",
        }
        cls.project = Project.objects.create(**cls.data)

    def test_guests_and_non_superusers_cannot_modify_projects(self):
        routes = (
            (reverse("main:create_project"), ("get", "post")),
            (reverse("main:update_project", args=[self.project.pk]), ("get", "post")),
            (reverse("main:delete_project", args=[self.project.pk]), ("post",)),
        )
        for user in (None, self.user, self.staff):
            self.client.logout()
            if user:
                self.client.force_login(user)
            for url, methods in routes:
                for method in methods:
                    with self.subTest(user=user, url=url, method=method):
                        response = getattr(self.client, method)(
                            url, {**self.data, "title": "Unauthorized change"}
                        )
                        if user is None:
                            self.assertEqual(response.status_code, 302)
                            self.assertTrue(response.url.startswith("/login/?next="))
                        else:
                            self.assertEqual(response.status_code, 403)
                        self.project.refresh_from_db()
                        self.assertEqual(self.project.title, self.data["title"])
                        self.assertEqual(Project.objects.count(), 1)

    def test_public_projects_hide_management_buttons_and_offer_login_for_star(self):
        url = reverse("main:show_projects")
        response = self.client.get(url, {"title": "Original"})
        self.assertContains(response, self.project.title)
        self.assertContains(response, "/login/?next=/projects/%3Ftitle%3DOriginal")
        for user in (None, self.user):
            if user:
                self.client.force_login(user)
            response = self.client.get(url)
            self.assertNotContains(response, reverse("main:create_project"))
            self.assertNotContains(response, reverse("main:update_project", args=[self.project.pk]))
            self.assertNotContains(response, reverse("main:delete_project", args=[self.project.pk]))

    def test_star_requires_login_and_post_and_toggles_for_regular_user(self):
        url = reverse("main:toggle_star", args=[self.project.pk])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/login/?next="))
        self.assertEqual(self.project.starred_by.count(), 0)

        self.client.force_login(self.user)
        for method in ("get", "head", "put", "delete"):
            self.assertEqual(getattr(self.client, method)(url).status_code, 405)
        self.assertEqual(self.project.starred_by.count(), 0)
        for expected in (1, 0):
            response = self.client.post(url)
            self.assertRedirects(response, reverse("main:show_projects"))
            self.assertEqual(self.project.starred_by.count(), expected)

    def test_star_requires_csrf(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.user)
        url = reverse("main:toggle_star", args=[self.project.pk])
        self.assertEqual(client.post(url).status_code, 403)
        self.assertEqual(self.project.starred_by.count(), 0)
        client.get(reverse("main:show_projects"))
        response = client.post(url, {"csrfmiddlewaretoken": client.cookies["csrftoken"].value})
        self.assertRedirects(response, reverse("main:show_projects"))
        self.assertTrue(self.project.starred_by.filter(pk=self.user.pk).exists())


    def test_editor_can_edit_but_cannot_create_or_delete(self):
        self.client.force_login(self.editor)
        update_url = reverse("main:update_project", args=[self.project.pk])
        response = self.client.get(update_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["form"].initial["title"], self.data["title"])
        response = self.client.post(update_url, {**self.data, "title": "Edited"})
        self.assertRedirects(response, reverse("main:show_projects"))
        self.project.refresh_from_db()
        self.assertEqual(self.project.title, "Edited")
        for method, url in (
            ("get", reverse("main:create_project")),
            ("post", reverse("main:create_project")),
            ("post", reverse("main:delete_project", args=[self.project.pk])),
        ):
            with self.subTest(method=method, url=url):
                self.assertEqual(getattr(self.client, method)(url, self.data).status_code, 403)
        self.assertEqual(Project.objects.count(), 1)
        self.project.refresh_from_db()
        self.assertEqual(self.project.title, "Edited")

    def test_management_buttons_match_each_role(self):
        create_url = reverse("main:create_project")
        update_url = reverse("main:update_project", args=[self.project.pk])
        delete_url = reverse("main:delete_project", args=[self.project.pk])
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
                response = self.client.get(reverse("main:show_projects"))
                for url, visible in (
                    (create_url, can_manage), (update_url, can_edit), (delete_url, can_manage),
                ):
                    if visible:
                        self.assertContains(response, url)
                    else:
                        self.assertNotContains(response, url)

    def test_removing_editor_group_revokes_edit_access(self):
        self.client.force_login(self.editor)
        self.editor.groups.clear()
        url = reverse("main:update_project", args=[self.project.pk])
        for method in ("get", "post"):
            self.assertEqual(getattr(self.client, method)(url, self.data).status_code, 403)
        self.project.refresh_from_db()
        self.assertEqual(self.project.title, self.data["title"])

    def test_every_authenticated_role_can_toggle_own_star(self):
        url = reverse("main:toggle_star", args=[self.project.pk])
        self.project.starred_by.add(self.staff)
        for user in (self.user, self.editor, self.owner):
            with self.subTest(user=user):
                self.client.force_login(user)
                response = self.client.post(url)
                self.assertRedirects(response, reverse("main:show_projects"))
                self.assertTrue(self.project.starred_by.filter(pk=user.pk).exists())
                self.assertEqual(self.project.starred_by.count(), 2)
                response = self.client.post(url)
                self.assertRedirects(response, reverse("main:show_projects"))
                self.assertFalse(self.project.starred_by.filter(pk=user.pk).exists())
                self.assertTrue(self.project.starred_by.filter(pk=self.staff.pk).exists())
                self.assertEqual(self.project.starred_by.count(), 1)

    def test_star_count_and_status_are_specific_to_user_and_project(self):
        other = Project.objects.create(**{**self.data, "title": "Other"})
        self.project.starred_by.add(self.user, self.editor)
        self.project.starred_by.add(self.user)
        self.assertEqual(self.project.starred_by.count(), 2)
        self.client.force_login(self.user)
        response = self.client.get(reverse("main:show_projects"))
        cards = {project.pk: project for project in response.context["project_list"]}
        self.assertTrue(cards[self.project.pk].is_starred)
        self.assertFalse(cards[other.pk].is_starred)
        self.assertContains(response, 'aria-pressed="true"', count=1)
        self.assertContains(response, 'aria-pressed="false"', count=1)
        self.assertContains(response, "Unstar", count=1)
        self.assertContains(response, '<span class="star-count">2</span>', html=True)
        self.assertContains(response, '<span class="star-count">0</span>', html=True)
        self.client.post(reverse("main:toggle_star", args=[self.project.pk]))
        response = self.client.get(reverse("main:show_projects"))
        self.assertNotContains(response, "Unstar")
        self.assertContains(response, '<span class="star-count">1</span>', html=True)
        self.client.logout()
        response = self.client.get(reverse("main:show_projects"))
        self.assertContains(response, '<span class="star-count">1</span>', html=True)
        self.assertNotContains(response, "Unstar")

    def test_star_on_missing_project_returns_404(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse("main:toggle_star", args=[uuid.uuid4()]))
        self.assertEqual(response.status_code, 404)
        self.assertEqual(self.project.starred_by.count(), 0)

    def test_public_json_exposes_project_and_public_star_fields(self):
        self.project.starred_by.add(self.user)
        response = self.client.get(reverse("main:get_projects_json"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [{
            "model": "main.project",
            "pk": str(self.project.pk),
            "fields": {
                **self.data, "project_url": "", "project_image_url": "",
                "star_count": 1, "is_starred": False,
                "starred_by_names": self.user.username,
            },
        }])
        for private_value in (self.user.password, '"starred_by":', "session", "token"):
            self.assertNotContains(response, private_value)
        self.assertEqual(
            self.client.post(reverse("main:get_projects_json")).status_code, 405
        )


class LoginRedirectTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        get_user_model().objects.create_user(
            username="visitor", password="test-password"
        )

    def test_login_preserves_next_through_form_and_failed_attempt(self):
        target = "/projects/?title=Django"
        response = self.client.get("/login/", {"next": target})
        self.assertContains(response, f'<input type="hidden" name="next" value="{target}">', html=True)
        response = self.client.post("/login/", {
            "username": "visitor", "password": "wrong-password", "next": target,
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["next"], target)
        response = self.client.post("/login/", {
            "username": "visitor", "password": "test-password",
            "next": response.context["next"],
        })
        self.assertRedirects(response, target)

    def test_unsafe_or_missing_next_falls_back_to_home(self):
        for target in ("", "https://example.com/", "//example.com/", "javascript:alert(1)"):
            with self.subTest(target=target):
                self.client.logout()
                response = self.client.post("/login/", {
                    "username": "visitor", "password": "test-password", "next": target,
                })
                self.assertRedirects(response, "/")

    def test_https_login_rejects_http_redirect(self):
        response = self.client.post("/login/", {
            "username": "visitor", "password": "test-password",
            "next": "http://testserver/projects/",
        }, secure=True)
        self.assertRedirects(response, "/")

    def test_same_host_next_is_allowed(self):
        response = self.client.post("/login/", {
            "username": "visitor", "password": "test-password",
            "next": "http://testserver/projects/",
        })
        self.assertRedirects(response, "http://testserver/projects/")
