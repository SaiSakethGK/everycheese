from typing import Any
from django.views.generic import ListView, DetailView
from .models import Cheese
import logging
from django.views.generic import CreateView


log = logging.getLogger(__name__)


class CheeseListView(ListView):
    model = Cheese
    
    def get_context_data(self, **kwargs: Any):
        log.info("Hello World")
        context = super().get_context_data(**kwargs)
        context['my_new_ch_list']=Cheese.objects.all()
        
        return context


class CheeseDetailView(DetailView):
    model = Cheese


class CheeseCreateView(CreateView):
    model = Cheese
    fields = [
        'name',
        'description',
        'firmness',
        'country_of_origin',
    ]
 
