import json
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from .models import Quiz, Answer, Question, GameSession, Player, PlayerAnswer
from .utils import generate_pin


def home(request):
    return render(request, "home.html")


def about(request):
    return render(request, "about.html")


def contact(request):
    return render(request, "contact.html")


def create(request):
    if request.method == "POST":
        title = request.POST.get("title")
        new_quiz = Quiz.objects.create(title=title)

        i = 1
        while True:
            question_text = request.POST.get(f"question_{i}")

            # pokud už další otázka není → konec
            if not question_text:
                break

            question = Question.objects.create(
                quiz=new_quiz,
                text=question_text
            )

            correct = request.POST.get(f"correct_{i}")

            for j in range(1, 5):
                answer_text = request.POST.get(f"answer{j}_{i}")

                Answer.objects.create(
                    question=question,
                    text=answer_text,
                    is_correct=(str(j) == correct)
                )

            i += 1

        return redirect("home_page")  # uprav podle svého
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


def my(request):
    return render(request, "my-quiz.html")


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
    })


def submit_answer(request, session_pin):
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

    player = get_object_or_404(Player, session=session, name=player_name)
    question = get_object_or_404(Question, id=question_id, quiz=session.quiz)
    answer = get_object_or_404(Answer, id=answer_id, question=question)

    player_answer, created = PlayerAnswer.objects.get_or_create(
        player=player,
        question=question,
        defaults={"selected_answer": answer},
    )

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

