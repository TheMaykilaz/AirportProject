import os
import json
import requests
from typing import Optional, Dict, Any
from django.conf import settings
from airport.models import Flight, Airport, Airline, Country
from django.db.models import Q
from django.utils import timezone


class LlamaAIAssistant:
    """AI Assistant service using Llama model for chat functionality."""

    def __init__(self):
        self.model_name = getattr(settings, 'LLAMA_MODEL_NAME', 'llama-2-7b-chat')
        self.api_base = getattr(settings, 'LLAMA_API_BASE', 'http://localhost:8000')
        self.api_key = getattr(settings, 'LLAMA_API_KEY', None)
        self.max_tokens = getattr(settings, 'LLAMA_MAX_TOKENS', 512)
        self.temperature = getattr(settings, 'LLAMA_TEMPERATURE', 0.7)
        self.model = None  # Cache the loaded model
        self._load_model_once()

    def _load_model_once(self):
        """Load the model once at startup for better performance."""
        try:
            # Try llama-cpp-python first (preferred)
            from llama_cpp import Llama
            model_path = getattr(settings, 'LLAMA_MODEL_PATH', None)

            if model_path and os.path.exists(model_path):
                print(f"Loading Llama model at startup: {model_path}")
                # Ultra-fast llama-cpp-python configuration
                self.model = Llama(
                    model_path=model_path,
                    n_ctx=512,  # Smaller context for speed
                    n_threads=2,  # Fewer threads for stability
                    n_batch=1,  # Minimal batch
                    verbose=False,  # Less output
                    logits_all=False,  # Faster
                    embedding=False,  # Not needed for chat
                    vocab_only=False
                )
                print("Model loaded successfully with llama-cpp-python!")
                self.backend = "llama-cpp-python"
                return

        except ImportError:
            print("llama-cpp-python not available, trying ctransformers...")
        except Exception as e:
            print(f"llama-cpp-python failed: {e}, trying ctransformers...")

        # Fallback to ctransformers
        try:
            from ctransformers import AutoModelForCausalLM
            model_path = getattr(settings, 'LLAMA_MODEL_PATH', None)

            if model_path and os.path.exists(model_path):
                print(f"Loading Llama model with ctransformers: {model_path}")
                self.model = AutoModelForCausalLM.from_pretrained(
                    model_path,
                    model_type="llama",
                    gpu_layers=0,
                    context_length=512,
                    threads=2,
                    batch_size=1,
                    max_new_tokens=self.max_tokens
                )
                print("Model loaded successfully with ctransformers!")
                self.backend = "ctransformers"
            else:
                print(f"Model path not found: {model_path}")

        except Exception as e:
            print(f"Failed to load model with any backend: {e}")
            self.model = None
            self.backend = None

    def generate_response(self, message: str, conversation_history: list = None) -> str:
        """
        Generate a response from the Llama model.

        Args:
            message (str): The user's message
            conversation_history (list): Previous conversation messages

        Returns:
            str: AI assistant's response
        """
        if conversation_history is None:
            conversation_history = []

        # Get relevant flight data based on the message
        flight_context = self._get_flight_context(message)

        # Prepare the prompt with conversation history and flight data
        prompt = self._build_prompt(message, conversation_history, flight_context)

        try:
            # Try using llama-cpp-python local model first
            return self._generate_local_response(prompt)
        except Exception as e:
            print(f"Local model failed: {e}")
            # For faster response, use a simple fallback response instead of API
            return "Вибачте, зараз виникають технічні проблеми з ШІ. Спробуйте ще раз через кілька хвилин, або скористайтеся пошуком рейсів на сайті."

    def _get_flight_context(self, message: str) -> str:
        """Get relevant flight data from database based on user message for any country."""
        # Ultra-fast context generation
        import re

        # Minimal sanitization for speed
        clean_message = re.sub(r'[^a-zA-Z0-9\s\-]', '', message.lower())[:30].strip()

        if not clean_message or len(clean_message) < 2:
            return ""

        context = ""

        try:
            # Only check for booking keywords - skip complex DB queries for speed
            booking_keywords = ["book", "booking", "reserve", "ticket", "buy", "purchase", "брон", "куп"]
            if any(keyword in clean_message for keyword in booking_keywords):
                context += "\nBOOKING: Need name, passport, dates, airports, class, passengers.\n"

            # Skip DB queries for now - too slow. Use static responses for speed
            if "ukraine" in clean_message or "україна" in clean_message:
                context += "\nUkraine flights: Kyiv Boryspil (KBP), Lviv (LWO). Airlines: Ukraine International, SkyUp.\n"

            if "usa" in clean_message or "america" in clean_message:
                context += "\nUSA flights: JFK, LAX, ORD. Airlines: Delta, United, American.\n"

        except Exception as e:
            print(f"Context error: {e}")

        return context[:200]  # Very short context for speed

    def _build_prompt(self, message: str, conversation_history: list, flight_context: str = "") -> str:
        """Build ultra-fast prompt with minimal context."""
        # Detect language for fast response
        is_ukrainian = any(char in message.lower() for char in ['і', 'ї', 'є', 'ґ', 'привіт', 'дякую'])

        if is_ukrainian:
            system_prompt = f"""Ти - AI асистент системи бронювання авіаквитків AirplaneDJ.

МОЖЛИВОСТІ:
- Допомагаю з бронюванням рейсів
- Надаю інформацію про рейси та ціни
- Відповідаю українською мовою

{flight_context}

Для бронювання потрібні: ПІБ, паспорт, дати, аеропорти, клас, пасажири."""
        else:
            system_prompt = f"""You are AirplaneDJ AI assistant for flight bookings.

CAPABILITIES:
- Help with flight bookings and information
- Provide flight details and prices
- Answer in English

{flight_context}

For booking need: name, passport, dates, airports, class, passengers."""

        if not conversation_history:
            return f"<s>[INST] <<SYS>>\n{system_prompt}\n<</SYS>>\n\n{message} [/INST]"

        # Add system prompt and conversation history
        prompt = f"<s>[INST] <<SYS>>\n{system_prompt}\n<</SYS>>\n\n"
        for msg in conversation_history[-5:]:  # Keep last 5 messages for context
            if msg['role'] == 'user':
                prompt += f"{msg['content']} [/INST]"
            else:
                prompt += f" {msg['content']} </s><s>[INST]"

        # Add current message
        prompt += f"{message} [/INST]"
        return prompt

    def _generate_local_response(self, prompt: str) -> str:
        """Generate response using cached model (llama-cpp-python or ctransformers)."""
        try:
            if self.model is None:
                raise Exception("Model not loaded")

            # Check which backend we're using
            if hasattr(self.model, 'create_completion'):  # llama-cpp-python
                response = self.model.create_completion(
                    prompt,
                    max_tokens=128,
                    temperature=0.3,
                    top_p=0.8,
                    top_k=30,
                    stop=["</s>", "[INST]", "\n"],
                    repeat_penalty=1.2,
                    echo=False
                )
                return response['choices'][0]['text'].strip()
            else:  # ctransformers
                response = self.model(
                    prompt,
                    max_new_tokens=128,
                    temperature=0.3,
                    top_p=0.8,
                    top_k=30,
                    stop=["</s>", "[INST]", "\n"],
                    repetition_penalty=1.2
                )
                return response.strip()

        except Exception as e:
            raise Exception(f"Local model error: {str(e)}")

    def _generate_api_response(self, prompt: str) -> str:
        """Generate response using Hugging Face Inference API for Llama model."""
        headers = {
            'Content-Type': 'application/json',
        }

        if self.api_key:
            headers['Authorization'] = f'Bearer {self.api_key}'

        payload = {
            'inputs': prompt,
            'parameters': {
                'max_new_tokens': self.max_tokens,
                'temperature': self.temperature,
                'do_sample': True,
                'return_full_text': False
            }
        }

        try:
            response = requests.post(
                self.api_base,
                headers=headers,
                json=payload,
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                return result[0]['generated_text'].strip()
            else:
                raise Exception(f"API request failed with status {response.status_code}: {response.text}")

        except requests.exceptions.RequestException as e:
            raise Exception(f"API request error: {str(e)}")

    def chat_completion(self, messages: list, **kwargs) -> Dict[str, Any]:
        """
        Generate chat completion using OpenAI-compatible API format.

        Args:
            messages (list): List of message dictionaries with 'role' and 'content'
            **kwargs: Additional parameters

        Returns:
            dict: Response in OpenAI format
        """
        # Convert messages to prompt format for Llama
        prompt = self._convert_messages_to_prompt(messages)

        response_text = self.generate_response("", messages)

        return {
            'id': f'chatcmpl-{os.urandom(4).hex()}',
            'object': 'chat.completion',
            'created': int(os.time.time()),
            'model': self.model_name,
            'choices': [{
                'index': 0,
                'message': {
                    'role': 'assistant',
                    'content': response_text
                },
                'finish_reason': 'stop'
            }],
            'usage': {
                'prompt_tokens': len(prompt.split()),
                'completion_tokens': len(response_text.split()),
                'total_tokens': len(prompt.split()) + len(response_text.split())
            }
        }

    def _convert_messages_to_prompt(self, messages: list) -> str:
        """Convert OpenAI-style messages to Llama prompt format."""
        system_prompt = """You are an AI assistant for an airport booking system called AirplaneDJ. Your role is to help users with flight bookings, comparisons, and travel planning.

Key capabilities:
- Help users find and compare flights between destinations like USA to Ukraine
- Provide information about airlines, flight schedules, prices, and seat availability
- Assist with booking processes and payment
- Answer questions about airport services, baggage policies, and travel requirements
- Recommend the best flight options based on price, duration, layovers, and user preferences

The system supports:
- Flight search and booking
- Seat selection and reservation
- Payment processing with Stripe
- User authentication and profiles
- Email notifications for bookings

Always be helpful, accurate, and focused on travel-related assistance. If you don't have specific flight data, provide general guidance and suggest using the booking system to search for current options."""

        prompt = ""
        for message in messages:
            role = message['role']
            content = message['content']

            if role == 'system':
                prompt += f"<s>[INST] <<SYS>>\n{system_prompt}\n{content}\n<</SYS>>\n\n"
            elif role == 'user':
                prompt += f"{content} [/INST]"
            elif role == 'assistant':
                prompt += f" {content} </s>"

        return prompt


# Global instance
ai_assistant = LlamaAIAssistant()