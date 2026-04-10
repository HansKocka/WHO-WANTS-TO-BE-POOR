
from django.db import models


class Quiz(models.Model):
    title = models.CharField(max_length=255)


class Question(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    text = models.CharField(max_length=255)


class Answer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)


class GameSession(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    pin = models.CharField(max_length=6, unique=True)
    is_active = models.BooleanField(default=True)


class Player(models.Model):
    name = models.CharField(max_length=100)
    score = models.IntegerField(default=0)
    session = models.ForeignKey(GameSession, on_delete=models.CASCADE, related_name='players')


class Meta:
    unique_together = ('name', 'session')
