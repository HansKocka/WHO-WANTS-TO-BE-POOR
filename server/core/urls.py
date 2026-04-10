from django.urls import path
from .views import home, about, contact, create, join, quiz, host, my, quiz_detail

urlpatterns = [
    path('', home, name="home_page"),
    path('about/', about, name="about_page"),
    path('contact/', contact, name="contact_page"),
    path('create/', create, name='create'),
    path('join/', join, name='join'),
    path('quiz/', quiz, name='quiz'),
    path('host/<int:quiz_id>/', host, name='host'),
    path('my-quizes/', my, name='my'),
    path('quiz/<int:quiz_id>/', quiz_detail, name='quiz_detail'),
]
