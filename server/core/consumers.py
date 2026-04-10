import json
from channels.generic.websocket import AsyncWebsocketConsumer


class QuizConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.session_pin = None
        self.room_group_name = None

    async def connect(self):
        try:
            self.session_pin = self.scope['url_route']['kwargs']['session_pin']
            self.room_group_name = f'quiz_{self.session_pin}'
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )
            await self.accept()
        except Exception as e:
            print(f"Connect error: {e}")
            await self.close()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data=None, bytes_data=None):
        if text_data:
            data = json.loads(text_data)

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'quiz_message',
                    'message': data
                }
            )

    async def quiz_message(self, event):
        message = event['message']
        await self.send(text_data=json.dumps(message))
