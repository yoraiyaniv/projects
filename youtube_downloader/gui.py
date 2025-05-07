import sys
import os
import platform
import subprocess
from PySide6.QtCore import (
    Qt, QPropertyAnimation, QEasingCurve,
    QThreadPool, QRunnable, Signal, Slot, QObject
)
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QPushButton, QLineEdit, QLabel, QProgressBar,
    QFileDialog
)
from PySide6.QtGui import QFont
import yt_dlp

# ────────────────────────────────────────────────────────────
# Worker Signals
# ────────────────────────────────────────────────────────────
class DownloadSignals(QObject):
    """
    Defines the signals available from a running download thread.
    """
    progress = Signal(int)   # Emitted with an integer 0..100
    finished = Signal(bool)  # Emitted when the download is done (True=success, False=failure)

# ────────────────────────────────────────────────────────────
# Download Worker
# ────────────────────────────────────────────────────────────
class DownloadWorker(QRunnable):
    """
    QRunnable to handle the download in a separate thread, keeping the GUI responsive.
    """
    def __init__(self, url: str, download_folder: str):
        super().__init__()
        self.url = url
        self.download_folder = download_folder
        self.signals = DownloadSignals()

    @Slot()
    def run(self):
        """
        The code that actually runs in the separate thread.
        Uses yt_dlp with progress_hooks to provide real-time progress updates.
        """
        def progress_hook(status_dict):
            """
            Called by yt_dlp whenever there's an update (progress, complete, etc.).
            We'll emit a signal with a 0..100 integer for the progress bar.
            """
            if status_dict['status'] == 'downloading':
                # Some streams may not have total_bytes.
                # Fall back to total_bytes_estimate if needed.
                total_bytes = status_dict.get('total_bytes') or status_dict.get('total_bytes_estimate', 0)
                downloaded = status_dict.get('downloaded_bytes', 0)

                if total_bytes > 0:
                    progress_percent = int(downloaded / total_bytes * 100)
                    self.signals.progress.emit(progress_percent)

            elif status_dict['status'] == 'finished':
                # The download is done; 100% for the bar
                self.signals.progress.emit(100)

        # Construct an output template for the final filename
        output_template = os.path.join(self.download_folder, "%(title)s.%(ext)s")

        # Prepare yt_dlp options, including our progress hook
        ydl_opts = {
            'format': 'best',
            'outtmpl': output_template,
            'progress_hooks': [progress_hook]
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([self.url])
            self.signals.finished.emit(True)
        except Exception as e:
            print("Error while downloading:", e)
            self.signals.finished.emit(False)

# ────────────────────────────────────────────────────────────
# Main Window
# ────────────────────────────────────────────────────────────
class YouTubeDownloader(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("YouTube Downloader")
        self.setFixedSize(500, 300)
        self.setStyleSheet(self.get_styles())

        self.thread_pool = QThreadPool()

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.main_layout = QVBoxLayout(central_widget)

        # URL Input
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Enter YouTube video URL here...")
        self.url_input.setFixedHeight(40)

        # Choose Directory Button
        self.dir_button = QPushButton("Choose Directory")
        self.dir_button.setFixedHeight(40)
        self.dir_button.clicked.connect(self.choose_directory)
        self.save_directory = ""

        # Download Button
        self.download_button = QPushButton("Download")
        self.download_button.setFixedHeight(40)
        self.download_button.clicked.connect(self.start_download)

        # Status Label
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("font-size: 16px;")
        self.status_label.setVisible(False)

        # Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)

        # Layout
        self.main_layout.addStretch(1)
        self.main_layout.addWidget(self.url_input)
        self.main_layout.addSpacing(10)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.dir_button)
        button_layout.addWidget(self.download_button)
        self.main_layout.addLayout(button_layout)

        self.main_layout.addSpacing(20)
        self.main_layout.addWidget(self.progress_bar)
        self.main_layout.addSpacing(10)
        self.main_layout.addWidget(self.status_label)
        self.main_layout.addStretch(1)

    # ─────────────────────────────────────────────────────────
    # Style
    # ─────────────────────────────────────────────────────────
    def get_styles(self):
        """
        Returns a custom CSS style for a modern, minimalist look
        with a teal accent color.
        """
        return """
            QMainWindow {
                background-color: #1f1f1f; /* dark background */
            }
            QLineEdit {
                background-color: #333;
                color: #eee;
                border: 1px solid #555;
                border-radius: 8px;
                padding-left: 10px;
                font-size: 16px;
            }
            QPushButton {
                background-color: #00bfa5;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #00a08d;
            }
            QPushButton:pressed {
                background-color: #008275;
            }
            QLabel {
                color: #eee;
            }
            QProgressBar {
                background-color: #333;
                border: 1px solid #555;
                border-radius: 8px;
                text-align: center;
                font-size: 16px;
                color: #eee;
            }
            QProgressBar::chunk {
                background-color: #00bfa5;
                border-radius: 8px;
            }
        """

    # ─────────────────────────────────────────────────────────
    # Slots & Logic
    # ─────────────────────────────────────────────────────────
    def choose_directory(self):
        """
        Opens a folder selection dialog and stores the chosen path.
        """
        directory = QFileDialog.getExistingDirectory(self, "Choose Download Directory")
        if directory:
            self.save_directory = directory

    def start_download(self):
        """
        Checks inputs and starts a background download (with real-time progress).
        """
        url = self.url_input.text().strip()
        if not url:
            self.show_message("Please enter a valid URL.", "#ff4444")
            return
        if not self.save_directory:
            self.show_message("Please choose a save directory.", "#ff4444")
            return

        self.status_label.setVisible(False)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)

        # Create the worker
        worker = DownloadWorker(url, self.save_directory)
        # Connect signals
        worker.signals.progress.connect(self.update_progress)
        worker.signals.finished.connect(self.on_download_finished)

        # Start it
        self.thread_pool.start(worker)

    @Slot(int)
    def update_progress(self, value: int):
        """
        Called whenever the worker emits a progress update (0..100).
        """
        self.progress_bar.setValue(value)

    @Slot(bool)
    def on_download_finished(self, success: bool):
        """
        Called once the worker signals the download is finished.
        """
        # If we never reached 100% in updates, ensure the bar is full on success
        if success and self.progress_bar.value() < 100:
            self.progress_bar.setValue(100)

        self.progress_bar.setVisible(False)
        if success:
            self.show_message("Download completed!", "#44ff44")
            self.open_folder(self.save_directory)
        else:
            self.show_message("Download failed!", "#ff4444")

    def show_message(self, message: str, color: str):
        """
        Displays a status message with a fade-in animation.
        """
        self.status_label.setStyleSheet(f"color: {color}; font-size: 16px;")
        self.status_label.setText(message)
        self.status_label.setVisible(True)
        self.fade_animation(self.status_label, 500, 0.0, 1.0)

    def fade_animation(self, widget, duration=500, start_opacity=0.0, end_opacity=1.0):
        """
        Animates the opacity of a widget from start_opacity to end_opacity
        over the specified duration (in ms).
        """
        animation = QPropertyAnimation(widget, b"windowOpacity")
        animation.setDuration(duration)
        animation.setStartValue(start_opacity)
        animation.setEndValue(end_opacity)
        animation.setEasingCurve(QEasingCurve.InOutQuad)
        animation.start()

    def open_folder(self, folder_path: str):
        """
        Opens the specified folder in the user's default file explorer,
        depending on their operating system.
        """
        if not folder_path:
            return

        if platform.system() == "Windows":
            os.startfile(folder_path)
        elif platform.system() == "Darwin":  # macOS
            subprocess.run(["open", folder_path])
        else:  # Linux and other Unix-like OS
            subprocess.run(["xdg-open", folder_path])

# ─────────────────────────────────────────────────────────
# Entry Point
# ─────────────────────────────────────────────────────────
def main():
    app = QApplication(sys.argv)
    font = QFont("Arial", 10)
    app.setFont(font)

    window = YouTubeDownloader()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
