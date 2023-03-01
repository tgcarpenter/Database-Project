from PyQt6.QtCore import QStringListModel, Qt, QModelIndex
from PyQt6.QtGui import QFont, QAction, QCursor, QKeySequence, QKeyEvent
from PyQt6.QtWidgets import QLineEdit, QPushButton, QWidget, QLabel, QListWidget, QComboBox, QVBoxLayout, QHBoxLayout, \
    QFormLayout, QSizePolicy, QCompleter, QTableWidget, QHeaderView, QTableWidgetItem, QMenu, QGridLayout, \
    QAbstractItemView, QStyledItemDelegate, QStyleOptionViewItem, QMessageBox

from Databases import Database
from MyWidgets import MySearchLineEdit
from UniversalFunctions import get_signal


class DbNameInputWindow(QWidget):
    def __init__(self, window):
        super().__init__()

        self.window = window
        self.setWindowTitle('Create Database')
        self.setFixedSize(400, 100)
        self.window.center_on_mainwindow(self)

        input_box = QLineEdit()
        input_box.setFixedWidth(250)
        input_box.setMaxLength(40)
        input_box.setFont(QFont('Ariel, 100'))
        input_box.setPlaceholderText('Type Name..')

        self.enter = QPushButton('Enter', self)
        self.enter.setFixedWidth(100)

        input_box.textChanged.connect(lambda: enter_connection())
        input_box.returnPressed.connect(self.enter.click)

        cancel = QPushButton('Cancel', self)
        cancel.setFixedWidth(100)
        cancel.clicked.connect(self.close)

        layout = QFormLayout()
        layout.addRow('Database Name:', input_box)

        layout2 = QHBoxLayout()
        layout2.addWidget(self.enter)
        layout2.addWidget(cancel)

        layout3 = QVBoxLayout()
        layout3.addSpacing(10)
        layout3.addLayout(layout)
        layout3.addLayout(layout2)

        self.setLayout(layout3)

        def enter_connection():
            if input_box.text() != '':
                if self.enter.isSignalConnected(get_signal(self.enter, "clicked")):
                    self.enter.disconnect()

                self.enter.clicked.connect(lambda: self.create_database(input_box.text()))
            else:
                self.enter.disconnect()

    def create_database(self, name):  # this should probably be in mainwindow class
        if self.window.current_database is not None:
            close = self.window.open_save_messagebox()
            if not close:
                return
            self.window.read_settings()
        self.window.databases.append(Database(name))
        self.window.databases_names[name] = self.window.database_amount
        self.window.database_amount += 1
        self.window.change_current_database(name)
        self.window.toolbar.insert_new_column.setEnabled(True)
        self.enter.disconnect()
        self.close()

    def closeEvent(self, event) -> None:
        self.window.setEnabled(True)
        event.accept()


class OpenDbWindow(QWidget):
    def __init__(self, window):
        super().__init__()

        self.window = window
        self.setWindowTitle("Open Database")
        self.setFixedSize(500, 500)
        self.window.center_on_mainwindow(self)

        new_db_button = QPushButton("New Database")
        new_db_button.setMaximumWidth(140)
        new_db_button.clicked.connect(self.close)
        new_db_button.clicked.connect(self.window.make_add_database_window)

        self.del_db_button = QPushButton("Delete Database")
        self.del_db_button.setMaximumWidth(140)
        self.del_db_button.setEnabled(False)
        self.del_db_button.clicked.connect(self.delete_database)

        self.spacer = QWidget()
        self.spacer.setMaximumHeight(24)
        self.spacer.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)

        self.list_view = QListWidget()
        header = QLabel("Select Database:")
        temp_databases = list(window.databases_names.keys())
        temp_databases.reverse()

        try:
            for database in temp_databases:
                self.list_view.addItem(database)
        except:
            pass

        self.list_view.itemDoubleClicked.connect(self.current_item)

        self.enter = QPushButton('Enter', self)
        self.enter.setFixedWidth(100)

        self.list_view.itemClicked.connect(self.enter_connection)

        cancel = QPushButton('Cancel', self)
        cancel.setFixedWidth(100)
        cancel.clicked.connect(self.close)

        self.filter = self.window.EnterKeyFilter()
        self.list_view.installEventFilter(self.filter)
        self.filter.enterKeyPressed.connect(self.enter.click)

        layout = QVBoxLayout()
        layout2 = QHBoxLayout()
        layout2.addWidget(header)
        layout2.addWidget(self.spacer)
        layout2.addWidget(self.del_db_button)
        layout2.addWidget(new_db_button)

        layout3 = QHBoxLayout()
        layout3.addWidget(self.enter)
        layout3.addWidget(cancel)

        layout.addLayout(layout2)
        layout.addWidget(self.list_view)
        layout.addLayout(layout3)

        self.setLayout(layout)

    def enter_connection(self):
        if self.enter.isSignalConnected(get_signal(self.enter, "clicked")):
            self.enter.disconnect()
        self.enter.clicked.connect(self.current_item)
        self.del_db_button.setEnabled(True)

    def current_item(self):
        if self.window.current_database is not None:
            close = self.window.open_save_messagebox()
            if not close:
                self.setFocus()
                return
            self.window.read_settings()
        temp = self.list_view.currentItem()
        item = temp.text()
        temp = self.window.databases_names.pop(item)
        self.window.databases_names[item] = temp
        self.window.change_current_database(item)
        self.close()

    def delete_database(self):
        name = self.list_view.currentItem().text()
        ret = QMessageBox.warning(self, "Delete", f"Are you sure you would like to delete "
                                                  f"{name}? \n Deleting a Database is permanent",
                                  QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                  QMessageBox.StandardButton.No)
        if ret == QMessageBox.StandardButton.No:
            return
        else:
            pos = self.window.databases_names[name]
            self.window.databases[pos].delete_database()
            self.window.databases.pop(pos)
            self.window.databases_names.pop(name)
            if pos == self.window.current_database and len(self.window.databases) > 0:
                self.list_view.takeItem(self.list_view.currentRow())
                self.window.change_current_database(self.list_view.item(0).text())
            else:
                self.window.close_current_database()
            self.window.save()
            self.close()

    def closeEvent(self, event) -> None:
        self.window.setEnabled(True)
        event.accept()


class AddNewColumn(QWidget):
    def __init__(self, window):
        super().__init__()

        self.window = window
        self.setWindowTitle("Create New Column")
        self.setFixedSize(400, 115)
        self.window.center_on_mainwindow(self)

        self.tips = ["Integer Columns contain numerical values i.e. 'counts', 'totals' or 'age'",
                     "Text Columns contain single input text items i.e. 'first name', 'notes', or 'dates'",
                     "List Columns contain a list of objects separated by ', ' between each entry i.e. "
                     "'eggs, bread, bacon'"]
        self.names = ["Integer Column", "Text Column", "List Column"]

        columns_list = QComboBox()
        columns_list.setPlaceholderText("Column Type...")
        for i in range(3):
            columns_list.addItem(self.names[i])
            columns_list.setItemData(i, self.tips[i], Qt.ItemDataRole.ToolTipRole)

        columns_list.currentIndexChanged.connect(self.update_description)

        label = QLabel("Column Type:   ")
        label2 = QLabel("Column Name:")
        self.description_label = QLabel()
        self.description_label.setWordWrap(True)
        self.description_label.setStyleSheet("color: red")
        self.description_label.hide()

        input_box = QLineEdit()
        input_box.setMaxLength(40)
        input_box.setPlaceholderText("Type Column Name..")

        self.enter = QPushButton("Enter", self)
        self.enter.setFixedWidth(100)

        columns_list.currentIndexChanged.connect(lambda: enter_connection())
        input_box.textChanged.connect(lambda: enter_connection())

        def enter_connection():
            if columns_list.currentIndex() != -1 and input_box.text() != '':
                self.enter.clicked.connect(lambda: self.window.add_new_column(columns_list.currentIndex(),
                                                                              input_box.text().strip()))
            else:
                try:
                    self.enter.disconnect()
                except TypeError:
                    pass

        cancel = QPushButton('Cancel', self)
        cancel.setFixedWidth(100)
        cancel.clicked.connect(self.close)

        self.filter = self.window.EnterKeyFilter()
        input_box.installEventFilter(self.filter)
        self.filter.enterKeyPressed.connect(self.enter.click)

        layout = QVBoxLayout()
        layout2 = QGridLayout()
        layout3 = QHBoxLayout()
        layout2.addWidget(label)
        layout2.addWidget(columns_list, 0, 1)
        layout2.addWidget(label2)
        layout2.addWidget(input_box, 1, 1)
        layout3.addWidget(self.enter)
        layout3.addWidget(cancel)
        layout.addLayout(layout2)
        layout.addWidget(self.description_label)
        layout.addLayout(layout3)

        self.setLayout(layout)

    def update_description(self, sel):
        if sel == -1:
            self.setFixedSize(400, 115)
            self.description_label.hide()
            return
        self.setFixedSize(400, 145)
        self.description_label.setText(self.tips[sel])
        self.description_label.show()

    def closeEvent(self, event) -> None:
        self.window.setEnabled(True)
        event.accept()


class SearchWindow(QWidget):
    def __init__(self, window):
        super().__init__()

        self.window = window
        self.setWindowTitle("Database Search")
        self.resize(700, 500)
        self.window.center_on_mainwindow(self)
        # setting up search bar and connection to search
        self.search_bar = MySearchLineEdit(self)
        self.search_bar.setFixedSize(180, 25)
        self.search_bar.setPlaceholderText("Search")
        self.search_bar.textChanged.connect(self.search_database)
        self.search_bar.textChanged.connect(self.autofill)
        # setting up completer and completer model
        self.completer = QCompleter()
        self.completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.completer_model = QStringListModel()
        self.completer.setModel(self.completer_model)
        self.search_bar.setCompleter(self.completer)
        # setting up table to update database
        self.search_table = QTableWidget()
        self.search_table.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.search_table.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.search_table.verticalHeader().setMinimumSectionSize(24)
        self.search_table.setSortingEnabled(True)
        self.search_table.cellChanged.connect(self.update_database)
        self.search_table.itemSelectionChanged.connect(self.change_selected)
        # setting header context menu
        self.search_table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.search_table.verticalHeader().setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.search_table.verticalHeader().customContextMenuRequested.connect(self.open_context)
        # accounting for tab irregularities useless
        # self.tableFilter = self.window.TableFilter(self.search_table)
        # self.search_table.installEventFilter(self.tableFilter)
        # making context menus
        self.make_context_menus()

        layout = QVBoxLayout()
        layout.addWidget(self.search_bar, alignment=Qt.AlignmentFlag.AlignRight)
        layout.addWidget(self.search_table)

        self.setLayout(layout)

    def search_database(self, text):
        self.search_table.blockSignals(True)
        if not text:  # If nothing is the search bar, passes search and restores default
            self.search_table.setColumnCount(0)
            self.search_table.setRowCount(0)
            return
        search_query = self.window.databases[self.window.current_database].general_query(search=text)
        if not search_query:  # If nothing is returned, passes search and restores default
            self.search_table.setColumnCount(0)
            self.search_table.setRowCount(0)
            return
        print(search_query)
        self.search_table.setColumnCount(len(search_query[0]))
        self.search_table.setRowCount(len(search_query))
        self.search_table.setHorizontalHeaderLabels(
            self.window.databases[self.window.current_database].get_column_headers())
        self.search_table.setVerticalHeaderLabels([str(row[0]) for row in search_query])
        self.search_table.horizontalHeader().hideSection(0)
        for row in range(len(search_query)):  # assigning queried statement to cells
            count = 0
            for cell in search_query[row]:
                if cell is None:
                    cell = ''
                item = QTableWidgetItem(str(cell))
                self.search_table.setItem(row, count, item)
                count += 1
        for i, size in enumerate(
                self.window.header_sizes[self.window.databases[self.window.current_database].name[:-3]]):
            self.search_table.horizontalHeader().resizeSection(i + 1, size)
        self.search_table.blockSignals(False)

    def autofill(self, search_text):
        if not search_text:
            return
        autofill = self.window.databases[self.window.current_database].autofill_query(search_text)
        self.completer_model.setStringList([str(a[0]) for a in autofill])
        self.completer.popup().resize(180, 24 * len(autofill))
        print("completer", self.completer_model.stringList())
        self.search_bar.setFocus()

    def update_database(self, row, column):
        self.window.update_cell(int(self.search_table.item(row, 0).text()) - self.window.table_query_start, column - 1,
                                self.search_table.currentItem().text() if self.search_table.currentItem() else '')

    def change_selected(self):
        self.blockSignals(True)
        self.window.change_selected(self.search_table.currentItem().text() if self.search_table.currentItem() else None)
        self.blockSignals(False)

    def make_context_menus(self):
        self.context = QMenu()

        self.go_to_action = QAction("Go To Row")
        self.go_to_action.triggered.connect(self.go_to)

        self.context.addAction(self.go_to_action)

    def open_context(self, pos):
        self.context.popup(QCursor.pos())
        vIndex = self.search_table.verticalHeader().logicalIndexAt(pos)
        self.search_table.verticalHeader().sectionPressed.emit(vIndex)
        row = int(self.search_table.verticalHeaderItem(vIndex).text())
        self.go_to_action.triggered.disconnect()
        self.go_to_action.triggered.connect(lambda: self.go_to(row))

    def go_to(self, row):
        self.close()
        self.window.scroll_to(row)

    def closeEvent(self, event) -> None:
        self.hide()
        self.window.setEnabled(True)
        self.window.query_database()
        event.accept()


class EditHotKeys(QWidget):
    def __init__(self, window, hotkeys):
        super(EditHotKeys, self).__init__()
        self.window = window
        self.setWindowTitle("Edit Hot Keys")
        self.setFixedSize(375, 450)
        self.hotkeys = hotkeys
        self.change = False

        self.hotKeyWindow = QTableWidget()
        self.hotKeyWindow.setRowCount(len(hotkeys))
        self.hotKeyWindow.setColumnCount(2)
        self.hotKeyWindow.horizontalHeader().hide()
        self.hotKeyWindow.verticalHeader().hide()
        self.hotKeyWindow.setStyleSheet("QTableWidget {gridline-color: transparent}")
        self.hotKeyWindow.setEditTriggers(QAbstractItemView.EditTrigger.AllEditTriggers)

        self.hotKeyWindow.setItemDelegate(self.Delegate(self.window))

        self.hotKeyWindow.cellChanged.connect(self.hotKeyWindow.clearSelection)
        self.hotKeyWindow.cellChanged.connect(self.hotKeyWindow.clearFocus)
        self.hotKeyWindow.cellChanged.connect(self.changed)

        self.hotKeyWindow.blockSignals(True)
        count = 0
        for item in hotkeys:
            add = QTableWidgetItem(item[0])
            add.setFlags(add.flags() & Qt.ItemFlag.ItemIsEditable)
            add2 = QTableWidgetItem(item[1])
            self.hotKeyWindow.setItem(count, 0, add)
            self.hotKeyWindow.setItem(count, 1, add2)
            count += 1
        self.hotKeyWindow.horizontalHeader().resizeSection(0, 250)
        self.hotKeyWindow.blockSignals(False)

        self.apply = QPushButton("Apply")
        self.apply.setFixedWidth(150)
        self.apply.pressed.connect(self.set_shortcut)

        restore_defaults = QPushButton("Restore Defaults")
        restore_defaults.setFixedWidth(150)
        restore_defaults.pressed.connect(window.restore_defaults)
        restore_defaults.pressed.connect(self.close)

        layout = QVBoxLayout()
        layout2 = QHBoxLayout()
        layout2.addWidget(restore_defaults)
        layout2.addWidget(self.apply)
        layout.addWidget(self.hotKeyWindow)
        layout.addLayout(layout2)
        self.setLayout(layout)

    def changed(self):
        self.change = True

    def set_shortcut(self):
        if self.change:
            for index in range(len(self.hotkeys)):
                print('cur', self.hotKeyWindow.currentItem().text())
                self.hotkeys[index][1] = self.hotKeyWindow.item(index, 1).text()
                for o in self.hotkeys[index][2]:
                    o.setShortcut(self.hotKeyWindow.item(index, 1).text().replace(" ", ""))
        self.change = False

    def closeEvent(self, event) -> None:
        self.window.setEnabled(True)
        if self.change:
            question_box = QMessageBox.question(self, "Close", "Would you like to apply your changes before closing?",
                                                QMessageBox.StandardButton.Cancel | QMessageBox.StandardButton.Apply
                                                | QMessageBox.StandardButton.Close)
            if question_box == QMessageBox.StandardButton.Cancel:
                event.ignore()
                return
            elif question_box == QMessageBox.StandardButton.Close:
                event.accept()
                return
            else:
                self.apply.pressed.emit()

        event.accept()

    class Delegate(QStyledItemDelegate):

        def __init__(self, window):
            super().__init__()
            self.window = window

        def createEditor(self, parent: QWidget, option: 'QStyleOptionViewItem', index: QModelIndex) -> QWidget:
            editor = self.Editor(parent, self.window, self)
            return editor

        class Editor(QLineEdit):

            def __init__(self, parent, window, delegate):
                super().__init__()
                self.setParent(parent)
                self.window = window
                self.delegate = delegate
                self.setReadOnly(True)
                self.new_text = []

            def keyPressEvent(self, a0: QKeyEvent) -> None:
                if a0.isAutoRepeat():
                    return
                if Qt.KeyboardModifier.ControlModifier in a0.keyCombination().keyboardModifiers():
                    if "Ctrl" not in self.new_text:
                        self.new_text.append("Ctrl")
                    print("ctrl")
                if Qt.KeyboardModifier.AltModifier in a0.keyCombination().keyboardModifiers():
                    if "Alt" not in self.new_text:
                        self.new_text.append("Alt")
                    print("alt")
                if Qt.KeyboardModifier.ShiftModifier in a0.keyCombination().keyboardModifiers():
                    if "Shift" not in self.new_text:
                        self.new_text.append("Shift")
                    print("shift")
                if a0.key() not in (Qt.Key.Key_Control, Qt.Key.Key_Shift, Qt.Key.Key_Alt):
                    key = QKeySequence(a0.key()).toString()
                    if key in ("!", "@", "#", "$", "%", "^", "&", "*", "(", ")", "_", "+", "{", "}", ":", '"', "<", ">",
                               "?", "~", "|"):
                        key = self.convert_sym(key)
                    self.new_text.append(key)
                    print(QKeySequence(a0.key()).toString())
                self.clear()
                return

            def keyReleaseEvent(self, a0: QKeyEvent) -> None:
                if a0.isAutoRepeat():
                    return
                if self.new_text:
                    self.new_text.sort(key=self.sort_function)
                    self.setText(" + ".join(self.new_text))
                else:
                    self.setText(self.window.hotkeys[self.window.window6.hotKeyWindow.currentRow()][1])
                self.new_text = []
                self.delegate.commitData.emit(self)
                self.delegate.closeEditor.emit(self)
                self.window.window6.hotKeyWindow.cellChanged.emit(0, 0)
                return

            @staticmethod
            def sort_function(e: str):
                if e == "Ctrl":
                    return 1
                if e == "Alt":
                    return 2
                if e == "Shift":
                    return 3
                else:
                    return int("".join(format(ord(i), 'b').zfill(8) for i in e))

            @staticmethod
            def convert_sym(sym):  # A manual key entry converter for the hotkey window
                if sym == "!":
                    return "1"
                elif sym == "~":
                    return "`"
                elif sym == "@":
                    return "2"
                elif sym == "#":
                    return "3"
                elif sym == "$":
                    return "4"
                elif sym == "%":
                    return "5"
                elif sym == "^":
                    return "6"
                elif sym == "&":
                    return "7"
                elif sym == "*":
                    return "8"
                elif sym == "(":
                    return "9"
                elif sym == ")":
                    return "0"
                elif sym == "_":
                    return "-"
                elif sym == "+":
                    return "="
                elif sym == "{":
                    return "["
                elif sym == "}":
                    return "]"
                elif sym == "|":
                    return r"\ ".strip()
                elif sym == ":":
                    return ";"
                elif sym == '"':
                    return "'"
                elif sym == "<":
                    return ","
                elif sym == ">":
                    return "."
                elif sym == "?":
                    return "/"
