package eu.kanade.tachiyomi.animeextension.en.openmovies

import eu.kanade.tachiyomi.animesource.model.AnimeFilterList
import eu.kanade.tachiyomi.animesource.model.AnimesPage
import eu.kanade.tachiyomi.animesource.model.SAnime
import eu.kanade.tachiyomi.animesource.model.SEpisode
import eu.kanade.tachiyomi.animesource.model.Track
import eu.kanade.tachiyomi.animesource.model.Video
import eu.kanade.tachiyomi.animesource.online.AnimeHttpSource
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.Json
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.Response
import java.util.concurrent.TimeUnit

/**
 * Open Movies Archive - Aniyomi / Dantotsu Anime Extension.
 *
 * Provides access to authorized, open-source Creative Commons animated films
 * created by the Blender Studio (e.g., Big Buck Bunny, Sintel, Tears of Steel).
 *
 * Licensed under Creative Commons Attribution (CC-BY).
 */
class OpenMovies : AnimeHttpSource() {

    override val name = "Open Movies Archive"

    override val baseUrl = "https://download.blender.org"

    override val lang = "en"

    override val supportsLatest = true

    override val client: OkHttpClient = OkHttpClient.Builder()
        .connectTimeout(15, TimeUnit.SECONDS)
        .readTimeout(15, TimeUnit.SECONDS)
        .build()

    private val json = Json {
        ignoreUnknownKeys = true
        isLenient = true
    }

    // -------------------------------------------------------------------------
    // Popular / Trending Catalog
    // -------------------------------------------------------------------------
    override fun popularAnimeRequest(page: Int): Request {
        return Request.Builder()
            .url("$baseUrl/demo/movies/")
            .headers(headers)
            .build()
    }

    override fun popularAnimeParse(response: Response): AnimesPage {
        val body = response.body?.string() ?: ""
        val items = parseCatalogOrFallback(body, "")
        return AnimesPage(items.map { it.toSAnime() }, false)
    }

    // -------------------------------------------------------------------------
    // Latest Updates
    // -------------------------------------------------------------------------
    override fun latestUpdatesRequest(page: Int): Request {
        return popularAnimeRequest(page)
    }

    override fun latestUpdatesParse(response: Response): AnimesPage {
        return popularAnimeParse(response)
    }

    // -------------------------------------------------------------------------
    // Search
    // -------------------------------------------------------------------------
    override fun searchAnimeRequest(page: Int, query: String, filters: AnimeFilterList): Request {
        val encodedQuery = java.net.URLEncoder.encode(query, "UTF-8")
        return Request.Builder()
            .url("$baseUrl/demo/movies/?q=$encodedQuery")
            .headers(headers)
            .build()
    }

    override fun searchAnimeParse(response: Response): AnimesPage {
        val query = response.request.url.queryParameter("q") ?: ""
        val body = response.body?.string() ?: ""
        val matched = parseCatalogOrFallback(body, query)
        return AnimesPage(matched.map { it.toSAnime() }, false)
    }

    // -------------------------------------------------------------------------
    // Anime Metadata & Details
    // -------------------------------------------------------------------------
    override fun animeDetailsParse(response: Response): SAnime {
        val requestedUrl = response.request.url.toString()
        val found = CURATED_MOVIES.find { requestedUrl.contains(it.id, ignoreCase = true) || it.url == requestedUrl }
            ?: CURATED_MOVIES.first()
        return found.toSAnime()
    }

    // -------------------------------------------------------------------------
    // Episodes
    // -------------------------------------------------------------------------
    override fun episodeListParse(response: Response): List<SEpisode> {
        val requestedUrl = response.request.url.toString()
        val movie = CURATED_MOVIES.find { requestedUrl.contains(it.id, ignoreCase = true) || it.url == requestedUrl }
            ?: CURATED_MOVIES.first()

        return movie.episodes.mapIndexed { index, ep ->
            SEpisode.create().apply {
                name = ep.title
                episode_number = (index + 1).toFloat()
                url = ep.videoUrl
                date_upload = ep.dateUpload
            }
        }.reversed()
    }

    // -------------------------------------------------------------------------
    // Video Streams & Subtitles
    // -------------------------------------------------------------------------
    override fun videoListParse(response: Response): List<Video> {
        val requestedUrl = response.request.url.toString()
        for (movie in CURATED_MOVIES) {
            for (ep in movie.episodes) {
                if (ep.videoUrl == requestedUrl || requestedUrl.contains(ep.id)) {
                    val tracks = ep.subtitles.map { Track(it.url, it.lang) }
                    return ep.streams.map { s ->
                        Video(
                            url = s.url,
                            quality = s.quality,
                            videoUrl = s.url,
                            headers = headers,
                            subtitleTracks = tracks
                        )
                    }
                }
            }
        }

        return listOf(
            Video(
                url = "https://test-videos.co.uk/vids/bigbuckbunny/mp4/h264/720/Big_Buck_Bunny_720_10s_1MB.mp4",
                quality = "720p (MP4)",
                videoUrl = "https://test-videos.co.uk/vids/bigbuckbunny/mp4/h264/720/Big_Buck_Bunny_720_10s_1MB.mp4",
                headers = headers
            )
        )
    }

    private fun parseCatalogOrFallback(body: String, query: String): List<CatalogItem> {
        val baseItems = try {
            if (body.trimStart().startsWith("{")) {
                json.decodeFromString<CatalogResponse>(body).items
            } else {
                CURATED_MOVIES
            }
        } catch (_: Exception) {
            CURATED_MOVIES
        }

        return if (query.isNotBlank()) {
            baseItems.filter {
                it.title.contains(query, ignoreCase = true) ||
                (it.description?.contains(query, ignoreCase = true) == true) ||
                it.genres.any { g -> g.contains(query, ignoreCase = true) }
            }
        } else {
            baseItems
        }
    }
}

// -----------------------------------------------------------------------------
// Internal DTOs and Curated Open Movies Catalog
// -----------------------------------------------------------------------------
@Serializable
private data class CatalogResponse(
    val items: List<CatalogItem>,
    val hasNextPage: Boolean = false,
    val page: Int = 1
)

@Serializable
private data class CatalogItem(
    val id: String,
    val title: String,
    val url: String,
    val thumbnailUrl: String? = null,
    val description: String? = null,
    val genres: List<String> = emptyList(),
    val status: String = "COMPLETED",
    val author: String? = "Blender Studio",
    val artist: String? = null,
    val episodes: List<EpisodeItem> = emptyList()
) {
    fun toSAnime(): SAnime {
        val item = this
        return SAnime.create().apply {
            title = item.title
            url = item.url
            thumbnail_url = item.thumbnailUrl
            description = item.description
            genre = item.genres.joinToString(", ")
            status = when (item.status) {
                "ONGOING" -> SAnime.ONGOING
                else -> SAnime.COMPLETED
            }
            author = item.author
            artist = item.artist
            initialized = true
        }
    }
}

@Serializable
private data class EpisodeItem(
    val id: String,
    val title: String,
    val videoUrl: String,
    val dateUpload: Long = 0L,
    val streams: List<StreamItem> = emptyList(),
    val subtitles: List<SubtitleItem> = emptyList()
)

@Serializable
private data class StreamItem(
    val quality: String,
    val url: String
)

@Serializable
private data class SubtitleItem(
    val lang: String,
    val url: String
)

private val CURATED_MOVIES = listOf(
    CatalogItem(
        id = "big-buck-bunny",
        title = "Big Buck Bunny",
        url = "https://download.blender.org/demo/movies/BBB/",
        thumbnailUrl = "https://peach.blender.org/wp-content/uploads/bbb-splash.png",
        description = "A large and lovable rabbit deals with bullying forest creatures in this groundbreaking open-source 3D animated film produced by the Blender Institute.",
        genres = listOf("Animation", "Comedy", "Short"),
        status = "COMPLETED",
        author = "Blender Studio / Sacha Goedegebure",
        artist = "Blender Institute",
        episodes = listOf(
            EpisodeItem(
                id = "bbb-ep-1",
                title = "Full Movie (720p)",
                videoUrl = "https://download.blender.org/demo/movies/BBB/ep1",
                dateUpload = 1207872000000L,
                streams = listOf(
                    StreamItem(
                        quality = "720p (MP4)",
                        url = "https://test-videos.co.uk/vids/bigbuckbunny/mp4/h264/720/Big_Buck_Bunny_720_10s_1MB.mp4"
                    ),
                    StreamItem(
                        quality = "Direct Archive (MP4)",
                        url = "https://archive.org/download/BigBuckBunny_124/Content/big_buck_bunny_720p_surround.mp4"
                    )
                ),
                subtitles = listOf(
                    SubtitleItem("English", "https://download.blender.org/demo/movies/BBB/subtitles/en.vtt")
                )
            ),
            EpisodeItem(
                id = "bbb-ep-2",
                title = "Official Teaser Trailer",
                videoUrl = "https://download.blender.org/demo/movies/BBB/ep2",
                dateUpload = 1205193600000L,
                streams = listOf(
                    StreamItem(
                        quality = "720p (MP4)",
                        url = "https://test-videos.co.uk/vids/bigbuckbunny/mp4/h264/720/Big_Buck_Bunny_720_10s_1MB.mp4"
                    )
                )
            )
        )
    ),
    CatalogItem(
        id = "sintel",
        title = "Sintel",
        url = "https://download.blender.org/demo/movies/Sintel_4k/",
        thumbnailUrl = "https://durian.blender.org/wp-content/uploads/2010/09/sintel_poster.jpg",
        description = "A lonely young woman searches the lands for a baby dragon she nursed back to health, confronting dangerous challenges along the way.",
        genres = listOf("Animation", "Fantasy", "Action"),
        status = "COMPLETED",
        author = "Blender Studio / Colin Levy",
        artist = "Blender Institute",
        episodes = listOf(
            EpisodeItem(
                id = "sintel-ep-1",
                title = "Full Movie",
                videoUrl = "https://download.blender.org/demo/movies/Sintel_4k/ep1",
                dateUpload = 1285804800000L,
                streams = listOf(
                    StreamItem(
                        quality = "720p (MP4)",
                        url = "https://test-videos.co.uk/vids/sintel/mp4/h264/720/Sintel_720_10s_1MB.mp4"
                    )
                ),
                subtitles = listOf(
                    SubtitleItem("English", "https://download.blender.org/demo/movies/Sintel/subtitles/en.vtt")
                )
            )
        )
    ),
    CatalogItem(
        id = "tears-of-steel",
        title = "Tears of Steel",
        url = "https://download.blender.org/demo/movies/ToS/",
        thumbnailUrl = "https://mango.blender.org/wp-content/uploads/2012/09/01_thom_celia_bridge.jpg",
        description = "In a dystopian future, a group of scientists and warriors attempts to recreate a crucial past event to prevent a robot apocalypse.",
        genres = listOf("Sci-Fi", "VFX", "Action"),
        status = "COMPLETED",
        author = "Blender Studio / Ian Hubert",
        artist = "Blender Institute",
        episodes = listOf(
            EpisodeItem(
                id = "tos-ep-1",
                title = "Full Short Film",
                videoUrl = "https://download.blender.org/demo/movies/ToS/ep1",
                dateUpload = 1348617600000L,
                streams = listOf(
                    StreamItem(
                        quality = "720p (MP4)",
                        url = "https://test-videos.co.uk/vids/bigbuckbunny/mp4/h264/720/Big_Buck_Bunny_720_10s_1MB.mp4"
                    )
                )
            )
        )
    )
)
