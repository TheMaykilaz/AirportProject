import json
import logging
import asyncio
from typing import List, Dict, Any
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from asgiref.sync import sync_to_async

from .services import ai_assistant

logger = logging.getLogger(__name__)


class ChatConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for real-time AI chat with streaming responses."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.conversation_history: List[Dict[str, str]] = []
        self.is_generating = False

    async def connect(self):
        """Handle WebSocket connection."""
        logger.info(f"WebSocket connection attempt from {self.scope['client']}")

        # Accept connection
        await self.accept()
        logger.info("WebSocket connection accepted")

        # Send welcome message
        await self.send(text_data=json.dumps({
            'type': 'welcome',
            'message': 'Connected to AI chat. How can I help you today?'
        }))

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        logger.info(f"WebSocket disconnected with code: {close_code}")
        self.is_generating = False
        # Clean up any ongoing operations
        self.conversation_history = []

    async def receive(self, text_data):
        """Handle incoming WebSocket messages."""
        try:
            data = json.loads(text_data)
            message_type = data.get('type', 'chat')

            if message_type == 'chat':
                await self.handle_chat_message(data)
            elif message_type == 'clear_history':
                await self.handle_clear_history()
            else:
                await self.send_error(f"Unknown message type: {message_type}")

        except json.JSONDecodeError:
            await self.send_error("Invalid JSON received")
        except Exception as e:
            logger.error(f"Error processing WebSocket message: {e}", exc_info=True)
            await self.send_error("Internal server error")

    async def handle_chat_message(self, data):
        """Handle chat message with streaming response."""
        message = data.get('message', '').strip()

        if not message:
            await self.send_error("Message cannot be empty")
            return

        if self.is_generating:
            await self.send_error("Please wait for the current response to complete")
            return

        # Add user message to history
        self.conversation_history.append({'role': 'user', 'content': message})

        # Keep only last 20 messages to prevent memory issues
        if len(self.conversation_history) > 20:
            self.conversation_history = self.conversation_history[-20:]

        # Set generating flag
        self.is_generating = True

        try:
            # Start streaming response
            await self.stream_ai_response(message)

        except Exception as e:
            logger.error(f"Error generating AI response: {e}", exc_info=True)
            await self.send_error("Failed to generate AI response")
            # Ensure flag is reset on error
            self.is_generating = False
        finally:
            self.is_generating = False

    async def stream_ai_response(self, message: str):
        """Stream AI response in real-time."""
        logger.info(f"Starting streaming response for message: {message[:50]}...")

        try:
            # Generate response with streaming
            response_text = await self.generate_streaming_response(message)
            # If the response indicates the backend is busy or invalid, send an error
            if not response_text:
                logger.warning("Empty response from AI assistant")
                await self.send_error("Empty response from AI assistant")
                return

            lower = response_text.lower()
            if 'busy' in lower and ('processing' in lower or 'try again' in lower or 'currently' in lower):
                logger.warning(f"Received busy response from backend: {response_text}")
                await self.send_error("AI model is busy. Please try again in a moment.")
                return

            # Simulate streaming by breaking response into chunks
            await self.simulate_streaming_response(response_text)

            # Add complete response to history
            self.conversation_history.append({'role': 'assistant', 'content': response_text})

            # Send completion signal
            await self.send(text_data=json.dumps({
                'type': 'response_complete',
                'full_response': response_text
            }))

        except asyncio.CancelledError:
            # Client disconnected or task was cancelled; stop generation quietly
            logger.info("Streaming response cancelled (likely client disconnect)")
            self.is_generating = False
        except Exception as e:
            logger.error(f"Streaming response failed: {e}", exc_info=True)
            await self.send_error("Response generation failed")
            # Reset generating flag on error
            self.is_generating = False

    async def simulate_streaming_response(self, full_response: str):
        """Simulate streaming by sending response in chunks."""
        words = full_response.split()
        current_chunk = ""
        chunk_size = 0

        for word in words:
            current_chunk += word + " "
            chunk_size += len(word) + 1

            # Send chunk when it reaches a reasonable size or at word boundaries
            if chunk_size >= 20:  # Send chunks of ~20 characters
                await self.send(text_data=json.dumps({
                    'type': 'stream_chunk',
                    'chunk': current_chunk
                }))
                await asyncio.sleep(0.05)  # Small delay for streaming effect
                current_chunk = ""
                chunk_size = 0

        # Send any remaining chunk
        if current_chunk.strip():
            await self.send(text_data=json.dumps({
                'type': 'stream_chunk',
                'chunk': current_chunk
            }))

    async def generate_streaming_response(self, message: str) -> str:
        """Generate AI response asynchronously for streaming."""
        try:
            if ai_assistant is None:
                logger.warning("AI assistant not initialized, using fallback")
                return "Hello! I'm the AI assistant. The full AI model isn't configured yet, but WebSocket streaming is working! How can I help you with flight bookings?"

            # For local models, they can take time, so let's be more patient
            # Don't use timeout wrapper, let the model run as long as it needs
            try:
                logger.info("Starting AI response generation (no timeout)")
                response = await ai_assistant.generate_response_async(message, self.conversation_history[:-1])
                logger.info("AI response generation completed successfully")
                return response
            except Exception as e:
                logger.error(f"AI response generation failed: {e}")
                # The model failed, return a helpful message
                return "Hello! I'm the AI assistant. There was an issue with the AI model, but WebSocket streaming is working perfectly! How can I help you with flight bookings?"

        except Exception as e:
            logger.error(f"AI generation failed: {e}", exc_info=True)
            # Return a fallback response instead of crashing
            return "Hello! I'm the AI assistant. There was an issue processing your request, but WebSocket streaming is working! How can I help you with flight bookings?"

    async def handle_clear_history(self):
        """Clear conversation history."""
        self.conversation_history = []
        await self.send(text_data=json.dumps({
            'type': 'history_cleared',
            'message': 'Conversation history cleared'
        }))

    async def send_error(self, message: str):
        """Send error message to client."""
        await self.send(text_data=json.dumps({
            'type': 'error',
            'message': message
        }))

    async def send_stream_chunk(self, chunk: str):
        """Send a chunk of the streaming response."""
        await self.send(text_data=json.dumps({
            'type': 'stream_chunk',
            'chunk': chunk
        }))

    # For future enhancement: implement actual streaming from AI model
    async def generate_streaming_response_async(self, message: str) -> str:
        """Placeholder for future streaming implementation."""
        # This would be replaced with actual streaming from the AI model
        # For now, we'll simulate streaming by yielding chunks

        full_response = await self.generate_streaming_response(message)

        # Simulate streaming by sending chunks
        words = full_response.split()
        current_chunk = ""

        for word in words:
            current_chunk += word + " "
            if len(current_chunk) >= 50:  # Send chunks of ~50 characters
                await self.send_stream_chunk(current_chunk)
                await asyncio.sleep(0.1)  # Small delay for streaming effect
                current_chunk = ""

        if current_chunk:
            await self.send_stream_chunk(current_chunk)

        return full_response