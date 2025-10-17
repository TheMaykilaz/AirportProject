import os
from dataclasses import dataclass
from enum import Enum
from django.conf import settings


class ModelBackend(Enum):
    LLAMA_CPP = "llama-cpp-python"
    CTRANSFORMERS = "ctransformers"
    API = "api"
    FALLBACK = "fallback"


@dataclass
class ModelConfig:
    model_name: str
    model_path: str | None
    api_base: str
    api_key: str | None
    max_tokens: int
    temperature: float
    context_length: int
    threads: int
    top_k: int
    top_p: float
    repetition_penalty: float

    @classmethod
    def from_settings(cls) -> "ModelConfig":
        return cls(
            model_name=getattr(settings, 'LLAMA_MODEL_NAME', 'llama-2-7b-chat'),
            model_path=getattr(settings, 'LLAMA_MODEL_PATH', None),
            api_base=getattr(settings, 'LLAMA_API_BASE', 'http://localhost:8000'),
            api_key=getattr(settings, 'LLAMA_API_KEY', None),
            max_tokens=getattr(settings, 'LLAMA_MAX_TOKENS', 160),
            temperature=getattr(settings, 'LLAMA_TEMPERATURE', 0.6),
            context_length=getattr(settings, 'LLAMA_CONTEXT_LENGTH', 1024),
            threads=getattr(settings, 'LLAMA_THREADS', max(1, (os.cpu_count() or 2) - 1)),
            top_k=getattr(settings, 'LLAMA_TOP_K', 20),
            top_p=getattr(settings, 'LLAMA_TOP_P', 0.7),
            repetition_penalty=getattr(settings, 'LLAMA_REPETITION_PENALTY', 1.15),
        )


