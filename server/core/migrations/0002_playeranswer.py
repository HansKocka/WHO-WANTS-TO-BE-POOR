from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="PlayerAnswer",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("player", models.ForeignKey(on_delete=models.deletion.CASCADE, related_name="answers", to="core.player")),
                ("question", models.ForeignKey(on_delete=models.deletion.CASCADE, related_name="player_answers", to="core.question")),
                ("selected_answer", models.ForeignKey(on_delete=models.deletion.CASCADE, to="core.answer")),
            ],
            options={
                "unique_together": {("player", "question")},
            },
        ),
    ]
