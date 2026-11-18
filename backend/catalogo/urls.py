from django.urls import path

from catalogo.views import CatalogoView

urlpatterns = [
    path('catalogo/', CatalogoView.as_view(), name='catalogo'),
]
