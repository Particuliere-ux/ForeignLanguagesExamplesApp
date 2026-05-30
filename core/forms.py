from django import forms
from .models import SearchQuery


class SearchForm(forms.ModelForm):
    class Meta:
        model = SearchQuery
        fields = ['query_text']
        labels = {
            'query_text': 'Введите слово или фразу'
        }
        widgets = {
            'query_text': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите слово или фразу...',
                'id': 'queryInput'
            })
        }

    def clean_query_text(self):
        query = self.cleaned_data.get('query_text', '').strip()
        if not query:
            raise forms.ValidationError('Пожалуйста, введите слово или фразу')
        word_count = len(query.split())
        if word_count > 4:
            raise forms.ValidationError(
                f'Слишком много слов ({word_count}). Введите до 4-х слов'
            )
        return query