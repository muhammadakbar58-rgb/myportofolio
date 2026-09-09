from django.shortcuts import render

from main.models import Experience


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