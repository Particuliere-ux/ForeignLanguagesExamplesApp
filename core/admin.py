from django.contrib import admin
from .models import SearchQuery, WordDefinition, Example


@admin.register(SearchQuery)
class SearchQueryAdmin(admin.ModelAdmin):
    list_display = ('query_text', 'ip_address', 'results_count', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('query_text', 'ip_address')
    readonly_fields = ('created_at',)


@admin.register(WordDefinition)
class WordDefinitionAdmin(admin.ModelAdmin):
    list_display = ('word', 'translation', 'transcription', 'created_at')
    search_fields = ('word', 'translation')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Example)
class ExampleAdmin(admin.ModelAdmin):
    list_display = ('word', 'text_preview', 'score', 'rating', 'source')
    list_filter = ('source', 'rating')
    search_fields = ('text', 'translated_text')
    readonly_fields = ('created_at',)

    def text_preview(self, obj):
        return obj.text[:50] + '...' if len(obj.text) > 50 else obj.text
    text_preview.short_description = 'Пример (превью)'