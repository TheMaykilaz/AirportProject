import json
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.conf import settings
from .services import ai_assistant


def ai_chat_window(request):
    """Render the AI chat window interface."""
    context = {
        'title': 'AI Assistant Chat',
        'websocket_url': getattr(settings, 'AI_CHAT_WEBSOCKET_URL', None),
    }
    return render(request, 'ai_chat/chat_window.html', context)


@csrf_exempt
@require_http_methods(["POST"])
def ai_chat_api(request):
    """API endpoint for AI chat functionality."""
    try:
        data = json.loads(request.body)
        message = data.get('message', '')
        conversation_history = data.get('conversation_history', [])

        if not message:
            return JsonResponse({
                'error': 'Message is required'
            }, status=400)

        # Generate AI response
        response = ai_assistant.generate_response(message, conversation_history)

        return JsonResponse({
            'response': response,
            'status': 'success'
        })

    except json.JSONDecodeError:
        return JsonResponse({
            'error': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'error': f'Internal server error: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def ai_chat_completion(request):
    """OpenAI-compatible chat completion API endpoint."""
    try:
        data = json.loads(request.body)
        messages = data.get('messages', [])

        if not messages:
            return JsonResponse({
                'error': 'Messages are required'
            }, status=400)

        # Generate chat completion response
        response = ai_assistant.chat_completion(messages)

        return JsonResponse(response)

    except json.JSONDecodeError:
        return JsonResponse({
            'error': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'error': f'Internal server error: {str(e)}'
        }, status=500)


def ai_chat_settings(request):
    """View to display AI assistant settings and status."""
    context = {
        'model_name': getattr(settings, 'LLAMA_MODEL_NAME', 'Not configured'),
        'api_base': getattr(settings, 'LLAMA_API_BASE', 'Not configured'),
        'max_tokens': getattr(settings, 'LLAMA_MAX_TOKENS', 512),
        'temperature': getattr(settings, 'LLAMA_TEMPERATURE', 0.7),
    }
    return render(request, 'ai_chat/settings.html', context)


@csrf_exempt
@require_http_methods(["GET"])
def health_check(request):
    """Health check endpoint for AI assistant."""
    try:
        # Simple test to see if the AI assistant is working
        test_response = ai_assistant.generate_response("Hello")
        return JsonResponse({
            'status': 'healthy',
            'message': 'AI assistant is working',
            'model': getattr(settings, 'LLAMA_MODEL_NAME', 'Unknown')
        })
    except Exception as e:
        return JsonResponse({
            'status': 'unhealthy',
            'error': str(e)
        }, status=503)