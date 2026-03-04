"""Unit tests for the Cheese and Rating models."""

import pytest
from django.db import IntegrityError

from ..models import Cheese, Rating
from .factories import CheeseFactory, RatingFactory
from ...users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


# ── Cheese model ─────────────────────────────────────────────────────────────


class TestCheeseStr:
    def test_str_returns_name(self):
        cheese = CheeseFactory(name="Gouda")
        assert str(cheese) == "Gouda"


class TestCheeseAbsoluteUrl:
    def test_url_contains_slug(self):
        cheese = CheeseFactory(name="Brie")
        url = cheese.get_absolute_url()
        assert cheese.slug in url
        assert url.startswith("/cheeses/")


class TestCheeseAverageRating:
    def test_no_ratings_returns_zero(self):
        cheese = CheeseFactory()
        assert cheese.average_rating == 0.0

    def test_single_rating_returned_correctly(self):
        cheese = CheeseFactory()
        user = UserFactory()
        Rating.objects.create(cheese=cheese, creator=user, score=4)
        assert cheese.average_rating == 4.0

    def test_average_across_multiple_ratings(self):
        cheese = CheeseFactory()
        u1, u2, u3 = UserFactory(), UserFactory(), UserFactory()
        Rating.objects.create(cheese=cheese, creator=u1, score=2)
        Rating.objects.create(cheese=cheese, creator=u2, score=4)
        Rating.objects.create(cheese=cheese, creator=u3, score=3)
        assert cheese.average_rating == 3.0

    def test_average_returns_float(self):
        """Avg() aggregation must return a float, not an int loop result."""
        cheese = CheeseFactory()
        user = UserFactory()
        Rating.objects.create(cheese=cheese, creator=user, score=5)
        assert isinstance(cheese.average_rating, float)


class TestCheeseOrdering:
    def test_cheeses_ordered_by_name(self):
        CheeseFactory(name="Zola")
        CheeseFactory(name="Asiago")
        CheeseFactory(name="Manchego")
        names = list(Cheese.objects.values_list("name", flat=True))
        assert names == sorted(names)


# ── Rating model ──────────────────────────────────────────────────────────────


class TestRatingStr:
    def test_str_contains_cheese_name_and_score(self):
        rating = RatingFactory(score=3)
        result = str(rating)
        assert "3" in result
        assert rating.cheese.name in result


class TestRatingUniqueness:
    def test_duplicate_rating_raises_integrity_error(self):
        cheese = CheeseFactory()
        user = UserFactory()
        Rating.objects.create(cheese=cheese, creator=user, score=4)
        with pytest.raises(IntegrityError):
            Rating.objects.create(cheese=cheese, creator=user, score=2)
