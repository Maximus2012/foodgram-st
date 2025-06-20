from django.shortcuts import get_object_or_404, redirect

from .models import Recipe


def short_link_redirect(request, pk):
    recipe = get_object_or_404(Recipe, pk=pk)
    return redirect(f'/recipes/{recipe.pk}')
