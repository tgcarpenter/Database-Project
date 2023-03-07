import sys

from Databases import *

from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtMultimedia import *

from PopupWindows import *
from MenusandToolbars import *
from MyWidgets import MyLineEdit, MyComboBox, MySpinBox, MyHHeaderView
from UniversalFunctions import get_signal


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # other windows
        self.window7 = None
        self.window6 = None
        self.window5 = None
        self.window4 = None
        self.window3 = None
        self.window2 = None

        # main window
        self.resize(800, 600)
        self.setMinimumHeight(200)
        self.setMinimumWidth(400)
        # centering
        self.center_window(self)

        # values stored in settings to be overwritten when settings read
        self.setWindowTitle("Database Organiser")
        self.databases_names = {}  # Will be stored as database name: position in databases
        self.databases = []  # list that stores all database interaction configs created by user
        self.database_amount = 0  # number of databases
        self.current_database = None  # Stores currently accessed Database position in self.databases
        self.table_query_start = 1  # Position of start of General Query
        self.table_query_end = 1  # Position of end of General Query
        self.selected_item = str()  # holds old value of item before change
        self.query_switch = False  # helps process queries faster when alot are performed at once
        self.header_sizes = {}  # dictionary that holds a list of each databases header sizes as [db name]
        self.first_cell_size = 0
        self.backup_num = 0
        self.rename_updates = []

        try:
            self.read_settings()
            pass
        except:
            pass

        #self.databases[self.current_database].row_count += 4
        # self.database_amount = 1

        self.signalMapper = QSignalMapper()
        self.signalMapper.mappedInt.connect(self.update_cell)

        # making menu bars
        self.file_menu = FileMenu(self)
        self.menuBar().addMenu(self.file_menu)
        self.edit_menu = EditMenu(self)
        self.menuBar().addMenu(self.edit_menu)
        self.tool_menu = ToolMenu(self)
        self.menuBar().addMenu(self.tool_menu)

        # making table
        self.table = QTableWidget()
        self.table.setWordWrap(True)

        # making toolbar
        self.option_bar = OptionBar(self)
        self.toolbar = ToolBar(self)

        # updating the database when the value of a cell is changed
        self.table.cellChanged.connect(self.update_cell)
        self.table.cellChanged.connect(self.change_selected)
        self.table.itemSelectionChanged.connect(self.change_selected)

        # installing table filter
        self.table_filter = self.TableFilter(self.table)
        self.table.installEventFilter(self.table_filter)

        # creating context menus
        self.h_header_context_menu = ContextMenus(self, self.toolbar, "h_header")
        self.v_header_context_menu = ContextMenus(self, self.toolbar, "v_header")
        self.table_context_menu = ContextMenus(self, self.toolbar, "table")

        self.context_filter = self.ContextFilter()  # not used

        # status bar
        self.setStatusBar(QStatusBar())
        self.table.cellEntered.connect(self.set_cell_status)
        self.table.setMouseTracking(True)

        # horizontal Header
        self.table.setHorizontalHeader(MyHHeaderView(self.table))
        self.table.horizontalHeader().customContextMenuRequested.connect(self.open_h_header_context)

        self.table_filter.selectColumn.connect(lambda: self.table.horizontalHeader().sectionPressed.
                                               emit(self.table.currentColumn()))
        self.table.horizontalHeader().headerLabelChanged.connect(self.hold_column_name)

        self.table.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)

            # Resizing the table based on text wrap
        self.table.horizontalHeader().sectionResized.connect(self.resize_vertical)

            # updating column order when column moved
        self.table.horizontalHeader().sectionMoved.connect(self.move_column)

            # connecting toolbar buttons (some anyway)
        self.table.horizontalHeader().sectionClicked.connect(self.activate_column_delete)
        self.table.itemSelectionChanged.connect(self.deactivate_column_delete)

        # vertical Header
        self.table.verticalHeader().setMinimumSectionSize(24)
        self.table.verticalHeader().setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.verticalHeader().customContextMenuRequested.connect(self.open_v_header_context)

        self.table_filter.selectRow.connect(lambda: self.table.verticalHeader().sectionPressed.
                                            emit(self.table.currentRow()))

            # Resizing the table based on text wrap
        self.table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)

            # connecting toolbar buttons (some anyway)
        self.table.verticalHeader().sectionPressed.connect(self.activate_row_delete)
        self.table.itemSelectionChanged.connect(self.deactivate_row_delete)

        # table
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.open_table_context)

            # making and connecting vertical scroll bars
        self.table.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.table.verticalScrollBar().rangeChanged.connect(self.v_scrollbar_resize)
        self.table.verticalScrollBar().installEventFilter(self)

        self.scrollbar = QScrollBar()
        self.scrollbar.setMinimum(1)
        self.set_scrollbar_max()
        self.scrollbar.valueChanged.connect(self.connect_scroll_bars)
        self.scrollbar.valueChanged.connect(self.deselect_input_widgets)
        self.scrollbar_total = 1

        if self.current_database is not None and len(self.databases[self.current_database].column_classes):
            self.table.setColumnCount(len(self.header_sizes[self.databases[self.current_database].name[:-3]]))
            self.resize_headers()

        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.default_hotkeys = [["Close Database", "Ctrl + F4", [self.file_menu.close_action]],
                                ["Delete Current Column", "Ctrl + Alt + D", [self.toolbar.delete_cur_column]],
                                ["Delete Selected Row", "Ctrl + D", [self.toolbar.delete_cur_row]],
                                ["Insert New Column", "Ctrl + Alt + N", [self.toolbar.insert_new_column]],
                                ["Insert New Row", "Ctrl + R", [self.toolbar.insert_row_action]],
                                ["New Database", "Ctrl + N", [self.file_menu.add_db_action]],
                                ["Open Database", "Ctrl + O", [self.file_menu.open_db_action]],
                                ["Save Database", "Ctrl + S", [self.file_menu.save_action]],
                                ["Search Database", "Ctrl + F", [self.toolbar.search_button]],
                                ["Select Column", "Ctrl + Space", (self.h_header_context_menu.sColumn_action,
                                                                   self.table_context_menu.tSColumn_action)],
                                ["Select Row", "Shift + Space", (self.v_header_context_menu.sRow_action,
                                                                 self.table_context_menu.tSRow_action)]]
        self.hotkeys = [["Close Database", "Ctrl + F4", [self.file_menu.close_action]],
                        ["Delete Current Column", "Ctrl + Alt + D", [self.toolbar.delete_cur_column]],
                        ["Delete Selected Row", "Ctrl + D", [self.toolbar.delete_cur_row]],
                        ["Insert New Column", "Ctrl + Alt + N", [self.toolbar.insert_new_column]],
                        ["Insert New Row", "Ctrl + R", [self.toolbar.insert_row_action]],
                        ["New Database", "Ctrl + N", [self.file_menu.add_db_action]],
                        ["Open Database", "Ctrl + O", [self.file_menu.open_db_action]],
                        ["Save Database", "Ctrl + S", [self.file_menu.save_action]],
                        ["Search Database", "Ctrl + F", [self.toolbar.search_button]],
                        ["Select Column", "Ctrl + Space", (self.h_header_context_menu.sColumn_action,
                                                           self.table_context_menu.tSColumn_action)],
                        ["Select Row", "Shift + Space", (self.v_header_context_menu.sRow_action,
                                                         self.table_context_menu.tSRow_action)]]
        self.load_hotkeys()
        self.assign_hotkeys()

        # making group box's
        outside_box = QGroupBox("Database Organiser")
        self.information_box = QGroupBox("Details")
        self.information_box.setMaximumWidth(1000)
        self.information_box.setMinimumWidth(500)
        self.information_box.hide()
        # layouts in descending order
        layout = QVBoxLayout()
        layout4 = QHBoxLayout()
        layout5 = QHBoxLayout()
        information_box_layout = QHBoxLayout()
        self.information_box_header_layout = QVBoxLayout()
        self.information_box_widget_layout = QVBoxLayout()
        information_box_layout.addLayout(self.information_box_header_layout)
        information_box_layout.addLayout(self.information_box_widget_layout)
        button = HideButton(self.information_box, "up")
        information_box_layout.addWidget(button)
        information_box_layout.setAlignment(button, Qt.AlignmentFlag.AlignTop)
        # table/scrollbar
        layout4.addWidget(self.table)
        layout4.addWidget(self.scrollbar)
        outside_box.setLayout(layout4)
        layout.addWidget(outside_box)
        self.information_box.setLayout(information_box_layout)
        layout5.addWidget(spacer)
        layout5.addWidget(self.information_box)
        layout5.addWidget(spacer)
        layout.addLayout(layout5)
        # dynamically adding input widgets
        self.dynam_add_input_widgets()
        # connecting input widgets when vertical header is pressed
        self.table.verticalHeader().sectionPressed.connect(self.connect_selected_to_widgets)
        self.table.itemSelectionChanged.connect(self.information_box.hide)
        self.scrollbar.valueChanged.connect(self.information_box.hide)

        widget = QWidget()
        widget.setLayout(layout)

        self.setCentralWidget(widget)
        self.repaint()

        # Gui Widgets control

    def assign_hotkeys(self):
        for key in self.hotkeys:
            for widget in key[2]:
                widget.setShortcut(key[1].replace(" ", ""))

    def restore_defaults(self):
        for i in range(len(self.default_hotkeys)):
            self.hotkeys[i][1] = self.default_hotkeys[i][1]
        self.assign_hotkeys()

    def open_h_header_context(self, pos):
        self.h_header_context_menu.popup(QCursor.pos())
        hIndex = self.table.horizontalHeader().logicalIndexAt(pos)
        if self.h_header_context_menu.sColumn_action. \
                isSignalConnected(get_signal(self.h_header_context_menu.sColumn_action, "triggered")):
            self.h_header_context_menu.sColumn_action.triggered.disconnect()
        self.h_header_context_menu.sColumn_action.triggered. \
            connect(lambda: self.table.horizontalHeader().sectionPressed.emit(hIndex))
        self.h_header_context_menu.sColumn_action.triggered. \
            connect(self.h_header_context_menu.sColumn_action.triggered.disconnect)
        print("h header context created")
        print(self.table.horizontalHeader().count())

    def open_v_header_context(self, pos):
        self.v_header_context_menu.popup(QCursor.pos())
        vIndex = self.table.verticalHeader().logicalIndexAt(pos)
        if self.v_header_context_menu.sRow_action. \
                isSignalConnected(get_signal(self.v_header_context_menu.sRow_action, "triggered")):
            self.v_header_context_menu.sRow_action.triggered.disconnect()
        self.v_header_context_menu.sRow_action.triggered. \
            connect(lambda: self.table.verticalHeader().sectionPressed.emit(vIndex))
        self.v_header_context_menu.sRow_action.triggered. \
            connect(self.v_header_context_menu.sRow_action.triggered.disconnect)
        print("v header context created")

    def open_table_context(self):
        self.table_context_menu.popup(QCursor.pos())
        print("table context emitted")

    def set_cell_status(self, row, column):  # used to find and display status bar info
        if self.table.itemAt(self.table.viewport().mapFromGlobal(QCursor.pos())) is not None:
            data = self.table.itemAt(self.table.viewport().mapFromGlobal(QCursor.pos())).text()
            self.statusBar().showMessage(f"Row: {self.table_query_start + row}, Column: {column}, "
                                         f"Entry: {data}")

    def activate_row_delete(self):
        self.toolbar.delete_cur_row.setEnabled(True)

    def deactivate_row_delete(self):
        self.toolbar.delete_cur_row.setDisabled(True)

    def activate_column_delete(self):
        self.toolbar.delete_cur_column.setEnabled(True)

    def deactivate_column_delete(self):
        self.toolbar.delete_cur_column.setDisabled(True)

    def dynam_add_input_widgets(self):
        if self.current_database is not None and self.databases[self.current_database].row_count > 0:
            for col in self.databases[self.current_database].column_classes:
                if col.table_name[1] == "T":
                    self.add_text_input_widget(col.column_name[2:-1])
                elif col.table_name[1] == "L":
                    self.add_list_input_widget(col.column_name[2:-1])  # change later - temp
                else:
                    self.add_integer_input_widget(col.column_name[2:-1])

    def add_integer_input_widget(self, col_name: str):
        int_input = MySpinBox(self)
        int_input.setRange(-9999, 9999)
        int_input.editingFinished.connect(self.signalMapper.map)
        header = QLabel(col_name + ":")
        self.information_box_header_layout.addWidget(header)
        self.information_box_widget_layout.addWidget(int_input)

    def add_text_input_widget(self, col_name: str):
        text_input = MyLineEdit(col_name, self)
        text_input.editingFinished.connect(self.signalMapper.map)
        header = QLabel(col_name + ":")
        self.information_box_header_layout.addWidget(header)
        self.information_box_widget_layout.addWidget(text_input)

    def add_list_input_widget(self, col_name: str):  # - may do this later, have to figure out formatting
        list_input = MyComboBox(col_name, self)
        list_input.currentTextChanged.connect(self.signalMapper.map)
        header = QLabel(col_name + ":")
        self.information_box_header_layout.addWidget(header)
        self.information_box_widget_layout.addWidget(list_input)

    def clearLayout(self, layout: QLayout):
        if layout is not None:
            while layout.count():
                child = layout.takeAt(0)
                if child.widget() is not None:
                    child.widget().deleteLater()
                elif child.layout() is not None:
                    self.clearLayout(child.layout())

    def connect_selected_to_widgets(self):  # updated table when widget is changed as well as updates database when
        self.information_box.setHidden(False)  # widget is done being edited
        for i, col in zip(range(0, self.information_box_widget_layout.count()),
                          self.databases[self.current_database].column_classes):

            input_widget = self.information_box_widget_layout.itemAt(i).widget()  # setting widget pointer

            if i >= len(self.table.selectedItems()):  # temporary solution. it might not work after i
                continue  # implement some other features

            if col.table_name[1] == "T":  # handles text and list columns
                if input_widget.isSignalConnected(get_signal(input_widget, "textChanged")):
                    input_widget.textChanged.disconnect()
                    print("textChanged disconnected")
                if self.table.selectedItems()[i].text():
                    input_widget.setText(self.table.selectedItems()[i].text())
                else:
                    input_widget.setText("")
                input_widget.textChanged.connect(self.table.item(self.table.currentRow(), i).setText)
                # connecting to update database when changed made
                input_widget.firstClicked.connect(self.change_selected)
                self.signalMapper.setMapping(input_widget, i)
                input_widget.set_autofill()

            elif col.table_name[1] == "L":
                if input_widget.lineEdit().isSignalConnected(get_signal(input_widget.lineEdit(), "textChanged")):
                    input_widget.lineEdit().textChanged.disconnect()
                    print("textChanged disconnected")
                input_widget.blockSignals(True)
                input_widget.set_autofill()
                if self.table.selectedItems()[i].text():
                    input_widget.lineEdit().setText(self.table.selectedItems()[i].text())
                else:
                    input_widget.lineEdit().setText("")
                input_widget.blockSignals(False)
                input_widget.lineEdit().textChanged.connect(self.table.item(self.table.currentRow(), i).setText)
                # connecting to update database when changed made
                input_widget.firstClicked.connect(self.change_selected)
                self.signalMapper.setMapping(input_widget, i)

            else:  # handles integer columns
                if input_widget.isSignalConnected(get_signal(input_widget, "textChanged")):
                    input_widget.textChanged.disconnect()
                if self.table.selectedItems()[i].text():
                    input_widget.setValue(int(self.table.selectedItems()[i].text()))
                else:
                    input_widget.setValue(0)
                input_widget.textChanged.connect(
                    self.table.item(self.table.currentRow(), i).setText)
                # connecting to update database when change made
                input_widget.firstClicked.connect(self.change_selected)
                self.signalMapper.setMapping(input_widget, i)

    def deselect_input_widgets(self):
        for i in range(0, self.information_box_widget_layout.count()):
            input_widget = self.information_box_widget_layout.itemAt(i).widget()
            if input_widget.hasFocus():
                input_widget.clearFocus()
                return

        # Gui media functions

    def connect_scroll_bars(self, s_value: int):
        self.scrollbar.blockSignals(True)
        while s_value < self.scrollbar_total:  # scrolling up
            self.table_query_start -= 1
            if self.table_query_start < 1:  # failsafe, shouldn't be needed
                self.table_query_start = 1
            self.table_query_end -= 1
            self.scroll_query(True)
            self.scrollbar_total -= self.first_cell_size
            if self.scrollbar.value() < 2:  # to catch instances where cell sizes are adjusted
                self.scrollbar_total = 1
                self.table_query_end = self.table_query_end - (self.table_query_start - 1)
                self.table_query_start = 1
                self.query_database()
            self.table.verticalScrollBar().setValue(s_value - self.scrollbar_total - 1)
            if self.first_cell_size > 24:
                self.scrollbar.setMaximum(self.scrollbar.maximum() - (self.first_cell_size - 24))
        while s_value > self.scrollbar_total + self.first_cell_size:  # scrolling down
            self.scrollbar_total += self.first_cell_size
            self.table_query_start += 1
            self.table_query_end += 1
            if self.first_cell_size > 24:
                self.scrollbar.setMaximum(self.scrollbar.maximum() + self.first_cell_size - 24)
            self.scroll_query(False)
            self.table.verticalScrollBar().setValue(s_value - self.scrollbar_total - 1)
        self.table.verticalScrollBar().setValue(s_value - self.scrollbar_total)
        self.update_v_headers()
        self.scrollbar.blockSignals(False)

    def scroll_to(self, row: int):
        if int(self.table.verticalHeaderItem(0).text()) == row:
            return
        elif int(self.table.verticalHeaderItem(0).text()) > row:
            amount = -24
        else:
            amount = 24

        while int(self.table.verticalHeaderItem(0).text()) != row:
            self.scrollbar.setValue(self.scrollbar.value() + amount)

        if self.table.verticalScrollBar().value() != 0:
            self.scrollbar.setValue(self.scrollbar.value() - self.table.verticalScrollBar().value())

        self.table.verticalHeader().sectionPressed.emit(0)

    # Retrieving the current size of the first cell
    def resize_vertical(self):
        self.table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.first_cell_size = self.table.verticalHeader().sectionSize(0)

    def v_scrollbar_resize(self, _, ma):  # used to resize scrollbar to always allow scrolling when when
                                            # scrollbar wouldn't exist
        if ma < 25:
            self.table.verticalScrollBar().setMaximum(self.first_cell_size)

        # Database Controls

    def query_database(self):
        self.table.blockSignals(True)
        if self.current_database is None:
            self.table.blockSignals(False)
            self.table.setColumnCount(0)
            self.update_row_count(0)
            return
        elif self.table_query_end == 0:
            self.table.blockSignals(False)
            self.update_column_count()
            self.update_row_count(0)
            return

        query = self.databases[self.current_database].general_query(self.table_query_start, self.table_query_end)
        self.update_column_count()  # setting table size might be able to get rid of this
        self.update_row_count(len(query))
        self.update_v_headers()
        for row in range(len(query)):  # assigning queried statement to cells
            count = 0
            for cell in query[row][1:]:
                if cell is None:
                    cell = ''
                item = QTableWidgetItem(str(cell))
                self.table.setItem(row, count, item)
                count += 1
        self.table.blockSignals(False)
        self.first_cell_size = self.table.verticalHeader().sectionSize(0)

    def scroll_query(self, top=True):
        self.table.blockSignals(True)
        if top:  # scrolling up
            query = self.databases[self.current_database].general_query(self.table_query_start, self.table_query_start)
            # print("maximum", self.table.verticalScrollBar().maximum(), "first cell size", self.first_cell_size)
            if self.table_query_start < \
                    self.databases[self.current_database].row_count - (self.table_query_end - self.table_query_start):
                self.table.removeRow(self.table.rowCount() - 1)
            self.table.insertRow(0)
            for count, cell in enumerate(query[0][1:]):  # assigning queried statement to cells
                if cell is None:
                    cell = ''
                item = QTableWidgetItem(str(cell))
                self.table.setItem(0, count, item)
        else:  # Scrolling down
            query = self.databases[self.current_database].general_query(self.table_query_end, self.table_query_end)
            self.table.removeRow(0)
            # print("maximum", self.table.verticalScrollBar().maximum(), "first cell size", self.first_cell_size)
            if query and self.table.verticalScrollBar().maximum() > self.first_cell_size:
                self.table.insertRow(self.table.rowCount())
                for count, cell in enumerate(query[0][1:]):  # assigning queried statement to cells
                    if cell is None:
                        cell = ''
                    item = QTableWidgetItem(str(cell))
                    self.table.setItem(self.table.rowCount() - 1, count, item)
        self.table.blockSignals(False)
        self.first_cell_size = self.table.verticalHeader().sectionSize(0)

    def add_new_row(self):
        if self.current_database is None or not self.databases[self.current_database].column_classes:  # isn't used
            self.error_sound.play()
            return
        self.toolbar.insert_row_action.blockSignals(True)
        self.databases[self.current_database].add_defaults()
        if self.databases[self.current_database].row_count == 1:
            self.dynam_add_input_widgets()
        self.resizeEvent(self.geometry())
        if self.table_query_end > 1:
            if self.table_query_end == 2:
                self.scrollbar.setMinimum(1)
            self.scrollbar.setMaximum(self.scrollbar.maximum() + 24)
            if self.databases[self.current_database].row_count > self.table_query_end:
                while self.scrollbar.value() != self.scrollbar.maximum():
                    self.scrollbar.setValue(self.scrollbar.maximum())
        self.table.clearSelection()
        self.toolbar.insert_row_action.blockSignals(False)
        print('new row added')

    def delete_row(self):
        print([obj.text() for obj in self.table.selectedItems()])
        self.scrollbar.setMaximum(self.scrollbar.maximum()
                                  - self.table.verticalHeader().sectionSize(self.table.currentRow()))
        self.databases[self.current_database].delete_row([obj.text() for obj in self.table.selectedItems()],
                                                         self.table_query_start + self.table.currentRow())
        self.query_database()
        self.table.verticalHeader().sectionPressed.emit(self.table.currentRow())

    def delete_empty_rows(self):
        if self.current_database is not None:
            self.databases[self.current_database].clear_empty_rows()
            self.query_database()

    def add_new_column(self, column: int, name: str):
        if column == 0:
            self.databases[self.current_database].add_column_integer(name)
            if self.databases[self.current_database].row_count > 0:
                self.add_integer_input_widget(name)
        elif column == 1:
            self.databases[self.current_database].add_column_text(name)
            if self.databases[self.current_database].row_count > 0:
                self.add_text_input_widget(name)
        else:
            self.databases[self.current_database].add_column_list(name)
            if self.databases[self.current_database].row_count > 0:
                self.add_list_input_widget(name)
        self.update_column_count()  # does this need to be here?
        new_header_label = QTableWidgetItem(name)
        self.table.setHorizontalHeaderItem(self.table.horizontalHeader().count() - 1, new_header_label)
        self.window4.enter.disconnect()
        self.window4.close()
        self.query_database()  # this is used to put blank objects in newly generated cells so input widgets connect
        self.toolbar.insert_row_action.setEnabled(True)
        print('new column added')

    def delete_column(self):
        if self.databases[self.current_database].row_count > 0:
            self.information_box_header_layout.itemAt(self.table.currentColumn()).widget().hide()
            self.information_box_widget_layout.itemAt(self.table.currentColumn()).widget().hide()
        self.databases[self.current_database].delete_column(self.table.currentColumn())
        if not self.databases[self.current_database].column_classes:  # if no more columns
            self.databases[self.current_database].row_count = 0
            self.table.setRowCount(0)
            self.toolbar.insert_row_action.setDisabled(True)
            self.clearLayout(self.information_box_widget_layout)
            self.clearLayout(self.information_box_header_layout)
        self.update_headers()
        self.query_database()

    def move_column(self, lIndex, oIndex, nIndex):
        header = self.table.horizontalHeader()
        header.blockSignals(True)
        print(lIndex, oIndex, nIndex)
        self.databases[self.current_database].move_column(oIndex, nIndex)
        header.moveSection(nIndex, oIndex)
        self.query_database()
        moved_header = QTableWidgetItem(header.model().headerData(oIndex, Qt.Orientation.Horizontal))
        moved_size = header.sectionSize(oIndex)
        # resizing and moving headers appropriately
        index_modifier = 1 if nIndex > oIndex else -1

        for index in range(oIndex, nIndex, index_modifier):
            item = QTableWidgetItem(header.model().headerData(index + index_modifier, Qt.Orientation.Horizontal))
            self.table.setHorizontalHeaderItem(index, item)
            size = header.sectionSize(index + index_modifier)
            header.resizeSection(index, size)

        self.table.setHorizontalHeaderItem(nIndex, moved_header)
        header.resizeSection(nIndex, moved_size)

        header.blockSignals(False)
        header.sectionPressed.emit(nIndex)

    def hold_column_name(self, column_index, name):
        self.databases[self.current_database].column_classes[column_index].set_temp_name(name)

    def update_column_count(self):  # why do I do this instead of just updating to the length of the query?
        self.table.setColumnCount(len(self.databases[self.current_database].column_classes))

    def update_row_count(self, count: int):
        self.table.setRowCount(count)

    def set_scrollbar_max(self):
        if self.current_database is not None:
            self.scrollbar.setMaximum((self.databases[self.current_database].row_count - 1) * 24)
        else:
            self.scrollbar.setMaximum(1)

    def change_current_database(self, db_name: str):  # Why doesn't this get called upon first loading?
        self.current_database = self.databases_names[db_name]
        self.databases[self.current_database].copy_database()
        self.table_query_start = 1
        self.resizeEvent(self.geometry())
        self.query_database()
        if db_name in self.header_sizes:
            self.resize_headers()
        self.clearLayout(self.information_box_widget_layout)
        self.clearLayout(self.information_box_header_layout)
        self.dynam_add_input_widgets()
        self.update_headers()
        self.scrollbar.blockSignals(True)
        self.set_scrollbar_max()
        self.scrollbar.setValue(1)
        self.scrollbar.blockSignals(False)
        self.setWindowTitle(db_name)
        if not self.databases[self.current_database].column_classes:
            self.toolbar.insert_row_action.setDisabled(True)
        else:
            self.toolbar.insert_row_action.setEnabled(True)
        self.toolbar.insert_new_column.setEnabled(True)

    def close_current_database(self):
        self.current_database = None
        self.query_database()
        self.set_scrollbar_max()
        self.toolbar.insert_new_column.setDisabled(True)
        self.toolbar.insert_row_action.setDisabled(True)

    def update_headers(self):
        if self.current_database is not None:
            headers = self.databases[self.current_database].get_column_headers()[1:]
            if headers is not None:
                self.table.setHorizontalHeaderLabels(headers)

    def resize_headers(self):
        for i, size in enumerate(self.header_sizes[self.databases[self.current_database].name[:-3]]):
            self.table.horizontalHeader().resizeSection(i, size)

    def update_v_headers(self):
        if self.current_database is not None:
            self.table.setVerticalHeaderLabels(
                [str(i) for i in range(self.table_query_start, self.table_query_end + 1)])

    def update_cell(self, row, column=None, new_value=None):  # When using search function row is Main.id, new_value
        print(row, column)  # is provided
        if column is None:
            column = row
            row = self.table.currentRow()
        if self.current_database is not None:  # might be redundant
            if new_value is None:
                if self.table.item(row, column).text():
                    new_value = self.table.item(row, column).text()
                else:
                    new_value = None
            if self.databases[self.current_database].column_classes[column].\
                    table_name == "Main" and new_value is not None:
                try:
                    int(new_value)
                except ValueError:
                    self.statusBar().setStyleSheet("color: red")
                    self.statusBar().showMessage("Error: Only Valid Integers Are Allowed In Integer Columns")
                    self.query_database()
                    return
            if new_value is not None:
                new_value = new_value.strip()
                new_value = new_value.strip(",")
                new_value = new_value.replace('"', "'" + "'")
            self.databases[self.current_database].update_column(column, self.table_query_start + row,
                                                                self.selected_item, new_value)

    def change_selected(self, text=False):
        self.blockSignals(True)
        if type(text) != bool:
            self.selected_item = text
        elif self.table.currentItem():
            self.selected_item = self.table.currentItem().text()
        else:
            self.selected_item = ''
        self.blockSignals(False)

        # window controls

    def write_settings(self):
        if self.current_database is not None and self.table.columnCount():
            self.header_sizes[self.databases[self.current_database].name[:-3]] = \
                [self.table.horizontalHeader().sectionSize(i) for i in range(self.table.horizontalHeader().count())]
        settings = QSettings(r'settings.ini', QSettings.Format.IniFormat)
        settings.beginGroup('windowconfig')
        settings.setValue("Database Organiser", self.windowTitle())
        settings.setValue('databases', self.databases)
        settings.setValue('databasenames', self.databases_names)
        settings.setValue('databaseamount', self.database_amount)
        settings.setValue('currentdatabase', self.current_database)
        settings.setValue('backupnum', self.backup_num)
        settings.setValue('hotkeys', [key[1] for key in self.hotkeys])
        settings.endGroup()
        settings.beginGroup('tableconfig')
        settings.setValue('columnconfig', self.table.horizontalHeader().saveState())
        settings.setValue('headersizes', self.header_sizes)
        settings.endGroup()

    def save_rowcount(self):  # this breaks with the new save system
        settings = QSettings(r'settings.ini', QSettings.Format.IniFormat)
        settings.beginGroup('windowconfig')
        settings.setValue('databases', self.databases)
        settings.endGroup()

    def write_backup(self):
        if self.current_database is not None and self.table.columnCount():
            self.header_sizes[self.databases[self.current_database].name[:-3]] = \
                [self.table.horizontalHeader().sectionSize(i) for i in range(self.table.horizontalHeader().count())]
        self.backup_num += 1 if self.backup_num < 10 else 0
        settings = QSettings(fr'backups\backup{str(self.backup_num)}.ini', QSettings.Format.IniFormat)
        settings.beginGroup('windowconfig')
        settings.setValue("Database Organiser", self.windowTitle())
        settings.setValue('databases', self.databases)
        settings.setValue('databasenames', self.databases_names)
        settings.setValue('databaseamount', self.database_amount)
        settings.setValue('currentdatabase', self.current_database)
        settings.setValue('backupnum', self.backup_num)
        settings.setValue('hotkeys', [key[1] for key in self.hotkeys])
        settings.endGroup()
        settings.beginGroup('tableconfig')
        settings.setValue('columnconfig', self.table.horizontalHeader().saveState())
        settings.setValue('headersizes', self.header_sizes)
        settings.endGroup()

    def read_settings(self):
        settings = QSettings(r'settings.ini', QSettings.Format.IniFormat)
        settings.beginGroup('windowconfig')
        self.setWindowTitle(settings.value("Database Organiser"))
        self.databases_names = settings.value('databasenames')
        self.databases = settings.value('databases')
        self.database_amount = int(settings.value('databaseamount'))
        self.current_database = int(settings.value('currentdatabase'))
        self.backup_num = int(settings.value('backupnum'))
        settings.endGroup()
        settings.beginGroup('tableconfig')
        self.header_sizes = settings.value('headersizes')
        settings.endGroup()

    def load_hotkeys(self):
        settings = QSettings(r'settings.ini', QSettings.Format.IniFormat)
        settings.beginGroup('windowconfig')
        hotkey = settings.value('hotkeys')
        if hotkey:
            for i in range(len(hotkey)):
                self.hotkeys[i][1] = hotkey[i]
        settings.endGroup()

    @staticmethod
    def center_window(win):
        a = win.frameGeometry()
        a.moveCenter(win.screen().availableGeometry().center())
        win.move(a.topLeft())

    def center_on_mainwindow(self, win):
        a = win.frameGeometry()
        a.moveCenter(self.frameGeometry().center())
        win.move(a.topLeft())

    def open_save_messagebox(self):  # returns true if the database is to be closed, else returns false
        ret = QMessageBox.question(self, "Save",
                                   f"Would you like to save {self.databases[self.current_database].name[:-3]} "
                                   f"before closing?",
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No |
                                   QMessageBox.StandardButton.Cancel)
        if ret == QMessageBox.StandardButton.Cancel:
            return False
        self.write_backup()
        if ret == QMessageBox.StandardButton.Yes:
            self.save()
        else:
            self.databases[self.current_database].not_saved()
        return True

    def save(self):
        self.databases[self.current_database].rename_columns()
        self.write_settings()
        self.databases[self.current_database].copy_database()

    def closeEvent(self, event):
        print(self.databases_names, self.databases, self.current_database)
        close = self.open_save_messagebox()
        if not close:
            event.ignore()
            return
        for win in [self.window2, self.window3, self.window4, self.window5, self.window6]:
            if win:
                win.close()
        event.accept()

    def resizeEvent(self, a0: QResizeEvent) -> None:  # Handles app opening query and re-queries with resize
        if not self.information_box.isHidden():  # hiding information box when window resized
            self.table.itemSelectionChanged.emit()
            self.table.clearSelection()
        QApplication.processEvents()  # updates geometry by forcing the process of events before grabbing geometry
        count = self.table.geometry().getRect()
        if self.current_database is None:
            self.query_database()  # sets initial state of scrollbar
        else:
            self.table_query_end = self.table_query_start + (count[3] // 24) + 10
            self.update_v_headers()
            if self.table.rowCount() < count[3] // 24:
                self.query_database()
        self.v_scrollbar_resize(None, self.table.verticalScrollBar().maximum())
        if self.table.horizontalHeaderItem(0) is None:
            self.update_headers()
            if self.databases[self.current_database] is not None:
                self.databases[self.current_database].copy_database()

    # These windows probably have a better place else wear
    def make_add_database_window(self):
        self.setDisabled(True)
        self.window2 = DbNameInputWindow(self)
        self.window2.show()

    def open_database_window(self):
        self.setDisabled(True)
        if self.current_database is not None and self.table.columnCount():
            self.header_sizes[self.databases[self.current_database].name[:-3]] = \
                [self.table.horizontalHeader().sectionSize(i) for i in range(self.table.horizontalHeader().count())]
        self.window3 = OpenDbWindow(self)
        self.window3.show()

    def open_new_column_window(self):
        if self.current_database is not None:
            self.setDisabled(True)
            self.window4 = AddNewColumn(self)
            self.window4.show()

    def open_search_window(self):
        if self.current_database is not None:
            self.setDisabled(True)
            self.window5 = SearchWindow(self)
            self.window5.show()

    def open_hotkeys_window(self):
        self.setDisabled(True)
        self.window6 = EditHotKeys(self, self.hotkeys)
        self.window6.show()

    def open_themes_window(self):
        from ThemesWidgets import EditThemes
        self.setDisabled(True)
        self.window7 = EditThemes(self)
        self.window7.show()

    def eventFilter(self, a0: 'QObject', a1: 'QWheelEvent') -> bool:
        if a1.type() == QEvent.Type.Wheel:
            y = a1.angleDelta().y()
            if y < 0:
                self.scrollbar.setValue(self.scrollbar.value() + 24)
            elif y > 0:
                self.scrollbar.setValue(self.scrollbar.value() - 24)
            self.table.clearSelection()
            return True
        return super(MainWindow, self).eventFilter(a0, a1)

    class EnterKeyFilter(QObject):
        enterKeyPressed = pyqtSignal(name="enterKeyPressed")

        def eventFilter(self, a0: 'QObject', a1: 'QEvent'):
            if a1.type() == QEvent.Type.KeyPress and a1.key() == Qt.Key.Key_Return:
                self.enterKeyPressed.emit()
                print('Enter Pressed')
                return True
            return False

    class TableFilter(QObject):
        tabbed = pyqtSignal(int, int, name="tabbed")
        selectColumn = pyqtSignal(name="selectColumn")
        selectRow = pyqtSignal(name="selectRow")

        def __init__(self, obj):
            super().__init__()
            self.table = obj
            self.switch = True

        def eventFilter(self, a0: 'QObject', a1: 'QEvent') -> bool:
            if a1.type() == QEvent.Type.KeyPress and a1.key() == Qt.Key.Key_Space and \
                    a1.keyCombination().keyboardModifiers() == Qt.KeyboardModifier.ControlModifier:
                if self.table.currentItem():
                    self.selectColumn.emit()
                    print("column selected")
                return True
            elif a1.type() == QEvent.Type.KeyPress and a1.key() == Qt.Key.Key_Space and \
                    a1.keyCombination().keyboardModifiers() == Qt.KeyboardModifier.ShiftModifier:
                if self.table.currentItem() and self.switch:
                    self.selectRow.emit()
                    self.switch = False
                    print("row selected")
                elif self.table.currentItem():
                    self.table.clearSelection()
                    self.switch = True
                return True
            return False

    class ContextFilter(QObject):  # useless?
        openScrollbarContextMenu = pyqtSignal(QPoint, name="openScrollbarContextMenu")

        def eventFilter(self, a0: 'QObject', a1: 'QEvent'):
            if a0 == window.scrollbar and a1.type() == QEvent.Type.MouseButtonRelease and \
                    a1.button() == Qt.MouseButton.RightButton:
                self.openScrollbarContextMenu.emit(QCursor.pos())
                print("scrollbar context emitted")
            return False

    class HighlightFilter(QObject):  # garbage?
        columnHighlighted = pyqtSignal(name="columnHighlighted")
