from django.conf import settings
from django.db import models


class Quiz(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)

    def __str__(self):
        return self.title


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

    current_question = models.IntegerField(default=0)

    state = models.CharField(
        max_length=20,
        choices=[
            ("waiting", "Waiting"),
            ("question", "Question"),
            ("results", "Results"),
            ("finished", "Finished"),
        ],
        default="waiting"
    )


class Player(models.Model):
    name = models.CharField(max_length=100)
    score = models.IntegerField(default=0)
    session = models.ForeignKey(GameSession, on_delete=models.CASCADE, related_name='players')

    class Meta:
        unique_together = ('name', 'session')


class PlayerAnswer(models.Model):
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name="answers")
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="player_answers")
    selected_answer = models.ForeignKey(Answer, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("player", "question")
