from django.contrib.auth.models import User
from django.core import mail
from django.test import TestCase
from django.urls import reverse

from .models import Answer, EmailVerification, Question, Quiz


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
