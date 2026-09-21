from django.contrib import messages
from django.core import serializers
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from main.forms import ProjectForm
from main.models import Experience, Project, Skill


def show_main(request):
    context = {
        "name": "Muhammad Akbar Rinaldy",
        "npm": "2506586311",
        "study_program": "S1 Ilmu Komputer",
        "bio": "CS student at Universitas Indonesia. Discovering and trying new things.",
    }
    return render(request, "index.html", context)


def show_experience(request):
    context = {
        "name": "Muhammad Akbar Rinaldy",
        "experience_list": Experience.objects.all(),
    }
    return render(request, "experience.html", context)


def show_skills(request):
    context = {
        "name": "Muhammad Akbar Rinaldy",
        "skill_list": Skill.objects.all(),
    }
    return render(request, "skills.html", context)


def _filtered_projects(request):
    projects = Project.objects.all()
    title_query = request.GET.get("title", "").strip()
    if title_query:
        projects = projects.filter(title__icontains=title_query)
    return projects


def show_projects(request):
    # Convert projects to JSON, then read that JSON in Python for the template.
    projects_json = serializers.serialize("json", _filtered_projects(request))
    projects = serializers.deserialize("json", projects_json)
    project_list = [project.object for project in projects]
    context = {
        "name": "Muhammad Akbar Rinaldy",
        "project_list": project_list,
        "title_query": request.GET.get("title", "").strip(),
    }
    return render(request, "project.html", context)


@require_http_methods(["GET", "POST"])
def create_project(request):
    form = ProjectForm(request.POST if request.method == "POST" else None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Proyek baru berhasil ditambahkan!")
        return redirect("main:show_projects")

    return render(request, "projects_form.html", {
        "name": "Muhammad Akbar Rinaldy",
        "form": form,
    })


@require_http_methods(["GET", "POST"])
def update_project(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    form = ProjectForm(
        request.POST if request.method == "POST" else None,
        instance=project,
    )
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Proyek berhasil diperbarui!")
        return redirect("main:show_projects")

    return render(request, "projects_form.html", {
        "name": "Muhammad Akbar Rinaldy",
        "form": form,
        "project": project,
    })


@require_GET
def get_projects_json(request):
    projects_json = serializers.serialize("json", _filtered_projects(request))
    return HttpResponse(projects_json, content_type="application/json")


@require_POST
def delete_project(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    project.delete()
    messages.success(request, "Project berhasil dihapus!")
    return redirect("main:show_projects")
