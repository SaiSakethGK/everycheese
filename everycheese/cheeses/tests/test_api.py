"""Integration tests for the DRF REST API endpoints."""

import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from ..models import Cheese, Rating
from .factories import CheeseFactory, RatingFactory
from ...users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


@pytest.fixture()
def api_client():
    return APIClient()


@pytest.fixture()
def auth_client():
    user = UserFactory()
    client = APIClient()
    client.force_authenticate(user=user)
    return client, user


# ── Cheese list endpoint ──────────────────────────────────────────────────────


class TestCheeseListAPI:
    url = "/api/v1/cheeses/"

    def test_returns_200_unauthenticated(self, api_client):
        response = api_client.get(self.url)
        assert response.status_code == 200

    def test_returns_all_cheeses(self, api_client):
        CheeseFactory.create_batch(3)
        response = api_client.get(self.url)
        assert response.data["count"] == 3

    def test_search_by_name(self, api_client):
        CheeseFactory(name="Emmental")
        CheeseFactory(name="Feta")
        response = api_client.get(self.url + "?search=Emmental")
        assert response.data["count"] == 1
        assert response.data["results"][0]["name"] == "Emmental"

    def test_filter_by_firmness(self, api_client):
        CheeseFactory(firmness=Cheese.Firmness.SOFT)
        CheeseFactory(firmness=Cheese.Firmness.HARD)
        response = api_client.get(self.url + "?firmness=soft")
        assert response.data["count"] == 1

    def test_ordering_by_name(self, api_client):
        CheeseFactory(name="Zola")
        CheeseFactory(name="Asiago")
        response = api_client.get(self.url + "?ordering=name")
        names = [r["name"] for r in response.data["results"]]
        assert names == sorted(names)


# ── Cheese create endpoint ────────────────────────────────────────────────────


class TestCheeseCreateAPI:
    url = "/api/v1/cheeses/"

    def test_unauthenticated_cannot_create(self, api_client):
        response = api_client.post(
            self.url,
            {"name": "TestCheese", "firmness": "soft"},
        )
        assert response.status_code == 403

    def test_authenticated_user_can_create(self, auth_client):
        client, user = auth_client
        response = client.post(
            self.url,
            {
                "name": "NewCheese",
                "description": "Tasty",
                "firmness": "soft",
                "country_of_origin": "IT",
            },
        )
        assert response.status_code == 201
        assert Cheese.objects.filter(name="NewCheese").exists()

    def test_creator_set_to_authenticated_user(self, auth_client):
        client, user = auth_client
        client.post(
            self.url,
            {"name": "MyCheese", "firmness": "hard"},
        )
        cheese = Cheese.objects.get(name="MyCheese")
        assert cheese.creator == user


# ── Cheese detail endpoint ────────────────────────────────────────────────────


class TestCheeseDetailAPI:
    def _url(self, slug):
        return f"/api/v1/cheeses/{slug}/"

    def test_returns_200_unauthenticated(self, api_client):
        cheese = CheeseFactory()
        response = api_client.get(self._url(cheese.slug))
        assert response.status_code == 200

    def test_detail_includes_nested_ratings(self, api_client):
        cheese = CheeseFactory()
        RatingFactory(cheese=cheese, score=4)
        response = api_client.get(self._url(cheese.slug))
        assert "ratings" in response.data
        assert len(response.data["ratings"]) == 1

    def test_slug_used_as_lookup(self, api_client):
        cheese = CheeseFactory(name="SlugCheese")
        response = api_client.get(self._url(cheese.slug))
        assert response.data["name"] == "SlugCheese"


# ── Rate action endpoint ──────────────────────────────────────────────────────


class TestRateAction:
    def _url(self, slug):
        return f"/api/v1/cheeses/{slug}/rate/"

    def test_unauthenticated_cannot_rate(self, api_client):
        cheese = CheeseFactory()
        response = api_client.post(self._url(cheese.slug), {"score": 3})
        assert response.status_code == 403

    def test_authenticated_user_can_rate(self, auth_client):
        client, user = auth_client
        cheese = CheeseFactory()
        response = client.post(self._url(cheese.slug), {"score": 4})
        assert response.status_code == 200
        assert Rating.objects.filter(creator=user, cheese=cheese).exists()

    def test_rating_updates_on_second_request(self, auth_client):
        client, user = auth_client
        cheese = CheeseFactory()
        client.post(self._url(cheese.slug), {"score": 2})
        client.post(self._url(cheese.slug), {"score": 5})
        assert Rating.objects.filter(creator=user, cheese=cheese).count() == 1
        assert Rating.objects.get(creator=user, cheese=cheese).score == 5

    def test_response_contains_average(self, auth_client):
        client, _ = auth_client
        cheese = CheeseFactory()
        response = client.post(self._url(cheese.slug), {"score": 5})
        assert "average" in response.data

    def test_invalid_score_returns_400(self, auth_client):
        client, _ = auth_client
        cheese = CheeseFactory()
        response = client.post(self._url(cheese.slug), {"score": 10})
        assert response.status_code == 400


# ── Pagination ────────────────────────────────────────────────────────────────


class TestPagination:
    url = "/api/v1/cheeses/"

    def test_response_is_paginated(self, api_client):
        CheeseFactory.create_batch(5)
        response = api_client.get(self.url)
        assert "count" in response.data
        assert "results" in response.data
        assert "next" in response.data
