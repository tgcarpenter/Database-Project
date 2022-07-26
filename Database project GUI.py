import sys
from Databases import *

from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtMultimedia import *
from PyQt6.QtMultimediaWidgets import *
from PyQt6.QtDesigner import *
from PyQt6.QtHelp import *


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("My App")
        self.setGeometry(600, 600, 800, 600)
        self.setMinimumHeight(200)
        self.setMinimumWidth(400)

        self.table = QTableWidget(8, 13)
        # values stored in settings to be overwritten when settings read
        self.first_cell_size = 24
        self.databases_names = {}  # Will be stored as database name: position in databases
        self.databases = []  # list that stores all database interaction configs created by user
        self.database_amount = 1  # number of databases + 1
        self.current_database = None  # Stores currently accessed Database position in self.databases
        self.table_query_start = 1  # Position of start of General Query
        self.table_query_end = 1  # Position of end of General Query

        try:
            self.read_settings()
        except:
            pass

        self.add_db_button = QPushButton('New Database', self)
        self.add_db_button.setFixedWidth(100)
        self.add_db_button.clicked.connect(self.make_add_database_window)

        self.open_db_button = QPushButton('Open Database', self)
        self.open_db_button.setFixedWidth(100)
        self.open_db_button.clicked.connect(self.open_database_window)

        self.table.setWordWrap(True)

        self.table.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.scrollbar = QScrollBar()
        if self.current_database:
            self.scrollbar.setMaximum((self.databases[self.current_database].row_count - 1) * 24)
        self.scrollbar.valueChanged.connect(lambda: connect_scroll_bars())

        def connect_scroll_bars():
            diff = self.table_query_end - self.table_query_start
            self.table_query_start = self.scrollbar.value() // self.first_cell_size
            if self.table_query_end - self.table_query_start != diff:
                self.table_query_end += diff - (self.table_query_end - self.table_query_start)
                self.query_database()
            self.table.verticalScrollBar().setValue(self.scrollbar.value() % (self.first_cell_size + 1))

        # Resizing the table based on text wrap
        self.table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().sectionResized.connect(lambda: resize_vertical())

        # Retrieving the current size of the first cell
        def resize_vertical():
            self.table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
            self.first_cell_size = self.table.verticalHeader().sectionSize(0)
            print(self.first_cell_size)

        self.query = [('AMaMagnificat & Nunc Dimittis', 'Song of Mary', 'Howells', 'Herbert', None, 'happy', 'Advent', None,
                  'SATB, SSAATTBB', 'Gern', None, None),
                 (None, None, None, None, None, None, None, None,
                  None, None, None, None),
                 ('CMagnificat & Nunc Dimittis', 'Song of Mary', 'Howells', 'Herbert', None, 'happy', 'Advent', None,
                  'SATB, SSAATTBB', 'Gern', None, None),
                 ('DMagnificat & Nunc Dimittis', 'Song of Mary', 'Howells', 'Herbert', None, 'happy', 'Advent', None,
                  'SATB, SSATTBB', 'German', 'ha', None),
                 ('EMagnificat &\n Nunc Dimittis', 'Song of Mary', 'Howells', 'Herbert', None, 'happy', 'Advent', None,
                  'SATB, SSAATTBB', 'Gern', None, None),
                 ('FMagnificat & Nunc Dimittis', 'Song of Mary', 'Howells', 'Herbert', None, 'happy', 'Advent', None,
                  'SATB, SSATTBB', 'German', 'ha', None),
                 ('GMagnificat & Nunc Dimittis', 'Song of Mary', 'Howells', 'Herbert', None, 'happy', 'Advent', None,
                  'SATB, SSAATTBB', 'Gern', None, None),
                 ('HMagnificat & Nunc Dimittis', 'Song of Mary', 'Howells', 'Herbert', None, 'happy', 'Advent', None,
                  'SATB, SSATTBB', 'German', 'ha', None)]

        for row in range(self.table.rowCount()):
            count = 0
            for cell in self.query[row]:
                item = QTableWidgetItem(cell)
                self.table.setItem(row, count, item)
                count += 1

        self.databases_names = {'db1': 1, 'db2': 2}

        self.layout = QVBoxLayout()
        self.layout2 = QHBoxLayout()
        self.layout3 = QHBoxLayout()
        self.layout3.addWidget(self.add_db_button, alignment=Qt.AlignmentFlag.AlignLeft)
        self.layout3.addWidget(self.open_db_button, alignment=Qt.AlignmentFlag.AlignLeft)
        self.layout.addLayout(self.layout3)
        self.layout.addWidget(self.table)
        self.layout2.addLayout(self.layout)
        self.layout2.addWidget(self.scrollbar)

        widget = QWidget()
        widget.setLayout(self.layout2)

        self.setCentralWidget(widget)

        # Database Controls
    def query_database(self):
        if self.current_database is None:
            self.table.setColumnCount(0)
            self.table.setRowCount(0)
            return  # Make setting column and row count its own methods
        self.query = self.databases[self.current_database].general_query(self.table_query_start, self.table_query_end)
        self.update_column_count()  # setting table size
        for row in range(self.table.rowCount()):  # assigning queried statement to cells
            count = 0
            for cell in self.query[row]:
                item = QTableWidgetItem(cell)
                self.table.setItem(row, count, item)
                count += 1

    def update_column_count(self):
        self.table.setColumnCount(len(self.databases[self.current_database].column_classes))

    def update_row_count(self, count):
        self.table.setRowCount(count)

        # window and table controls
    def write_settings(self):
        settings = QSettings('MyApp', 'DatabaseBuilderApp')
        settings.beginGroup('windowconfig')
        settings.setValue('geometry', self.geometry())
        settings.setValue('databases', self.databases)
        settings.setValue('databasenames', self.databases_names)
        settings.setValue('databaseamount', self.database_amount)
        settings.setValue('currentdatabase', self.current_database)
        settings.endGroup()
        settings.beginGroup('tableconfig')
        settings.setValue('columnconfig', self.table.horizontalHeader().saveState())
        settings.setValue('firstcellsize', self.first_cell_size)
        settings.endGroup()

    def read_settings(self):
        settings = QSettings('MyApp', 'DatabaseBuilderApp')
        settings.beginGroup('windowconfig')
        try:
            self.setGeometry(settings.value('geometry'))
        except:
            pass
        self.databases_names = settings.value('databasenames')
        self.databases = settings.value('databases')
        self.database_amount = settings.value('databaseamount')
        self.current_database = settings.value('currentdatabase')
        settings.endGroup()
        settings.beginGroup('tableconfig')
        try:
            self.table.horizontalHeader().restoreState(settings.value('columnconfig'))
        except:
            pass
        self.first_cell_size = settings.value('firstcellsize')
        settings.endGroup()

    def closeEvent(self, event):
        self.write_settings()
        event.accept()

    def make_add_database_window(self):
        self.window2 = self.DbNameInputWindow()
        self.window2.show()

    def open_database_window(self):
        self.window3 = self.OpenDbWindow()
        self.window3.show()

    def change_current_database(self, db_name):
        self.current_database = self.databases_names[db_name]
        self.scrollbar.setMaximum((self.databases[self.current_database].row_count - 1) * 24)
        self.table_query_start = 1
        self.resizeEvent(self.geometry())
        self.query_database()

    def resizeEvent(self, a0: QResizeEvent) -> None:  # Handles app opening query and re-queries with resize
        count = self.table.geometry().getRect()
        if self.current_database is None:
            self.query_database()
            return
        elif count[3] // 24 > self.databases[self.current_database].row_count - 1:
            self.table_query_end = self.databases[self.current_database].row_count - 1
            self.update_row_count(self.table_query_end)
            self.query_database()
        else:
            self.table_query_end = self.table_query_start + (count[3] // 24 + 1)
            self.update_row_count(count[3] // 24 + 2)
            self.query_database()

    class EnterKeyFilter(QObject):
        entrkeypressed = pyqtSignal()

        def eventFilter(self, a0: 'QObject', a1: 'QEvent'):
            if a1.type() == QEvent.Type.KeyPress:
                if a1.key() == Qt.Key.Key_Return:
                    self.entrkeypressed.emit()
                    print('yes')
                    return True
            return False

    class DbNameInputWindow(QWidget):
        def __init__(self):
            super().__init__()

            self.setWindowTitle('Create Database')
            self.setStyleSheet('background-color: light grey')
            self.setFixedSize(400, 100)
            input_box = QLineEdit()
            input_box.setFixedWidth(250)
            input_box.setMaxLength(40)
            input_box.setFont(QFont('Ariel, 100'))
            input_box.setPlaceholderText('Type Name')

            enter = QPushButton('Enter', self)
            enter.setFixedWidth(100)
            if input_box.text() != '':
                enter.clicked.connect(lambda: self.create_database(input_box.text()))
                enter.clicked.connect(self.close)
            cancel = QPushButton('Cancel', self)
            cancel.setFixedWidth(100)
            cancel.clicked.connect(self.close)

            self.filter = window.EnterKeyFilter()
            input_box.installEventFilter(self.filter)
            self.filter.entrkeypressed.connect(cancel.click)

            layout = QFormLayout()
            layout.addRow('Database Name:', input_box)

            layout2 = QHBoxLayout()
            layout2.addWidget(enter)
            layout2.addWidget(cancel)

            layout3 = QVBoxLayout()
            layout3.addSpacing(10)
            layout3.addLayout(layout)
            layout3.addLayout(layout2)

            self.setLayout(layout3)

        def create_database(self, name):  # needs testing
            window.databases.append(Database(name))
            window.databases_names[name] = window.database_amount
            window.database_amount += 1
            window.change_current_database(name)

    class OpenDbWindow(QWidget):
        def __init__(self):
            super().__init__()

            self.setWindowTitle('Open Database')
            self.setFixedSize(500, 500)

            list_view = QListWidget()
            header = QLabel('Select Database:')
            temp_databases = list(window.databases_names.keys())
            temp_databases.reverse()

            try:
                for database in temp_databases:
                    item = QListWidgetItem(database)
                    list_view.addItem(item)
            except:
                pass

            list_view.itemDoubleClicked.connect(lambda: current_item())

            enter = QPushButton('Enter', self)
            enter.setFixedWidth(100)
            if list_view.currentItem():
                enter.clicked.connect(lambda: current_item())
                enter.clicked.connect(self.close)
            cancel = QPushButton('Cancel', self)
            cancel.setFixedWidth(100)
            cancel.clicked.connect(self.close)

            self.filter = window.EnterKeyFilter()
            list_view.installEventFilter(self.filter)
            self.filter.entrkeypressed.connect(cancel.click)

            layout = QVBoxLayout()
            layout.addWidget(header)
            layout.addWidget(list_view)

            layout2 = QHBoxLayout()
            layout2.addWidget(enter)
            layout2.addWidget(cancel)

            layout.addLayout(layout2)

            self.setLayout(layout)

            def current_item():
                self.temp = list_view.currentItem()
                self.item = self.temp.text()
                temp = window.databases_names.pop(self.item)
                window.databases_names[self.item] = temp
                window.change_current_database(self.item)
                self.close()


app = QApplication(sys.argv)

window = MainWindow()
window.show()

app.exec()
