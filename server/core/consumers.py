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

        if data["type"] == "join":
            await self.join_game(data)

        elif data["type"] == "start":
            await self.start_game()

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "quiz_message",
                "message": data
            }
        )

    async def join_game(self, data):
        from .models import GameSession, Player   # 👈 DŮLEŽITÉ: import sem

        session = await sync_to_async(GameSession.objects.get)(
            pin=self.session_pin
        )

        await sync_to_async(Player.objects.create)(
            name=data["name"],
            session=session
        )

    async def start_game(self):
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "quiz_message",
                "message": {"type": "start"}
            }
        )

    async def quiz_message(self, event):
        await self.send(text_data=json.dumps(event["message"]))