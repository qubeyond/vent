from __future__ import annotations

import re
from collections import Counter
from datetime import datetime

from app.domain.entities import Tag
from app.domain.repositories import EntryRepository, TagRepository

_STOPWORDS = frozenset(
    """
    и в во не что он на я с со как а то все она так его но да ты к у же вы за
    бы по только ее мне было вот от меня еще нет о из ему теперь когда даже
    ну вдруг ли если уже или ни быть был него до вас нибудь опять уж вам ведь
    там потом себя ничего ей может они тут где есть надо ней для мы тебя их
    чем была сам чтоб без будто чего раз тоже себе под будет ж тогда кто этот
    того потому этого какой совсем ним здесь этом одного впрочем хорошо свою
    этой перед иногда лучше чуть том нельзя такой им более всегда конечно
    всю между это эта эти этот тот та то те кажется который которая которое
    которые чтобы также очень просто может свои свой моя мой твой твоя наш
    наша при об про над после через был была были будем будешь будете есть
    имеет имел имела имели быть являюсь является являются пока
    """.split()
)

_WORD_RE = re.compile(r"[а-яёa-z-]+", re.IGNORECASE)
_NEGATION_RE = re.compile(r"\b(не|ни)\s+(?=[а-яё])", re.IGNORECASE)


def _tokenize(text: str) -> list[str]:
    merged = _NEGATION_RE.sub(r"\1-", text)
    return _WORD_RE.findall(merged.lower())


class StatsService:
    def __init__(self, entry_repo: EntryRepository, tag_repo: TagRepository):
        self._entry_repo = entry_repo
        self._tag_repo = tag_repo

    async def summary(self) -> tuple[int, int, int]:
        total_entries = await self._entry_repo.count(None, None)
        tags = await self._tag_repo.list_with_counts(None, None)
        texts = await self._entry_repo.list_raw_texts(None, None)
        total_chars = sum(len(t) for t in texts)
        return total_entries, len(tags), total_chars

    async def tag_cloud(
        self,
        date_from: datetime | None,
        date_to: datetime | None,
        search: str | None = None,
    ) -> list[tuple[Tag, int]]:
        return await self._tag_repo.list_with_counts(date_from, date_to, search)

    async def top_words(
        self,
        date_from: datetime | None,
        date_to: datetime | None,
        limit: int = 30,
        min_count: int = 3,
    ) -> list[tuple[str, int]]:
        texts = await self._entry_repo.list_raw_texts(date_from, date_to)
        counter: Counter[str] = Counter()
        for text in texts:
            for word in _tokenize(text):
                if len(word) >= 3 and word not in _STOPWORDS:
                    counter[word] += 1
        return [(word, count) for word, count in counter.most_common(limit) if count >= min_count]

    async def top_quotes(
        self,
        date_from: datetime | None,
        date_to: datetime | None,
        limit: int = 10,
        min_count: int = 2,
    ) -> list[tuple[str, int]]:
        quotes = await self._entry_repo.list_quotes(date_from, date_to)
        counter: Counter[str] = Counter(q.strip().lower() for q in quotes if q and q.strip())
        return [(quote, count) for quote, count in counter.most_common(limit) if count >= min_count]
