from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtMultimedia import *
from PyQt5.QtMultimediaWidgets import *

class PreviewWidget(QGroupBox):

    def __init__(self):
        super().__init__("Preview")
        self.setup_video_player()
        self.setup_slider()
        self.setup_buttons()
        self.setup_layout()
    
    def setup_video_player(self):
        self.video_widget = QVideoWidget()
        self.video_widget.setStyleSheet("background-color: black");
        self.video_widget.setAspectRatioMode(Qt.KeepAspectRatio)
        self.video_playlist = QMediaPlaylist()
        self.video_playlist.setPlaybackMode(QMediaPlaylist.Sequential)
        self.video_player = QMediaPlayer()
        self.video_player.setPlaylist(self.video_playlist)
        self.video_player.setVideoOutput(self.video_widget)
        self.video_player.setVolume(0)
        self.video_player.stateChanged.connect(self.on_state_change)
        self.video_player.mediaStatusChanged.connect(self.on_media_status_change)
        self.video_player.positionChanged.connect(self.on_position_change)

    def setup_slider(self):
        self.slider = QSlider(Qt.Horizontal)
        self.slider_scale = 10000
        self.slider.setRange(0, self.slider_scale)
        self.slider.sliderMoved.connect(self.on_slider_move)

    def setup_buttons(self):
        self.play_button = QPushButton()
        self.play_icon = self.style().standardIcon(QStyle.SP_MediaPlay)
        self.play_button.setIcon(self.play_icon)
        self.play_button.clicked.connect(self.play)

        self.pause_button = QPushButton()
        self.pause_icon = self.style().standardIcon(QStyle.SP_MediaPause)
        self.pause_button.setIcon(self.pause_icon)
        self.pause_button.clicked.connect(self.pause)
        
        self.stop_button = QPushButton()
        self.stop_icon = self.style().standardIcon(QStyle.SP_MediaStop)
        self.stop_button.setIcon(self.stop_icon)
        self.stop_button.clicked.connect(self.stop)
        
        self.left_spacer = QWidget()
        self.left_spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.right_spacer = QWidget()
        self.right_spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.buttons = QWidget()
        self.buttons_layout = QHBoxLayout()
        self.buttons_layout.setContentsMargins(0, 0, 0, 0)
        self.buttons_layout.addWidget(self.left_spacer)
        self.buttons_layout.addWidget(self.play_button)
        self.buttons_layout.addWidget(self.pause_button)
        self.buttons_layout.addWidget(self.stop_button)
        self.buttons_layout.addWidget(self.right_spacer)
        self.buttons.setLayout(self.buttons_layout)
        self.disable_buttons()

    def enable_buttons(self):
        self.play_button.setEnabled(True)
        self.pause_button.setEnabled(True)
        self.stop_button.setEnabled(True)

    def disable_buttons(self):
        self.play_button.setEnabled(False)
        self.pause_button.setEnabled(False)
        self.stop_button.setEnabled(False)

    def setup_layout(self):
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.video_widget)
        self.layout.addWidget(self.slider)
        self.layout.addWidget(self.buttons)
        self.setLayout(self.layout)

    def add_media(self, file_path):
        file_url = QUrl("file://" + file_path)
        media = QMediaContent(file_url)
        self.video_playlist.addMedia(media)
    
    def clear_media(self):
        self.video_playlist.clear()

    def play(self):
        self.video_player.play()
    
    def pause(self):
        self.video_player.pause()

    def stop(self):
        self.video_player.stop()
        self.slider.setValue(0)

    def on_state_change(self):
        pass

    def on_media_status_change(self):
        status = self.video_player.mediaStatus()
        if status == QMediaPlayer.LoadedMedia:
            self.video_player.setPosition(0)
            self.video_player.play()
            self.video_player.pause()
    
    def on_position_change(self, progress):
        duration = self.video_player.duration()
        slider_progress = self.slider_scale * progress / duration if duration != 0 else 0
        self.slider.setValue(slider_progress)

    def on_slider_move(self, position):
        duration = self.video_player.duration()
        video_position = duration * position / self.slider_scale
        self.video_player.setPosition(video_position)