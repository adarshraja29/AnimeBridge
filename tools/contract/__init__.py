"""
AnimeBridge Contract and Model Definition (Tooling & Automated Verification Harness)
Mirrors Aniyomi/Dantotsu runtime interfaces for local test isolation, contract validation, and mock verification.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Set, Any
from abc import ABC, abstractmethod
import time
from datetime import datetime, timezone


class ConnectorError(Exception):
    """Base exception for all AnimeBridge connector operations."""
    def __init__(self, message: str, connector_id: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(f"[{connector_id}] {message}")
        self.message = message
        self.connector_id = connector_id
        self.details = details or {}


class NetworkError(ConnectorError):
    """Raised when an HTTP request fails, times out, or encounters DNS/connection issues."""
    def __init__(self, message: str, connector_id: str, status_code: Optional[int] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, connector_id, details)
        self.status_code = status_code


class TimeoutError(NetworkError):
    """Raised when an external request exceeds the configured deadline."""
    pass


class ParseError(ConnectorError):
    """Raised when the remote source returns malformed JSON, invalid HTML, or unexpected types."""
    def __init__(self, message: str, connector_id: str, raw_payload: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, connector_id, details)
        self.raw_payload = raw_payload


class ContentUnavailableError(ConnectorError):
    """Raised when requested media, episode, or stream has been removed or is inaccessible."""
    def __init__(self, message: str, connector_id: str, content_id: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, connector_id, details)
        self.content_id = content_id


class UnsupportedCapabilityError(ConnectorError):
    """Raised when an operation is invoked that the connector does not declare or support."""
    def __init__(self, capability: str, connector_id: str):
        super().__init__(f"Connector does not support declared capability: '{capability}'", connector_id)
        self.capability = capability


@dataclass
class AnimeDetails:
    id: str
    title: str
    url: str
    thumbnail_url: Optional[str] = None
    description: Optional[str] = None
    genres: List[str] = field(default_factory=list)
    status: str = "COMPLETED"
    author: Optional[str] = None
    artist: Optional[str] = None
    release_year: Optional[int] = None
    extra_metadata: Dict[str, str] = field(default_factory=dict)


@dataclass
class Episode:
    id: str
    name: str
    episode_number: float
    url: str
    date_upload: Optional[int] = None
    scanlator: Optional[str] = None


@dataclass
class SubtitleTrack:
    url: str
    lang: str


@dataclass
class VideoStream:
    url: str
    quality: str
    video_url: str
    headers: Dict[str, str] = field(default_factory=dict)
    subtitles: List[SubtitleTrack] = field(default_factory=list)


@dataclass
class SearchResult:
    id: str
    title: str
    url: str
    thumbnail_url: Optional[str] = None


@dataclass
class SearchPage:
    items: List[SearchResult]
    has_next_page: bool = False
    page: int = 1


@dataclass
class HealthCheckResult:
    connector_id: str
    is_healthy: bool
    latency_ms: float
    message: str
    timestamp: str


class BaseConnector(ABC):
    def __init__(
        self,
        connector_id: str,
        name: str,
        base_url: str,
        language: str,
        capabilities: Set[str],
        timeout_seconds: float = 10.0
    ):
        self.connector_id = connector_id
        self.name = name
        self.base_url = base_url.rstrip("/")
        self.language = language
        self.capabilities = set(capabilities)
        self.timeout_seconds = timeout_seconds

    def assert_capability(self, capability: str) -> None:
        if capability not in self.capabilities:
            raise UnsupportedCapabilityError(capability, self.connector_id)

    @abstractmethod
    def search(self, query: str, page: int = 1) -> SearchPage:
        pass

    @abstractmethod
    def get_popular(self, page: int = 1) -> SearchPage:
        pass

    @abstractmethod
    def get_latest(self, page: int = 1) -> SearchPage:
        pass

    @abstractmethod
    def get_details(self, content_url: str) -> AnimeDetails:
        pass

    @abstractmethod
    def get_episodes(self, content_url: str) -> List[Episode]:
        pass

    @abstractmethod
    def get_video_streams(self, episode_url: str) -> List[VideoStream]:
        pass

    def health_check(self) -> HealthCheckResult:
        start = time.perf_counter()
        try:
            self.assert_capability("health_check")
            if "popular" in self.capabilities:
                res = self.get_popular(page=1)
                latency = (time.perf_counter() - start) * 1000
                return HealthCheckResult(
                    connector_id=self.connector_id,
                    is_healthy=True,
                    latency_ms=round(latency, 2),
                    message=f"Healthy: retrieved {len(res.items)} items in page 1",
                    timestamp=datetime.now(timezone.utc).isoformat()
                )
            latency = (time.perf_counter() - start) * 1000
            return HealthCheckResult(
                connector_id=self.connector_id,
                is_healthy=True,
                latency_ms=round(latency, 2),
                message="Healthy: connector responsive",
                timestamp=datetime.now(timezone.utc).isoformat()
            )
        except Exception as e:
            latency = (time.perf_counter() - start) * 1000
            return HealthCheckResult(
                connector_id=self.connector_id,
                is_healthy=False,
                latency_ms=round(latency, 2),
                message=f"Unhealthy: {str(e)}",
                timestamp=datetime.now(timezone.utc).isoformat()
            )
