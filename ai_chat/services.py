import os
import re
import time
import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum

import requests
from django.conf import settings
from django.core.cache import cache


# Configure logger
logger = logging.getLogger(__name__)


class ModelBackend(Enum):
    """Supported model backends."""
    LLAMA_CPP = "llama-cpp-python"
    CTRANSFORMERS = "ctransformers"
    API = "api"
    FALLBACK = "fallback"


@dataclass
class ModelConfig:
    """Configuration for Llama model."""
    model_name: str
    model_path: Optional[str]
    api_base: str
    api_key: Optional[str]
    max_tokens: int
    temperature: float
    context_length: int
    threads: int
    
    @classmethod
    def from_settings(cls):
        """Load configuration from Django settings."""
        return cls(
            model_name=getattr(settings, 'LLAMA_MODEL_NAME', 'llama-2-7b-chat'),
            model_path=getattr(settings, 'LLAMA_MODEL_PATH', None),
            api_base=getattr(settings, 'LLAMA_API_BASE', 'http://localhost:8000'),
            api_key=getattr(settings, 'LLAMA_API_KEY', None),
            max_tokens=getattr(settings, 'LLAMA_MAX_TOKENS', 128),
            temperature=getattr(settings, 'LLAMA_TEMPERATURE', 0.3),
            context_length=getattr(settings, 'LLAMA_CONTEXT_LENGTH', 1024),
            threads=getattr(settings, 'LLAMA_THREADS', max(1, (os.cpu_count() or 2) - 1))
        )


class ModelLoader:
    """Handles loading of different model backends."""
    
    @staticmethod
    def load_llama_cpp(config: ModelConfig):
        """Load model using llama-cpp-python."""
        try:
            from llama_cpp import Llama
            
            if not config.model_path or not os.path.exists(config.model_path):
                raise FileNotFoundError(f"Model path not found: {config.model_path}")
            
            logger.info(f"Loading model with llama-cpp-python: {config.model_path}")
            model = Llama(
                model_path=config.model_path,
                n_ctx=config.context_length,
                n_threads=config.threads,
                n_batch=1,
                verbose=False,
                logits_all=False,
                embedding=False,
            )
            logger.info("Model loaded successfully with llama-cpp-python")
            return model, ModelBackend.LLAMA_CPP
            
        except ImportError:
            logger.debug("llama-cpp-python not available")
            raise
        except Exception as e:
            logger.error(f"Failed to load model with llama-cpp-python: {e}", exc_info=True)
            raise
    
    @staticmethod
    def load_ctransformers(config: ModelConfig):
        """Load model using ctransformers."""
        try:
            from ctransformers import AutoModelForCausalLM
            
            if not config.model_path or not os.path.exists(config.model_path):
                raise FileNotFoundError(f"Model path not found: {config.model_path}")
            
            logger.info(f"Loading model with ctransformers: {config.model_path}")
            model = AutoModelForCausalLM.from_pretrained(
                config.model_path,
                model_type="llama",
                gpu_layers=0,
                context_length=config.context_length,
                threads=config.threads,
                batch_size=1,
                max_new_tokens=config.max_tokens
            )
            logger.info("Model loaded successfully with ctransformers")
            return model, ModelBackend.CTRANSFORMERS
            
        except ImportError:
            logger.debug("ctransformers not available")
            raise
        except Exception as e:
            logger.error(f"Failed to load model with ctransformers: {e}", exc_info=True)
            raise
    
    @staticmethod
    def load_model(config: ModelConfig):
        """Select appropriate backend based on configuration."""
        try:
            # Prefer local model only if a valid path is configured
            if config.model_path and os.path.exists(config.model_path):
                loaders = [
                    ModelLoader.load_llama_cpp,
                    ModelLoader.load_ctransformers,
                ]
                for loader in loaders:
                    try:
                        return loader(config)
                    except Exception:
                        logger.debug(f"Loader {loader.__name__} failed, trying next option")
                        continue
                # If local attempts fail, fall back to API if available
                if config.api_base:
                    logger.warning("Local model loading failed, switching to API backend")
                    return None, ModelBackend.API
                logger.warning("Local model loading failed and no API configured; using fallback mode")
                return None, ModelBackend.FALLBACK

            # No local model configured, use API if available
            if config.api_base:
                logger.info("No local model configured. Using API backend.")
                return None, ModelBackend.API

            # Nothing configured, use fallback
            logger.warning("No model path or API configured; using fallback mode")
            return None, ModelBackend.FALLBACK
        except Exception:
            logger.error("Unexpected error during model selection", exc_info=True)
            return None, ModelBackend.FALLBACK


class PromptBuilder:
    """Builds prompts for Llama model."""
    
    SYSTEM_PROMPT = """You are AirplaneDJ AI assistant for flight bookings.

CAPABILITIES:
- Help with flight bookings and information
- Provide flight details and prices
- Answer questions about flights, airlines, and travel

{context}

For booking, you need: name, passport, dates, airports, class, number of passengers."""
    
    @classmethod
    def build_system_prompt(cls, context: str) -> str:
        """Build system prompt with context."""
        return cls.SYSTEM_PROMPT.format(context=context)
    
    @classmethod
    def build_prompt(cls, message: str, conversation_history: List[Dict], 
                    flight_context: str = "") -> str:
        """Build complete prompt with conversation history."""
        system_prompt = cls.build_system_prompt(flight_context)
        
        logger.debug(f"Building prompt for message (length: {len(message)})")
        
        # No conversation history - simple prompt
        if not conversation_history:
            return f"<s>[INST] <<SYS>>\n{system_prompt}\n<</SYS>>\n\n{message} [/INST]"
        
        # Build prompt with conversation history (last 5 messages)
        prompt = f"<s>[INST] <<SYS>>\n{system_prompt}\n<</SYS>>\n\n"
        
        for msg in conversation_history[-5:]:
            role = msg.get('role', 'user')
            content = msg.get('content', '')
            
            if role == 'user':
                prompt += f"{content} [/INST]"
            else:
                prompt += f" {content} </s><s>[INST] "
        
        prompt += f"{message} [/INST]"
        logger.debug(f"Prompt built with {len(conversation_history)} history messages")
        return prompt


class FlightContextGenerator:
    """Generates flight context from user messages."""
    
    BOOKING_KEYWORDS = [
        'book', 'booking', 'reserve', 'ticket', 'buy', 'purchase'
    ]
    
    LOCATION_CONTEXTS = {
        'ukraine': "Ukraine flights: Kyiv Boryspil (KBP), Lviv (LWO). Airlines: Ukraine International, SkyUp.",
        'usa': "USA flights: JFK, LAX, ORD. Airlines: Delta, United, American.",
        'america': "USA flights: JFK, LAX, ORD. Airlines: Delta, United, American.",
        'europe': "Europe flights: LHR, CDG, FRA. Airlines: Lufthansa, British Airways, Air France.",
        'asia': "Asia flights: NRT, HKG, SIN. Airlines: ANA, Cathay Pacific, Singapore Airlines.",
    }
    
    @classmethod
    def generate(cls, message: str) -> str:
        """Generate flight context from message."""
        # Sanitize and normalize message
        clean_message = re.sub(r'[^a-zA-Z0-9\s\-]', '', message.lower())[:50].strip()
        
        if not clean_message or len(clean_message) < 2:
            logger.debug("Message too short or empty for context generation")
            return ""
        
        context_parts = []
        
        # Check for booking intent
        if any(keyword in clean_message for keyword in cls.BOOKING_KEYWORDS):
            context_parts.append("BOOKING: Need name, passport, dates, airports, class, passengers.")
            logger.debug("Booking intent detected")
        
        # Add location-specific context
        for keyword, context in cls.LOCATION_CONTEXTS.items():
            if keyword in clean_message:
                context_parts.append(context)
                logger.debug(f"Location context added: {keyword}")
                break  # Only add one location context
        
        generated_context = "\n".join(context_parts)[:300]
        logger.debug(f"Generated context length: {len(generated_context)}")
        return generated_context


class LlamaAIAssistant:
    """Main AI assistant for flight booking system."""
    
    FALLBACK_RESPONSE = "Sorry, there are technical issues with AI right now. Please try again in a few minutes, or use the flight search on the website."
    
    def __init__(self):
        """Initialize the AI assistant."""
        logger.info("Initializing LlamaAIAssistant")
        self.config = ModelConfig.from_settings()
        logger.debug(f"Config loaded: model={self.config.model_name}, backend={self.config.api_base}")
        self.model = None
        self.backend = ModelBackend.FALLBACK
        self._load_model()
    
    def _load_model(self):
        """Load the AI model at startup."""
        logger.info("Starting model loading process")
        self.model, self.backend = ModelLoader.load_model(self.config)
        logger.info(f"Model initialization complete. Backend: {self.backend.value}")
    
    def generate_response(self, message: str, conversation_history: Optional[List[Dict]] = None, user: Optional[Any] = None) -> str:
        """Generate AI response to user message."""
        conversation_history = conversation_history or []
        
        logger.info(f"Generating response for message (length: {len(message)})")
        logger.debug(f"Conversation history: {len(conversation_history)} messages")
        
        # Generate flight context
        flight_context = FlightContextGenerator.generate(message)

        # Safely enrich context with database facts (no raw SQL; ORM only)
        try:
            db_context_parts: List[str] = []
            # Lazy import to avoid circular imports at module load
            from django.utils import timezone as _tz
            from airport.models import Airport, Flight
            from bookings.models import Order

            # Add top 3 airports matching tokens in the message
            tokens = [t for t in re.findall(r"[a-zA-Z]{2,}", message or "")][:5]
            if tokens:
                airport_q = Airport.objects.all()
                # Filter by code or city/name contains any token
                from django.db.models import Q
                q = Q()
                for t in tokens:
                    q |= Q(code__iexact=t) | Q(city__icontains=t) | Q(name__icontains=t)
                airports = list(airport_q.filter(q).select_related("country").order_by("name")[:3])
                if airports:
                    db_context_parts.append("Known airports:")
                    for ap in airports:
                        db_context_parts.append(f"- {ap.name} ({ap.code}) in {ap.city}, {ap.country.code}")

            # Add next 3 upcoming flights between hinted airports if both codes detected
            codes = [t.upper() for t in tokens if len(t) in (3,)]
            if len(codes) >= 2:
                dep_code, arr_code = codes[0], codes[1]
                now = _tz.now()
                upcoming = (
                    Flight.objects.select_related("airline", "departure_airport", "arrival_airport")
                    .filter(
                        departure_airport__code__iexact=dep_code,
                        arrival_airport__code__iexact=arr_code,
                        departure_time__gte=now,
                    )
                    .order_by("departure_time")[:3]
                )
                upcoming = list(upcoming)
                if upcoming:
                    db_context_parts.append("Upcoming flights:")
                    for f in upcoming:
                        db_context_parts.append(
                            f"- {f.airline.code} {f.flight_number} {f.departure_airport.code}->{f.arrival_airport.code} at {f.departure_time:%Y-%m-%d %H:%M}"
                        )

            # If authenticated user, add last order summary (no sensitive PII)
            if user and getattr(user, 'is_authenticated', False):
                last_order = (
                    Order.objects.select_related("flight__airline", "flight__departure_airport", "flight__arrival_airport")
                    .filter(user=user)
                    .order_by("-created_at")
                    .first()
                )
                if last_order and getattr(last_order, 'flight', None):
                    f = last_order.flight
                    db_context_parts.append(
                        f"Your last booking: {f.airline.code} {f.flight_number} {f.departure_airport.code}->{f.arrival_airport.code} on {f.departure_date} (status: {last_order.get_status_display()})."
                    )

            if db_context_parts:
                flight_context = (flight_context + "\n" + "\n".join(db_context_parts)).strip()
        except Exception as _e:
            logger.debug(f"DB context enrichment skipped due to error: {_e}")
        
        # Build prompt
        prompt = PromptBuilder.build_prompt(message, conversation_history, flight_context)
        
        # Generate response
        try:
            if self.backend in (ModelBackend.LLAMA_CPP, ModelBackend.CTRANSFORMERS):
                logger.debug(f"Using local model backend: {self.backend.value}")
                response = self._generate_local_response(prompt)
            elif self.backend == ModelBackend.API:
                logger.debug("Using API backend")
                response = self._generate_api_response(prompt)
            else:
                logger.warning("No model backend available, using fallback")
                response = self._get_fallback_response()
            
            logger.info(f"Response generated successfully (length: {len(response)})")
            return response
                
        except Exception as e:
            logger.error(f"Response generation failed: {e}", exc_info=True)
            return self._get_fallback_response()
    
    def _generate_local_response(self, prompt: str) -> str:
        """Generate response using local model."""
        if self.model is None:
            logger.error("Attempted to generate response with unloaded model")
            raise RuntimeError("Model not loaded")
        
        generation_params = {
            'max_tokens': self.config.max_tokens if self.backend == ModelBackend.LLAMA_CPP else None,
            'max_new_tokens': None if self.backend == ModelBackend.LLAMA_CPP else self.config.max_tokens,
            'temperature': self.config.temperature,
            'top_p': 0.8,
            'top_k': 30,
            # Keep stop list minimal to avoid premature truncation
            'stop': ["</s>"],
        }
        
        logger.debug(f"Generation parameters: {generation_params}")
        
        try:
            start_time = time.time()
            
            if self.backend == ModelBackend.LLAMA_CPP:
                logger.debug("Calling llama-cpp-python model")
                response = self.model.create_completion(
                    prompt,
                    max_tokens=generation_params['max_tokens'],
                    temperature=generation_params['temperature'],
                    top_p=generation_params['top_p'],
                    top_k=generation_params['top_k'],
                    stop=generation_params['stop'],
                    repeat_penalty=1.2,
                    echo=False
                )
                result = response['choices'][0]['text'].strip()
            
            else:  # CTRANSFORMERS
                logger.debug("Calling ctransformers model")
                response = self.model(
                    prompt,
                    max_new_tokens=generation_params['max_new_tokens'],
                    temperature=generation_params['temperature'],
                    top_p=generation_params['top_p'],
                    top_k=generation_params['top_k'],
                    stop=generation_params['stop'],
                    repetition_penalty=1.15
                )
                result = response.strip()
            
            elapsed_time = time.time() - start_time
            logger.info(f"Local model response generated in {elapsed_time:.2f}s")
            return result
                
        except Exception as e:
            logger.error(f"Local model generation error: {e}", exc_info=True)
            raise RuntimeError(f"Local model error: {e}")
    
    def _generate_api_response(self, prompt: str) -> str:
        """Generate response using API."""
        headers = {'Content-Type': 'application/json'}
        
        if self.config.api_key:
            headers['Authorization'] = f'Bearer {self.config.api_key}'
            logger.debug("API key configured")
        
        payload = {
            'inputs': prompt,
            'parameters': {
                'max_new_tokens': self.config.max_tokens,
                'temperature': self.config.temperature,
                'do_sample': True,
                'return_full_text': False
            }
        }
        
        logger.debug(f"Sending API request to {self.config.api_base}")
        
        try:
            start_time = time.time()
            
            response = requests.post(
                self.config.api_base,
                headers=headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            generated_text = result[0]['generated_text'].strip()
            
            elapsed_time = time.time() - start_time
            logger.info(f"API response received in {elapsed_time:.2f}s")
            
            return generated_text
            
        except requests.exceptions.Timeout:
            logger.error("API request timed out after 30s")
            raise RuntimeError("API request timeout")
        except requests.exceptions.HTTPError as e:
            logger.error(f"API HTTP error {response.status_code}: {response.text}")
            raise RuntimeError(f"API HTTP error: {e}")
        except requests.exceptions.RequestException as e:
            logger.error(f"API request error: {e}", exc_info=True)
            raise RuntimeError(f"API request error: {e}")
    
    def _get_fallback_response(self) -> str:
        """Get fallback response when model fails."""
        logger.info("Returning fallback response")
        return self.FALLBACK_RESPONSE
    
    def chat_completion(self, messages: List[Dict], **kwargs) -> Dict[str, Any]:
        """OpenAI-compatible chat completion interface."""
        logger.debug(f"Chat completion called with {len(messages)} messages")
        
        # Extract last user message
        user_message = next(
            (msg['content'] for msg in reversed(messages) if msg['role'] == 'user'),
            ""
        )
        
        if not user_message:
            logger.warning("No user message found in chat completion request")
        
        # Generate response
        response_text = self.generate_response(user_message, messages[:-1])
        
        completion_response = {
            'id': f'chatcmpl-{os.urandom(4).hex()}',
            'object': 'chat.completion',
            'created': int(time.time()),
            'model': self.config.model_name,
            'choices': [{
                'index': 0,
                'message': {
                    'role': 'assistant',
                    'content': response_text
                },
                'finish_reason': 'stop'
            }],
            'usage': {
                'prompt_tokens': len(user_message.split()),
                'completion_tokens': len(response_text.split()),
                'total_tokens': len(user_message.split()) + len(response_text.split())
            }
        }
        
        logger.debug("Chat completion response prepared")
        return completion_response


# Global singleton instance
logger.info("Creating global ai_assistant instance")
ai_assistant = LlamaAIAssistant()