"""
URL mappings for recipe app
"""
from django.urls import (
    path,
    include
)

from rest_framework.routers import DefaultRouter

from recipe import views


router = DefaultRouter()
router.register('recipes', viewset=views.RecipeViewSet)
router.register('tags', viewset=views.TagViewSet)
router.register('ingredients', viewset=views.IngredientViewSet)

app_name = 'recipe'

urlpatterns = [
    path('', include(router.urls)),
    path('p/', views.PublicRecipeListView.as_view(), name="public-recipes")
]
