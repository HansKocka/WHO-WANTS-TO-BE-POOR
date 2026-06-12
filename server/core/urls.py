from django.urls import path
from .views import (
    home, about, contact, create, join, quiz, host, quiz_detail,
    session_players, game, submit_answer, leaderboard, joined, result, my_quizzes, login_page, register_page,
    logout_page, edit_quiz, delete_quiz, quiz_review
)

urlpatterns = [
    path('', home, name="home_page"),
    path('about/', about, name="about_page"),
    path('contact/', contact, name="contact_page"),
    path('create/', create, name='create'),
    path('join/', join, name='join'),
    path('quiz/', quiz, name='quiz'),
    path('host/<int:quiz_id>/', host, name='host'),
    path('game/<str:session_pin>/', game, name='game'),
    path('joined/<str:pin>/', joined, name='joined'),
    path('game/<str:session_pin>/answer/', submit_answer, name='submit_answer'),
    path('leaderboard/<str:session_pin>/', leaderboard, name='leaderboard'),
    path('leaderboard/<str:session_pin>/review/', quiz_review, name='quiz_review'),
    path('result/<str:session_pin>/', result, name='result'),
    path('sessions/<str:session_pin>/players/', session_players, name='session_players'),
    path('quiz/<int:quiz_id>/', quiz_detail, name='quiz_detail'),
    path('quiz/<int:quiz_id>/edit/', edit_quiz, name='edit_quiz'),
    path('quiz/<int:quiz_id>/delete/', delete_quiz, name='delete_quiz'),
    path("my-quizzes/", my_quizzes, name="my_quizzes"),
    path("login/", login_page, name="login"),
    path("forgot-password/", forgot_password_page, name="forgot_password"),
    path("reset-password/", reset_password_page, name="reset_password"),
    path("register/", register_page, name="register"),
    path("verify-email/", verify_email_page, name="verify_email"),
    path("logout/", logout_page, name="logout"),
]
