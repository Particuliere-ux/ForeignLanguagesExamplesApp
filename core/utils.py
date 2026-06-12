import re
import requests
from typing import List, Dict, Optional
from PyMultiDictionary import MultiDictionary, DICT_MW
from bs4 import BeautifulSoup
from django.conf import settings

POS_MAP = {
    'noun': 'существительное',
    'verb': 'глагол',
    'adjective': 'прилагательное',
    'adverb': 'наречие',
    'preposition': 'предлог',
    'conjunction': 'союз',
    'interjection': 'междометие',
    'pronoun': 'местоимение',
    'article': 'артикль'
}

IDIOMS = {
    "break the ice": "растопить лёд, начать разговор",
    "hit the nail on the head": "попасть в точку",
    "under the weather": "быть не в форме, плохо себя чувствовать",
    "piece of cake": "легче лёгкого, простое дело",
    "cost an arm and a leg": "влететь в копеечку, стоить очень дорого",
    "spill the beans": "выдать секрет, проболтаться",
    "bend over backwards": "лезть из кожи вон, стараться изо всех сил",
    "kick the bucket": "сыграть в ящик, умереть",
    "once in a blue moon": "раз в сто лет, очень редко",
    "cut corners": "делать проще (иногда нечестно)",
    "call it a day": "закончить на сегодня",
    "face the music": "отвечать за свои поступки",
    "go the extra mile": "приложить дополнительные усилия",
    "let the cat out of the bag": "выпустить кота из мешка, раскрыть секрет",
    "raining cats and dogs": "льёт как из ведра (о дожде)",
    "kill two birds with one stone": "убить двух зайцев одним выстрелом",
    "burn the midnight oil": "работать допоздна",
    "the ball is in your court": "мяч на вашей стороне, очередь за вами",
}


class ExampleGenerator:
    """Класс генерации примеров с Yandex Dictionary API"""

    def __init__(self):
        self.dictionary = MultiDictionary()
        self.common_words = self._load_common_words()
        self.yandex_available = bool(settings.YANDEX_API_KEY)
        self._yandex_examples_cache = []

    def _load_common_words(self) -> set:
        common = {
            'the', 'be', 'to', 'of', 'and', 'a', 'in', 'that', 'have', 'i',
            'it', 'for', 'not', 'on', 'with', 'he', 'as', 'you', 'do', 'at',
            'this', 'but', 'his', 'by', 'from', 'they', 'we', 'say', 'her', 'she',
            'or', 'an', 'will', 'my', 'one', 'all', 'would', 'there', 'their', 'what',
            'so', 'up', 'out', 'if', 'about', 'who', 'get', 'which', 'go', 'me',
            'when', 'make', 'can', 'like', 'time', 'no', 'just', 'him', 'know', 'take',
            'people', 'into', 'year', 'your', 'good', 'some', 'could', 'them', 'see', 'other',
        }
        return common

    def is_phrase(self, text: str) -> bool:
        words = text.strip().split()
        return 2 <= len(words) <= 4

    def clean_infinitive(self, text: str) -> tuple:
        text = text.strip()
        if text.lower().startswith('to '):
            return text[3:].strip(), True
        return text, False

    def get_yandex_translation(self, word: str) -> Optional[Dict]:
        if not self.yandex_available:
            return None

        try:
            params = {
                "key": settings.YANDEX_API_KEY,
                "lang": "en-ru",
                "text": word
            }

            response = requests.get(
                settings.YANDEX_BASE_URL,
                params=params,
                timeout=settings.API_TIMEOUT
            )

            if response.status_code == 200:
                return response.json()
            return None

        except Exception:
            return None

    def parse_yandex_response(self, data: Dict, word: str) -> Dict:
        result = {
            "meanings": {},
            "examples": [],
            "transcription": "",
            "synonyms": [],
            "russian_translation": ""
        }

        # Fixed: Исправлена ошибка, при которой Yandex API возвращал пустой ответ
        if not data or 'def' not in data:
            return result

        try:
            for definition in data.get('def', []):
                pos = definition.get('pos', 'unknown')
                pos_ru = POS_MAP.get(pos, pos)

                text = definition.get('text', '')
                if text:
                    result["russian_translation"] = text

                translations = []
                for tr in definition.get('tr', []):
                    tr_text = tr.get('text', '')
                    if tr_text and tr_text not in translations:
                        translations.append(tr_text)

                    for syn in tr.get('syn', []):
                        syn_text = syn.get('text', '')
                        if syn_text and syn_text not in result["synonyms"]:
                            result["synonyms"].append(syn_text)

                    for ex in tr.get('ex', []):
                        ex_text = ex.get('text', '')
                        if ex_text and ex_text not in result["examples"]:
                            result["examples"].append(ex_text)

                if translations:
                    result["meanings"][pos_ru] = translations[:3]

                if not result["transcription"]:
                    ts = definition.get('ts', '')
                    if ts:
                        result["transcription"] = ts

        except Exception:
            pass

        return result

    def get_definition(self, word: str, is_infinitive: bool = False) -> Dict:
        try:
            meanings = {}
            russian_translation = None
            examples = []
            synonyms = []
            transcription = ""

            if self.yandex_available:
                yandex_data = self.get_yandex_translation(word)
                if yandex_data:
                    parsed = self.parse_yandex_response(yandex_data, word)
                    meanings = parsed.get("meanings", {})
                    examples = parsed.get("examples", [])
                    synonyms = parsed.get("synonyms", [])
                    transcription = parsed.get("transcription", "")
                    russian_translation = parsed.get("russian_translation", "")
                    self._yandex_examples_cache = examples

            if not meanings:
                try:
                    url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
                    response = requests.get(url, timeout=settings.API_TIMEOUT)
                    if response.status_code == 200:
                        data = response.json()
                        for entry in data:
                            for meaning in entry.get('meanings', []):
                                part = meaning.get('partOfSpeech', 'unknown')
                                defs = []
                                for definition in meaning.get('definitions', []):
                                    def_text = definition.get('definition', '')
                                    defs.append(def_text)
                                if defs:
                                    pos_ru = POS_MAP.get(part, part)
                                    meanings[pos_ru] = defs[:2]
                                    for definition in meaning.get('definitions', []):
                                        example = definition.get('example', '')
                                        if example and example not in examples:
                                            examples.append(example)
                except Exception:
                    pass

            if not meanings:
                try:
                    eng_meanings = self.dictionary.meaning('en', word, dictionary=DICT_MW)
                    if eng_meanings:
                        for pos, defs in eng_meanings.items():
                            pos_ru = POS_MAP.get(pos, pos)
                            meanings[pos_ru] = defs[:2]
                except Exception:
                    pass

            if is_infinitive and meanings and 'глагол' in meanings:
                meanings['глагол (инфинитив)'] = meanings.pop('глагол')

            if russian_translation and not meanings:
                meanings['перевод'] = [russian_translation]
            elif russian_translation and 'перевод' not in meanings:
                meanings['перевод'] = [russian_translation]

            if examples:
                self._examples_cache = examples[:5]

            return {
                "word": word,
                "meanings": meanings,
                "is_infinitive": is_infinitive,
                "russian_translation": russian_translation,
                "transcription": transcription,
                "synonyms": synonyms[:5],
                "examples": examples[:5],
                "error": None if meanings else "Определение не найдено"
            }
        except Exception as e:
            return {
                "word": word,
                "meanings": {},
                "is_infinitive": is_infinitive,
                "russian_translation": None,
                "transcription": "",
                "synonyms": [],
                "examples": [],
                "error": str(e)
            }

    def search_phrase_in_text(self, text: str, phrase: str) -> bool:
        if not text or not phrase:
            return False

        text_lower = text.lower()
        phrase_lower = phrase.lower()
        phrase_words = phrase_lower.split()

        if phrase_lower in text_lower:
            return True

        if len(phrase_words) >= 2:
            text_words = text_lower.split()
            for i in range(len(text_words) - len(phrase_words) + 1):
                if text_words[i:i + len(phrase_words)] == phrase_words:
                    return True

        return all(word in text_lower for word in phrase_words)

    def get_examples_from_dictionaryapi(self, query: str, limit: int = 5) -> List[str]:
        examples = []
        try:
            url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{requests.utils.quote(query)}"
            response = requests.get(url, timeout=settings.API_TIMEOUT)

            if response.status_code == 200:
                data = response.json()
                for entry in data:
                    for meaning in entry.get('meanings', []):
                        for definition in meaning.get('definitions', []):
                            example = definition.get('example', '')
                            if example and self.search_phrase_in_text(example, query):
                                clean_ex = self._clean_sentence(example)
                                if clean_ex:
                                    examples.append(clean_ex)
                                    if len(examples) >= limit:
                                        return examples
        except Exception:
            pass
        return examples

    def get_examples_from_linguee(self, query: str, limit: int = 5) -> List[str]:
        examples = []
        try:
            encoded_query = requests.utils.quote(query)
            url = f"https://www.linguee.com/english-russian/search?source=auto&q={encoded_query}"
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

            response = requests.get(url, headers=headers, timeout=settings.LINGUEE_TIMEOUT)

            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                example_elements = soup.find_all('div', class_='example')

                for element in example_elements[:limit]:
                    source_text = element.find('div', class_='source')
                    if source_text:
                        text = source_text.get_text(strip=True)
                        if self.search_phrase_in_text(text, query):
                            clean_text = self._clean_sentence(text)
                            if clean_text and len(clean_text) > 10:
                                examples.append(clean_text)
        except Exception:
            pass
        return examples

    def _clean_sentence(self, sentence: str) -> str:
        if not sentence:
            return ""

        sentence = re.sub(r'<[^>]+>', '', sentence)
        sentence = re.sub(r'\s+', ' ', sentence)
        sentence = re.sub(r'[^\w\s.,!?\'"()-]', '', sentence)
        sentence = sentence.strip()

        if len(sentence) < 15 or len(sentence.split()) < 5:
            return ""
        return sentence

    def _get_word_complexity(self, word: str) -> int:
        word_lower = word.lower().strip('.,!?\'"()-')
        if not word_lower:
            return 0

        if word_lower in self.common_words:
            return 0

        if len(word_lower) > 7:
            return 2

        return 1

    def _analyze_example_complexity(self, text: str, query: str) -> Dict:
        words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
        query_words = set(query.lower().split())

        stop_words = {'the', 'a', 'an', 'of', 'to', 'for', 'with', 'on', 'at', 'from',
                      'by', 'in', 'into', 'through', 'during', 'including', 'without'}

        analyzed_words = []
        for word in words:
            if word in stop_words or word in query_words:
                continue
            analyzed_words.append(word)

        if not analyzed_words:
            return {
                'complexity_score': 0,
                'rare_words': [],
                'common_words': [],
                'total_analyzed': 0
            }

        rare_words = []
        common_words = []

        for word in analyzed_words:
            complexity = self._get_word_complexity(word)
            if complexity >= 2:
                rare_words.append(word)
            else:
                common_words.append(word)

        total = len(analyzed_words)
        rare_ratio = len(rare_words) / total if total > 0 else 0

        return {
            'complexity_score': rare_ratio,
            'rare_words': rare_words[:5],
            'common_words': common_words,
            'total_analyzed': total
        }

    def translate_text(self, text: str) -> str:
        try:
            url = f"https://api.mymemory.translated.net/get?q={text}&langpair=en|ru"
            response = requests.get(url, timeout=3)
            if response.status_code == 200:
                data = response.json()
                if data.get('responseData'):
                    translation = data['responseData'].get('translatedText', '')
                    if translation and translation != text:
                        return translation
        except Exception:
            pass
        return text

    def rank_examples(self, examples: List[str], query: str) -> List[Dict]:
        ranked = []
        query_words = set(query.lower().split())

        for example in examples:
            score = 0
            example_lower = example.lower()
            query_lower = query.lower()

            if query_lower in example_lower:
                score += 20
            elif all(word in example_lower for word in query_words):
                example_words = example_lower.split()
                try:
                    indices = [example_words.index(word) for word in query_words]
                    if all(indices[i] < indices[i + 1] for i in range(len(indices) - 1)):
                        score += 15
                    else:
                        score += 5
                except ValueError:
                    score += 3
            else:
                continue

            complexity = self._analyze_example_complexity(example, query)
            rare_ratio = complexity['complexity_score']

            if rare_ratio == 0:
                score += 15
                complexity_rating = 'отличный'
            elif rare_ratio < 0.2:
                score += 10
                complexity_rating = 'хороший'
            elif rare_ratio < 0.4:
                score += 5
                complexity_rating = 'средний'
            else:
                score += 0
                complexity_rating = 'сложный'

            words_count = len(example.split())
            if 5 <= words_count <= 15:
                score += 10
                length_rating = 'оптимальная длина'
            elif 16 <= words_count <= 25:
                score += 5
                length_rating = 'средняя длина'
            elif 26 <= words_count <= 35:
                score += 2
                length_rating = 'длинный пример'
            else:
                score += 0
                length_rating = 'очень длинный пример'

            if example and example[0].isupper():
                score += 3
            if example and example[-1] in '.!?':
                score += 2

            if example_lower.startswith(query_lower):
                score += 5

            if score >= 40:
                rating_text = 'Отличный пример'
            elif score >= 30:
                rating_text = 'Хороший пример'
            elif score >= 20:
                rating_text = 'Средний пример'
            else:
                rating_text = 'Простой пример'

            translated_example = self.translate_text(example)

            ranked.append({
                "text": example,
                "translated_text": translated_example,
                "score": score,
                "word_count": words_count,
                "rating_text": rating_text,
                "complexity_rating": complexity_rating,
                "length_rating": length_rating,
                "rare_words": complexity['rare_words'],
                "total_analyzed_words": complexity['total_analyzed']
            })

        ranked.sort(key=lambda x: x["score"], reverse=True)
        return ranked

    def generate_examples(self, query: str) -> Dict:
        original_query = query
        clean_word, is_infinitive = self.clean_infinitive(query)

        if is_infinitive:
            query = clean_word

        is_phrase_input = self.is_phrase(query)

        if is_phrase_input:
            phrase_lower = query.lower()
            translation = IDIOMS.get(phrase_lower, self.translate_text(query))
            definition_data = {
                "word": query,
                "meanings": {"фраза": [f"Фраза: {query}"]},
                "is_infinitive": False,
                "russian_translation": translation,
                "transcription": "",
                "synonyms": [],
                "examples": [],
                "error": None
            }
        else:
            definition_data = self.get_definition(query, is_infinitive)

        all_examples = []

        if hasattr(self, '_yandex_examples_cache'):
            all_examples.extend(self._yandex_examples_cache[:3])
            self._yandex_examples_cache = []

        dict_examples = self.get_examples_from_dictionaryapi(query)
        all_examples.extend(dict_examples)

        linguee_examples = self.get_examples_from_linguee(query)
        all_examples.extend(linguee_examples)

        ranked = self.rank_examples(all_examples, query)

        return {
            "query": original_query,
            "clean_query": query,
            "is_phrase": is_phrase_input,
            "is_infinitive": is_infinitive,
            "word_count": len(query.split()),
            "definition": definition_data,
            "examples": ranked[:5],
            "total_examples_found": len(all_examples),
            "sources": {
                "yandex": len(dict_examples) if self.yandex_available else 0,
                "dictionary": len(dict_examples),
                "linguee": len(linguee_examples)
            }
        }