FROM python:3.11

WORKDIR /youtube_downloader

RUN pip install flask yt_dlp

COPY app.py /youtube_downloader/app.py
COPY yt.py /youtube_downloader/yt.py

RUN mkdir downloads

CMD ["python", "app.py"]