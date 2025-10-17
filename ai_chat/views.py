import json
import logging
from typing import Dict, Any, Optional

from django.shortcuts import render
from django.http import JsonResponse, HttpRequest, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods, require_GET, require_POST
from django.conf import settings
from django.core.exceptions import ValidationError

from .services import ai_assistant


logger = logging.getLogger(__name__)


def parse_json_body(request: HttpRequest) -> Dict[str, Any]:
    try:
        if not request.body:
            raise ValidationError("Request body is empty")
        return json.loads(request.body)
    except json.JSONDecodeError as e:
        logger.warning(f"Invalid JSON in request: {e}")
        raise ValidationError("Invalid JSON data")


def error_response(message: str, status: int = 400) -> JsonResponse:
    logger.debug(f"Returning error response: {message} (status={status})")
    return JsonResponse({'error': message, 'status': 'error'}, status=status)


def success_response(data: Dict[str, Any], status: int = 200) -> JsonResponse:
    response_data = {'status': 'success', **data}
    return JsonResponse(response_data, status=status)


@require_GET
def ai_chat_window(request: HttpRequest) -> HttpResponse:
    logger.debug(f"Rendering chat window for user: {request.user}")
    
    context = {
        'title': 'AI Assistant Chat',
        'user': request.user,
    }
    return render(request, 'ai_chat/chat_window.html', context)


@require_GET
def ai_chat_settings(request: HttpRequest) -> HttpResponse:
    logger.debug("Rendering chat settings page")
    
    context = {
        'model_name': getattr(settings, 'LLAMA_MODEL_NAME', 'Not configured'),
        'api_base': getattr(settings, 'LLAMA_API_BASE', 'Not configured'),
        'max_tokens': getattr(settings, 'LLAMA_MAX_TOKENS', 512),
        'temperature': getattr(settings, 'LLAMA_TEMPERATURE', 0.7),
        'backend': getattr(ai_assistant, 'backend', 'Unknown'),
    }
    return render(request, 'ai_chat/settings.html', context)

@csrf_exempt
@require_POST
def ai_chat_api(request: HttpRequest) -> JsonResponse:
    try:
        # Parse request data
        data = parse_json_body(request)
        message = data.get('message', '').strip()
        conversation_history = data.get('conversation_history', [])
        
        # Validate input
        if not message:
            logger.warning("Empty message received in chat API")
            return error_response('Message is required', status=400)
        
        if len(message) > 5000:
            logger.warning(f"Message too long: {len(message)} characters")
            return error_response('Message too long (max 5000 characters)', status=400)
        
        # Validate conversation history
        if not isinstance(conversation_history, list):
            logger.warning("Invalid conversation_history type")
            return error_response('conversation_history must be a list', status=400)
        
        # Log request
        logger.info(f"Processing chat message (length: {len(message)}, history: {len(conversation_history)})")
        
        # Generate AI response
        response = ai_assistant.generate_response(message, conversation_history, request.user)
        
        logger.info("Chat response generated successfully")
        return success_response({'response': response})
        
    except ValidationError as e:
        return error_response(str(e), status=400)
    except Exception as e:
        logger.error(f"Unexpected error in chat API: {e}", exc_info=True)
        return error_response('Internal server error', status=500)


@csrf_exempt
@require_POST
def ai_chat_completion(request: HttpRequest) -> JsonResponse:
    try:
        # Parse request data
        data = parse_json_body(request)
        messages = data.get('messages', [])
        
        # Validate input
        if not messages:
            logger.warning("Empty messages array in completion API")
            return error_response('Messages are required', status=400)
        
        if not isinstance(messages, list):
            logger.warning("Invalid messages type in completion API")
            return error_response('Messages must be a list', status=400)
        
        # Validate message format
        for idx, msg in enumerate(messages):
            if not isinstance(msg, dict):
                return error_response(f'Message at index {idx} must be a dict', status=400)
            if 'role' not in msg or 'content' not in msg:
                return error_response(f'Message at index {idx} missing role or content', status=400)
            if msg['role'] not in ['user', 'assistant', 'system']:
                return error_response(f'Invalid role at index {idx}: {msg["role"]}', status=400)
        
        # Log request
        logger.info(f"Processing chat completion with {len(messages)} messages")
        
        # Generate chat completion response
        response = ai_assistant.chat_completion(messages)
        
        logger.info("Chat completion generated successfully")
        return JsonResponse(response)
        
    except ValidationError as e:
        return error_response(str(e), status=400)
    except Exception as e:
        logger.error(f"Unexpected error in completion API: {e}", exc_info=True)
        return error_response('Internal server error', status=500)


@csrf_exempt
@require_GET
def health_check(request: HttpRequest) -> JsonResponse:
    logger.debug("Health check requested")
    
    try:
        # Get model info
        model_name = getattr(settings, 'LLAMA_MODEL_NAME', 'Unknown')
        backend = getattr(ai_assistant, 'backend', None)
        
        # Test basic functionality
        logger.debug("Running health check test query")
        test_response = ai_assistant.generate_response("Hello")
        
        if not test_response:
            raise ValueError("AI assistant returned empty response")
        
        logger.info("Health check passed")
        return JsonResponse({
            'status': 'healthy',
            'message': 'AI assistant is working',
            'model': model_name,
            'backend': backend.value if backend else 'unknown',
            'test_response_length': len(test_response)
        }, status=200)
        
    except Exception as e:
        logger.error(f"Health check failed: {e}", exc_info=True)
        return JsonResponse({
            'status': 'unhealthy',
            'error': str(e),
            'model': getattr(settings, 'LLAMA_MODEL_NAME', 'Unknown')
        }, status=503)


@csrf_exempt
@require_GET
def ai_model_info(request: HttpRequest) -> JsonResponse:
    logger.debug("Model info requested")
    
    try:
        config = {
            'model_name': getattr(settings, 'LLAMA_MODEL_NAME', 'Not configured'),
            'model_path': getattr(settings, 'LLAMA_MODEL_PATH', 'Not configured'),
            'api_base': getattr(settings, 'LLAMA_API_BASE', 'Not configured'),
            'max_tokens': getattr(settings, 'LLAMA_MAX_TOKENS', 512),
            'temperature': getattr(settings, 'LLAMA_TEMPERATURE', 0.7),
            'backend': getattr(ai_assistant, 'backend', None),
            'is_loaded': ai_assistant.model is not None,
        }
        
        # Don't expose API key
        if hasattr(ai_assistant, 'config') and ai_assistant.config.api_key:
            config['api_key_configured'] = True
        
        if config['backend']:
            config['backend'] = config['backend'].value
        
        return JsonResponse(config)
        
    except Exception as e:
        logger.error(f"Error retrieving model info: {e}", exc_info=True)
        return error_response('Failed to retrieve model info', status=500)


@csrf_exempt
@require_POST
def ai_clear_cache(request: HttpRequest) -> JsonResponse:
    logger.info("Cache clear requested")
    
    try:
        # Add cache clearing logic here if needed
        # For example: cache.clear()
        
        return success_response({
            'message': 'Cache cleared successfully'
        })
        
    except Exception as e:
        logger.error(f"Error clearing cache: {e}", exc_info=True)
        return error_response('Failed to clear cache', status=500)