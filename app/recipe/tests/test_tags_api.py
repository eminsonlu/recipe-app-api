"""
Test for tags API
"""
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Tag, Recipe

from recipe.serializers import TagSerializer


TAGS_URL = reverse("recipe:tag-list")


def detail_url(tag_id):
    """Create an return a tag url"""
    return reverse("recipe:tag-detail", args=[tag_id])


def create_user(email="user@example.com", password="testpass123"):
    """Create and return a new user"""
    return get_user_model().objects.create_user(email, password)


class PublicTagsApiTests(TestCase):
    """Test unauthenticated API requests"""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test auth is required"""
        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateTagsAPITests(TestCase):
    """Test authenticated API requests"""

    def setUp(self):
        self.client = APIClient()
        self.user = create_user()
        self.client.force_authenticate(self.user)

    def test_retrieve_tags(self):
        """Test retrieving a list of tags"""
        Tag.objects.create(user=self.user, name="drink")
        Tag.objects.create(user=self.user, name="dessert")

        res = self.client.get(TAGS_URL)

        tags = Tag.objects.all().order_by('-name')
        serializer = TagSerializer(tags, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_tags_limited_to_user(self):
        """Test list of tags is limited to authenticated user"""
        user2 = create_user(email="user2@example.com")
        Tag.objects.create(user=user2, name="fruit")
        tag = Tag.objects.create(user=self.user, name="dinner")

        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], tag.name)
        self.assertEqual(res.data[0]['id'], tag.id)

    def test_update_tag(self):
        """Test updating tag"""
        tag = Tag.objects.create(user=self.user, name="fruit")
        payload = {'name': 'desert'}
        url = detail_url(tag.id)

        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        tag.refresh_from_db()
        self.assertEqual(tag.name, payload['name'])

    def test_delete_tag(self):
        """Test deleting tag"""
        tag = Tag.objects.create(user=self.user, name="fruit")

        url = detail_url(tag.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        tags = Tag.objects.filter(user=self.user)
        self.assertFalse(tags.exists())

    def test_filter_tags_assigned_to_recipes(self):
        """Test filtering tags by those assigned to recipes"""
        tag1 = Tag.objects.create(user=self.user, name="breakfast")
        tag2 = Tag.objects.create(user=self.user, name="lunch")
        recipe = Recipe.objects.create(
            user=self.user,
            title="Coriander eggs on toast",
            time_minutes=10,
            price=Decimal("5.00")
        )
        recipe.tags.add(tag1)

        res = self.client.get(TAGS_URL, {'assigned_only': 1})

        serializer1 = TagSerializer(tag1)
        serializer2 = TagSerializer(tag2)

        self.assertIn(serializer1.data, res.data)
        self.assertNotIn(serializer2.data, res.data)

    def test_filter_tags_assigned_unique(self):
        """Test filtering tags by assigned returns unique items"""
        tag = Tag.objects.create(user=self.user, name="breakfast")
        Tag.objects.create(user=self.user, name="lunch")
        recipe1 = Recipe.objects.create(
            user=self.user,
            title="Pancakes",
            time_minutes=5,
            price=Decimal("3.00")
        )
        recipe1.tags.add(tag)
        recipe2 = Recipe.objects.create(
            user=self.user,
            title="Porridge",
            time_minutes=3,
            price=Decimal("2.00")
        )
        recipe2.tags.add(tag)

        res = self.client.get(TAGS_URL, {'assigned_only': 1})

        self.assertEqual(len(res.data), 1)