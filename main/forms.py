from django.core.exceptions import ValidationError
from django.utils.html import strip_tags
from django.forms import DateTimeInput, ModelForm, TextInput, Textarea, URLInput

from main.models import Experience, Project, Skill

class ProjectForm(ModelForm):
    class Meta:
        model = Project
        fields = [
            "title",
            "description",
            "tech_stack",
            "project_url",
            "project_image_url",
        ]

        labels = {
            "title": "Nama Proyek",
            "description": "Deskripsi Proyek",
            "tech_stack": "Teknologi yang Digunakan",
            "project_url": "URL Proyek",
            "project_image_url": "URL Gambar Proyek",
        }

        widgets = {
            "title": TextInput(
                attrs={
                    "placeholder": "Portfolio Website",
                    "maxlength": 255,
                }
            ),
            "description": Textarea(
                attrs={
                    "placeholder": "Ceritakan Proyekmu",
                    "rows": 3,
                }
            ),
            "tech_stack": TextInput(
                attrs={
                    "placeholder": "Django, Python, HTML, CSS",
                }
            ),
            "project_url": URLInput(
                attrs={
                    "placeholder": "https://github.com/kakBurhan/burhanquestv4",
                }
            ),
            "project_image_url": URLInput(
                attrs={
                    "placeholder": "https://drive.google.com/thumbnail?id=...&sz=w1000",
                }
            ),
        }


    def clean_title(self):
        title = strip_tags(self.cleaned_data["title"]).strip()
        if not title:
            raise ValidationError("Nama proyek tidak boleh hanya berisi tag HTML.")
        return title

    def clean_tech_stack(self):
        return strip_tags(self.cleaned_data["tech_stack"]).strip()

    def clean_description(self):
        return strip_tags(self.cleaned_data["description"]).strip()


class ExperienceForm(ModelForm):
    class Meta:
        model = Experience
        fields = ["title", "description", "category", "image", "year", "thumbnail", "ended_at"]
        labels = {
            "title": "Nama Pengalaman",
            "description": "Deskripsi",
            "category": "Kategori",
            "image": "Gambar",
            "year": "Tahun",
            "thumbnail": "URL Thumbnail",
            "ended_at": "Tanggal Selesai",
        }
        help_texts = {
            "image": "Path gambar di folder static, misalnya img/company.png.",
            "ended_at": "Kosongkan jika masih berlangsung.",
        }
        widgets = {
            "description": Textarea(attrs={"rows": 3}),
            "image": TextInput(attrs={"placeholder": "img/company.png"}),
            "year": TextInput(attrs={"placeholder": "2025 - Present"}),
            "ended_at": DateTimeInput(
                format="%Y-%m-%dT%H:%M", attrs={"type": "datetime-local"}
            ),
        }


class SkillForm(ModelForm):
    class Meta:
        model = Skill
        fields = ["name", "description", "image"]
        labels = {
            "name": "Nama Skill",
            "description": "Deskripsi",
            "image": "Gambar",
        }
        help_texts = {
            "image": "Path gambar di folder static, misalnya img/python.png.",
        }
        widgets = {
            "description": Textarea(attrs={"rows": 3}),
            "image": TextInput(attrs={"placeholder": "img/python.png"}),
        }
