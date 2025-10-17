import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer

from .services import ai_assistant


logger = logging.getLogger(__name__)


class ChatConsumer(AsyncWebsocketConsumer):
    group_name = "ai_chat_room"

    async def connect(self):
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        await self.send_json({"type": "ready", "message": "connected"})

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        try:
            data = json.loads(text_data or "{}")
            message = (data.get("message") or "").strip()
            history = data.get("conversation_history") or []

            if not message:
                await self.send_json({"type": "error", "error": "Message is required"})
                return

            # Broadcast the user message to all clients (multi-browser sync)
            await self.channel_layer.group_send(
                self.group_name,
                {
                    "type": "chat.user_message",
                    "message": message,
                },
            )

            # Generate AI response (run in thread to avoid blocking event loop)
            from asgiref.sync import sync_to_async

            # Pass user for personalization and DB-backed context
            response = await sync_to_async(ai_assistant.generate_response)(message, history, self.scope.get("user"))
            # Send AI response only back to the sender, not the whole group
            await self.send_json({
                "type": "assistant",
                "response": response,
            })
        except json.JSONDecodeError:
            await self.send_json({"type": "error", "error": "Invalid JSON"})
        except Exception as e:
            logger.error(f"WS receive error: {e}", exc_info=True)
            await self.send_json({"type": "error", "error": "Internal error"})

    async def chat_user_message(self, event):
        await self.send_json({
            "type": "user",
            "message": event.get("message"),
        })

    async def chat_ai_message(self, event):
        await self.send_json({
            "type": "assistant",
            "response": event.get("response"),
        })

    async def send_json(self, payload):
        await self.send(text_data=json.dumps(payload))


