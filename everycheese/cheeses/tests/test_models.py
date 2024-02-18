import pytest
from ..models import Cheese

# Connects our tests with our database
pytestmark = pytest.mark.django_d

@pytest.mark.django_db
def test__str__():
    cheese = Cheese.objects.create(name="Stracchino", description="Semi-sweet cheese eaten with starches.", firmness=Cheese.Firmness.SOFT, )
    assert cheese.__str__() == "Stracchino"
    assert str(cheese) == "Stracchino"
