console.log('script.js загружен');

// Управление темой

function toggleTheme() {
    console.log('toggleTheme вызван');
    const html = document.documentElement;
    const currentTheme = html.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    setTheme(newTheme);
}

function setTheme(theme) {
    console.log('setTheme вызван с:', theme);
    const html = document.documentElement;
    const btn = document.getElementById('themeToggle');

    html.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);

    if (btn) {
        btn.textContent = theme === 'dark' ? 'Светлая тема' : 'Темная тема';
        console.log('Кнопка обновлена:', btn.textContent);
    }

    console.log('Тема изменена на:', theme);
}

function loadTheme() {
    const savedTheme = localStorage.getItem('theme');
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    const theme = savedTheme || (prefersDark ? 'dark' : 'light');
    console.log('Загружаем тему:', theme);
    setTheme(theme);
}

// История

let history = [];

function loadHistory() {
    const saved = localStorage.getItem('searchHistory');
    if (saved) {
        try {
            history = JSON.parse(saved);
        } catch (e) {
            history = [];
        }
        renderHistory();
    }
}

function saveHistory() {
    localStorage.setItem('searchHistory', JSON.stringify(history));
    renderHistory();
}

function addToHistory(query) {
    history = history.filter(item => item !== query);
    history.unshift(query);
    if (history.length > 50) history.pop();
    saveHistory();
}

function clearHistory() {
    history = [];
    saveHistory();
}

function renderHistory() {
    const container = document.getElementById('historyList');
    if (!container) return;

    if (history.length === 0) {
        container.innerHTML = '<span style="color: var(--text-light); font-size: 14px;">История пуста</span>';
        return;
    }

    container.innerHTML = history.map(item =>
        `<span class="history-item" onclick="searchQuery('${item.replace(/'/g, "\\'")}')">${item}</span>`
    ).join(', ');
}

// Поиск

function searchQuery(query) {
    console.log('Поиск по истории:', query);
    const input = document.getElementById('queryInput');
    if (input) input.value = query;
    performSearch(query);
}

// Получение CSRF-токена для Django
function getCSRFToken() {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, 10) === ('csrftoken' + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(10));
                break;
            }
        }
    }
    return cookieValue;
}

async function performSearch(query) {
    console.log('Выполняется поиск для:', query);

    const statusEl = document.getElementById('statusMessage');
    const definitionEl = document.getElementById('definitionResult');
    const examplesEl = document.getElementById('examplesResult');
    const searchBtn = document.getElementById('searchBtn');

    if (!query) {
        console.log('Пустой запрос');
        return;
    }

    if (searchBtn) searchBtn.disabled = true;
    if (statusEl) statusEl.innerHTML = '<span class="loading"></span> Поиск...';
    if (definitionEl) definitionEl.innerHTML = '<div class="placeholder">Поиск...</div>';
    if (examplesEl) examplesEl.innerHTML = '<div class="placeholder">Поиск примеров...</div>';

    try {
        console.log('Отправка запроса на /search/...');

        const csrfToken = getCSRFToken();

        const response = await fetch('/search/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({ query: query })
        });

        console.log('Ответ получен, статус:', response.status);

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'HTTP error! status: ' + response.status);
        }

        const data = await response.json();
        console.log('Данные получены');

        if (data.error) {
            console.log('Ошибка от сервера:', data.error);
            if (statusEl) statusEl.textContent = 'Ошибка: ' + data.error;
            if (definitionEl) definitionEl.innerHTML = '<div class="placeholder">' + data.error + '</div>';
            if (examplesEl) examplesEl.innerHTML = '<div class="placeholder">Попробуйте другой запрос</div>';
            if (searchBtn) searchBtn.disabled = false;
            return;
        }

        console.log('Поиск успешен');
        addToHistory(query);
        displayDefinition(data, definitionEl);
        displayExamples(data, examplesEl);
        if (statusEl) statusEl.textContent = 'Найдено ' + data.total_examples_found + ' примеров';

    } catch (error) {
        console.log('Ошибка соединения:', error);
        if (statusEl) statusEl.textContent = 'Ошибка соединения с сервером';
        if (definitionEl) definitionEl.innerHTML = '<div class="placeholder">Ошибка при выполнении запроса</div>';
        if (examplesEl) examplesEl.innerHTML = '<div class="placeholder">Проверьте подключение к интернету</div>';
    }

    if (searchBtn) searchBtn.disabled = false;
}

// Отображение результатов

function displayDefinition(data, container) {
    if (!container) return;
    console.log('Отображение определения для:', data.query);
    const query = data.query;
    const definition = data.definition;
    const isPhrase = data.is_phrase;
    const isInfinitive = data.is_infinitive;

    let htmlContent = '<div class="definition-content">';

    let title = isPhrase ? 'Определение фразы: ' + query : 'Определение слова: ' + query;
    if (isInfinitive) {
        title = 'Определение глагола (инфинитив): ' + query;
    }
    htmlContent += '<h2>' + title + '</h2>';

    if (definition.meanings && Object.keys(definition.meanings).length > 0) {
        htmlContent += '<div class="meanings-block">';

        for (const [pos, defs] of Object.entries(definition.meanings)) {
            if (pos === 'перевод') continue;

            htmlContent += '<div class="part-of-speech">';
            htmlContent += '<div class="pos-header">';
            htmlContent += '<span class="pos-icon">▸</span>';
            htmlContent += '<span class="pos-name">' + pos + '</span>';
            htmlContent += '</div>';

            htmlContent += '<ul class="definitions-list">';
            if (defs && defs.length > 0) {
                defs.forEach((def, index) => {
                    const cleanDef = def.trim();
                    if (cleanDef) {
                        htmlContent += '<li class="definition-item">';
                        htmlContent += '<span class="def-number">' + (index + 1) + '.</span>';
                        htmlContent += '<span class="def-text">' + cleanDef + '</span>';
                        htmlContent += '</li>';
                    }
                });
            }
            htmlContent += '</ul>';
            htmlContent += '</div>';
        }

        htmlContent += '</div>';
    } else {
        htmlContent += '<p class="no-definition">Определение не найдено</p>';
        if (isPhrase) {
            htmlContent += '<p style="color: var(--text-muted); font-size: 14px; margin-top: 10px;">Совет: Попробуйте ввести отдельные слова из фразы</p>';
        }
    }

    htmlContent += '<div class="source">';
    htmlContent += 'Всего примеров: ' + data.total_examples_found + ' | ';
    htmlContent += 'Источники: ';
    const sources = [];
    for (const [source, count] of Object.entries(data.sources)) {
        if (count > 0) {
            const sourceNames = {
                'yandex': 'Yandex',
                'dictionary': 'Dictionary API',
                'linguee': 'Linguee'
            };
            sources.push((sourceNames[source] || source) + ' (' + count + ')');
        }
    }
    htmlContent += sources.join(', ') || 'нет данных';
    htmlContent += '</div>';

    htmlContent += '</div>';
    container.innerHTML = htmlContent;
    console.log('Определение отображено');
}

function displayExamples(data, container) {
    if (!container) return;
    const query = data.clean_query || data.query;
    console.log('Отображение примеров для:', query);

    let htmlContent = '<div class="examples-wrapper">';
    htmlContent += '<div class="examples-header">';
    htmlContent += '<h2>Контекстные примеры</h2>';

    htmlContent += '<div class="rating-legend">';
    htmlContent += '<span class="legend-title">Оценки примеров:</span>';
    htmlContent += '<span class="legend-item excellent">Отличный</span>';
    htmlContent += '<span class="legend-separator">, </span>';
    htmlContent += '<span class="legend-item good">Хороший</span>';
    htmlContent += '<span class="legend-separator">, </span>';
    htmlContent += '<span class="legend-item average">Средний</span>';
    htmlContent += '<span class="legend-separator">, </span>';
    htmlContent += '<span class="legend-item simple">Простой</span>';
    htmlContent += '</div>';
    htmlContent += '</div>';

    htmlContent += '<p style="color: var(--text-muted); font-size: 13px; margin-bottom: 15px; clear: both;">';
    htmlContent += 'Рейтинг показывает, насколько пример подходит для изучения. ';
    htmlContent += 'Чем рейтинг выше, тем больше акцента в примере на изучаемом слове. ';
    htmlContent += 'Оценка учитывает сложность остальных слов в предложении - чем они легче, тем рейтинг примера выше.';
    htmlContent += '</p>';

    if (data.examples && data.examples.length > 0) {
        data.examples.forEach((example, index) => {
            let text = example.text;
            let translatedText = example.translated_text || example.text;

            text = text.replace(/\*\*\*/g, '');
            translatedText = translatedText.replace(/\*\*\*/g, '');

            const escapedQuery = query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
            const regex = new RegExp('\\b(' + escapedQuery + ')\\b', 'gi');
            text = text.replace(regex, '<span class="highlight">$1</span>');

            const translatedRegex = new RegExp('(' + escapedQuery + ')', 'gi');
            translatedText = translatedText.replace(translatedRegex, '<span class="highlight">$1</span>');

            let ratingClass = '';
            let ratingDescription = '';
            if (example.rating_text) {
                ratingDescription = example.rating_text;
                if (example.rating_text === 'Отличный пример') ratingClass = 'excellent';
                else if (example.rating_text === 'Хороший пример') ratingClass = 'good';
                else if (example.rating_text === 'Средний пример') ratingClass = 'average';
                else if (example.rating_text === 'Простой пример') ratingClass = 'simple';
            }

            let lengthInfo = '';
            if (example.length_rating) {
                lengthInfo = ' | ' + example.length_rating;
            }

            htmlContent += '<div class="example-item ' + ratingClass + '">';
            htmlContent += '<div class="text">';
            htmlContent += '<span class="number">' + (index + 1) + '.</span> ' + text;
            htmlContent += '</div>';
            htmlContent += '<div class="translation">';
            htmlContent += '<span class="translation-icon">→</span> ' + translatedText;
            htmlContent += '</div>';
            htmlContent += '<div class="meta">';
            htmlContent += '<b>Рейтинг:</b> ' + example.score + ' | <b>Слов:</b> ' + example.word_count;
            if (ratingDescription) {
                htmlContent += ' | <span class="rating-badge ' + ratingClass + '">' + ratingDescription + '</span>';
            }
            htmlContent += lengthInfo;
            htmlContent += '</div>';
            htmlContent += '</div>';
        });
    } else {
        htmlContent += '<div class="no-examples">';
        htmlContent += '<p>Примеры не найдены</p>';
        htmlContent += '<p style="font-size: 14px; color: var(--text-muted); margin-top: 10px;">';
        htmlContent += 'Совет: Попробуйте другое слово или фразу<br>';
        htmlContent += 'Совет: Проверьте написание<br>';
        htmlContent += 'Совет: Для фраз попробуйте отдельные слова';
        htmlContent += '</p>';
        htmlContent += '</div>';
    }

    htmlContent += '</div>';
    container.innerHTML = htmlContent;
    console.log('Примеры отображены');
}

// Инициализация

document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM загружен');

    loadTheme();
    loadHistory();

    const queryInput = document.getElementById('queryInput');
    const searchBtn = document.getElementById('searchBtn');
    const clearBtn = document.getElementById('clearBtn');
    const clearHistoryBtn = document.getElementById('clearHistoryBtn');
    const themeToggle = document.getElementById('themeToggle');

    console.log('Элементы найдены:', {
        queryInput: !!queryInput,
        searchBtn: !!searchBtn,
        clearBtn: !!clearBtn,
        clearHistoryBtn: !!clearHistoryBtn,
        themeToggle: !!themeToggle
    });

    if (queryInput) {
        queryInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                const query = queryInput.value.trim();
                console.log('Enter нажат, запрос:', query);
                if (query) performSearch(query);
            }
        });
    }

    if (searchBtn) {
        searchBtn.addEventListener('click', function() {
            const query = queryInput ? queryInput.value.trim() : '';
            console.log('Кнопка "Найти" нажата, запрос:', query);
            if (query) performSearch(query);
        });
    }

    if (clearBtn) {
        clearBtn.addEventListener('click', function() {
            console.log('Кнопка "Очистить" нажата');
            if (queryInput) queryInput.value = '';
            const defEl = document.getElementById('definitionResult');
            const exEl = document.getElementById('examplesResult');
            const stEl = document.getElementById('statusMessage');
            if (defEl) defEl.innerHTML = '<div class="placeholder">Введите слово или фразу для поиска</div>';
            if (