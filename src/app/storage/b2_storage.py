"""
Backblaze B2 storage for evidence frames (cheating detection images).
Uploads frames to B2 when configured via environment variables.

Required env vars:
  B2_KEY_ID          - Application Key ID from B2 dashboard
  B2_APPLICATION_KEY - Application Key secret
  B2_BUCKET_NAME     - Bucket name (use "allPublic" type for public evidence URLs)

Optional:
  B2_EVIDENCE_PREFIX - Subfolder in bucket (default: evidence/frames)
  B2_CUSTOM_DOMAIN   - Custom domain/CDN URL (e.g. https://cdn.example.com)
"""

from __future__ import annotations

import os
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Environment variable names
B2_KEY_ID = "B2_KEY_ID"
B2_APPLICATION_KEY = "B2_APPLICATION_KEY"
B2_BUCKET_NAME = "B2_BUCKET_NAME"
B2_EVIDENCE_PREFIX = "B2_EVIDENCE_PREFIX"  # e.g. "evidence/frames" - subfolder in bucket
B2_CUSTOM_DOMAIN = "B2_CUSTOM_DOMAIN"  # Optional: custom domain or CDN URL (e.g. https://cdn.example.com)


def _is_b2_configured() -> bool:
    """Check if B2 credentials are set (B2_KEY_ID, B2_APPLICATION_KEY, B2_BUCKET_NAME)."""
    return bool(
        os.getenv(B2_KEY_ID)
        and os.getenv(B2_APPLICATION_KEY)
        and os.getenv(B2_BUCKET_NAME)
    )


def upload_evidence_frame(local_path: str | Path) -> Optional[str]:
    """
    Upload an evidence frame (cheating detection image) to Backblaze B2.
    
    Args:
        local_path: Local filesystem path to the image file.
        
    Returns:
        Public URL to the uploaded file, or None if upload failed or B2 not configured.
    """
    if not _is_b2_configured():
        return None

    path = Path(local_path)
    if not path.exists() or not path.is_file():
        logger.warning("Evidence frame not found: %s", local_path)
        return None

    try:
        import b2sdk.v2 as b2

        key_id = os.getenv(B2_KEY_ID)
        app_key = os.getenv(B2_APPLICATION_KEY)
        bucket_name = os.getenv(B2_BUCKET_NAME)
        prefix = os.getenv(B2_EVIDENCE_PREFIX, "evidence/frames").rstrip("/")
        custom_domain = os.getenv(B2_CUSTOM_DOMAIN)

        # Remote file name: evidence/frames/filename.jpg (avoids collisions via unique frame names)
        remote_name = f"{prefix}/{path.name}"

        info = b2.InMemoryAccountInfo()
        api = b2.B2Api(info)
        api.authorize_account("production", key_id, app_key)
        bucket = api.get_bucket_by_name(bucket_name)

        bucket.upload_local_file(
            local_file=str(path),
            file_name=remote_name,
            content_type="image/jpeg",
        )

        # Get download URL
        if custom_domain:
            url = f"{custom_domain.rstrip('/')}/{remote_name}"
        else:
            url = api.get_download_url_for_file_name(bucket_name, remote_name)

        logger.info("Uploaded evidence frame to B2: %s", remote_name)
        return url

    except ImportError:
        logger.warning("b2sdk not installed. Run: pip install b2sdk")
        return None
    except Exception as e:
        logger.warning("B2 upload failed for %s: %s", local_path, e)
        return None


# -------------------------
# Report evidence download (B2 -> local for report links)
# -------------------------

# Relative to project root (same as reports uploads/reports)
EVIDENCE_DOWNLOADS_DIR = Path("uploads/downloads/evidence")


def _is_remote_url(url: Optional[str]) -> bool:
    """True if URL is a remote HTTP/HTTPS URL (B2, CDN, etc.)."""
    if not url or not isinstance(url, str):
        return False
    url = url.strip()
    return url.startswith("http://") or url.startswith("https://")


def _ensure_downloads_dir() -> Path:
    """Ensure uploads/downloads/evidence exists."""
    EVIDENCE_DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)
    return EVIDENCE_DOWNLOADS_DIR


def _parse_b2_url(url: str) -> Optional[tuple[str, str]]:
    """
    Parse B2 friendly URL into (bucket_name, file_name).
    e.g. https://f005.backblazeb2.com/file/ForeSyte-blob/evidence/frames/foo.jpg -> ("ForeSyte-blob", "evidence/frames/foo.jpg")
    """
    if not url or "backblazeb2.com/file/" not in url:
        return None
    try:
        # .../file/BUCKET_NAME/path/to/file.jpg
        parts = url.split("/file/", 1)[-1].split("/", 1)
        if len(parts) != 2:
            return None
        bucket_name, file_name = parts[0], parts[1]
        if not bucket_name or not file_name:
            return None
        return (bucket_name, file_name)
    except Exception:
        return None


def _download_from_b2(bucket_name: str, file_name: str, save_path: Path) -> bool:
    """Download a file from B2 using SDK (works with private buckets)."""
    if not _is_b2_configured():
        return False
    try:
        import b2sdk.v2 as b2
        key_id = os.getenv(B2_KEY_ID)
        app_key = os.getenv(B2_APPLICATION_KEY)
        info = b2.InMemoryAccountInfo()
        api = b2.B2Api(info)
        api.authorize_account("production", key_id, app_key)
        bucket = api.get_bucket_by_name(bucket_name)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        downloaded = bucket.download_file_by_name(file_name)
        downloaded.save_to(save_path)
        logger.info("Downloaded from B2: %s/%s -> %s", bucket_name, file_name, save_path.name)
        return True
    except Exception as e:
        logger.warning("B2 download failed for %s/%s: %s", bucket_name, file_name, e)
        return False


def _download_via_http(url: str, save_path: Path) -> bool:
    """Download via HTTP GET (for public URLs only)."""
    try:
        import urllib.request
        req = urllib.request.Request(url, headers={"User-Agent": "ForeSyte-Report/1.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = resp.read()
        save_path.parent.mkdir(parents=True, exist_ok=True)
        save_path.write_bytes(data)
        return True
    except Exception as e:
        logger.warning("HTTP download failed for %s: %s", url[:80], e)
        return False


def download_evidence_for_report(
    report_id: str,
    evidence_urls: list[str],
    base_url: Optional[str] = None,
) -> dict[str, str]:
    """
    Download evidence images from B2/remote URLs to uploads/downloads/evidence.
    Returns mapping of original_url -> localhost URL for use in report.

    Args:
        report_id: Report UUID string (for unique filenames)
        evidence_urls: List of evidence URLs (B2, local /uploads/..., etc.)
        base_url: Server base URL for links (default: http://localhost:8000)

    Returns:
        Dict mapping original_url -> display URL (localhost link to view image)
    """
    base = (base_url or os.getenv("REPORT_BASE_URL", "http://localhost:8000")).rstrip("/")
    out_dir = _ensure_downloads_dir()
    url_map: dict[str, str] = {}
    seen_urls: set[str] = set()

    for idx, orig_url in enumerate(evidence_urls):
        if not orig_url or orig_url in ("N/A", ""):
            continue
        orig_url = str(orig_url).strip()

        # Already local path (/uploads/...)
        if orig_url.startswith("/uploads"):
            # Ensure it's a full URL for the report
            display_url = f"{base}{orig_url}" if not orig_url.startswith("http") else orig_url
            url_map[orig_url] = display_url
            continue

        # Remote URL (B2 or other) - download and store locally so report links work without auth
        if _is_remote_url(orig_url):
            if orig_url in seen_urls:
                url_map[orig_url] = url_map.get(orig_url, "N/A")
                continue
            seen_urls.add(orig_url)
            ext = ".jpg"
            if "." in orig_url.split("?")[0]:
                ext = "." + orig_url.split("?")[0].rsplit(".", 1)[-1].lower()
            if ext not in (".jpg", ".jpeg", ".png", ".webp"):
                ext = ".jpg"
            safe_id = str(report_id).replace("-", "_")
            filename = f"evidence_{safe_id}_{idx}{ext}"
            local_path = out_dir / filename
            downloaded = False
            b2_parsed = _parse_b2_url(orig_url)
            if b2_parsed:
                bucket_name, file_name = b2_parsed
                downloaded = _download_from_b2(bucket_name, file_name, local_path)
            if not downloaded:
                downloaded = _download_via_http(orig_url, local_path)
            if downloaded:
                rel = f"/uploads/downloads/evidence/{filename}"
                display_url = f"{base}{rel}"
                url_map[orig_url] = display_url
                logger.info("Downloaded evidence for report %s: %s", report_id, filename)
            else:
                # Do not use B2 link in report (often 401); show N/A so user is not shown broken link
                url_map[orig_url] = "N/A"
        else:
            # Other (e.g. relative path) - convert to full URL if possible
            if orig_url.startswith("/"):
                url_map[orig_url] = f"{base}{orig_url}"
            else:
                url_map[orig_url] = orig_url

    return url_map
