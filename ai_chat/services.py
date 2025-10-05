import os
import json
import requests
from typing import Optional, Dict, Any
from django.conf import settings


class LlamaAIAssistant:
    """AI Assistant service using Llama model for chat functionality."""

    def __init__(self):
        self.model_name = getattr(settings, 'LLAMA_MODEL_NAME', 'llama-2-7b-chat')
        self.api_base = getattr(settings, 'LLAMA_API_BASE', 'http://localhost:8000')
        self.api_key = getattr(settings, 'LLAMA_API_KEY', None)
        self.max_tokens = getattr(settings, 'LLAMA_MAX_TOKENS', 512)
        self.temperature = getattr(settings, 'LLAMA_TEMPERATURE', 0.7)

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

        # Prepare the prompt with conversation history
        prompt = self._build_prompt(message, conversation_history)

        try:
            # Try using llama-cpp-python local model first
            return self._generate_local_response(prompt)
        except Exception as e:
            print(f"Local model failed: {e}")
            try:
                # Fallback to API-based generation
                return self._generate_api_response(prompt)
            except Exception as api_error:
                print(f"API model failed: {api_error}")
                return "I'm sorry, I'm having trouble connecting to the AI model right now. Please try again later."

    def _build_prompt(self, message: str, conversation_history: list) -> str:
        """Build the prompt with conversation history."""
        if not conversation_history:
            return f"<s>[INST] {message} [/INST]"

        # Add conversation history to the prompt
        prompt = ""
        for msg in conversation_history[-5:]:  # Keep last 5 messages for context
            if msg['role'] == 'user':
                prompt += f"<s>[INST] {msg['content']} [/INST]"
            else:
                prompt += f" {msg['content']} </s>"

        # Add current message
        prompt += f"<s>[INST] {message} [/INST]"
        return prompt

    def _generate_local_response(self, prompt: str) -> str:
        """Generate response using local llama-cpp-python model."""
        try:
            from llama_cpp import Llama

            # Path to the model file
            model_path = getattr(settings, 'LLAMA_MODEL_PATH', None)
            if not model_path or not os.path.exists(model_path):
                raise FileNotFoundError("Model file not found")

            # Initialize the Llama model
            llm = Llama(
                model_path=model_path,
                n_ctx=2048,
                n_threads=4,
                verbose=False
            )

            # Generate response
            response = llm(
                prompt,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                stop=["</s>", "[INST]"],
                echo=False
            )

            return response['choices'][0]['text'].strip()

        except ImportError:
            raise Exception("llama-cpp-python not installed")
        except Exception as e:
            raise Exception(f"Local model error: {str(e)}")

    def _generate_api_response(self, prompt: str) -> str:
        """Generate response using API-based Llama model."""
        headers = {
            'Content-Type': 'application/json',
        }

        if self.api_key:
            headers['Authorization'] = f'Bearer {self.api_key}'

        payload = {
            'model': self.model_name,
            'prompt': prompt,
            'max_tokens': self.max_tokens,
            'temperature': self.temperature,
            'stream': False
        }

        try:
            response = requests.post(
                f"{self.api_base}/v1/completions",
                headers=headers,
                json=payload,
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['text'].strip()
            else:
                raise Exception(f"API request failed with status {response.status_code}")

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
        prompt = ""
        for message in messages:
            role = message['role']
            content = message['content']

            if role == 'system':
                prompt += f"<s>[INST] <<SYS>>\n{content}\n<</SYS>>\n\n"
            elif role == 'user':
                prompt += f"{content} [/INST]"
            elif role == 'assistant':
                prompt += f" {content} </s>"

        return prompt


# Global instance
ai_assistant = LlamaAIAssistant()