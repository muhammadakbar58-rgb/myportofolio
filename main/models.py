import uuid
from django.db import models
from django.conf import settings

class Experience(models.Model):
    EXPERIENCE_CHOICES = [
        ('internship', 'Internship'),
        ('research', 'Research'),
        ('volunteer', 'Volunteer'),
        ('part-time', 'Part-Time'),
        ('full-time', 'Full-Time'),
        ('freelance', 'Freelance'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    description = models.TextField()
    category = models.CharField(max_length=20, choices=EXPERIENCE_CHOICES, default='full-time')
    image = models.CharField(max_length=255, blank=True, default="")
    year = models.CharField(max_length=50, blank=True, default="")
    thumbnail = models.URLField(blank=True, null=True)
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(blank=True, null=True)
    starred_by = models.ManyToManyField(
        settings.AUTH_USER_MODEL, related_name="starred_experiences", blank=True
    )
    def __str__(self):
        return self.title
    
    @property
    def is_ongoing(self):
        return self.ended_at is None


class Skill(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField()
    image = models.CharField(max_length=255)
    starred_by = models.ManyToManyField(
        settings.AUTH_USER_MODEL, related_name="starred_skills", blank=True
    )

    def __str__(self):
        return self.name
class Project(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    description = models.TextField()
    tech_stack = models.CharField(max_length=255)
    project_url = models.URLField(blank=True)
    project_image_url = models.URLField(blank=True, max_length=500)
    starred_by = models.ManyToManyField(
        settings.AUTH_USER_MODEL, related_name="starred_projects", blank=True
    )

    def __str__(self):
        return self.title