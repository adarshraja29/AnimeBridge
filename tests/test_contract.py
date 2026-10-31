"""
Unit & integration-contract tests for the OpenMovies connector harness.
Tests search, metadata, episodes, video streams, subtitles, timeouts, empty results, and malformed responses.
"""

from pathlib import Path
import pytest

from tools.contract import (
    BaseConnector,
    AnimeDetails,
    Episode,
    VideoStream,
    SubtitleTrack,
    SearchPage,
    HealthCheckResult,
    ContentUnavailableError,
    UnsupportedCapabilityError,
    ParseError,
    TimeoutError,
    NetworkError
)


FIXTURE_PATH = Path(__file__).parent.parent / "src" / "en" / "openmovies" / "fixtures" / "catalog.json"


class OpenMoviesTestConnector(BaseConnector):
    """Test connector harness using the Open Movies catalog fixture."""
    def __init__(self, fixture_path: Path = FIXTURE_PATH, timeout_seconds: float = 10.0):
        super().__init__(
            connector_id="openmovies",
            name="Open Movies",
            base_url="https://download.blender.org",
            language="en",
            capabilities={
                "search",
                "metadata",
                "episodes",
                "playback",
                "subtitles",
                "audio_tracks",
                "health_check",
                "popular",
                "latest_updates"
            },
            timeout_seconds=timeout_seconds
        )
        self.fixture_path = fixture_path

    def _load_catalog(self):
        import json
        if not self.fixture_path.exists():
            raise NetworkError("Fixture not found", self.connector_id)
        try:
            with open(self.fixture_path, "r", encoding="utf-8") as f:
                raw = f.read()
            data = json.loads(raw)
            return data.get("items", [])
        except json.JSONDecodeError as e:
            raise ParseError(f"Malformed JSON: {e}", self.connector_id, raw_payload=raw[:100])

    def search(self, query: str, page: int = 1) -> SearchPage:
        self.assert_capability("search")
        items = self._load_catalog()
        q = query.strip().lower()
        matched = [
            it for it in items
            if q in it["title"].lower() or q in it.get("description", "").lower()
        ]
        from tools.contract import SearchResult
        results = [
            SearchResult(
                id=it["id"],
                title=it["title"],
                url=it["url"],
                thumbnail_url=it.get("thumbnailUrl")
            )
            for it in matched
        ]
        return SearchPage(items=results, has_next_page=False, page=page)

    def get_popular(self, page: int = 1) -> SearchPage:
        self.assert_capability("popular")
        items = self._load_catalog()
        from tools.contract import SearchResult
        results = [
            SearchResult(
                id=it["id"],
                title=it["title"],
                url=it["url"],
                thumbnail_url=it.get("thumbnailUrl")
            )
            for it in items
        ]
        return SearchPage(items=results, has_next_page=False, page=page)

    def get_latest(self, page: int = 1) -> SearchPage:
        self.assert_capability("latest_updates")
        items = sorted(self._load_catalog(), key=lambda x: x.get("releaseYear", 0), reverse=True)
        from tools.contract import SearchResult
        results = [
            SearchResult(
                id=it["id"],
                title=it["title"],
                url=it["url"],
                thumbnail_url=it.get("thumbnailUrl")
            )
            for it in items
        ]
        return SearchPage(items=results, has_next_page=False, page=page)

    def get_details(self, content_url: str) -> AnimeDetails:
        self.assert_capability("metadata")
        items = self._load_catalog()
        for it in items:
            if it["url"] == content_url or it["id"] == content_url:
                return AnimeDetails(
                    id=it["id"],
                    title=it["title"],
                    url=it["url"],
                    thumbnail_url=it.get("thumbnailUrl"),
                    description=it.get("description"),
                    genres=it.get("genres", []),
                    status=it.get("status", "COMPLETED"),
                    author=it.get("author"),
                    artist=it.get("artist"),
                    release_year=it.get("releaseYear")
                )
        raise ContentUnavailableError(f"Content not found: {content_url}", self.connector_id, content_id=content_url)

    def get_episodes(self, content_url: str):
        self.assert_capability("episodes")
        items = self._load_catalog()
        for it in items:
            if it["url"] == content_url or it["id"] == content_url:
                return [
                    Episode(
                        id=ep["id"],
                        name=ep["title"],
                        episode_number=float(i + 1),
                        url=ep["videoUrl"],
                        date_upload=ep.get("dateUpload")
                    )
                    for i, ep in enumerate(it.get("episodes", []))
                ]
        raise ContentUnavailableError(f"Episodes not found: {content_url}", self.connector_id, content_id=content_url)

    def get_video_streams(self, episode_url: str):
        self.assert_capability("playback")
        items = self._load_catalog()
        for it in items:
            for ep in it.get("episodes", []):
                if ep["videoUrl"] == episode_url or ep["id"] == episode_url:
                    subs = [SubtitleTrack(url=s["url"], lang=s["lang"]) for s in ep.get("subtitles", [])]
                    return [
                        VideoStream(
                            url=s["url"],
                            quality=s["quality"],
                            video_url=s["url"],
                            subtitles=subs
                        )
                        for s in ep.get("streams", [])
                    ]
        raise ContentUnavailableError(f"Streams not found: {episode_url}", self.connector_id, content_id=episode_url)


@pytest.fixture
def connector():
    return OpenMoviesTestConnector()


def test_search_exact_match(connector):
    """Test searching for 'Big Buck Bunny' returns matching item."""
    res = connector.search("Big Buck Bunny")
    assert len(res.items) >= 1
    assert any("Big Buck Bunny" in it.title for it in res.items)


def test_search_case_insensitive(connector):
    """Test case-insensitivity in search."""
    res = connector.search("sintel")
    assert len(res.items) >= 1
    assert "Sintel" in res.items[0].title


def test_search_empty_results(connector):
    """Test search with no matches returns empty SearchPage without crashing."""
    res = connector.search("non_existent_movie_title_xyz_123")
    assert isinstance(res, SearchPage)
    assert len(res.items) == 0
    assert res.has_next_page is False


def test_popular_and_latest(connector):
    """Test popular and latest updates listings."""
    pop = connector.get_popular()
    assert len(pop.items) >= 3

    latest = connector.get_latest()
    assert len(latest.items) >= 3
    # Tears of Steel (2012) should appear before Big Buck Bunny (2008)
    titles = [it.title for it in latest.items]
    assert titles.index("Tears of Steel") < titles.index("Big Buck Bunny")


def test_get_details(connector):
    """Test normalized metadata retrieval."""
    details = connector.get_details("https://download.blender.org/demo/movies/BBB/")
    assert isinstance(details, AnimeDetails)
    assert details.title == "Big Buck Bunny"
    assert "Animation" in details.genres
    assert details.release_year == 2008


def test_get_episodes(connector):
    """Test episode listing."""
    eps = connector.get_episodes("https://download.blender.org/demo/movies/BBB/")
    assert len(eps) == 2
    assert eps[0].name == "Full Movie (1080p)"
    assert eps[0].episode_number == 1.0


def test_get_video_streams_and_subtitles(connector):
    """Test video stream extraction and subtitle tracks."""
    streams = connector.get_video_streams("https://download.blender.org/demo/movies/BBB/ep1")
    assert len(streams) >= 2
    qualities = [s.quality for s in streams]
    assert "1080p" in qualities
    assert "720p" in qualities

    # Check subtitles
    first_stream = streams[0]
    assert len(first_stream.subtitles) >= 2
    langs = [sub.lang for sub in first_stream.subtitles]
    assert "English" in langs
    assert "Spanish" in langs


def test_content_unavailable_raises_proper_error(connector):
    """Test requesting non-existent media raises ContentUnavailableError."""
    with pytest.raises(ContentUnavailableError) as exc_info:
        connector.get_details("https://non-existent-url.org")
    assert exc_info.value.connector_id == "openmovies"


def test_unsupported_capability_raises_error(connector):
    """Test invoking capability not declared raises UnsupportedCapabilityError."""
    connector.capabilities.remove("search")
    with pytest.raises(UnsupportedCapabilityError) as exc_info:
        connector.search("test")
    assert exc_info.value.capability == "search"


def test_health_check_healthy(connector):
    """Test health check execution reports healthy on valid catalog."""
    res = connector.health_check()
    assert isinstance(res, HealthCheckResult)
    assert res.is_healthy is True
    assert res.latency_ms > 0
    assert "Healthy" in res.message


def test_malformed_json_raises_parse_error(tmp_path):
    """Test that a malformed JSON catalog payload triggers ParseError."""
    bad_fixture = tmp_path / "bad_catalog.json"
    bad_fixture.write_text("{ this is not valid json : [", encoding="utf-8")
    broken_conn = OpenMoviesTestConnector(fixture_path=bad_fixture)
    with pytest.raises(ParseError):
        broken_conn.search("test")


def test_source_id_matches_aniyomi_specification():
    """Verify source ID matches Aniyomi generateId(name.lowercase(), lang, versionId) formula."""
    import hashlib
    import struct
    import json

    manifest_path = Path(__file__).parent.parent / "src" / "en" / "openmovies" / "manifest.json"
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    src = manifest["sources"][0]
    expected_key = f"{src['name'].lower()}/{src['lang']}/1".encode("utf-8")
    digest = hashlib.md5(expected_key).digest()
    expected_id = struct.unpack(">q", digest[:8])[0] & 0x7FFFFFFFFFFFFFFF

    assert expected_id == 2462941301767738396
    assert src["id"] == expected_id


def test_all_catalog_movies_have_valid_metadata(connector):
    """Verify all items in catalog have valid titles, genres, release years, episodes, and streams."""
    items = connector._load_catalog()
    assert len(items) >= 6

    for item in items:
        assert item["id"]
        assert item["title"]
        assert item["url"].startswith("https://") or item["url"].startswith("/")
        assert len(item.get("genres", [])) >= 1
        assert item.get("releaseYear", 0) >= 2000
        assert item.get("status") in ["COMPLETED", "ONGOING"]
        assert len(item.get("episodes", [])) >= 1

        for ep in item["episodes"]:
            assert ep["id"]
            assert ep["title"]
            assert ep["videoUrl"]
            assert len(ep.get("streams", [])) >= 1
            for stream in ep["streams"]:
                assert stream["quality"]
                assert stream["url"].startswith("https://") or stream["url"].startswith("http://")


def test_apk_contains_openmovies_and_configurable_interface():
    """Verify compiled APK contains OpenMovies class and ConfigurableAnimeSource reference in DEX."""
    import zipfile

    apk_path = Path(__file__).parent.parent / "repo" / "apk" / "aniyomi-en.openmovies-v14.1.apk"
    assert apk_path.exists(), "Compiled APK must exist in repo/apk/"

    with zipfile.ZipFile(apk_path) as z:
        all_dex_data = b"".join(z.read(f) for f in z.namelist() if f.endswith(".dex"))

    assert b"Leu/kanade/tachiyomi/animeextension/en/openmovies/OpenMovies;" in all_dex_data
    assert b"ConfigurableAnimeSource" in all_dex_data

