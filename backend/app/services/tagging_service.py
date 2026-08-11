from __future__ import annotations

import json
from dataclasses import dataclass, field

import structlog
from pydantic import BaseModel, ValidationError

from app.domain.color import fallback_color, is_valid_hex
from app.domain.entities import Category
from app.domain.llm_client import ChatMessage, LLMClient, LLMError

logger = structlog.get_logger(__name__)

_CATEGORY_VALUES = ", ".join(f'"{c.value}"' for c in Category)

_SYSTEM_PROMPT = (
    "Ты — классификатор коротких заметок из потока мыслей пользователя. "
    "На вход дан сырой текст заметки (часто с опечатками и без знаков препинания — "
    "исправляй их мысленно при чтении, не зацикливайся на них) и список уже "
    "существующих тегов/тем, упорядоченный от самых часто используемых к редким.\n"
    "Верни ЧИСТЫЙ JSON (без пояснений и markdown) со схемой:\n"
    '{"topic": {"name": string, "color": string, "category": string}, '
    '"subtopic": {"name": string, "color": string, "category": string}|null, '
    '"tags": [{"name": string, "color": string, "category": string}], '
    '"quote": string|null}\n'
    "Правила:\n"
    "- В потоке мыслей часто затронуто НЕСКОЛЬКО разных тем сразу — не сжимай их в одну "
    "общую. На каждую по-настоящему отдельную сферу жизни, упомянутую в тексте, должен "
    "появиться свой тег (в topic, subtopic или tags — неважно куда именно он попадёт, "
    "при сохранении все они становятся равноправными тегами записи). Не экономь на "
    "количестве тегов, если тем реально несколько — это важнее, чем лаконичность.\n"
    "- name (у topic/subtopic/tags) — нижний регистр, единственное число, именительный "
    "падеж, широкое переиспользуемое понятие, а не пересказ содержания "
    "(например: «работа», а не «рабочие дела» или «дедлайн по проекту»).\n"
    "- color — HEX-цвет вида #rrggbb для ЭТОГО тега/темы. Разным по смыслу тегам подбирай "
    "визуально разные, приятные глазу цвета средней яркости (не чёрный, не белый, не "
    "кислотный). Если используешь существующий тег из списка — всё равно укажи какой-то "
    "цвет, он будет проигнорирован (у существующих тегов цвет уже зафиксирован).\n"
    f"- category — строго одно значение из списка: {_CATEGORY_VALUES}. Это сфера жизни "
    "(колесо баланса), к которой относится тег. Ориентир по категориям: "
    "здоровье — спорт, сон, питание, самочувствие, лечение; "
    "карьера — работа, проекты, разработка, сервисы, профессиональные задачи и навыки, "
    "рабочее планирование; "
    "финансы — деньги, покупки, штрафы, доходы и расходы; "
    "отношения — близкие, друзья, общение, конфликты; "
    "саморазвитие — учёба, книги, идеи, новые навыки, личностный рост; "
    "отдых — хобби, игры, развлечения, путешествия, отдых от дел; "
    "быт — дом, бытовые дела, документы, разовые поручения; "
    "эмоции — настроение, чувства, переживания как таковые (без привязки к причине). "
    'Перед тем как поставить "другое", сверься с этим списком — почти всегда что-то '
    'подходит. "другое" — редкое исключение, когда тег действительно не укладывается '
    "ни в одну из категорий выше, а не значение по умолчанию для всего неочевидного. "
    "Тоже игнорируется для уже существующих тегов.\n"
    "- name НИКОГДА не должно дословно совпадать ни с одним из значений category "
    "(не заводи тег «быт» с category «быт», не заводи тег «финансы» с category "
    "«финансы», не заводи тег «отдых» с category «отдых» и т.д.). category — это "
    "отдельное служебное поле для группировки облака тегов, а не сам тег: если "
    "name совпадёт с category, в облаке появится тег-дубликат самой категории. "
    "Если для темы не находится ничего более узкого, чем сама категория — либо "
    "используй существующий topic/тег из списка (даже не идеально узкий), либо "
    "подбери синоним, который не совпадает с category дословно.\n"
    "- Сильно предпочитай существующие теги/темы новым: если что-то из списка "
    "подходит по смыслу хотя бы приблизительно — используй его написание (name) дословно. "
    "Заводи новый тег, только если ни один существующий вообще не подходит.\n"
    "- Различай разовые бытовые/бюрократические дела и повторяющиеся темы. Для "
    "разового поручения (оплатить конкретный штраф, забрать конкретный документ, "
    "разовая бытовая задача) НЕ заводи узкий тег с названием именно этого дела "
    '(например «штраф», «паспорт») — используй вместо этого широкое переиспользуемое '
    'слово вроде «дела», «поручения», «документы», «покупки» (по смыслу, но НЕ '
    "название самой category — см. правило выше). Специфичный тег заводи только для "
    "того, что вероятно повторится ещё — хобби, проекты, интересы, навыки, конкретные "
    "игры/инструменты/сервисы. Если что-то похожее уже есть среди существующих "
    "тегов — это сильный сигнал, что тема повторяющаяся и заслуживает своего тега.\n"
    "- Если в тексте явно выражено эмоциональное состояние — подбирай для него "
    "конкретное слово из широкого спектра (радость, грусть, раздражение, тревога, "
    "апатия, безразличие, воодушевление, вина, обида, усталость), которое реально "
    "соответствует тону именно этого текста, а не одно и то же слово по умолчанию "
    "для всех записей.\n"
    "- subtopic — не больше одного уточнения ГЛАВНОЙ темы (topic), только если оно явно "
    "есть, иначе null.\n"
    "- tags — все остальные отдельные темы/сферы жизни из текста, не вошедшие в topic/"
    "subtopic, по одному тегу на каждую. Обычно это 1-5 тегов, но их может быть и больше, "
    "если текст объективно затрагивает много всего — не ограничивай себя произвольным "
    "потолком. Не дублируй topic/subtopic и не разбивай одну и ту же мысль на теги-"
    "синонимы.\n"
    "- quote — короткая дословная цитата из текста, если в нём есть яркая фраза, "
    "которую стоит сохранить отдельно; иначе null.\n"
    "\n"
    "Пример. Текст: «учился весь день, работал, устал как всегда, ложусь поздно уже "
    "пол 5. еще надо записаться в зал. завтра куча всего — курс закрыть, работа, паспорт "
    "забрать. штраф оплатить за просрочку.»\n"
    "Хороший ответ (одна тема на topic, но текст явно затрагивает ещё четыре разные "
    "сферы — все они должны стать отдельными тегами, а не потеряться в одном общем "
    'теге или в "другое"; при этом «паспорт» и «штраф» — два РАЗНЫХ разовых бытовых '
    'поручения, оба ушли в тег «дела» с category «быт», а НЕ в тег с именем самой '
    "категории («быт») и не в два узких тега с их конкретными названиями; эмоция "
    'взята конкретная — «усталость», а не общее слово вроде "плохо"):\n'
    '{"topic": {"name": "работа", "category": "карьера", "color": "#60a5fa"}, '
    '"subtopic": {"name": "учёба", "category": "саморазвитие", "color": "#a78bfa"}, '
    '"tags": ['
    '{"name": "сон", "category": "здоровье", "color": "#4ade80"}, '
    '{"name": "спорт", "category": "здоровье", "color": "#22c55e"}, '
    '{"name": "дела", "category": "быт", "color": "#94a3b8"}, '
    '{"name": "усталость", "category": "эмоции", "color": "#f87171"}'
    '], "quote": null}\n'
    "Плохой ответ (так делать не надо): tags содержит "
    '{"name": "быт", "category": "быт", ...} — имя тега дословно совпадает с '
    'категорией; или всё сжато в один topic "дела", хотя в тексте явно несколько '
    "разных сфер жизни.\n"
    "- Ответ — только JSON, ничего больше."
)


@dataclass(frozen=True, slots=True)
class TagSuggestion:
    name: str
    color: str
    category: Category


@dataclass(frozen=True, slots=True)
class TaggingResult:
    topic: TagSuggestion
    subtopic: TagSuggestion | None
    tags: list[TagSuggestion] = field(default_factory=list)
    quote: str | None = None


class _TagSuggestionSchema(BaseModel):
    name: str
    color: str | None = None
    category: str | None = None


class _TaggingResponseSchema(BaseModel):
    topic: _TagSuggestionSchema
    subtopic: _TagSuggestionSchema | None = None
    tags: list[_TagSuggestionSchema] = []
    quote: str | None = None


FALLBACK_TOPIC_NAME = "не разобрано"

_FALLBACK_TOPIC = TagSuggestion(
    name=FALLBACK_TOPIC_NAME, color=fallback_color(FALLBACK_TOPIC_NAME), category=Category.OTHER
)

_CATEGORY_NAME_VALUES = {c.value for c in Category}


def _is_category_name(name: str) -> bool:
    return name.strip().lower() in _CATEGORY_NAME_VALUES


class TaggingService:
    def __init__(self, llm_client: LLMClient):
        self._llm_client = llm_client

    async def tag_entry(self, raw_text: str, existing_tag_names: list[str]) -> TaggingResult:
        try:
            return await self.tag_entry_strict(raw_text, existing_tag_names)
        except (LLMError, json.JSONDecodeError, ValidationError) as exc:
            logger.warning(
                "llm_tagging_failed", error=str(exc), fallback_topic=_FALLBACK_TOPIC.name
            )
            return TaggingResult(topic=_FALLBACK_TOPIC, subtopic=None, tags=[], quote=None)

    async def tag_entry_strict(self, raw_text: str, existing_tag_names: list[str]) -> TaggingResult:
        messages = [
            ChatMessage(role="system", content=_SYSTEM_PROMPT),
            ChatMessage(
                role="user",
                content=(
                    f"Существующие теги/темы: {', '.join(existing_tag_names) or '(пока нет)'}\n\n"
                    f"Текст заметки:\n{raw_text}"
                ),
            ),
        ]
        content = await self._llm_client.complete(messages, json_mode=True)
        parsed = _TaggingResponseSchema.model_validate(json.loads(content))

        subtopic = _to_suggestion(parsed.subtopic) if parsed.subtopic else None
        if subtopic is not None and _is_category_name(subtopic.name):
            subtopic = None

        tags = [_to_suggestion(t) for t in parsed.tags if t.name and t.name.strip()]
        tags = [t for t in tags if not _is_category_name(t.name)]

        return TaggingResult(
            topic=_to_suggestion(parsed.topic),
            subtopic=subtopic,
            tags=tags,
            quote=parsed.quote.strip() if parsed.quote else None,
        )


def _to_suggestion(schema: _TagSuggestionSchema) -> TagSuggestion:
    name = schema.name.strip().lower()
    color = schema.color.strip() if schema.color else None
    try:
        category = Category(schema.category) if schema.category else Category.OTHER
    except ValueError:
        category = Category.OTHER
    return TagSuggestion(
        name=name,
        color=color if is_valid_hex(color) else fallback_color(name),
        category=category,
    )
