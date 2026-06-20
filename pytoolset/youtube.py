from __future__ import annotations

import argparse
import logging
import os
import sys
from copy import deepcopy
from pathlib import Path


class YouTubeDownloader:
    """Download YouTube videos or whole playlists via ``yt-dlp``.

    Requires the optional ``yt-dlp`` dependency (``pip install
    pytoolset[youtube]``) and, for merging separate video and audio streams, the
    ``ffmpeg`` binary on the system ``PATH``.

    Args:
        output_dir: Directory to save downloads to. Created if it does not
            exist. Defaults to ``"./downloads"``.
        video_quality: A ``yt-dlp`` format string. Defaults to ``None``, which
            selects the best MP4 video plus M4A audio (falling back to the best
            available). Ignored when ``audio_only`` is ``True``.
        audio_only: Whether to download audio only. Defaults to ``False``.
        retries: Number of times to retry a failed download. Defaults to ``5``.
        concurrent_downloads: Number of fragments to download concurrently.
            Defaults to ``5``.
        subtitles: Whether to download subtitles. Defaults to ``False``.
        subtitles_langs: Subtitle languages to fetch. Defaults to ``None``,
            which is treated as ``["en"]``.
    """

    def __init__(
        self,
        output_dir: str | os.PathLike[str] = "./downloads",
        video_quality: str | None = None,
        audio_only: bool = False,
        retries: int = 5,
        concurrent_downloads: int = 5,
        subtitles: bool = False,
        subtitles_langs: list[str] | None = None,
    ) -> None:
        if subtitles_langs is None:
            subtitles_langs = ["en"]

        if audio_only:
            video_quality = "bestaudio/best"
            merge_format = None
        else:
            video_quality = (
                video_quality or "bestvideo[ext=mp4]+bestaudio[ext=m4a]/mp4"
            )
            merge_format = "mp4"

        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.default_opts: dict[str, object] = {
            "format": video_quality,
            "merge_output_format": merge_format,
            "download_archive": str(self.output_dir / "downloaded_videos.txt"),
            "ignoreerrors": True,
            "concurrent_fragment_downloads": concurrent_downloads,
            "retries": retries,
            "writethumbnail": True,
            "writesubtitles": subtitles,
            "subtitleslangs": subtitles_langs,
            "subtitlesformat": "best",
            "writeinfojson": True,
            "windowsfilenames": True,  # keep filenames safe across platforms
        }

        self._configure_logging()

    def _configure_logging(self) -> None:
        """Attach a file handler writing to ``download.log`` in the output dir.

        Uses a per-instance logger keyed by the log-file path, so messages from
        one downloader never leak into another instance's log file. Skips
        re-attaching if a handler for the same file already exists, so repeated
        instantiation does not duplicate log lines.
        """
        log_path = (self.output_dir / "download.log").resolve()
        self._logger = logging.getLogger(f"{__name__}.{log_path}")
        self._logger.setLevel(logging.INFO)
        self._logger.propagate = False
        already_attached = any(
            isinstance(handler, logging.FileHandler)
            and Path(getattr(handler, "baseFilename", "")) == log_path
            for handler in self._logger.handlers
        )
        if not already_attached:
            handler = logging.FileHandler(log_path)
            handler.setFormatter(
                logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
            )
            self._logger.addHandler(handler)

    def _get_info(self, url: str) -> dict | None:
        """Fetch metadata for a URL without downloading.

        Args:
            url: The video or playlist URL.

        Returns:
            The ``yt-dlp`` info dict, or ``None`` if extraction failed.
        """
        import yt_dlp

        try:
            with yt_dlp.YoutubeDL({"ignoreerrors": True}) as ydl:
                return ydl.extract_info(url, download=False)
        except Exception as exc:
            self._logger.error(f"Failed to extract info: {url} - {exc}")
            return None

    def download(
        self,
        url: str,
        start_index: int | None = None,
        end_index: int | None = None,
    ) -> None:
        """Download a single video or every video in a playlist.

        Args:
            url: The video or playlist URL.
            start_index: For playlists, the 1-based index of the first video to
                download. Defaults to ``None`` (start at the beginning).
            end_index: For playlists, the 1-based index of the last video to
                download, inclusive. Defaults to ``None`` (run to the end).
        """
        info = self._get_info(url)
        if not info:
            print("Could not retrieve video/playlist info.")
            return

        if "entries" in info:  # Playlist
            playlist_title = info.get("title", "Unnamed_Playlist")
            videos = info["entries"]
            print(f"Playlist detected: {playlist_title} ({len(videos)} videos)")

            for idx, entry in enumerate(videos, 1):
                if entry is None:
                    print(f"Skipping unavailable video {idx}")
                    continue
                if start_index and idx < start_index:
                    continue
                if end_index and idx > end_index:
                    break
                if not entry.get("title") or not entry.get("webpage_url"):
                    print(f"Skipping video {idx} due to missing metadata.")
                    continue
                title = entry["title"]
                video_url = entry["webpage_url"]
                print(f"Downloading video {idx}: {title}")
                self._run_download(video_url, playlist_title, idx)
        else:  # Single video
            print(f"Downloading single video: {info.get('title', 'Unknown')}")
            self._run_download(url)

    def _run_download(
        self,
        url: str,
        playlist_name: str | None = None,
        playlist_index: int | None = None,
    ) -> None:
        """Run a single download with the configured options.

        Args:
            url: The video URL to download.
            playlist_name: If given, the playlist sub-folder to save into.
                Defaults to ``None`` (save directly under the output dir).
            playlist_index: The 1-based position of the video within the
                playlist, used to prefix the filename. Defaults to ``None``.
        """
        import yt_dlp

        opts = deepcopy(self.default_opts)

        if playlist_name:
            folder = self.output_dir / playlist_name
            opts["outtmpl"] = str(folder / f"{playlist_index:02d} - %(title)s.%(ext)s")
            opts["noplaylist"] = False
        else:
            opts["outtmpl"] = str(self.output_dir / "%(title)s.%(ext)s")
            opts["noplaylist"] = True

        with yt_dlp.YoutubeDL(opts) as ydl:
            try:
                ydl.download([url])
            except Exception as exc:
                self._logger.error(f"Failed download: {url} - {exc}")
                print(f"Download failed for {url}\n   Reason: {exc}")


def _main(argv: list[str] | None = None) -> int:
    """Entry point for ``python -m pytoolset.youtube <url> [options]``.

    Args:
        argv: Argument list to parse. Defaults to ``None`` (uses ``sys.argv``).

    Returns:
        A process exit code: ``0`` on success, ``1`` if no URL was provided.
    """
    import shutil

    parser = argparse.ArgumentParser(
        prog="pytoolset.youtube",
        description="Download a YouTube video or playlist via yt-dlp.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("url", nargs="?", default=None,
                        help="YouTube video or playlist URL (prompted if omitted)")
    parser.add_argument("-o", "--output-dir", default="./downloads",
                        help="directory to save downloads")
    parser.add_argument("--quality", default=None,
                        help="yt-dlp video quality format string")
    parser.add_argument("--audio-only", action="store_true", help="download audio only")
    parser.add_argument("--subtitles", action="store_true", help="download subtitles")
    parser.add_argument("--subtitles-lang", default="en", help="subtitle language")
    parser.add_argument("--retries", type=int, default=5, help="download retry count")
    parser.add_argument("--concurrent-downloads", type=int, default=5,
                        help="number of concurrent fragment downloads")
    parser.add_argument("--start-index", type=int, default=None,
                        help="start index for playlist download")
    parser.add_argument("--end-index", type=int, default=None,
                        help="end index for playlist download")
    args = parser.parse_args(argv)

    url = args.url or input("Enter YouTube URL: ").strip()
    if not url:
        print("no URL provided", file=sys.stderr)
        return 1

    if not shutil.which("ffmpeg"):
        print(
            "warning: ffmpeg not found; audio and video may not merge properly",
            file=sys.stderr,
        )

    downloader = YouTubeDownloader(
        output_dir=args.output_dir,
        video_quality=args.quality,
        audio_only=args.audio_only,
        retries=args.retries,
        concurrent_downloads=args.concurrent_downloads,
        subtitles=args.subtitles,
        subtitles_langs=[args.subtitles_lang],
    )
    downloader.download(url, args.start_index, args.end_index)
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
