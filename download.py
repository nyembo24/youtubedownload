import os
import zipfile
import yt_dlp

ydl_opts = {
    "quiet": False,
    "noplaylist": False,
}

def get_formats(url):
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)

        # Si c'est une playlist, agréger les formats sur toutes les vidéos.
        if "entries" in info:
            entries = [v for v in info.get("entries") or [] if v]
            if not entries:
                return []
            total = len(entries)
            aggregated = {}
            for entry in entries:
                for fmt in entry.get("formats") or []:
                    format_id = fmt.get("format_id")
                    if not format_id:
                        continue
                    slot = aggregated.get(format_id)
                    if not slot:
                        slot = {
                            "format_id": format_id,
                            "ext": fmt.get("ext"),
                            "format": fmt.get("format"),
                            "acodec": fmt.get("acodec"),
                            "vcodec": fmt.get("vcodec"),
                            "filesize": 0,
                            "filesize_approx": 0,
                            "available_count": 0,
                            "total_count": total,
                        }
                    if fmt.get("filesize"):
                        slot["filesize"] += fmt["filesize"]
                    elif fmt.get("filesize_approx"):
                        slot["filesize_approx"] += fmt["filesize_approx"]
                    slot["available_count"] += 1
                    aggregated[format_id] = slot
            return list(aggregated.values())

        return info.get("formats", [])


def download_format(url, format_id, download_dir="/tmp/fastyoutube"):
    os.makedirs(download_dir, exist_ok=True)

    opts = {
        "format": format_id,
        "outtmpl": os.path.join(download_dir, "%(title).200s.%(ext)s"),
        "quiet": True,
        "noplaylist": False,
    }

    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)

        # Si c'est une playlist, zipper tous les fichiers téléchargés.
        if "entries" in info:
            entries = [v for v in info.get("entries") or [] if v]
            if not entries:
                return ""
            paths = []
            for entry in entries:
                if not entry:
                    continue
                requested = entry.get("requested_downloads") or []
                if requested:
                    path = requested[0].get("filepath")
                else:
                    path = ydl.prepare_filename(entry)
                if path:
                    paths.append(path)
            if not paths:
                return ""
            title = info.get("title") or "playlist"
            safe_title = "".join(c for c in title if c.isalnum() or c in (" ", "-", "_")).strip() or "playlist"
            zip_path = os.path.join(download_dir, f"{safe_title}.zip")
            with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
                for path in paths:
                    if os.path.exists(path):
                        zf.write(path, arcname=os.path.basename(path))
            return zip_path

        # Si c'est une vidéo
        if "requested_downloads" in info and info["requested_downloads"]:
            filepath = info["requested_downloads"][0].get("filepath")
        else:
            filepath = ydl.prepare_filename(info)

        return filepath
