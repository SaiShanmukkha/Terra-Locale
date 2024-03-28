from django.urls import re_path,path
from .views import do_search,ProductSearchListView
from . import views


urlpatterns = [
    path(route='/', view=views.ProductSearchListView.as_view(), name='search'),
    #re_path(r'^$', do_search, name='search')
]

app_name: str = 'search'

__all__ = ('app_name', 'urlpatterns',)