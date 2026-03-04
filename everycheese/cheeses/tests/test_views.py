"""
Integration tests for cheese CRUD views and the AJAX rating endpoint.

Author: Sai Saketh Gooty Kase
"""

import json

import pytest
from django.urls import reverse

from ..models import Cheese, Rating
from .factories import CheeseFactory, RatingFactory
from ...users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


# ── Helpers ───────────────────────────────────────────────────────────────────


def _url(name, **kwargs):
    return reverse(f"cheeses:{name}", kwargs=kwargs)


# ── CheeseListView ────────────────────────────────────────────────────────────


class TestCheeseListView:
    def test_returns_200_for_anonymous_user(self, client):
        response = client.get(_url("list"))
        assert response.status_code == 200

    def test_lists_all_cheeses(self, client):
        CheeseFactory.create_batch(3)
        response = client.get(_url("list"))
        assert len(response.context["cheese_list"]) == 3

    def test_search_filters_by_name(self, client):
        CheeseFactory(name="Gouda")
        CheeseFactory(name="Brie")
        response = client.get(_url("list") + "?q=gouda")
        names = [c.name for c in response.context["cheese_list"]]
        assert "Gouda" in names
        assert "Brie" not in names

    def test_firmness_filter(self, client):
        CheeseFactory(firmness=Cheese.Firmness.SOFT)
        CheeseFactory(firmness=Cheese.Firmness.HARD)
        response = client.get(_url("list") + "?firmness=soft")
        for cheese in response.context["cheese_list"]:
            assert cheese.firmness == Cheese.Firmness.SOFT

    def test_empty_search_shows_no_results_state(self, client):
        response = client.get(_url("list") + "?q=xyzzynosuch")
        assert len(response.context["cheese_list"]) == 0


# ── CheeseDetailView ──────────────────────────────────────────────────────────


class TestCheeseDetailView:
    def test_returns_200_for_anonymous_user(self, client):
        cheese = CheeseFactory()
        response = client.get(_url("detail", slug=cheese.slug))
        assert response.status_code == 200

    def test_context_contains_cheese(self, client):
        cheese = CheeseFactory()
        response = client.get(_url("detail", slug=cheese.slug))
        assert response.context["cheese"] == cheese

    def test_user_rating_in_context_when_authenticated(self, client):
        user = UserFactory()
        cheese = CheeseFactory()
        RatingFactory(creator=user, cheese=cheese, score=4)
        client.force_login(user)
        response = client.get(_url("detail", slug=cheese.slug))
        assert response.context["user_rating"] == 4

    def test_user_rating_zero_when_not_rated(self, client):
        user = UserFactory()
        cheese = CheeseFactory()
        client.force_login(user)
        response = client.get(_url("detail", slug=cheese.slug))
        assert response.context["user_rating"] == 0


# ── CheeseCreateView ──────────────────────────────────────────────────────────


class TestCheeseCreateView:
    def test_redirects_anonymous_to_login(self, client):
        response = client.get(_url("add"))
        assert response.status_code == 302
        assert "/accounts/" in response["Location"]

    def test_authenticated_user_sees_form(self, client):
        client.force_login(UserFactory())
        response = client.get(_url("add"))
        assert response.status_code == 200

    def test_create_assigns_creator(self, client):
        user = UserFactory()
        client.force_login(user)
        client.post(
            _url("add"),
            {
                "name": "Test Cheese",
                "description": "Tasty",
                "firmness": Cheese.Firmness.SOFT,
                "country_of_origin": "FR",
            },
        )
        cheese = Cheese.objects.get(name="Test Cheese")
        assert cheese.creator == user


# ── CheeseUpdateView ──────────────────────────────────────────────────────────


class TestCheeseUpdateView:
    def test_redirects_anonymous_to_login(self, client):
        cheese = CheeseFactory()
        response = client.get(_url("update", slug=cheese.slug))
        assert response.status_code == 302

    def test_creator_can_access_update_form(self, client):
        user = UserFactory()
        cheese = CheeseFactory(creator=user)
        client.force_login(user)
        response = client.get(_url("update", slug=cheese.slug))
        assert response.status_code == 200

    def test_non_creator_gets_403(self, client):
        cheese = CheeseFactory()
        other_user = UserFactory()
        client.force_login(other_user)
        response = client.get(_url("update", slug=cheese.slug))
        assert response.status_code == 403

    def test_staff_can_access_any_update_form(self, client):
        cheese = CheeseFactory()
        staff = UserFactory(is_staff=True)
        client.force_login(staff)
        response = client.get(_url("update", slug=cheese.slug))
        assert response.status_code == 200

    def test_valid_post_updates_rating(self, client):
        user = UserFactory()
        cheese = CheeseFactory(creator=user)
        client.force_login(user)
        client.post(
            _url("update", slug=cheese.slug),
            {
                "name": cheese.name,
                "description": cheese.description,
                "firmness": cheese.firmness,
                "country_of_origin": cheese.country_of_origin,
                "rating": "5",
            },
        )
        rating = Rating.objects.get(creator=user, cheese=cheese)
        assert rating.score == 5


# ── CheeseDeleteView ──────────────────────────────────────────────────────────


class TestCheeseDeleteView:
    def test_redirects_anonymous_to_login(self, client):
        cheese = CheeseFactory()
        response = client.post(_url("delete", slug=cheese.slug))
        assert response.status_code == 302

    def test_creator_can_delete(self, client):
        user = UserFactory()
        cheese = CheeseFactory(creator=user)
        client.force_login(user)
        client.post(_url("delete", slug=cheese.slug))
        assert not Cheese.objects.filter(pk=cheese.pk).exists()

    def test_non_creator_cannot_delete(self, client):
        cheese = CheeseFactory()
        intruder = UserFactory()
        client.force_login(intruder)
        response = client.post(_url("delete", slug=cheese.slug))
        assert response.status_code == 403
        assert Cheese.objects.filter(pk=cheese.pk).exists()

    def test_delete_redirects_to_list(self, client):
        user = UserFactory()
        cheese = CheeseFactory(creator=user)
        client.force_login(user)
        response = client.post(_url("delete", slug=cheese.slug))
        assert response.status_code == 302
        assert response["Location"] == _url("list")


# ── RateCheeseView ────────────────────────────────────────────────────────────


class TestRateCheeseView:
    def _post(self, client, slug, score):
        return client.post(
            _url("rate", slug=slug),
            data=json.dumps({"score": score}),
            content_type="application/json",
        )

    def test_anonymous_user_redirected(self, client):
        cheese = CheeseFactory()
        response = self._post(client, cheese.slug, 4)
        assert response.status_code == 302

    def test_valid_rating_returns_200(self, client):
        user = UserFactory()
        cheese = CheeseFactory()
        client.force_login(user)
        response = self._post(client, cheese.slug, 4)
        assert response.status_code == 200

    def test_rating_persisted_to_db(self, client):
        user = UserFactory()
        cheese = CheeseFactory()
        client.force_login(user)
        self._post(client, cheese.slug, 3)
        assert Rating.objects.filter(
            creator=user, cheese=cheese, score=3
        ).exists()

    def test_second_rating_updates_existing(self, client):
        user = UserFactory()
        cheese = CheeseFactory()
        client.force_login(user)
        self._post(client, cheese.slug, 2)
        self._post(client, cheese.slug, 5)
        assert Rating.objects.filter(creator=user, cheese=cheese).count() == 1
        assert Rating.objects.get(creator=user, cheese=cheese).score == 5

    def test_out_of_range_score_returns_400(self, client):
        user = UserFactory()
        cheese = CheeseFactory()
        client.force_login(user)
        response = self._post(client, cheese.slug, 9)
        assert response.status_code == 400

    def test_response_contains_new_average(self, client):
        user = UserFactory()
        cheese = CheeseFactory()
        client.force_login(user)
        response = self._post(client, cheese.slug, 4)
        data = json.loads(response.content)
        assert "average" in data
        assert data["average"] == 4.0
