from PyQt5.QtWidgets import *

class DirectoryWidget(QWidget):

    def __init__(self, box_name):
        super().__init__()
        self.setup_dialog()
        self.setup_buttons()
        self.setup_list()
        self.setup_layout(box_name)

    def setup_dialog(self):
        self.dialog = QFileDialog(options=QFileDialog.DontUseNativeDialog)
        self.dialog.setFileMode(QFileDialog.Directory)
        self.dialog.fileSelected.connect(self.add_dir_path)

    def setup_buttons(self):
        self.buttons = QWidget()
        self.add_button = QPushButton("Add")
        self.add_button.clicked.connect(self.on_add)
        self.remove_button = QPushButton("Remove")
        self.remove_button.clicked.connect(self.remove_dir_path)
        self.button_layout = QHBoxLayout()
        self.button_layout.addWidget(self.add_button)
        self.button_layout.addWidget(self.remove_button)
        self.buttons.setLayout(self.button_layout)
        self.button_layout.setContentsMargins(0, 0, 0, 0)
    
    def setup_list(self):
        self.dir_paths = []
        self.dir_paths_list = QListWidget()
    
    def setup_layout(self, box_name):
        self.box = QGroupBox(box_name)
        self.box_layout = QVBoxLayout()
        self.box_layout.addWidget(self.buttons)
        self.box_layout.addWidget(self.dir_paths_list)
        self.box.setLayout(self.box_layout)
        self.layout = QHBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.addWidget(self.box)
        self.setLayout(self.layout)

    def on_add(self):
        self.dialog.show()

    def add_dir_path(self, dir_path):
        self.dir_paths.append(dir_path)
        self.dir_paths_list.addItem(dir_path)

    def remove_dir_path(self):
        curr_item = self.dir_paths_list.currentItem()
        if curr_item != None:
            curr_index = self.dir_paths_list.row(curr_item)
            dir_path = curr_item.text()
            self.dir_paths.remove(dir_path)
            self.dir_paths_list.takeItem(curr_index)