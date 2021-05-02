import numpy as np
import os
os.environ["QT_LOGGING_RULES"] = "qt5ct.debug=false"
os.environ["QT_STYLE_OVERRIDE"] = "Fusion"
import sys
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
def handler(msg_type, msg_log_context, msg_string): pass
qInstallMessageHandler(handler)
from dupylicate.ui import *
from dupylicate.io import *

class App(QApplication):

    def __init__(self):
        super().__init__([])
        
        #self.video_surface = VideoSurface()
        
        """
        self.video_playlist = QMediaPlaylist()
        self.video_playlist.setPlaybackMode(QMediaPlaylist.Sequential)
        self.video_player = QMediaPlayer()
        self.video_player.setPlaylist(self.video_playlist)
        #self.video_player.setVideoOutput(self.video_surface)
        self.video_player.setVolume(0)

        #self.video_player.stateChanged.connect(self.on_state_change)
        #self.video_player.mediaStatusChanged.connect(self.on_media_status_change)
        #self.video_player.positionChanged.connect(self.on_position_change)
        
        file_url = QUrl("file://" + file_path)
        media = QMediaContent(file_url)
        self.video_playlist.addMedia(media)
        self.video_player.play()
        """

        width = 800
        height = 60
        file_path = b"/media/anish/usb_drive/Videos/java.mp4"
        frame_data = np.empty((height * width * 3), dtype=np.uint8) 
        self.video_reader = VideoReader(width, height)
        self.video_reader.open(file_path)
        self.video_reader.seek_exact(0)
        self.video_reader.read_frame(width, height, frame_data)

        image = QImage(frame_data, width, height, QImage.Format_RGB888)
        pixmap = QPixmap(image)  
        self.main_widget = QLabel()
        self.main_widget.setPixmap(pixmap)

        self.window = QMainWindow()
        self.window.setWindowTitle("Dupylicate")
        self.window.setCentralWidget(self.main_widget)
        self.window.show()

app = App()
os._exit(app.exec_())