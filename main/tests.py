from django.templatetags.static import static
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from main.models import Experience, Skill


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
