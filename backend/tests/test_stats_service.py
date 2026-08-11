from app.infra.db.repositories import SqlAlchemyEntryRepository, SqlAlchemyTagRepository
from app.services.stats_service import StatsService
from tests.test_entry_service import create_and_process, make_result, make_service


async def test_top_words_excludes_stopwords_and_counts(session):
    entry_service = make_service(session, make_result("общее"))
    await entry_service.create_entry("работа работа и снова работа", source="web")
    await entry_service.create_entry("работа тоже волк", source="web")

    stats = StatsService(SqlAlchemyEntryRepository(session), SqlAlchemyTagRepository(session))
    words = await stats.top_words(date_from=None, date_to=None, limit=10, min_count=1)

    counts = dict(words)
    assert counts["работа"] == 4
    assert "и" not in counts  # stopword


async def test_top_words_default_drops_rare_words(session):
    entry_service = make_service(session, make_result("общее"))
    await entry_service.create_entry("частослово частослово частослово", source="web")
    await entry_service.create_entry("частослово редкословцо", source="web")

    stats = StatsService(SqlAlchemyEntryRepository(session), SqlAlchemyTagRepository(session))
    counts = dict(await stats.top_words(date_from=None, date_to=None))

    assert counts["частослово"] == 4
    assert "редкословцо" not in counts


async def test_top_words_keeps_negation_meaning(session):
    entry_service = make_service(session, make_result("общее"))
    await entry_service.create_entry("не нравится не нравится не нравится", source="web")
    await entry_service.create_entry("очень нравится очень нравится очень нравится", source="web")

    stats = StatsService(SqlAlchemyEntryRepository(session), SqlAlchemyTagRepository(session))
    counts = dict(await stats.top_words(date_from=None, date_to=None, min_count=1))

    assert counts["не-нравится"] == 3
    assert counts["нравится"] == 3
    assert "не" not in counts


async def test_top_quotes_only_repeated(session):
    repeated_service = make_service(session, make_result("x", quote="время лечит"))
    await create_and_process(repeated_service, "первая")
    await create_and_process(repeated_service, "вторая")

    once_service = make_service(session, make_result("x", quote="уникальная мысль"))
    await create_and_process(once_service, "третья")

    stats = StatsService(SqlAlchemyEntryRepository(session), SqlAlchemyTagRepository(session))
    quotes = await stats.top_quotes(date_from=None, date_to=None, limit=10, min_count=2)

    assert quotes == [("время лечит", 2)]


async def test_tag_cloud_counts_entries_per_tag(session):
    service = make_service(session, make_result("здоровье"))
    await create_and_process(service, "а")
    await create_and_process(service, "б")

    stats = StatsService(SqlAlchemyEntryRepository(session), SqlAlchemyTagRepository(session))
    cloud = await stats.tag_cloud(date_from=None, date_to=None)

    assert any(tag.canonical_name == "здоровье" and count == 2 for tag, count in cloud)


async def test_summary_counts_entries_and_tags(session):
    service = make_service(session, make_result("тема", tags=("подтег",)))
    await create_and_process(service, "первая")
    await create_and_process(service, "вторая")

    stats = StatsService(SqlAlchemyEntryRepository(session), SqlAlchemyTagRepository(session))
    total_entries, total_tags, total_chars = await stats.summary()

    assert total_entries == 2
    assert total_tags == 2  # "тема" + "подтег"
    assert total_chars == len("первая") + len("вторая")


async def test_tag_cloud_search_only_counts_matching_entries(session):
    service = make_service(session, make_result("работа"))
    await create_and_process(service, "обычный рабочий день")

    other_service = make_service(session, make_result("работа"))
    await create_and_process(other_service, "горящий дедлайн на работе")

    stats = StatsService(SqlAlchemyEntryRepository(session), SqlAlchemyTagRepository(session))
    cloud = await stats.tag_cloud(date_from=None, date_to=None, search="дедлайн")

    work_count = next(count for tag, count in cloud if tag.canonical_name == "работа")
    assert work_count == 1
