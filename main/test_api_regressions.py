import uuid
from types import SimpleNamespace

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.urls import reverse
from rest_framework.test import APIClient, APITestCase

from main.models import Project, Skill
from main.serializers import ProjectSerializer, SkillSerializer


class APIRegressionTest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        users = get_user_model().objects
        cls.owner = users.create_superuser("api-owner", "owner@example.com", "test-password")
        cls.visitor = users.create_user("api-visitor", password="test-password")
        cls.other = users.create_user("other")
        cls.staff = users.create_user("api-staff", is_staff=True)
        cls.editor = users.create_user("api-editor")
        cls.editor.groups.add(Group.objects.create(name="Editor"))
        cls.project = Project.objects.create(
            title="Portfolio", description="Website", tech_stack="Django",
        )
        cls.skill = Skill.objects.create(name="Python", description="Programming", image="img/python.png")

    def test_project_serializer_shape_validation_and_sensitive_data(self):
        self.project.starred_by.add(self.visitor)
        expected = {
            "id": str(self.project.pk), "title": "Portfolio", "description": "Website",
            "tech_stack": "Django", "project_url": "", "project_image_url": "",
            "star_count": 1, "is_starred": False, "starred_by_names": self.visitor.username,
        }
        self.assertEqual(ProjectSerializer(self.project).data, expected)
        serializer = ProjectSerializer(self.project, context={"request": SimpleNamespace(user=self.visitor)})
        self.assertTrue(serializer.data["is_starred"])
        self.assertNotIn(self.visitor.password, str(serializer.data))
        self.assertNotIn(self.owner.email, str(serializer.data))
        valid = ProjectSerializer(data={"title": "<b>Clean</b>", "description": "<p>Text</p>", "tech_stack": "<i>Django</i>"})
        self.assertTrue(valid.is_valid(), valid.errors)
        self.assertEqual(valid.validated_data, {"title": "Clean", "description": "Text", "tech_stack": "Django"})
        invalid = ProjectSerializer(data={"title": ""})
        self.assertFalse(invalid.is_valid())
        self.assertEqual(set(invalid.errors), {"title", "description", "tech_stack"})

    def test_project_filtering_preserves_existing_full_text_search(self):
        url = reverse("api:project-list")
        for params in ({"title": "  PORT  "}, {"search": " website "}, {"search": "DJANGO"}):
            with self.subTest(params=params):
                response = self.client.get(url, params)
                self.assertEqual(response.status_code, 200)
                self.assertEqual([row["id"] for row in response.data], [str(self.project.pk)])
        self.assertEqual(self.client.get(url, {"search": "missing"}).data, [])

    def test_read_methods_do_not_modify_projects_and_wrong_methods_fail(self):
        before = Project.objects.count()
        for route, args in (("project-list", []), ("project-detail", [self.project.pk])):
            url = reverse("api:" + route, args=args)
            self.assertEqual(self.client.head(url).status_code, 200)
            self.assertEqual(self.client.options(url).status_code, 200)
        self.assertEqual(Project.objects.count(), before)
        self.client.force_authenticate(self.owner)
        self.assertEqual(self.client.post(reverse("api:project-detail", args=[self.project.pk])).status_code, 405)
        self.assertEqual(self.client.get(reverse("api:project-star", args=[self.project.pk])).status_code, 405)
        self.assertFalse(self.project.starred_by.exists())

    def test_invalid_project_updates_preserve_data_and_stars(self):
        self.client.force_authenticate(self.owner)
        self.project.starred_by.add(self.other)
        url = reverse("api:project-detail", args=[self.project.pk])
        for payload in ({"title": " "}, {"title": "<b></b>"}, {"title": "x" * 256}, {"project_image_url": "javascript:alert(1)"}):
            self.assertEqual(self.client.patch(url, payload, format="json").status_code, 400)
        self.assertEqual(self.client.patch(url, '{"title":', content_type="application/json").status_code, 400)
        self.project.refresh_from_db()
        self.assertEqual(self.project.title, "Portfolio")
        self.assertTrue(self.project.starred_by.filter(pk=self.other.pk).exists())

    def test_project_read_only_ids_and_stars_cannot_be_forged_on_update(self):
        self.client.force_authenticate(self.owner)
        self.project.starred_by.add(self.other)
        response = self.client.patch(reverse("api:project-detail", args=[self.project.pk]), {
            "id": str(uuid.uuid4()), "starred_by": [self.visitor.pk],
            "star_count": 99, "is_starred": True, "starred_by_names": "forged",
        }, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["id"], str(self.project.pk))
        self.assertEqual(response.data["star_count"], 1)
        self.assertFalse(response.data["is_starred"])
        self.assertEqual(response.data["starred_by_names"], self.other.username)

    def test_star_toggles_only_request_user_for_both_models(self):
        for prefix, item in (("project", self.project), ("skill", self.skill)):
            item.starred_by.add(self.other)
            self.client.force_authenticate(self.visitor)
            url = reverse("api:" + prefix + "-star", args=[item.pk])
            for expected in (True, False):
                response = self.client.post(url, {"user_id": self.other.pk, "starred_by": []}, format="json")
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.data["is_starred"], expected)
                self.assertEqual(response.data["star_count"], 2 if expected else 1)
                self.assertTrue(item.starred_by.filter(pk=self.other.pk).exists())
            self.client.force_authenticate(self.other)
            detail = self.client.get(reverse("api:" + prefix + "-detail", args=[item.pk]))
            self.assertTrue(detail.data["is_starred"])

    def test_missing_objects_return_json_404_for_authorized_methods(self):
        self.client.force_authenticate(self.owner)
        for prefix in ("project", "skill"):
            detail = reverse("api:" + prefix + "-detail", args=[uuid.uuid4()])
            for method in ("get", "put", "patch", "delete"):
                response = getattr(self.client, method)(detail)
                self.assertEqual(response.status_code, 404)
                self.assertIn("detail", response.data)
            response = self.client.post(reverse("api:" + prefix + "-star", args=[uuid.uuid4()]))
            self.assertEqual(response.status_code, 404)

    def test_project_api_denies_staff_and_editor_all_management_methods(self):
        for user in (self.staff, self.editor):
            self.client.force_authenticate(user)
            self.assertEqual(self.client.post(reverse("api:project-list"), {}, format="json").status_code, 403)
            for method in ("put", "patch", "delete"):
                url = reverse("api:project-detail", args=[self.project.pk])
                self.assertEqual(getattr(self.client, method)(url, {}, format="json").status_code, 403)
        self.project.refresh_from_db()
        self.assertEqual(self.project.title, "Portfolio")

    def test_skill_serializer_contract_and_public_search(self):
        self.skill.starred_by.add(self.visitor)
        data = SkillSerializer(self.skill).data
        self.assertEqual(set(data), {"id", "name", "description", "image", "star_count", "is_starred", "starred_by_names"})
        self.assertEqual(data["star_count"], 1)
        self.assertFalse(data["is_starred"])
        response = self.client.get(reverse("api:skill-list"), {"name": " PY "})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, [data])
        self.assertEqual(self.client.get(reverse("api:skill-list"), {"name": "absent"}).data, [])
        self.assertEqual(self.client.get(reverse("api:skill-detail", args=[self.skill.pk])).data, data)

    def test_skill_owner_can_create_replace_patch_and_delete(self):
        self.client.force_authenticate(self.owner)
        payload = {"name": "SQL", "description": "Databases", "image": "img/sql.png"}
        created = self.client.post(reverse("api:skill-list"), payload, format="json")
        self.assertEqual(created.status_code, 201)
        url = reverse("api:skill-detail", args=[created.data["id"]])
        self.assertEqual(self.client.put(url, {"name": "Missing fields"}, format="json").status_code, 400)
        updated = self.client.put(url, {**payload, "name": "PostgreSQL"}, format="json")
        self.assertEqual(updated.status_code, 200)
        patched = self.client.patch(url, {"description": "Relational databases"}, format="json")
        self.assertEqual(patched.status_code, 200)
        self.assertEqual(patched.data["name"], "PostgreSQL")
        self.assertEqual(Skill.objects.get(pk=created.data["id"]).description, "Relational databases")
        deleted = self.client.delete(url)
        self.assertEqual(deleted.status_code, 204)
        self.assertEqual(deleted.content, b"")
        self.assertFalse(Skill.objects.filter(pk=created.data["id"]).exists())

    def test_skill_editor_can_update_but_cannot_create_delete_or_forge_stars(self):
        self.client.force_authenticate(self.editor)
        url = reverse("api:skill-detail", args=[self.skill.pk])
        payload = {"name": "Edited", "description": "Updated", "image": "img/python.png"}
        self.assertEqual(self.client.put(url, payload, format="json").status_code, 200)
        response = self.client.patch(url, {"name": "Patched", "starred_by": [self.other.pk]}, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["star_count"], 0)
        self.assertEqual(self.client.post(reverse("api:skill-list"), payload, format="json").status_code, 403)
        self.assertEqual(self.client.delete(url).status_code, 403)
        self.skill.refresh_from_db()
        self.assertEqual(self.skill.name, "Patched")
        self.editor.groups.clear()
        self.assertEqual(self.client.patch(url, {"name": "No"}, format="json").status_code, 403)

    def test_skill_guests_visitors_and_staff_cannot_manage(self):
        url = reverse("api:skill-detail", args=[self.skill.pk])
        for user in (None, self.visitor, self.staff):
            self.client.force_authenticate(user)
            self.assertEqual(self.client.post(reverse("api:skill-list"), {}, format="json").status_code, 403)
            for method in ("put", "patch", "delete"):
                self.assertEqual(getattr(self.client, method)(url, {}, format="json").status_code, 403)
        self.skill.refresh_from_db()
        self.assertEqual(self.skill.name, "Python")
        self.client.force_authenticate(None)
        self.assertEqual(self.client.post(reverse("api:skill-star", args=[self.skill.pk])).status_code, 403)

    def test_skill_validation_and_read_only_fields(self):
        self.client.force_authenticate(self.owner)
        payload = {"name": "SQL", "description": "Database", "image": "img/sql.png"}
        for field, value in (("name", ""), ("name", "<b></b>"), ("name", "x" * 256), ("description", ""), ("image", "")):
            response = self.client.post(reverse("api:skill-list"), {**payload, field: value}, format="json")
            self.assertEqual(response.status_code, 400)
            self.assertIn(field, response.data)
        self.assertEqual(Skill.objects.count(), 1)
        forged_id = str(uuid.uuid4())
        response = self.client.post(reverse("api:skill-list"), {
            **payload, "id": forged_id, "starred_by": [self.other.pk],
            "star_count": 10, "is_starred": True, "starred_by_names": "forged",
        }, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertNotEqual(response.data["id"], forged_id)
        self.assertEqual(response.data["star_count"], 0)
        self.assertFalse(response.data["is_starred"])
        self.assertEqual(response.data["starred_by_names"], "")

    def test_session_csrf_protects_every_write_method_and_star(self):
        for prefix, item, payload in (
            ("project", self.project, {"title": "New", "description": "Details", "tech_stack": "Django"}),
            ("skill", self.skill, {"name": "New", "description": "Details", "image": "img/python.png"}),
        ):
            client = APIClient(enforce_csrf_checks=True)
            self.assertTrue(client.login(username=self.owner.username, password="test-password"))
            client.get(reverse("main:show_projects"))
            token = client.cookies["csrftoken"].value
            operations = [
                ("post", reverse("api:" + prefix + "-list"), payload),
                ("patch", reverse("api:" + prefix + "-detail", args=[item.pk]), payload),
                ("put", reverse("api:" + prefix + "-detail", args=[item.pk]), payload),
                ("post", reverse("api:" + prefix + "-star", args=[item.pk]), {}),
                ("delete", reverse("api:" + prefix + "-detail", args=[item.pk]), {}),
            ]
            for method, url, data in operations:
                with self.subTest(prefix=prefix, method=method, url=url):
                    for headers in ({}, {"HTTP_X_CSRFTOKEN": "invalid"}):
                        self.assertEqual(getattr(client, method)(url, data, format="json", **headers).status_code, 403)
                    self.assertTrue(type(item).objects.filter(pk=item.pk).exists())
                    response = getattr(client, method)(url, data, format="json", HTTP_X_CSRFTOKEN=token)
                    self.assertIn(response.status_code, (200, 201, 204))
            client.logout()

    def test_frontend_api_routes_and_legacy_contract_remain_available(self):
        self.client.force_login(self.owner)
        response = self.client.get(reverse("main:show_projects"))
        self.assertContains(response, 'data-projects-url="/api/v1/projects/"')
        self.assertContains(response, 'data-ajax-url="/api/v1/projects/"')
        self.assertContains(response, 'id="projects-csrf"')
        response = self.client.get(reverse("main:show_skills"))
        self.assertContains(response, 'data-list-url="/api/v1/skills/"')
        self.assertContains(response, "js/skills.js")
        for route, args, method in (("create_skill", [], "POST"), ("update_skill", [self.skill.pk], "PUT")):
            response = self.client.get(reverse("main:" + route, args=args))
            self.assertContains(response, 'data-api-method="' + method + '"')
        for route in ("login", "register"):
            response = self.client.get(reverse("main:" + route))
            self.assertContains(response, "Muhammad Akbar Rinaldy")
            self.assertNotContains(response, "Burhan")
        legacy = self.client.get(reverse("main:get_projects_json")).json()
        self.assertEqual(legacy[0]["pk"], str(self.project.pk))
        self.assertEqual(legacy[0]["fields"]["title"], self.project.title)
        self.assertEqual(legacy[0]["model"], "main.project")
