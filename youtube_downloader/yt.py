import yt_dlp

def download(url: str, download_path: str) -> None:
    ydl_opts = {
    'format': 'best[ext=mp4]',
    'outtmpl': download_path
}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])