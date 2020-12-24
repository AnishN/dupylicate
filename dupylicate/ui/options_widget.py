from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from dupylicate.io import *

class OptionsWidget(QGroupBox):

    def __init__(self):
        super().__init__("Options")
        self.setup_widgets()
        self.setup_layout()

    def setup_widgets(self):
        self.include_images = QCheckBox()
        self.include_images.setChecked(True)
        self.include_videos = QCheckBox()
        self.include_videos.setChecked(True)
        self.thumbnail_width = QSpinBox()
        self.thumbnail_width.setRange(1, 256)
        self.thumbnail_width.setValue(64)
        self.thumbnail_height = QSpinBox()
        self.thumbnail_height.setRange(1, 256)
        self.thumbnail_height.setValue(64)
        self.num_thumbnails = QSpinBox()
        self.num_thumbnails.setRange(1, 99)
        self.num_thumbnails.setValue(3)
        self.similarity = QSpinBox()
        self.similarity.setRange(0, 100)
        self.similarity.setValue(95)
        self.seek_exact = QCheckBox()
        self.seek_exact.setChecked(False)

    def setup_layout(self):
        self.layout = QFormLayout()
        self.layout.addRow("Include Images", self.include_images)
        self.layout.addRow("Include Videos", self.include_videos)
        self.layout.addRow("Thumbnail Width", self.thumbnail_width)
        self.layout.addRow("Thumbnail Height", self.thumbnail_height)
        self.layout.addRow("# Thumbnails", self.num_thumbnails)
        self.layout.addRow("% Similarity", self.similarity)
        self.layout.addRow("Seek Exact", self.seek_exact)
        self.setLayout(self.layout)

    def build_scanner(self):
        scanner = VideoScanner(
            self.include_images.isChecked(),
            self.include_videos.isChecked(),
            self.num_thumbnails.value(),
            self.thumbnail_width.value(), 
            self.thumbnail_height.value(), 
            self.similarity.value(), 
            self.seek_exact.isChecked(),
        )
        return scanner