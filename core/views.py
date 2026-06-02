import json
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.exceptions import ValidationError
from .forms import SearchForm
from .models import SearchQuery
from .utils import ExampleGenerator

generator = ExampleGenerator()


def index(request):
    """Главная страница"""
    form = SearchForm()
    return render(request, 'index.html', {'form': form})


@csrf_exempt
@require_http_methods(["POST"])
def search(request):
    """Обработка поискового запроса"""
    try:
        data = json.loads(request.body)
        query = data.get('query', '').strip()

        form = SearchForm({'query_text': query})
        if not form.is_valid():
            return JsonResponse({'error': form.errors['query_text'][0]})

        # Сохраняем запрос в историю
        search_query = form.save(commit=False)
        search_query.ip_address = request.META.get('REMOTE_ADDR', '')
        search_query.user_agent = request.META.get('HTTP_USER_AGENT', '')
        search_query.results_count = 0
        search_query.save()

        # Выполняем поиск
        result = generator.generate_examples(query)

        # Обновляем количество результатов
        search_query.results_count = len(result.get('examples', []))
        search_query.save()

        return JsonResponse(result)

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Неверный формат запроса'}, status=400)
    except Exception as e:
        return JsonResponse({'error': f'Ошибка при поиске: {str(e)}'}, status=500)