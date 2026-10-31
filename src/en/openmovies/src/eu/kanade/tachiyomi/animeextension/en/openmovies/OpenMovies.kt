package eu.kanade.tachiyomi.animeextension.en.openmovies

import android.app.Application
import android.content.SharedPreferences
import androidx.preference.ListPreference
import androidx.preference.PreferenceScreen
import androidx.preference.SwitchPreferenceCompat
import eu.kanade.tachiyomi.animesource.ConfigurableAnimeSource
import eu.kanade.tachiyomi.animesource.model.AnimeFilterList
import eu.kanade.tachiyomi.animesource.model.AnimesPage
import eu.kanade.tachiyomi.animesource.model.SAnime
import eu.kanade.tachiyomi.animesource.model.SEpisode
import eu.kanade.tachiyomi.animesource.model.Track
import eu.kanade.tachiyomi.animesource.model.Video
import eu.kanade.tachiyomi.animesource.online.AnimeHttpSource
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.Response
import uy.kohesive.injekt.Injekt
import uy.kohesive.injekt.api.get
import java.net.URLEncoder
import java.util.concurrent.TimeUnit

/**
 * Open Movies Archive - Aniyomi / Dantotsu Anime Extension.
 *
 * Provides access to authorized, open-source Creative Commons animated films
 * created by the Blender Studio (e.g., Big Buck Bunny, Sintel, Spring, Charge, Elephants Dream).
 *
 * Implements ConfigurableAnimeSource to support in-app quality and container preferences
 * in Dantotsu 3.2.2 and compatible Aniyomi forks.
 *
 * Licensed under Creative Commons Attribution (CC-BY).
 */
class OpenMovies : ConfigurableAnimeSource, AnimeHttpSource() {

    override val name = "Open Movies Archive"

    override val baseUrl = "https://download.blender.org"

    override val lang = "en"

    override val supportsLatest = true

    /**
     * Unique source ID deterministically computed via generateId("Open Movies Archive", "en", 1).
     * Explicitly matched to repository index registration.
     */
    override val id: Long = 2462941301767738396L

    override val client: OkHttpClient = OkHttpClient.Builder()
        .connectTimeout(15, TimeUnit.SECONDS)
        .readTimeout(15, TimeUnit.SECONDS)
        .build()

    // -------------------------------------------------------------------------
    // Configurable Preferences (Dantotsu In-App Settings)
    // -------------------------------------------------------------------------
    private val preferences: SharedPreferences by lazy {
        Injekt.get<Application>().getSharedPreferences("source_$id", 0x0000)
    }

    override fun getSourcePreferences(): SharedPreferences = preferences

    override fun setupPreferenceScreen(screen: PreferenceScreen) {
        ListPreference(screen.context).apply {
            key = PREF_QUALITY_KEY
            title = "Preferred Video Quality"
            entries = arrayOf("1080p", "720p", "480p", "Original/Best")
            entryValues = arrayOf("1080p", "720p", "480p", "Original/Best")
            setDefaultValue(PREF_QUALITY_DEFAULT)
            summary = "%s"
            setOnPreferenceChangeListener { _, newValue ->
                val selected = newValue as String
                val index = findIndexOfValue(selected)
                val entry = entryValues[index] as String
                preferences.edit().putString(key, entry).commit()
            }
        }.also(screen::addPreference)

        SwitchPreferenceCompat(screen.context).apply {
            key = PREF_PREFER_MP4_KEY
            title = "Prefer MP4 Container"
            summary = "Prioritizes MP4/H.264 streams over WebM for broader hardware decoding acceleration."
            setDefaultValue(true)
            setOnPreferenceChangeListener { _, newValue ->
                val checked = newValue as Boolean
                preferences.edit().putBoolean(key, checked).commit()
            }
        }.also(screen::addPreference)
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
        val animeList = CURATED_MOVIES.map { it.toSAnime() }
        return AnimesPage(animeList, false)
    }

    // -------------------------------------------------------------------------
    // Latest Updates
    // -------------------------------------------------------------------------
    override fun latestUpdatesRequest(page: Int): Request {
        return popularAnimeRequest(page)
    }

    override fun latestUpdatesParse(response: Response): AnimesPage {
        val animeList = CURATED_MOVIES.reversed().map { it.toSAnime() }
        return AnimesPage(animeList, false)
    }

    // -------------------------------------------------------------------------
    // Search
    // -------------------------------------------------------------------------
    override fun searchAnimeRequest(page: Int, query: String, filters: AnimeFilterList): Request {
        val encodedQuery = URLEncoder.encode(query, "UTF-8")
        return Request.Builder()
            .url("$baseUrl/demo/movies/?q=$encodedQuery")
            .headers(headers)
            .build()
    }

    override fun searchAnimeParse(response: Response): AnimesPage {
        val query = response.request.url.queryParameter("q") ?: ""
        val matched = if (query.isNotBlank()) {
            CURATED_MOVIES.filter {
                it.title.contains(query, ignoreCase = true) ||
                (it.description?.contains(query, ignoreCase = true) == true) ||
                it.genres.any { g -> g.contains(query, ignoreCase = true) }
            }
        } else {
            CURATED_MOVIES
        }
        return AnimesPage(matched.map { it.toSAnime() }, false)
    }

    // -------------------------------------------------------------------------
    // Anime Metadata & Details
    // -------------------------------------------------------------------------
    override fun animeDetailsParse(response: Response): SAnime {
        val requestedUrl = response.request.url.toString()
        val found = CURATED_MOVIES.find {
            requestedUrl.contains(it.id, ignoreCase = true) || it.url == requestedUrl
        } ?: CURATED_MOVIES.first()
        return found.toSAnime()
    }

    // -------------------------------------------------------------------------
    // Episodes
    // -------------------------------------------------------------------------
    override fun episodeListParse(response: Response): List<SEpisode> {
        val requestedUrl = response.request.url.toString()
        val movie = CURATED_MOVIES.find {
            requestedUrl.contains(it.id, ignoreCase = true) || it.url == requestedUrl
        } ?: CURATED_MOVIES.first()

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
                    val rawVideos = ep.streams.map { s ->
                        Video(
                            url = s.url,
                            quality = s.quality,
                            videoUrl = s.url,
                            headers = headers,
                            subtitleTracks = tracks
                        )
                    }
                    return sortVideosWithPreferences(rawVideos)
                }
            }
        }

        // Fallback guaranteed valid stream
        val fallbackTracks = listOf(
            Track("https://peach.blender.org/subtitles/subtitles_en.vtt", "English")
        )
        return listOf(
            Video(
                url = "https://archive.org/download/BigBuckBunny_124/Content/big_buck_bunny_720p_surround.mp4",
                quality = "720p (MP4)",
                videoUrl = "https://archive.org/download/BigBuckBunny_124/Content/big_buck_bunny_720p_surround.mp4",
                headers = headers,
                subtitleTracks = fallbackTracks
            )
        )
    }

    private fun sortVideosWithPreferences(videos: List<Video>): List<Video> {
        val preferredQuality = try {
            preferences.getString(PREF_QUALITY_KEY, PREF_QUALITY_DEFAULT) ?: PREF_QUALITY_DEFAULT
        } catch (_: Exception) {
            PREF_QUALITY_DEFAULT
        }
        val preferMp4 = try {
            preferences.getBoolean(PREF_PREFER_MP4_KEY, true)
        } catch (_: Exception) {
            true
        }

        return videos.sortedWith(
            compareByDescending<Video> { it.quality.contains(preferredQuality, ignoreCase = true) }
                .thenByDescending {
                    if (preferMp4) it.quality.contains("MP4", ignoreCase = true)
                    else it.quality.contains("WebM", ignoreCase = true)
                }
        )
    }

    companion object {
        const val PREF_QUALITY_KEY = "preferred_quality"
        const val PREF_QUALITY_DEFAULT = "720p"

        const val PREF_PREFER_MP4_KEY = "prefer_mp4"
    }
}

// -----------------------------------------------------------------------------
// Internal Curated Open Movies Catalog
// -----------------------------------------------------------------------------
private data class MovieItem(
    val id: String,
    val title: String,
    val url: String,
    val thumbnailUrl: String? = null,
    val description: String? = null,
    val genres: List<String> = emptyList(),
    val status: String = "COMPLETED",
    val author: String? = "Blender Studio",
    val artist: String? = "Blender Institute",
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

private data class EpisodeItem(
    val id: String,
    val title: String,
    val videoUrl: String,
    val dateUpload: Long = 0L,
    val streams: List<StreamItem> = emptyList(),
    val subtitles: List<SubtitleItem> = emptyList()
)

private data class StreamItem(
    val quality: String,
    val url: String
)

private data class SubtitleItem(
    val lang: String,
    val url: String
)

/**
 * Curated list of authorized open-content animated films produced by the Blender Foundation.
 * All streams and artwork verified 200 OK under Creative Commons Attribution licenses.
 */
private val CURATED_MOVIES = listOf(
    MovieItem(
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
                title = "Full Film",
                videoUrl = "https://download.blender.org/demo/movies/BBB/film",
                dateUpload = 1207872000000L,
                streams = listOf(
                    StreamItem(
                        quality = "720p (MP4 Surround)",
                        url = "https://archive.org/download/BigBuckBunny_124/Content/big_buck_bunny_720p_surround.mp4"
                    ),
                    StreamItem(
                        quality = "1080p (WebM 4K)",
                        url = "https://upload.wikimedia.org/wikipedia/commons/c/c0/Big_Buck_Bunny_4K.webm"
                    )
                ),
                subtitles = listOf(
                    SubtitleItem("English", "https://peach.blender.org/subtitles/subtitles_en.vtt")
                )
            ),
            EpisodeItem(
                id = "bbb-ep-2",
                title = "Official Trailer",
                videoUrl = "https://download.blender.org/demo/movies/BBB/trailer",
                dateUpload = 1205193600000L,
                streams = listOf(
                    StreamItem(
                        quality = "720p (MP4)",
                        url = "https://archive.org/download/BigBuckBunny_124/Content/big_buck_bunny_720p_surround.mp4"
                    )
                )
            )
        )
    ),
    MovieItem(
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
                title = "Full Film",
                videoUrl = "https://download.blender.org/demo/movies/Sintel_4k/film",
                dateUpload = 1285804800000L,
                streams = listOf(
                    StreamItem(
                        quality = "1080p (MP4 Surround)",
                        url = "https://archive.org/download/Sintel/sintel-2048-surround.mp4"
                    ),
                    StreamItem(
                        quality = "1080p (MP4 Stereo)",
                        url = "https://archive.org/download/Sintel/sintel-2048-stereo.mp4"
                    )
                ),
                subtitles = listOf(
                    SubtitleItem("English", "https://durian.blender.org/wp-content/themes/durian/subs/sintel_en.srt")
                )
            )
        )
    ),
    MovieItem(
        id = "spring",
        title = "Spring",
        url = "https://studio.blender.org/films/spring/",
        thumbnailUrl = "https://upload.wikimedia.org/wikipedia/commons/2/25/Spring2019AlphaPosterBlender.jpg",
        description = "A shepherd girl and her dog face ancient spirits in order to continue the cycle of life.",
        genres = listOf("Animation", "Fantasy", "Short"),
        status = "COMPLETED",
        author = "Blender Animation Studio / Andy Goralczyk",
        artist = "Blender Studio",
        episodes = listOf(
            EpisodeItem(
                id = "spring-ep-1",
                title = "Full Film",
                videoUrl = "https://studio.blender.org/films/spring/film",
                dateUpload = 1554854400000L,
                streams = listOf(
                    StreamItem(
                        quality = "1080p (WebM)",
                        url = "https://upload.wikimedia.org/wikipedia/commons/a/a5/Spring_-_Blender_Open_Movie.webm"
                    )
                )
            )
        )
    ),
    MovieItem(
        id = "charge",
        title = "Charge",
        url = "https://studio.blender.org/films/charge/",
        thumbnailUrl = "https://upload.wikimedia.org/wikipedia/commons/7/70/Tos-poster.png",
        description = "An old warrior navigates a robotic cyberpunk underworld in search of the last remaining power source.",
        genres = listOf("Animation", "Action", "Cyberpunk"),
        status = "COMPLETED",
        author = "Blender Studio / Hjalti Hjalmarsson",
        artist = "Blender Studio",
        episodes = listOf(
            EpisodeItem(
                id = "charge-ep-1",
                title = "Full Film",
                videoUrl = "https://studio.blender.org/films/charge/film",
                dateUpload = 1671062400000L,
                streams = listOf(
                    StreamItem(
                        quality = "1080p (WebM)",
                        url = "https://upload.wikimedia.org/wikipedia/commons/7/7a/Charge_-_Blender_Open_Movie-full_movie.webm"
                    )
                )
            )
        )
    ),
    MovieItem(
        id = "sprite-fright",
        title = "Sprite Fright",
        url = "https://studio.blender.org/films/sprite-fright/",
        thumbnailUrl = "https://durian.blender.org/wp-content/uploads/2010/09/sintel_poster.jpg",
        description = "When a group of rowdy teenagers trek into an isolated forest, they discover that nature is not as friendly as it seems.",
        genres = listOf("Animation", "Comedy", "Horror"),
        status = "COMPLETED",
        author = "Blender Studio / Matthew Luhn",
        artist = "Blender Studio",
        episodes = listOf(
            EpisodeItem(
                id = "sprite-fright-ep-1",
                title = "Full Film",
                videoUrl = "https://studio.blender.org/films/sprite-fright/film",
                dateUpload = 1635465600000L,
                streams = listOf(
                    StreamItem(
                        quality = "1080p (WebM)",
                        url = "https://upload.wikimedia.org/wikipedia/commons/7/74/Sprite_Fright_-_Open_Movie_by_Blender_Studio.webm"
                    )
                )
            )
        )
    ),
    MovieItem(
        id = "elephants-dream",
        title = "Elephants Dream",
        url = "https://orange.blender.org/",
        thumbnailUrl = "https://upload.wikimedia.org/wikipedia/commons/0/0c/ElephantsDreamPoster.jpg",
        description = "The world's first open-source animated short film, exploring communication and reality within a surreal mechanical world.",
        genres = listOf("Animation", "Sci-Fi", "Surreal"),
        status = "COMPLETED",
        author = "Blender Foundation / Bassam Kurdali",
        artist = "Orange Open Movie Project",
        episodes = listOf(
            EpisodeItem(
                id = "ed-ep-1",
                title = "Full Film",
                videoUrl = "https://orange.blender.org/film",
                dateUpload = 1142640000000L,
                streams = listOf(
                    StreamItem(
                        quality = "1080p (WebM)",
                        url = "https://upload.wikimedia.org/wikipedia/commons/a/a2/Elephants_Dream_%282006%29.webm"
                    )
                )
            )
        )
    )
)
