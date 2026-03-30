import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from chat.models import ChatMessage


ROOM_GROUP_NAME = "public_chat"


class ChatConsumer(AsyncWebsocketConsumer):
	async def connect(self):
		user = self.scope.get("user")
		if user is None or user.is_anonymous:
			await self.close(code=4401)
			return

		self.roomGroupName = ROOM_GROUP_NAME
		await self.channel_layer.group_add(
			self.roomGroupName ,
			self.channel_name
		)
		await self.accept()

	async def disconnect(self , close_code):
		await self.channel_layer.group_discard(
			self.roomGroupName ,
			self.channel_name
		)

	async def receive(self, text_data):
		text_data_json = json.loads(text_data)
		message = text_data_json["message"].strip()
		if not message:
			return

		saved_message = await self.save_message(message)
		await self.channel_layer.group_send(
			self.roomGroupName,
			{
				"type": "chat.message",
				"message": saved_message["message"],
				"username": saved_message["username"],
				"timestamp": saved_message["timestamp"],
			},
		)

	@database_sync_to_async
	def save_message(self, message):
		saved_message = ChatMessage.objects.create(
			user=self.scope["user"],
			content=message,
		)
		return {
			"message": saved_message.content,
			"username": self.scope["user"].username,
			"timestamp": saved_message.created_at.strftime("%H:%M"),
		}

	async def chat_message(self, event):
		await self.send(
			text_data=json.dumps(
				{
					"message": event["message"],
					"username": event["username"],
					"timestamp": event["timestamp"],
				}
			)
		)
