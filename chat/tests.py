import json
from types import SimpleNamespace
from unittest.mock import AsyncMock

from asgiref.sync import async_to_sync
from channels.testing import WebsocketCommunicator
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth import get_user_model
from django.test import TestCase, TransactionTestCase

from chat.consumers import ChatConsumer, ROOM_GROUP_NAME
from chat.models import ChatMessage


User = get_user_model()


class ChatPageTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="tester",
            password="strong-test-password",
        )

    def test_chat_page_redirects_anonymous_users(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 302)
        self.assertIn("/auth/login/", response.url)

    def test_chat_page_shows_recent_messages_for_authenticated_users(self):
        ChatMessage.objects.create(user=self.user, content="Earlier message")
        self.client.force_login(self.user)

        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Earlier message")
        self.assertContains(response, "tester")

    def test_register_page_loads(self):
        response = self.client.get("/auth/register/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Create your account.")

    def test_register_page_creates_user_and_logs_them_in(self):
        response = self.client.post(
            "/auth/register/",
            {
                "username": "new-user",
                "password1": "VeryStrongPassword123",
                "password2": "VeryStrongPassword123",
            },
        )

        self.assertRedirects(response, "/")
        self.assertTrue(User.objects.filter(username="new-user").exists())
        self.assertEqual(
            int(self.client.session["_auth_user_id"]),
            User.objects.get(username="new-user").id,
        )


class ChatConsumerTests(TransactionTestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="socket-user",
            password="strong-test-password",
        )

    def test_consumer_rejects_anonymous_connections(self):
        communicator = WebsocketCommunicator(ChatConsumer.as_asgi(), "/")
        communicator.scope["user"] = AnonymousUser()
        connected, close_code = async_to_sync(communicator.connect)()

        self.assertFalse(connected)
        self.assertEqual(close_code, 4401)

    def test_receive_persists_message_and_emits_group_event(self):
        consumer = ChatConsumer()
        consumer.scope = {"user": self.user}
        consumer.roomGroupName = ROOM_GROUP_NAME
        consumer.channel_layer = SimpleNamespace(group_send=AsyncMock())

        async_to_sync(consumer.receive)(
            json.dumps({"message": "Hello from the socket"})
        )

        self.assertTrue(
            ChatMessage.objects.filter(
                user=self.user,
                content="Hello from the socket",
            ).exists()
        )
        consumer.channel_layer.group_send.assert_awaited_once()
        group_name, payload = consumer.channel_layer.group_send.await_args.args
        self.assertEqual(group_name, ROOM_GROUP_NAME)
        self.assertEqual(payload["type"], "chat.message")
        self.assertEqual(payload["message"], "Hello from the socket")
        self.assertEqual(payload["username"], "socket-user")
        self.assertTrue(payload["timestamp"])

    def test_receive_ignores_blank_messages(self):
        consumer = ChatConsumer()
        consumer.scope = {"user": self.user}
        consumer.roomGroupName = ROOM_GROUP_NAME
        consumer.channel_layer = SimpleNamespace(group_send=AsyncMock())

        async_to_sync(consumer.receive)(json.dumps({"message": "   "}))

        self.assertFalse(ChatMessage.objects.exists())
        consumer.channel_layer.group_send.assert_not_called()

    def test_chat_message_serializes_payload(self):
        consumer = ChatConsumer()
        consumer.send = AsyncMock()

        async_to_sync(consumer.chat_message)(
            {
                "message": "Hello from the socket",
                "username": "socket-user",
                "timestamp": "12:00",
            }
        )

        consumer.send.assert_awaited_once_with(
            text_data=json.dumps(
                {
                    "message": "Hello from the socket",
                    "username": "socket-user",
                    "timestamp": "12:00",
                }
            )
        )
