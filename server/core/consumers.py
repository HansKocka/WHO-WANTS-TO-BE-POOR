import json
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async


class QuizConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.session_pin = self.scope['url_route']['kwargs']['session_pin']
        self.room_group_name = f'quiz_{self.session_pin}'

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        msg_type = data.get("type")

        if msg_type == "join":
            await self.join_game(data)
        elif msg_type == "start":
            await self.start_game()
        elif msg_type == "end":
            await self.end_game()
        elif msg_type == "answer":
            await self.handle_answer(data)

    async def join_game(self, data):
        from .models import GameSession, Player

        session = await sync_to_async(GameSession.objects.get)(
            pin=self.session_pin
        )

        await sync_to_async(Player.objects.get_or_create)(
            name=data["name"],
            session=session
        )

        players = await sync_to_async(list)(
            Player.objects.filter(session=session).values_list("name", flat=True)
        )

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "quiz_message",
                "event_type": "players_update",
                "players": players
            }
        )

    async def start_game(self):
        from .models import GameSession

        session = await sync_to_async(GameSession.objects.get)(
            pin=self.session_pin
        )

        session.state = "question"
        await sync_to_async(session.save)()

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "quiz_message",
                "event_type": "start",
                "session_pin": self.session_pin
            }
        )

    async def end_game(self):
        from .models import GameSession

        session = await sync_to_async(GameSession.objects.get)(
            pin=self.session_pin
        )

        session.state = "finished"
        await sync_to_async(session.save)()

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "quiz_message",
                "event_type": "end",
                "session_pin": self.session_pin
            }
        )

    async def handle_answer(self, data):
        from .models import Player, Answer

        player = await sync_to_async(Player.objects.get)(
            name=data["name"],
            session__pin=self.session_pin
        )

        answer = await sync_to_async(Answer.objects.get)(
            id=data["answer_id"]
        )

        correct = answer.is_correct

        if correct:
            player.score += 1
            await sync_to_async(player.save)()

        await self.send(text_data=json.dumps({
            "type": "answer_result",
            "correct": correct,
            "score": player.score
        }))

    async def quiz_message(self, event):
        await self.send(text_data=json.dumps({
            "type": event.get("event_type"),
            "players": event.get("players"),
            "question": event.get("question"),
            "answers": event.get("answers"),
            "session_pin": event.get("session_pin"),
        }))
