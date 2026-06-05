from django.contrib.auth.models import User
from django.core import mail
from django.test import TestCase
from django.urls import reverse

from .models import Answer, EmailVerification, GameSession, PasswordResetCode, Player, PlayerAnswer, Question, Quiz


class AuthQuizTests(TestCase):
    def test_register_sends_verification_email(self):
        response = self.client.post(reverse("register"), {
            "username": "alice",
            "email": "alice@example.com",
            "password": "strong-pass-123",
        })

        self.assertRedirects(response, reverse("verify_email"))
        user = User.objects.get(username="alice")
        self.assertFalse(user.is_active)
        self.assertEqual(user.email, "alice@example.com")
        self.assertTrue(EmailVerification.objects.filter(user=user).exists())
        self.assertEqual(len(mail.outbox), 1)

    def test_verify_email_activates_and_logs_user_in(self):
        self.client.post(reverse("register"), {
            "username": "alice",
            "email": "alice@example.com",
            "password": "strong-pass-123",
        })
        user = User.objects.get(username="alice")
        code = user.email_verification.code

        response = self.client.post(reverse("verify_email"), {
            "code": code,
        })

        self.assertRedirects(response, reverse("my_quizzes"))
        user.refresh_from_db()
        self.assertTrue(user.is_active)
        self.assertEqual(self.client.session["_auth_user_id"], str(user.id))

    def test_login_logs_user_in(self):
        user = User.objects.create_user(username="alice", password="strong-pass-123")

        response = self.client.post(reverse("login"), {
            "username": "alice",
            "password": "strong-pass-123",
        })

        self.assertRedirects(response, reverse("my_quizzes"))
        self.assertEqual(self.client.session["_auth_user_id"], str(user.id))

    def test_password_reset_sends_code_and_changes_password(self):
        user = User.objects.create_user(
            username="alice",
            email="alice@example.com",
            password="old-pass-123",
        )

        response = self.client.post(reverse("forgot_password"), {
            "email": "alice@example.com",
        })

        self.assertRedirects(response, reverse("reset_password"))
        reset_code = PasswordResetCode.objects.get(user=user)
        self.assertEqual(len(mail.outbox), 1)

        response = self.client.post(reverse("reset_password"), {
            "code": reset_code.code,
            "password": "new-pass-123",
            "password_confirm": "new-pass-123",
        })

        self.assertRedirects(response, reverse("login"))
        user.refresh_from_db()
        self.assertTrue(user.check_password("new-pass-123"))
        self.assertFalse(PasswordResetCode.objects.filter(user=user).exists())

    def test_my_quizzes_shows_only_logged_in_users_quizzes(self):
        alice = User.objects.create_user(username="alice", password="strong-pass-123")
        bob = User.objects.create_user(username="bob", password="strong-pass-123")
        alices_quiz = Quiz.objects.create(owner=alice, title="Alice quiz")
        Quiz.objects.create(owner=bob, title="Bob quiz")

        self.client.force_login(alice)
        response = self.client.get(reverse("my_quizzes"))

        self.assertContains(response, alices_quiz.title)
        self.assertNotContains(response, "Bob quiz")

    def test_create_assigns_logged_in_user_as_owner(self):
        alice = User.objects.create_user(username="alice", password="strong-pass-123")
        self.client.force_login(alice)

        self.client.post(reverse("create"), {
            "title": "Alice quiz",
            "question_1": "Question?",
            "answer1_1": "A",
            "answer2_1": "B",
            "answer3_1": "C",
            "answer4_1": "D",
            "correct_1": "1",
        })

        self.assertTrue(Quiz.objects.filter(owner=alice, title="Alice quiz").exists())

    def test_owner_can_edit_quiz(self):
        alice = User.objects.create_user(username="alice", password="strong-pass-123")
        quiz = Quiz.objects.create(owner=alice, title="Old title")
        question = Question.objects.create(quiz=quiz, text="Old question?")
        answer = Answer.objects.create(question=question, text="Old answer", is_correct=True)

        self.client.force_login(alice)
        response = self.client.post(reverse("edit_quiz", args=[quiz.id]), {
            "title": "New title",
            f"question_{question.id}": "New question?",
            f"answer_{answer.id}": "New answer",
            f"correct_{question.id}": str(answer.id),
        })

        self.assertRedirects(response, reverse("quiz_detail", args=[quiz.id]))
        quiz.refresh_from_db()
        question.refresh_from_db()
        answer.refresh_from_db()
        self.assertEqual(quiz.title, "New title")
        self.assertEqual(question.text, "New question?")
        self.assertEqual(answer.text, "New answer")

    def test_non_owner_cannot_edit_quiz(self):
        alice = User.objects.create_user(username="alice", password="strong-pass-123")
        bob = User.objects.create_user(username="bob", password="strong-pass-123")
        quiz = Quiz.objects.create(owner=alice, title="Alice quiz")

        self.client.force_login(bob)
        response = self.client.post(reverse("edit_quiz", args=[quiz.id]), {
            "title": "Bob title",
        })

        self.assertEqual(response.status_code, 404)
        quiz.refresh_from_db()
        self.assertEqual(quiz.title, "Alice quiz")

    def test_owner_can_delete_quiz(self):
        alice = User.objects.create_user(username="alice", password="strong-pass-123")
        quiz = Quiz.objects.create(owner=alice, title="Alice quiz")

        self.client.force_login(alice)
        response = self.client.post(reverse("delete_quiz", args=[quiz.id]))

        self.assertRedirects(response, reverse("my_quizzes"))
        self.assertFalse(Quiz.objects.filter(id=quiz.id).exists())

    def test_player_finish_time_is_saved_after_all_questions(self):
        owner = User.objects.create_user(username="owner", password="strong-pass-123")
        quiz = Quiz.objects.create(owner=owner, title="Timed quiz")
        question = Question.objects.create(quiz=quiz, text="Question?")
        answer = Answer.objects.create(question=question, text="A", is_correct=True)
        session = GameSession.objects.create(quiz=quiz, pin="123456")
        player = Player.objects.create(session=session, name="Player")

        response = self.client.post(
            reverse("submit_answer", args=[session.pin]),
            data={
                "player_name": player.name,
                "question_id": question.id,
                "answer_id": answer.id,
            },
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        player.refresh_from_db()
        self.assertIsNotNone(player.started_at)
        self.assertIsNotNone(player.finished_at)
        self.assertEqual(player.answer_time_display, "0:00")

    def test_quiz_review_shows_answer_counts(self):
        owner = User.objects.create_user(username="owner", password="strong-pass-123")
        quiz = Quiz.objects.create(owner=owner, title="Review quiz")
        question = Question.objects.create(quiz=quiz, text="Question?")
        correct = Answer.objects.create(question=question, text="Correct", is_correct=True)
        wrong = Answer.objects.create(question=question, text="Wrong", is_correct=False)
        session = GameSession.objects.create(quiz=quiz, pin="654321")
        player = Player.objects.create(session=session, name="Player")
        PlayerAnswer.objects.create(player=player, question=question, selected_answer=wrong)

        response = self.client.get(reverse("quiz_review", args=[session.pin]))

        self.assertContains(response, "Review quiz")
        self.assertContains(response, "1 wrong")
        self.assertContains(response, "Correct")
        self.assertContains(response, "Wrong")
        self.assertContains(response, "1 chose this")
