import json
import traceback
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
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
    print("=== ЗАПРОС ПОЛУЧЕН ===")
    print("Request body:", request.body)

    try:
        data = json.loads(request.body)
        query = data.get('query', '').strip()
        print("Query:", query)

        form = SearchForm({'query_text': query})
        if not form.is_valid():
            print("Form is invalid:", form.errors)
            return JsonResponse({'error': form.errors['query_text'][0]})

        # Сохраняем запрос в историю
        search_query = form.save(commit=False)
        search_query.ip_address = request.META.get('REMOTE_ADDR', '')
        search_query.user_agent = request.META.get('HTTP_USER_AGENT', '')
        search_query.results_count = 0
        search_query.save()
        print("Search query saved:", search_query.query_text)

        # Выполняем поиск
        print("Calling generator.generate_examples...")
        result = generator.generate_examples(query)
        print("Result received:", result.keys() if result else "None")

        # Обновляем количество результатов
        search_query.results_count = len(result.get('examples', []))
        search_query.save()
        print("Results count updated:", search_query.results_count)

        return JsonResponse(result)

    except json.JSONDecodeError as e:
        print("JSON Decode Error:", e)
        return JsonResponse({'error': 'Неверный формат запроса'}, status=400)
    except Exception as e:
        print("=" * 60)
        print("ОШИБКА В SEARCH VIEW:")
        print(traceback.format_exc())
        print("=" * 60)
        return JsonResponse({'error': f'Ошибка при поиске: {str(e)}'}, status=500)