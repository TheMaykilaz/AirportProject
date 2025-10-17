import logging
import time
from typing import Any, Dict, List, Optional

import requests

from .config import ModelBackend, ModelConfig
from .backends import load_model
from .prompts import PromptBuilder
from .context import generate_basic_context, generate_db_context


logger = logging.getLogger(__name__)


class LlamaAIAssistant:
    FALLBACK_RESPONSE = (
        "Sorry, there are technical issues with AI right now. Please try again in a few minutes, "
        "or use the flight search on the website."
    )

    def __init__(self):
        logger.info("Initializing LlamaAIAssistant")
        self.config = ModelConfig.from_settings()
        self.model = None
        self.backend = ModelBackend.FALLBACK
        self._load_model()

    def _load_model(self):
        logger.info("Starting model loading process")
        self.model, self.backend = load_model(self.config)
        logger.info(f"Model initialization complete. Backend: {self.backend.value}")

    def generate_response(self, message: str, conversation_history: Optional[List[Dict]] = None, user: Optional[Any] = None) -> str:
        conversation_history = conversation_history or []
        logger.info(f"Generating response for message (length: {len(message)})")

        flight_context = generate_basic_context(message)
        # Enrich with DB context (safe ORM-only)
        db_context = generate_db_context(message, user)
        if db_context:
            flight_context = (flight_context + "\n" + db_context).strip()

        prompt = PromptBuilder.build_prompt(message, conversation_history, flight_context)

        try:
            if self.backend in (ModelBackend.LLAMA_CPP, ModelBackend.CTRANSFORMERS):
                return self._generate_local_response(prompt)
            if self.backend == ModelBackend.API:
                return self._generate_api_response(prompt)
            logger.warning("No model backend available, using fallback")
            return self._get_fallback_response()
        except Exception as e:
            logger.error(f"Response generation failed: {e}", exc_info=True)
            return self._get_fallback_response()

    def _generate_local_response(self, prompt: str) -> str:
        if self.model is None:
            logger.error("Attempted to generate response with unloaded model")
            raise RuntimeError("Model not loaded")

        params = {
            'max_tokens': self.config.max_tokens if self.backend == ModelBackend.LLAMA_CPP else None,
            'max_new_tokens': None if self.backend == ModelBackend.LLAMA_CPP else self.config.max_tokens,
            'temperature': self.config.temperature,
            'top_p': self.config.top_p,
            'top_k': self.config.top_k,
            'stop': ["</s>"],
        }

        start = time.time()
        if self.backend == ModelBackend.LLAMA_CPP:
            response = self.model.create_completion(
                prompt,
                max_tokens=params['max_tokens'],
                temperature=params['temperature'],
                top_p=params['top_p'],
                top_k=params['top_k'],
                stop=params['stop'],
                repeat_penalty=self.config.repetition_penalty,
                echo=False,
            )
            result = response['choices'][0]['text'].strip()
        else:
            response = self.model(
                prompt,
                max_new_tokens=params['max_new_tokens'],
                temperature=params['temperature'],
                top_p=params['top_p'],
                top_k=params['top_k'],
                stop=params['stop'],
                repetition_penalty=self.config.repetition_penalty,
            )
            result = response.strip()
        logger.info(f"Local model response generated in {time.time()-start:.2f}s")
        return result

    def _generate_api_response(self, prompt: str) -> str:
        headers = {'Content-Type': 'application/json'}
        if self.config.api_key:
            headers['Authorization'] = f'Bearer {self.config.api_key}'
        payload = {
            'inputs': prompt,
            'parameters': {
                'max_new_tokens': self.config.max_tokens,
                'temperature': self.config.temperature,
                'do_sample': True,
                'return_full_text': False,
            }
        }
        start = time.time()
        r = requests.post(self.config.api_base, headers=headers, json=payload, timeout=30)
        r.raise_for_status()
        data = r.json()
        text = data[0]['generated_text'].strip()
        logger.info(f"API response received in {time.time()-start:.2f}s")
        return text

    def _get_fallback_response(self) -> str:
        return self.FALLBACK_RESPONSE


