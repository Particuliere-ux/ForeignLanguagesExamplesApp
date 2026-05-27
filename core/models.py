from django.db import models


class SearchQuery(models.Model):
    """Модель для хранения истории поисковых запросов"""
    query_text = models.CharField(
        max_length=255,
        verbose_name="Текст запроса"
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name="IP-адрес"
    )
    user_agent = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="User Agent"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата создания"
    )
    results_count = models.IntegerField(
        default=0,
        verbose_name="Количество результатов"
    )

    class Meta:
        verbose_name = "Поисковый запрос"
        verbose_name_plural = "Поисковые запросы"
        ordering = ['-created_at']

    def __str__(self):
        return self.query_text


class WordDefinition(models.Model):
    """Модель для кэширования определений слов"""
    word = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Слово"
    )
    definition_data = models.JSONField(
        default=dict,
        verbose_name="Данные определения"
    )
    translation = models.TextField(
        blank=True,
        verbose_name="Перевод"
    )
    transcription = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Транскрипция"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата создания"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Дата обновления"
    )

    class Meta:
        verbose_name = "Определение слова"
        verbose_name_plural = "Определения слов"
        ordering = ['word']

    def __str__(self):
        return self.word


class Example(models.Model):
    """Модель для хранения примеров употребления слов"""
    word = models.ForeignKey(
        WordDefinition,
        on_delete=models.CASCADE,
        related_name='examples',
        verbose_name="Слово"
    )
    text = models.TextField(
        verbose_name="Текст примера"
    )
    translated_text = models.TextField(
        blank=True,
        verbose_name="Перевод примера"
    )
    source = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Источник"
    )
    score = models.IntegerField(
        default=0,
        verbose_name="Рейтинг"
    )
    rating = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Оценка"
    )
    word_count = models.IntegerField(
        default=0,
        verbose_name="Количество слов"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата создания"
    )

    class Meta:
        verbose_name = "Пример"
        verbose_name_plural = "Примеры"
        ordering = ['-score']

    def __str__(self):
        return f"{self.word.word}: {self.text[:50]}..."