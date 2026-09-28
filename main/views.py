import datetime

from django.contrib import messages
from django.contrib.auth import get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.core import serializers
from django.core.exceptions import PermissionDenied
from django.db.models import Prefetch
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from main.forms import ExperienceForm, ProjectForm, SkillForm
from main.models import Experience, Project, Skill


def show_main(request):
    last_login = request.COOKIES.get('last_login', 'Belum ada sesi login / Cookie tidak ditemukan')
    context = {
        "name": "Muhammad Akbar Rinaldy",
        "npm": "2506586311",
        "study_program": "S1 Ilmu Komputer",
        "bio": (
            "Second-year Computer Science student at Universitas Indonesia exploring the intersection of data, intelligence, and real-world problem solving."
        ),
        "last_login": last_login,
    }
    return render(request, "index.html", context)
def show_experience(request):
    context = {
        "name": "Muhammad Akbar Rinaldy",
        "experience_list": _with_star_status(Experience.objects.all(), request.user),
        "can_edit_portfolio": _can_edit_portfolio(request.user),
    }
    return render(request, "experience.html", context)


def show_skills(request):
    context = {
        "name": "Muhammad Akbar Rinaldy",
        "skill_list": _with_star_status(Skill.objects.all(), request.user),
        "can_edit_portfolio": _can_edit_portfolio(request.user),
    }
    return render(request, "skills.html", context)


def _filtered_projects(request):
    projects = Project.objects.all()
    title_query = request.GET.get("title", "").strip()
    if title_query:
        projects = projects.filter(title__icontains=title_query)
    return projects


def _can_edit_portfolio(user):
    return user.is_authenticated and (
        user.is_superuser or user.groups.filter(name="Editor").exists()
    )


def _with_star_status(items, user):
    items = items.prefetch_related(
        Prefetch("starred_by", queryset=get_user_model().objects.only("pk", "username"))
    )
    for item in items:
        item.is_starred = user.is_authenticated and any(
            starred_user.pk == user.pk for starred_user in item.starred_by.all()
        )
    return items


def show_projects(request):
    project_list = _with_star_status(_filtered_projects(request), request.user)
    context = {
        "name": "Muhammad Akbar Rinaldy",
        "project_list": project_list,
        "can_edit_projects": _can_edit_portfolio(request.user),
        "title_query": request.GET.get("title", "").strip(),
    }
    return render(request, "project.html", context)


@require_http_methods(["GET", "POST"])
@login_required(login_url="/login/")
def create_project(request):
    if not request.user.is_superuser:
        raise PermissionDenied

    form = ProjectForm(
        request.POST if request.method == "POST" else None
    )

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Proyek baru berhasil ditambahkan!")
        return redirect("main:show_projects")

    return render(request, "projects_form.html", {
        "name": "Muhammad Akbar Rinaldy",
        "form": form,
    })

@require_http_methods(["GET", "POST"])
@login_required(login_url="/login/")
def update_project(request, project_id):
    if not _can_edit_portfolio(request.user):
        raise PermissionDenied

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
    # Keep the existing JSON structure while exposing only public project fields.
    projects_json = serializers.serialize(
        "json",
        _filtered_projects(request),
        fields=("title", "description", "tech_stack", "project_url", "project_image_url"),
    )
    return HttpResponse(projects_json, content_type="application/json")


@require_POST
@login_required(login_url="/login/")
def delete_project(request, project_id):
    if not request.user.is_superuser:
        raise PermissionDenied

    project = get_object_or_404(Project, pk=project_id)
    project.delete()

    messages.success(request, "Project berhasil dihapus!")
    return redirect("main:show_projects")

def register(request):
    form = UserCreationForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Akun berhasil dibuat. Silakan login.")
        return redirect("main:login")

    context = {
        "name": "Burhan",
        "form": form,
    }
    return render(request, "register.html", context)
def login_user(request):
    form = AuthenticationForm(request, data=request.POST or None)
    next_url = request.POST.get("next", request.GET.get("next", ""))
    if not url_has_allowed_host_and_scheme(
        next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        next_url = ""

    if request.method == "POST" and form.is_valid():
        user = form.get_user()
        login(request, user)
        response = redirect(next_url or "main:show_main")
        response.set_cookie('last_login', datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        return response

    context = {
        "name": "Burhan",
        "form": form,
    }
    context["next"] = next_url
    return render(request, "login.html", context)
def logout_user(request):
    logout(request)
    response = redirect("main:show_main")
    response.delete_cookie('last_login')
    return response

# Semua akun yang sudah login boleh memberi star.
@require_POST
@login_required(login_url="/login/")
def toggle_star(request, project_id):
    project = get_object_or_404(Project, pk=project_id)

    if project.starred_by.filter(pk=request.user.pk).exists():
        project.starred_by.remove(request.user)
    else:
        project.starred_by.add(request.user)

    return redirect("main:show_projects")


@require_http_methods(["GET", "POST"])
@login_required(login_url="main:login")
def create_experience(request):
    if not request.user.is_superuser:
        raise PermissionDenied

    form = ExperienceForm(request.POST if request.method == "POST" else None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Pengalaman berhasil ditambahkan!")
        return redirect("main:show_experience")

    return render(request, "portfolio_item_form.html", {
        "name": "Muhammad Akbar Rinaldy",
        "form": form,
        "item_label": "Pengalaman",
        "list_url_name": "main:show_experience",
    })


@require_http_methods(["GET", "POST"])
@login_required(login_url="main:login")
def update_experience(request, experience_id):
    if not _can_edit_portfolio(request.user):
        raise PermissionDenied

    item = get_object_or_404(Experience, pk=experience_id)
    form = ExperienceForm(
        request.POST if request.method == "POST" else None, instance=item,
    )
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Pengalaman berhasil diperbarui!")
        return redirect("main:show_experience")

    return render(request, "portfolio_item_form.html", {
        "name": "Muhammad Akbar Rinaldy",
        "form": form,
        "item": item,
        "item_label": "Pengalaman",
        "list_url_name": "main:show_experience",
    })


@require_POST
@login_required(login_url="main:login")
def delete_experience(request, experience_id):
    if not request.user.is_superuser:
        raise PermissionDenied

    item = get_object_or_404(Experience, pk=experience_id)
    item.delete()
    messages.success(request, "Pengalaman berhasil dihapus!")
    return redirect("main:show_experience")


@require_POST
@login_required(login_url="main:login")
def toggle_experience_star(request, experience_id):
    item = get_object_or_404(Experience, pk=experience_id)
    if item.starred_by.filter(pk=request.user.pk).exists():
        item.starred_by.remove(request.user)
    else:
        item.starred_by.add(request.user)
    return redirect("main:show_experience")



@require_http_methods(["GET", "POST"])
@login_required(login_url="main:login")
def create_skill(request):
    if not request.user.is_superuser:
        raise PermissionDenied

    form = SkillForm(request.POST if request.method == "POST" else None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Skill berhasil ditambahkan!")
        return redirect("main:show_skills")

    return render(request, "portfolio_item_form.html", {
        "name": "Muhammad Akbar Rinaldy",
        "form": form,
        "item_label": "Skill",
        "list_url_name": "main:show_skills",
    })


@require_http_methods(["GET", "POST"])
@login_required(login_url="main:login")
def update_skill(request, skill_id):
    if not _can_edit_portfolio(request.user):
        raise PermissionDenied

    item = get_object_or_404(Skill, pk=skill_id)
    form = SkillForm(
        request.POST if request.method == "POST" else None, instance=item,
    )
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Skill berhasil diperbarui!")
        return redirect("main:show_skills")

    return render(request, "portfolio_item_form.html", {
        "name": "Muhammad Akbar Rinaldy",
        "form": form,
        "item": item,
        "item_label": "Skill",
        "list_url_name": "main:show_skills",
    })


@require_POST
@login_required(login_url="main:login")
def delete_skill(request, skill_id):
    if not request.user.is_superuser:
        raise PermissionDenied

    item = get_object_or_404(Skill, pk=skill_id)
    item.delete()
    messages.success(request, "Skill berhasil dihapus!")
    return redirect("main:show_skills")


@require_POST
@login_required(login_url="main:login")
def toggle_skill_star(request, skill_id):
    item = get_object_or_404(Skill, pk=skill_id)
    if item.starred_by.filter(pk=request.user.pk).exists():
        item.starred_by.remove(request.user)
    else:
        item.starred_by.add(request.user)
    return redirect("main:show_skills")
