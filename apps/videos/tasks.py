from celery import shared_task


@shared_task(bind=True, max_retries=3)
def import_youtube_playlist(self, playlist_import_id):
    """
    Async task: fetch videos from a YouTube playlist and create Video objects.
    Requires YOUTUBE_API_KEY in settings.
    """
    import requests
    from django.conf import settings
    from apps.videos.models import Video, YouTubePlaylistImport

    try:
        pl = YouTubePlaylistImport.objects.select_related("course", "lesson").get(
            id=playlist_import_id
        )
        pl.status = YouTubePlaylistImport.ImportStatus.PROCESSING
        pl.save(update_fields=["status"])

        api_key = getattr(settings, "YOUTUBE_API_KEY", "")
        if not api_key:
            pl.status = YouTubePlaylistImport.ImportStatus.FAILED
            pl.error_message = "YOUTUBE_API_KEY not configured."
            pl.save(update_fields=["status", "error_message"])
            return

        # Extract playlist ID from URL
        import re
        match = re.search(r"list=([a-zA-Z0-9_-]+)", pl.playlist_url)
        if not match:
            pl.status = YouTubePlaylistImport.ImportStatus.FAILED
            pl.error_message = "Could not extract playlist ID from URL."
            pl.save(update_fields=["status", "error_message"])
            return

        playlist_id = match.group(1)
        next_page = ""
        order = Video.objects.filter(lesson=pl.lesson).count()
        count = 0

        while True:
            url = (
                f"https://www.googleapis.com/youtube/v3/playlistItems"
                f"?part=snippet&maxResults=50&playlistId={playlist_id}"
                f"&key={api_key}&pageToken={next_page}"
            )
            resp = requests.get(url, timeout=30)
            data = resp.json()

            for item in data.get("items", []):
                snippet = item["snippet"]
                yt_id = snippet["resourceId"]["videoId"]
                Video.objects.create(
                    lesson=pl.lesson,
                    course=pl.course,
                    title=snippet.get("title", "Untitled"),
                    description=snippet.get("description", "")[:500],
                    order=order,
                    source_type=Video.SourceType.YOUTUBE,
                    youtube_id=yt_id,
                    thumbnail=f"https://img.youtube.com/vi/{yt_id}/hqdefault.jpg",
                )
                order += 1
                count += 1

            next_page = data.get("nextPageToken", "")
            if not next_page:
                break

        pl.videos_imported = count
        pl.status = YouTubePlaylistImport.ImportStatus.COMPLETED
        pl.save(update_fields=["status", "videos_imported"])

    except Exception as exc:
        YouTubePlaylistImport.objects.filter(id=playlist_import_id).update(
            status=YouTubePlaylistImport.ImportStatus.FAILED,
            error_message=str(exc)[:500],
        )
        raise self.retry(exc=exc, countdown=120)
