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
        self.setup_options_widget()
        self.setup_preview_widget()
        self.setup_dir_widgets()
        self.setup_match_scan_widget()
        self.setup_status_bar()
        self.setup_window()

    def setup_options_widget(self):
        self.options_widget = OptionsWidget()

    def setup_preview_widget(self):
        self.preview_widget = PreviewWidget()
    
    def setup_dir_widgets(self):
        self.include_widget = DirectoryWidget("Include Directories")
        self.exclude_widget = DirectoryWidget("Exclude Directories")
        self.dir_widgets = QSplitter()
        self.dir_widgets.setHandleWidth(10)
        self.dir_widgets.setContentsMargins(0, 5, 0, 5)
        self.dir_widgets.setChildrenCollapsible(False)
        self.dir_widgets.addWidget(self.include_widget)
        self.dir_widgets.addWidget(self.exclude_widget)

    def setup_match_scan_widget(self):
        self.matches = None
        self.match_widget = MatchWidget()
        self.match_widget.table_view.current_changed.connect(self.on_current_changed)
        self.scan_pool = QThreadPool()
        self.scan_button = QPushButton("Scan")
        self.scan_button.clicked.connect(self.scan)
        self.scan_bar = QProgressBar()
        
        self.match_scan_widget = QWidget()
        self.match_scan_layout = QVBoxLayout()
        self.match_scan_layout.setContentsMargins(0, 5, 0, 0)
        self.match_scan_layout.addWidget(self.match_widget)
        self.match_scan_layout.addWidget(self.scan_button)
        self.match_scan_layout.addWidget(self.scan_bar)
        self.match_scan_widget.setLayout(self.match_scan_layout)

    def setup_status_bar(self):
        self.status_bar = QStatusBar()
        self.status_bar.showMessage("Welcome to Dupylicate!")

    def setup_window(self):
        self.options_preview_splitter = QSplitter()
        self.options_preview_splitter.setHandleWidth(10)
        self.options_preview_splitter.setContentsMargins(0, 0, 0, 5)
        self.options_preview_splitter.setChildrenCollapsible(False)
        self.options_preview_splitter.addWidget(self.options_widget)
        self.options_preview_splitter.addWidget(self.preview_widget)

        self.main_widget = QSplitter(Qt.Vertical)
        self.main_widget.setHandleWidth(10)
        self.main_widget.setContentsMargins(10, 10, 10, 10)
        self.main_widget.setChildrenCollapsible(False)
        self.main_widget.addWidget(self.options_preview_splitter)
        self.main_widget.addWidget(self.dir_widgets)
        self.main_widget.addWidget(self.match_scan_widget)
        
        self.window = QMainWindow()
        self.window.setWindowTitle("Dupylicate")
        self.window.setCentralWidget(self.main_widget)
        self.window.setStatusBar(self.status_bar)
        self.window.show()    
    
    def get_files(self):
        include_dirs = self.include_widget.dir_paths
        exclude_dirs = self.exclude_widget.dir_paths
        include_files = []
        exclude_files = []
        for include_dir in include_dirs:
            for dir_path, dir_names, file_names in os.walk(include_dir):
                include_files.extend([os.path.join(dir_path, file_name).encode("utf-8") for file_name in file_names])
        if exclude_dirs == None:
            exclude_dirs = []
        for exclude_dir in exclude_dirs:
            for dir_path, dir_names, file_names in os.walk(exclude_dir):
                exclude_files.extend([os.path.join(dir_path, file_name).encode("utf-8") for file_name in file_names])
        files = sorted(list(set(include_files) - set(exclude_files)))
        return files

    def scan(self):
        scan_worker = Worker(self.scan_execute)
        scan_worker.signals.finished.connect(self.scan_complete)
        scan_worker.signals.progress.connect(self.scan_progress)
        
        self.scan_button.setEnabled(False)
        self.scanner = self.options_widget.build_scanner()
        self.scan_pool.start(scan_worker)

    def scan_execute(self, callback):
        files = self.get_files()
        num_files = len(files)
        progress_data = {
            "progress": 0,
            "current_file": 0,
            "current_file_path": None,
            "num_files": num_files,
        }
        if num_files > 0:
            self.scanner.startup(files)
            for i in range(num_files):
                current_file = i + 1
                file_path = files[i]
                progress = round(100 * current_file / num_files)
                progress_data["current_file"] = current_file
                progress_data["current_file_path"] = file_path
                progress_data["progress"] = progress
                callback.emit(progress_data)
                self.scanner.extract_file_thumbnails(i)
                self.scanner.determine_file_group(i)
            self.matches = self.scanner.get_matches()
            self.scanner.cleanup()

    def scan_progress(self, data):
        self.scan_bar.setValue(data["progress"])
        base_message = "Scanning [{0}/{1}]: {2}"
        message = base_message.format(
            data["current_file"], 
            data["num_files"],
            data["current_file_path"].decode(),
        )
        self.status_bar.showMessage(message)
    
    def scan_complete(self):
        self.scan_bar.reset()
        self.status_bar.showMessage("Scan complete.")
        self.scan_button.setEnabled(True)
        self.preview_widget.clear_media()
        self.match_widget.set_matches(self.matches)
        self.scanner.cleanup()
        num_matches = 0
        if self.matches:
            num_matches = self.matches.data.shape[0]
        if num_matches > 0:
            self.preview_widget.enable_buttons()
            for i in range(num_matches):
                file_path = self.matches.data[i]["file_path"]
                self.preview_widget.add_media(file_path.decode())
            self.match_widget.table_view.selectRow(0)
            self.match_widget.table_view.resizeRowsToContents()
            self.match_widget.setFocus()
        else:
            self.preview_widget.disable_buttons()

    def on_current_changed(self, row, column):
        playlist = self.preview_widget.video_playlist
        player = self.preview_widget.video_player
        playlist.setCurrentIndex(row)
        player.setPosition(0)
        player.play()
        player.pause()
        index = self.match_widget.table_model.index(row, 0)
        self.match_widget.table_view.scrollTo(index)

app = App()
os._exit(app.exec_())