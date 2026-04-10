from django.shortcuts import render, redirect, get_object_or_404
from .models import Quiz, Answer, Question, GameSession
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
        "session": session
    })


def my(request):
    return render(request, "my-quiz.html")

