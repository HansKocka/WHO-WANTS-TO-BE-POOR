import json
import random
from django.db import OperationalError, ProgrammingError
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.cache import never_cache
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.conf import settings
from .models import Quiz, Answer, Question, GameSession, Player, PlayerAnswer, EmailVerification
from .utils import generate_pin
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout


def create_email_code():
    return f"{random.randint(100000, 999999)}"


def send_verification_email(user):
    code = create_email_code()
    EmailVerification.objects.update_or_create(
        user=user,
        defaults={
            "code": code,
            "expires_at": timezone.now() + timezone.timedelta(minutes=15),
        },
    )

    send_mail(
        "Your Who Wants To Be Poor verification code",
        f"Your verification code is: {code}\n\nThis code expires in 15 minutes.",
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False,
    )


def home(request):
    return render(request, "home.html")


def about(request):
    return render(request, "about.html")


def contact(request):
    return render(request, "contact.html")


@login_required
def my_quizzes(request):
    quizzes = Quiz.objects.filter(owner=request.user).order_by("-id")

    return render(request, "my_quizzes.html", {
        "quizzes": quizzes
    })


@never_cache
def login_page(request):
    if request.user.is_authenticated:
        return redirect("my_quizzes")

    error = None

    if request.method == "POST":
        username = (request.POST.get("username") or "").strip()
        password = request.POST.get("password") or ""

        if not username or not password:
            error = "Fill in username and password"
        else:
            user = authenticate(request, username=username, password=password)

            if user is not None:
                login(request, user)
                return redirect("my_quizzes")
            else:
                error = "Wrong login"

    return render(request, "login.html", {"error": error})


@never_cache
def register_page(request):
    if request.user.is_authenticated:
        return redirect("my_quizzes")

    error = None

    if request.method == "POST":
        username = (request.POST.get("username") or "").strip()
        email = (request.POST.get("email") or "").strip().lower()
        password = request.POST.get("password") or ""

        if not username or not email or not password:
            error = "Fill in username, email and password"
        elif User.objects.filter(username=username).exists():
            error = "User already exists"
        elif User.objects.filter(email=email).exists():
            error = "Email is already used"
        else:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password
            )
            user.is_active = False
            user.save(update_fields=["is_active"])
            send_verification_email(user)
            request.session["pending_verification_user_id"] = user.id
            return redirect("verify_email")

    return render(request, "register.html", {"error": error})


@never_cache
def verify_email_page(request):
    user_id = request.session.get("pending_verification_user_id")
    user = User.objects.filter(id=user_id).first()

    if not user:
        return redirect("register")

    error = None
    message = f"We sent a verification code to {user.email}."

    if request.method == "POST":
        code = (request.POST.get("code") or "").strip()
        verification = EmailVerification.objects.filter(user=user).first()

        if not verification:
            error = "Verification code was not found."
        elif verification.is_expired():
            send_verification_email(user)
            error = "Code expired. We sent you a new one."
        elif verification.code != code:
            error = "Wrong verification code."
        else:
            user.is_active = True
            user.save(update_fields=["is_active"])
            verification.delete()
            login(request, user)
            request.session.pop("pending_verification_user_id", None)
            return redirect("my_quizzes")

    return render(request, "verify_email.html", {
        "error": error,
        "message": message,
        "email": user.email,
    })


def logout_page(request):
    logout(request)
    return redirect("home_page")


def csrf_failure(request, reason=""):
    return render(request, "csrf_failure.html", status=403)


@login_required
def create(request):
    if request.method == "POST":
        title = (request.POST.get("title") or "").strip()
        if not title:
            return render(request, "create.html", {
                "error": "Quiz title is required."
            })
        new_quiz = Quiz.objects.create(
            title=title,
            owner=request.user
        )

        i = 1
        while True:
            question_text = request.POST.get(f"question_{i}")

            if not question_text:
                break

            question = Question.objects.create(
                quiz=new_quiz,
                text=question_text
            )

            correct = request.POST.get(f"correct_{i}")

            for j in range(1, 5):
                answer_text = (request.POST.get(f"answer{j}_{i}") or "").strip()

                Answer.objects.create(
                    question=question,
                    text=answer_text,
                    is_correct=(str(j) == correct)
                )

            i += 1

        return redirect("my_quizzes")

    return render(request, "create.html")


def join(request):
    if request.method == "POST":
        name = (request.POST.get("name") or "").strip()
        pin = (request.POST.get("pin") or "").strip()

        if not name or not pin:
            return JsonResponse(
                {"ok": False, "error": "Name and PIN are required."},
                status=400
            )

        try:
            session = GameSession.objects.get(pin=pin, is_active=True)
        except GameSession.DoesNotExist:
            return JsonResponse(
                {"ok": False, "error": "Game session was not found."},
                status=404
            )

        Player.objects.get_or_create(
            session=session,
            name=name,
        )

        return JsonResponse({"ok": True, "pin": pin})

    return render(request, "join.html")


def quiz(request):
    quizzes = Quiz.objects.all()
    return render(request, "quiz.html", {"quizzes": quizzes})


def quiz_detail(request, quiz_id):
    quiz_obj = Quiz.objects.get(id=quiz_id)
    questions = Question.objects.filter(quiz=quiz_obj)
    return render(request, "quiz_detail.html", {
        "quiz": quiz_obj,
        "questions": questions
    })


def host(request, quiz_id):
    quiz_instance = get_object_or_404(Quiz, id=quiz_id)

    session = GameSession.objects.create(
        quiz=quiz_instance,  # <- teď je to správně instance
        pin=generate_pin(),
        is_active=True
    )

    return render(request, "hostquiz.html", {
        "quiz": quiz_instance,
        "session": session,
        "players": session.players.all(),
    })


def session_players(request, session_pin):
    session = get_object_or_404(GameSession, pin=session_pin)
    players = list(session.players.order_by("id").values_list("name", flat=True))
    return JsonResponse({"players": players})


def game(request, session_pin):
    session = get_object_or_404(
        GameSession.objects.select_related("quiz"),
        pin=session_pin
    )
    questions = Question.objects.filter(quiz=session.quiz).prefetch_related("answer_set")

    return render(request, "game.html", {
        "session": session,
        "quiz": session.quiz,
        "questions": questions,
        "players": session.players.order_by("id"),
        "is_host": True,
    })


@csrf_exempt
def submit_answer(request, session_pin):
    try:
        if request.method != "POST":
            return JsonResponse({"ok": False, "error": "POST required."}, status=405)

        session = get_object_or_404(GameSession.objects.select_related("quiz"), pin=session_pin)

        try:
            payload = json.loads(request.body.decode("utf-8"))
        except json.JSONDecodeError:
            return JsonResponse({"ok": False, "error": "Invalid JSON."}, status=400)

        player_name = (payload.get("player_name") or "").strip()
        question_id = payload.get("question_id")
        answer_id = payload.get("answer_id")

        if not player_name or not question_id or not answer_id:
            return JsonResponse({"ok": False, "error": "Missing answer data."}, status=400)

        player = Player.objects.filter(session=session, name=player_name).first()
        if not player:
            return JsonResponse({"ok": False, "error": "Player was not found."}, status=404)

        question = Question.objects.filter(id=question_id, quiz=session.quiz).first()
        if not question:
            return JsonResponse({"ok": False, "error": "Question was not found."}, status=404)

        answer = Answer.objects.filter(id=answer_id, question=question).first()
        if not answer:
            return JsonResponse({"ok": False, "error": "Answer was not found."}, status=404)

        try:
            player_answer, created = PlayerAnswer.objects.get_or_create(
                player=player,
                question=question,
                defaults={"selected_answer": answer},
            )
        except (OperationalError, ProgrammingError):
            answered_key = f"answered_{session_pin}_{player_name}"
            answered_questions = request.session.get(answered_key, [])

            if question.id in answered_questions:
                created = False
            else:
                answered_questions.append(question.id)
                request.session[answered_key] = answered_questions
                request.session.modified = True
                created = True

        if not created:
            return JsonResponse({
                "ok": False,
                "error": "You already answered this question.",
                "score": player.score,
            }, status=400)

        if answer.is_correct:
            player.score += 1
            player.save(update_fields=["score"])

        return JsonResponse({
            "ok": True,
            "correct": answer.is_correct,
            "score": player.score,
        })
    except Exception as error:
        return JsonResponse({
            "ok": False,
            "error": f"Server error: {error}",
        }, status=500)


def leaderboard(request, session_pin):
    session = get_object_or_404(GameSession.objects.select_related("quiz"), pin=session_pin)
    if session.state != "finished":
        session.state = "finished"
        session.save(update_fields=["state"])

    players = session.players.order_by("-score", "name")

    return render(request, "leaderboard.html", {
        "session": session,
        "quiz": session.quiz,
        "players": players,
    })


def joined(request, pin):
    session = get_object_or_404(
        GameSession.objects.select_related("quiz"),
        pin=pin
    )
    questions = Question.objects.filter(quiz=session.quiz).prefetch_related("answer_set")
    player_name = (request.GET.get("player_name") or "").strip()

    return render(request, "joined.html", {
        "session": session,
        "quiz": session.quiz,
        "questions": questions,
        "players": session.players.order_by("id"),
        "player_name": player_name,
    })


def result(request, session_pin):
    player_name = (request.GET.get("player_name") or "").strip()
    session = get_object_or_404(
        GameSession.objects.select_related("quiz"),
        pin=session_pin
    )

    player = None
    if player_name:
        player = Player.objects.filter(session=session, name=player_name).first()

    return render(request, "result.html", {
        "session": session,
        "quiz": session.quiz,
        "player": player,
        "player_name": player_name,
    })
