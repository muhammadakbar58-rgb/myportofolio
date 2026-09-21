from django.templatetags.static import static
import uuid

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
        self.assertNotContains(response, "<script")
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
        self.assertEqual(self.client.get(self.json_url).json()[0]["fields"], data)

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
        self.assertEqual(data[str(self.project.pk)]["fields"], self.data)
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
