from django.urls import path
from . import views
app_name = 'transfer'
urlpatterns = [
    path('sign-up/', views.sign_up, name='sign_up'),
    path('login/', views.login_view, name='login'),
    path('profile/', views.profile, name='profile'),
    path('home/', views.home, name='home'),
]
