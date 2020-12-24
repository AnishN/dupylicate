import os
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

class CheckBoxDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)

    def createEditor(self, parent, option, index):
        return None

    def paint(self, painter, option, index):
        model = index.model()
        checked = model.data(index, Qt.DisplayRole)
        opts = QStyleOptionButton()
        opts.state |= QStyle.State_Active
        if index.flags() & Qt.ItemIsEditable:
            opts.state |= QStyle.State_Enabled
        else:
            opts.state |= QStyle.State_ReadOnly
        if checked == True:
            opts.state |= QStyle.State_On
        else:
            opts.state |= QStyle.State_Off
        opts.rect = self.get_rect(option)
        QApplication.style().drawControl(QStyle.CE_CheckBox, opts, painter)

    def editorEvent(self, event, model, option, index):
        if event.button() == Qt.LeftButton:
            if event.type() == QEvent.MouseButtonRelease:
                if self.get_rect(option).contains(event.pos()):
                    self.setModelData(None, model, index)
                    return True
            elif event.type() == QEvent.MouseButtonDblClick:
                if self.get_rect(option).contains(event.pos()):
                    return True
        return False

    def setModelData(self, editor, model, index):
        checked = not model.data(index, Qt.DisplayRole)
        model.setData(index, checked, Qt.EditRole)

    def get_rect(self, option):
        opts = QStyleOptionButton()
        rect = QApplication.style().subElementRect(QStyle.SE_CheckBoxIndicator, opts, None)
        x = option.rect.x()
        y = option.rect.y()
        w = option.rect.width()
        h = option.rect.height()
        top_left = QPoint(x + w // 2 - rect.width() // 2, y + h // 2 - rect.height() // 2)
        return QRect(top_left, rect.size())

class MatchWidget(QGroupBox):
    def __init__(self):
        super().__init__("Matches")
        self.setup_table()
        self.setup_buttons()
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.addWidget(self.buttons)
        self.layout.addWidget(self.table_view)
        self.setLayout(self.layout)
    
    def setup_buttons(self):
        self.buttons = QWidget()
        self.delete_button = QPushButton("Delete Selected Files")
        self.delete_button.clicked.connect(self.delete_files)
        self.count_label = QLabel(); self.set_count_label(0)
        self.buttons_layout = QHBoxLayout()
        self.buttons_layout.setContentsMargins(0, 0, 0, 0)
        self.buttons_layout.addWidget(self.delete_button)
        self.buttons_layout.addWidget(self.count_label)
        self.buttons.setLayout(self.buttons_layout)

    def setup_table(self):
        self.table_view = MatchTableView()
        self.table_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.table_model = MatchTableModel(self)
        self.table_model.dataChanged.connect(self.on_data_changed)
        self.table_view.setModel(self.table_model)
        self.table_delegate = CheckBoxDelegate()
        self.table_view.setItemDelegateForColumn(0, self.table_delegate)

    def set_matches(self, matches):
        self.table_model = MatchTableModel(self, matches=matches)
        self.table_model.dataChanged.connect(self.on_data_changed)
        num_rows = self.table_model.rowCount(self)
        for i in range(num_rows):
            self.table_view.showRow(i)
        self.table_view.reset()
        self.table_view.setModel(self.table_model)
        self.set_count_label(0)
    
    def on_data_changed(self, top_left, bottom_right):
        num_selected_files = sum(self.table_model.selected)
        self.set_count_label(num_selected_files)

    def delete_files(self):
        num_rows = self.table_model.rowCount(self)
        for i in range(num_rows):
            index = self.table_model.index(i, 0)
            is_checked = self.table_model.data(index, Qt.DisplayRole)
            if is_checked:
                file_path = self.table_model.matches.data[index.row()]["file_path"]
                os.remove(file_path)
                self.table_view.hideRow(index.row())
        self.table_model.selected = [False] * num_rows
        self.set_count_label(0)        

    def set_count_label(self, num_selected_files):
        base_text = "# Match Groups: {0} | # Match Files: {1} | # Selected Files: {2}"
        num_match_groups = 0
        num_match_files = 0
        matches = self.table_model.matches
        if matches:
            num_match_groups = matches.num_match_groups
            num_match_files = matches.num_match_files
        text = base_text.format(num_match_groups, num_match_files, num_selected_files)
        self.count_label.setText(text)

class MatchTableView(QTableView):
    current_changed = pyqtSignal(int, int)
    data_changed = pyqtSignal(object, object)

    def __init__(self):
        super().__init__()
        self.setup_properties()
        self.setup_headers()
        #self.show()

    def setup_properties(self):
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.verticalHeader().setVisible(False)
        #self.setFocusPolicy(Qt.NoFocus)

        self.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.setShowGrid(False)
        self.setAutoScroll(False)
        self.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Minimum)
        self.setSelectionMode(QTableView.SingleSelection)
        self.setSelectionBehavior(QTableView.SelectRows)
    
    def setup_headers(self):
        self.h_header = self.horizontalHeader()
        self.h_header.setSectionResizeMode(QHeaderView.ResizeToContents)
        self.h_header.setStretchLastSection(True)
        self.h_header.setDefaultAlignment(Qt.AlignLeft)
        self.h_header.setHighlightSections(False)
        self.v_header = self.verticalHeader()
        self.v_header.setVisible(False)
    
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.resizeColumnsToContents()
        self.h_header.setSectionResizeMode(QHeaderView.ResizeToContents)
        self.h_header.setStretchLastSection(True)
    
    def currentChanged(self, current, previous):
        self.current_changed.emit(current.row(), current.column())

class MatchTableModel(QAbstractTableModel):

    def __init__(self, parent=None, matches=None):
        super().__init__(parent)
        self.matches = matches
        if self.matches == None:
            self.selected = []
        else:
            self.selected = [False] * self.matches.data.shape[0]
        self.column_names = [
            "selected", "group_num", "file_num", "file_path", 
            "file_size", "duration", "width", "height",
            "bit_rate", "frame_rate", "sample_rate", 
            "num_channels", "video_codec", "audio_codec",
        ]
        self.header_names = [
            "Selected", "Group #", "File #", "File Path",
            "File Size (bytes)", "Duration (hh:mm:ss:zzz)", "Width (px)", "Height (px)", 
            "Bit Rate (kbps)", "Frame Rate (fps)", "Sample Rate (Hz)", 
            "# Channels", "Video Codec", "Audio Codec",
        ]
        self.transforms = {
            "selected": lambda value: str(value),#not really used
            "group_num": lambda value: str(value + 1),
            "file_num": lambda value: str(value + 1),
            "file_path": lambda value: value.decode(),
            "file_size": lambda value: self.get_formatted_file_size(value),
            "duration": lambda value: self.get_formatted_duration(value),
            "width": lambda value: str(value),
            "height": lambda value: str(value),
            "bit_rate": lambda value: str(round(value / 1000)),
            "frame_rate": lambda value: "{0:.2f}".format(round(value, 2)),
            "sample_rate": lambda value: str(value),
            "num_channels": lambda value: str(value),
            "video_codec": lambda value: self.get_formatted_codec(value),
            "audio_codec": lambda value: self.get_formatted_codec(value),
        }

    def get_formatted_file_size(self, file_size):
        return QLocale.system().formattedDataSize(file_size)

    def get_formatted_duration(self, duration):
        microseconds = min(duration, 100 * 60 * 60 * 1000 * 1000 - 1)#caps at 100 hours
        x = microseconds // 1000; milliseconds = x % 1000
        x //= 1000; seconds = x % 60
        x //= 60; minutes = x % 60
        x //= 60; hours = x
        base = "{0:02}:{1:02}:{2:02}:{3:03}"
        out = base.format(hours, minutes, seconds, milliseconds)
        return out

    def get_formatted_codec(self, codec_id):
        if not self.matches:
            return ""
        else:
            return self.matches.get_codec_str(codec_id)

    def rowCount(self, parent):
        if self.matches == None:
            return 0    
        return self.matches.data.shape[0]

    def columnCount(self, parent):
        return len(self.column_names)

    def data(self, index, role):
        row = index.row()
        column = index.column()
        column_name = self.column_names[column]
        if self.matches != None:
            if column == 0:
                value = self.selected[row]
            else:
                value = self.matches.data[row][column_name]
            if role == Qt.DisplayRole:
                if column == 0:
                    return self.selected[row]
                else:
                    value = self.matches.data[row][column_name]
                    transform = self.transforms[column_name]
                    transformed_value = transform(value)
                    return transformed_value
    
    def headerData(self, column, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.header_names[column]
        return None

    def flags(self, index):
        column = index.column()
        if column == 0:
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsUserCheckable | Qt.ItemIsEditable
        else:
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable

    def setData(self, index, value, role):
        row = index.row()
        column = index.column()
        column_name = self.column_names[column]
        if role == Qt.EditRole:
            if column == 0:
                self.selected[row] = value
                self.dataChanged.emit(index, index)
                return True
        return False