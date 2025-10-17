import logging
import os
from typing import Tuple, Any

from .config import ModelConfig, ModelBackend


logger = logging.getLogger(__name__)


def load_llama_cpp(config: ModelConfig) -> Tuple[Any, ModelBackend]:
    from llama_cpp import Llama
    if not config.model_path or not os.path.exists(config.model_path):
        raise FileNotFoundError(f"Model path not found: {config.model_path}")

    logger.info(f"Loading model with llama-cpp-python: {config.model_path}")
    model = Llama(
        model_path=config.model_path,
        n_ctx=config.context_length,
        n_threads=config.threads,
        n_batch=16,
        verbose=False,
        logits_all=False,
        embedding=False,
    )
    return model, ModelBackend.LLAMA_CPP


def load_ctransformers(config: ModelConfig) -> Tuple[Any, ModelBackend]:
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
        max_new_tokens=config.max_tokens,
    )
    return model, ModelBackend.CTRANSFORMERS


def load_model(config: ModelConfig) -> Tuple[Any, ModelBackend]:
    try:
        if config.model_path and os.path.exists(config.model_path):
            for loader in (load_llama_cpp, load_ctransformers):
                try:
                    return loader(config)
                except Exception:
                    logger.debug(f"Loader {loader.__name__} failed, trying next option")
                    continue
            if config.api_base:
                logger.warning("Local model loading failed, switching to API backend")
                return None, ModelBackend.API
            logger.warning("Local model loading failed and no API configured; using fallback mode")
            return None, ModelBackend.FALLBACK

        if config.api_base:
            logger.info("No local model configured. Using API backend.")
            return None, ModelBackend.API

        logger.warning("No model path or API configured; using fallback mode")
        return None, ModelBackend.FALLBACK
    except Exception:
        logger.error("Unexpected error during model selection", exc_info=True)
        return None, ModelBackend.FALLBACK


