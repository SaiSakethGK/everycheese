"""Test factories for the cheeses app."""

import factory
import factory.fuzzy
from django.template.defaultfilters import slugify

from ..models import Cheese, Rating
from ...users.tests.factories import UserFactory


class CheeseFactory(factory.django.DjangoModelFactory):
    name = factory.fuzzy.FuzzyText()
    slug = factory.LazyAttribute(lambda obj: slugify(obj.name))
    description = factory.Faker(
        "paragraph", nb_sentences=3, variable_nb_sentences=True
    )
    firmness = factory.fuzzy.FuzzyChoice(
        [x[0] for x in Cheese.Firmness.choices]
    )
    country_of_origin = factory.Faker("country_code")
    creator = factory.SubFactory(UserFactory)

    class Meta:
        model = Cheese


class RatingFactory(factory.django.DjangoModelFactory):
    score = factory.fuzzy.FuzzyInteger(1, 5)
    creator = factory.SubFactory(UserFactory)
    cheese = factory.SubFactory(CheeseFactory)

    class Meta:
        model = Rating
