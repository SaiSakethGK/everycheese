import pytest
from ..models import Cheese
from .factories import CheeseFactory


# Connects our tests with our database
pytestmark = pytest.mark.django_d

@pytest.mark.django_db
def test__str__():
    cheese = CheeseFactory()
    assert cheese.__str__() == cheese.name
    assert str(cheese) == cheese.name
