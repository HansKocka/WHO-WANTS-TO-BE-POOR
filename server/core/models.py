from django.conf import settings
from django.db import models
from django.utils import timezone


class EmailVerification(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="email_verification")
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def is_expired(self):
        return timezone.now() > self.expires_at


class PasswordResetCode(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="password_reset_code")
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def is_expired(self):
        return timezone.now() > self.expires_at


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
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    @property
    def answer_time_display(self):
        if not self.started_at or not self.finished_at:
            return "-"

        total_seconds = max(0, int((self.finished_at - self.started_at).total_seconds()))
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        return f"{minutes}:{seconds:02d}"

    class Meta:
        unique_together = ('name', 'session')


class PlayerAnswer(models.Model):
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name="answers")
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="player_answers")
    selected_answer = models.ForeignKey(Answer, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("player", "question")
