from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/quiz/(?P<session_pin>\w+)/$', consumers.QuizConsumer.as_asgi()),
]