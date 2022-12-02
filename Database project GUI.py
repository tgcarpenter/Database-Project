import sys

from Databases import *

from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtMultimedia import *


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # other windows
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
        self.header_sizes = {}
        self.first_cell_size = 0

        try:
            self.read_settings()
            pass
        except:
            pass

        self.instantiate_icons()
        self.instantiate_sounds()
        self.signalMapper = QSignalMapper()

        # making menu bars
        self.make_menus()

        # making table
        self.table = QTableWidget()
        self.table.setWordWrap(True)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)  # never completed this idea

        # making toolbar
        self.make_toolbars()

        # make label
        self.error_label = QLabel()
        self.error_label.setStyleSheet("color: red")
        self.error_label.hide()
        self.table.cellChanged.connect(self.error_label.hide)

        # connecting toolbar buttons (some anyway)
        self.table.verticalHeader().sectionPressed.connect(self.activate_row_delete)
        self.table.itemSelectionChanged.connect(self.deactivate_row_delete)

        self.table.horizontalHeader().sectionPressed.connect(self.activate_column_delete)
        self.table.itemSelectionChanged.connect(self.deactivate_column_delete)

        # updating column order when column moved
        self.table.horizontalHeader().setSectionsMovable(True)
        self.table.horizontalHeader().sectionMoved.connect(self.move_column)

        # updating the database when the value of a cell is changed
        self.table.cellChanged.connect(self.update_cell)
        self.table.itemSelectionChanged.connect(self.change_selected)

        # installing table filter
        self.table_filter = self.TableFilter(self.table)
        self.table.installEventFilter(self.table_filter)

        # updating even if tab is pressed
        self.table_filter.tabbed.connect(self.update_cell)

        # creating context menus
        self.make_context_menus()
        self.context_filter = self.ContextFilter()
        # horizontal Header
        self.table.horizontalHeader().setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.horizontalHeader().customContextMenuRequested.connect(self.open_h_header_context)

        self.table_filter.selectColumn.connect(lambda: self.table.horizontalHeader().sectionPressed.
                                               emit(self.table.currentColumn()))
        # vertical Header
        self.table.verticalHeader().setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.verticalHeader().customContextMenuRequested.connect(self.open_v_header_context)

        self.table_filter.selectRow.connect(lambda: self.table.verticalHeader().sectionPressed.
                                            emit(self.table.currentRow()))

        # Resizing the table based on text wrap
        self.table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().sectionResized.connect(self.resize_vertical)

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
        self.scrollbar.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.set_scrollbar_max()
        self.scrollbar.valueChanged.connect(self.connect_scroll_bars)
        self.scrollbar_total = 1

        if self.current_database is not None and len(self.databases[self.current_database].column_classes):
            self.table.setColumnCount(len(self.header_sizes[self.databases[self.current_database].name[:-3]]))
            self.resize_headers()

        # making group box's
        outside_box = QGroupBox("Database Organiser")
        self.information_box = QGroupBox("Details")
        self.information_box.hide()
        # layouts in descending order
        layout = QVBoxLayout()
        layout2 = QHBoxLayout()
        layout3 = QVBoxLayout()
        layout4 = QHBoxLayout()
        information_box_layout = QHBoxLayout()
        self.information_box_header_layout = QVBoxLayout()
        self.information_box_widget_layout = QVBoxLayout()
        information_box_layout.addLayout(self.information_box_header_layout)
        information_box_layout.addLayout(self.information_box_widget_layout)
        # toolbars
        layout.addWidget(self.option_bar)
        layout.addWidget(self.toolbar)
        # table/scrollbar
        layout3.addWidget(self.error_label)
        layout4.addWidget(self.table)
        layout4.addWidget(self.scrollbar)
        layout3.addLayout(layout4)
        outside_box.setLayout(layout3)
        layout.addWidget(outside_box)
        self.information_box.setLayout(information_box_layout)
        layout.addWidget(self.information_box)
        layout2.addLayout(layout)
        # dynamically adding input widgets
        self.dynam_add_input_widgets()
        # connecting input widgets when vertical header is pressed
        self.table.verticalHeader().sectionPressed.connect(self.connect_selected_to_widgets)
        self.table.itemSelectionChanged.connect(lambda: self.information_box.hide())

        widget = QWidget()
        widget.setLayout(layout2)

        self.setCentralWidget(widget)

        # Gui Widgets

    def make_menus(self):
        # making File Menu
        self.file_menu = QMenu(title="&File")
        add_db_action = QAction("&New", self)
        add_db_action.triggered.connect(self.make_add_database_window)
        add_db_action.setShortcut("Ctrl+N")

        open_db_action = QAction("&Open", self)
        open_db_action.triggered.connect(self.open_database_window)
        open_db_action.setShortcut("Ctrl+O")

        save_action = QAction("&Save", self)
        save_action.triggered.connect(self.write_settings)
        save_action.setShortcut("Ctrl+S")

        close_action = QAction("Close", self)
        close_action.triggered.connect(self.close_current_database)
        close_action.setShortcut("Ctrl+F4")

        # adding actions
        self.file_menu.addAction(add_db_action)
        self.file_menu.addAction(open_db_action)
        self.file_menu.addAction(save_action)
        self.file_menu.addSeparator()
        self.file_menu.addAction(close_action)

        self.menuBar().addMenu(self.file_menu)

    def make_toolbars(self):  # add hotkeys for buttons
        self.option_bar = QToolBar()
        self.option_bar.setFixedHeight(30)

        self.open_database_action = QAction("Open Database")
        self.open_database_action.triggered.connect(self.open_database_window)

        self.new_database_action = QAction("New Database")
        self.new_database_action.triggered.connect(self.make_add_database_window)

        self.option_bar.addAction(self.new_database_action)
        self.option_bar.addSeparator()
        self.option_bar.addAction(self.open_database_action)

        self.toolbar = QToolBar()
        self.toolbar.setIconSize(QSize(40, 40))
        # Actions
        self.insert_new_column = QAction(self.insert_column_icon, "Insert New Column", self)
        self.insert_new_column.setShortcut("Ctrl+Alt+N")
        self.insert_new_column.triggered.connect(self.open_new_column_window)
        if self.current_database is None:
            self.insert_new_column.setDisabled(True)

        self.delete_cur_column = QAction(self.delete_column_icon, "Delete Current Column", self)
        self.delete_cur_column.triggered.connect(self.delete_column)
        self.delete_cur_column.setDisabled(True)

        self.insert_row_action = QAction(self.insert_row_icon, 'Insert New Row', self)
        self.insert_row_action.setShortcut("Ctrl+R")
        self.insert_row_action.triggered.connect(self.add_new_row)
        if self.current_database is None \
                or (self.current_database is not None and not self.databases[self.current_database].column_classes):
            self.insert_row_action.setDisabled(True)

        self.delete_cur_row = QAction(self.delete_row_icon, "Delete Current Row", self)
        self.delete_cur_row.triggered.connect(self.delete_row)
        self.delete_cur_row.setDisabled(True)

        self.search_button = QAction(self.search_icon, "Search Database", self)
        self.search_button.setShortcut("Ctrl+F")
        self.search_button.triggered.connect(self.open_search_window)

        self.spacer = QWidget()
        self.spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.spacer2 = QWidget()
        self.spacer2.setFixedWidth(50)

        self.toolbar.addAction(self.insert_new_column)
        self.toolbar.addAction(self.insert_row_action)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.delete_cur_column)
        self.toolbar.addAction(self.delete_cur_row)
        self.toolbar.addSeparator()
        self.toolbar.addWidget(self.spacer)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.search_button)
        self.toolbar.addWidget(self.spacer2)

    def make_context_menus(self):
        self.h_header_context_menu = QMenu()

        self.sColumn_action = QAction("&Select Column", self)
        self.sColumn_action.setShortcut("Ctrl+Space")

        self.nColumn_action = QAction("&New Column", self)
        self.nColumn_action.triggered.connect(self.open_new_column_window)
        self.nColumn_action.setShortcut("Ctrl+Alt+N")

        self.dColumn_action = QAction("Delete Current Column", self)
        self.dColumn_action.triggered.connect(self.delete_column)
        self.dColumn_action.setShortcut("Ctrl+Alt+D")
        self.dColumn_action.setDisabled(True)

        self.h_header_context_menu.addAction(self.sColumn_action)
        self.h_header_context_menu.addSeparator()
        self.h_header_context_menu.addAction(self.nColumn_action)
        self.h_header_context_menu.addAction(self.dColumn_action)

        self.v_header_context_menu = QMenu()

        self.sRow_action = QAction("&Select Row", self)
        self.sRow_action.setShortcut("Shift+Space")

        nRow_Action = QAction("&New Row", self)
        nRow_Action.triggered.connect(self.add_new_row)
        nRow_Action.setShortcut("Ctrl+R")

        self.dRow_action = QAction("Delete Current Row", self)
        self.dRow_action.triggered.connect(self.delete_row)
        self.dRow_action.setShortcut("Ctrl+D")
        self.dRow_action.setDisabled(True)

        self.v_header_context_menu.addAction(self.sRow_action)
        self.v_header_context_menu.addSeparator()
        self.v_header_context_menu.addAction(nRow_Action)
        self.v_header_context_menu.addAction(self.dRow_action)

        self.table_context_menu = QMenu()

        tSColumn_action = QAction("&Select Column", self)
        tSColumn_action.triggered.connect(lambda: self.table.horizontalHeader().sectionPressed.
                                          emit(self.table.currentColumn()))
        tSColumn_action.setShortcut("Ctrl+Space")

        tSRow_action = QAction("&Select Row", self)
        tSRow_action.triggered.connect(lambda: self.table.verticalHeader().sectionPressed.emit(self.table.currentRow()))
        tSRow_action.setShortcut("Shift+Space")

        self.table_context_menu.addAction(tSColumn_action)
        self.table_context_menu.addSeparator()
        self.table_context_menu.addAction(tSRow_action)

        self.scrollbar_context_menu = QMenu()

        scrollHere_action = QAction("Scroll Here", self)

    def open_h_header_context(self, pos):
        self.h_header_context_menu.popup(QCursor.pos())
        self.hIndex = self.table.horizontalHeader().logicalIndexAt(pos)
        if self.sColumn_action.isSignalConnected(self.get_signal(self.sColumn_action, "triggered")):
            self.sColumn_action.triggered.disconnect()
        self.sColumn_action.triggered.connect(lambda: self.table.horizontalHeader().sectionPressed.
                                                emit(self.hIndex))
        self.sColumn_action.triggered.connect(self.sColumn_action.triggered.disconnect)
        print("h header context created")

    def open_v_header_context(self, pos):
        self.v_header_context_menu.popup(QCursor.pos())
        self.vIndex = self.table.verticalHeader().logicalIndexAt(pos)
        if self.sRow_action.isSignalConnected(self.get_signal(self.sRow_action, "triggered")):
            self.sRow_action.triggered.disconnect()
        self.sRow_action.triggered.connect(lambda: self.table.verticalHeader().sectionPressed.
                                             emit(self.vIndex))
        self.sRow_action.triggered.connect(self.sRow_action.triggered.disconnect)
        print("v header context created")

    def open_table_context(self):
        self.table_context_menu.popup(QCursor.pos())
        print("table context emitted")

    def open_scrollbar_context(self):
        pass

    def activate_row_delete(self):
        self.dRow_action.setEnabled(True)
        self.delete_cur_row.setEnabled(True)

    def deactivate_row_delete(self):
        self.dRow_action.setDisabled(True)
        self.delete_cur_row.setDisabled(True)

    def activate_column_delete(self):
        self.dColumn_action.setEnabled(True)
        self.delete_cur_column.setEnabled(True)

    def deactivate_column_delete(self):
        self.dColumn_action.setDisabled(True)
        self.delete_cur_column.setDisabled(True)

    def dynam_add_input_widgets(self):
        if self.current_database is not None:
            for col in self.databases[self.current_database].column_classes:
                if col.table_name[1] == "T":
                    self.add_text_input_widget(col.column_name[2:-1])
                elif col.table_name[1] == "L":
                    self.add_text_input_widget(col.column_name[2:-1])  # change later - temp
                else:
                    self.add_integer_input_widget(col.column_name[2:-1])

    def add_integer_input_widget(self, col_name):
        int_input = self.MySpinBox()
        int_input.setRange(-9999, 9999)
        int_input.editingFinished.connect(self.signalMapper.map)
        header = QLabel(col_name + ":")
        self.information_box_header_layout.addWidget(header)
        self.information_box_widget_layout.addWidget(int_input)

    def add_text_input_widget(self, col_name):
        text_input = self.MyLineEdit()
        text_input.editingFinished.connect(self.signalMapper.map)
        header = QLabel(col_name + ":")
        self.information_box_header_layout.addWidget(header)
        self.information_box_widget_layout.addWidget(text_input)

    def clearLayout(self, layout):
        if layout is not None:
            while layout.count():
                child = layout.takeAt(0)
                if child.widget() is not None:
                    child.widget().deleteLater()
                elif child.layout() is not None:
                    self.clearLayout(child.layout())

    # def add_list_input_widget(self): - may do this later, have to figure out formatting

    def connect_selected_to_widgets(self):  # updated table when widget is changed as well as updates database when
        self.information_box.setHidden(False)  # widget is done being edited
        for i, col in zip(range(0, self.information_box_widget_layout.count()),
                          self.databases[self.current_database].column_classes):

            input_widget = self.information_box_widget_layout.itemAt(i).widget()  # setting widget pointer

            if i >= len(self.table.selectedItems()):  # temporary solution. it might not work after i
                continue  # implement some other features

            if col.table_name[1] == "T" or col.table_name[1] == "L":  # handles text and list columns
                if input_widget.isSignalConnected(self.get_signal(input_widget, "textChanged")):
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
                self.signalMapper.mappedInt.connect(self.update_cell)

            else:  # handles integer columns
                if input_widget.isSignalConnected(self.get_signal(input_widget, "textChanged")):
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
                self.signalMapper.mappedInt.connect(self.update_cell)

        # Gui media functions

    def instantiate_icons(self):
        self.insert_row_icon = QIcon("New Row Graphic.PNG")
        self.insert_column_icon = QIcon("New Column Graphic 2.PNG")
        self.delete_column_icon = QIcon("Delete Column Graphic")
        self.delete_row_icon = QIcon("Delete Row Graphic")
        self.search_icon = QIcon("Search Graphic")

    def instantiate_sounds(self):
        self.error_sound = QSoundEffect()
        self.error_sound.setSource(QUrl.fromLocalFile("error-beep.WAV"))

    def connect_scroll_bars(self, s_value):
        self.query_switch = True
        while s_value > self.scrollbar_total + self.first_cell_size:
            self.scrollbar_total += self.first_cell_size
            self.table_query_start += 1
            self.table_query_end += 1
            if self.first_cell_size > 24:
                self.scrollbar.setMaximum(self.scrollbar.maximum() + self.first_cell_size - 24)
                print("maximum", self.scrollbar.maximum())
            self.query_database()
            self.table.verticalScrollBar().setValue(s_value - self.scrollbar_total - 1)
        while s_value < self.scrollbar_total:
            self.table_query_start -= 1
            self.table_query_end -= 1
            self.query_database()
            self.scrollbar_total -= self.first_cell_size
            self.table.verticalScrollBar().setValue(s_value - self.scrollbar_total - 1)
            if self.first_cell_size > 24:
                self.scrollbar.setMaximum(self.scrollbar.maximum() - (self.first_cell_size - 24))
        self.table.verticalScrollBar().setValue(s_value - self.scrollbar_total)
        self.query_switch = False
        self.query_database()
        # print(self.scrollbar.value(), s_value)
        print("scrollbar total:", self.scrollbar_total, "table query start:", self.table_query_start, "scrollbar value:", self.scrollbar.value())

    def scroll_to(self, row):
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

    def v_scrollbar_resize(self):
        print(self.table.verticalScrollBar().maximum())
        if self.table.verticalScrollBar().maximum() < 25:
            self.table.verticalScrollBar().setMaximum(25)

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

        if self.query_switch:
            query = self.databases[self.current_database].general_query(self.table_query_start, self.table_query_start)
            # this is jank. it's to make adding new row more efficient
            # by avoiding a bunch of querying and data mapping and such
        else:
            query = self.databases[self.current_database].general_query(self.table_query_start, self.table_query_end)
        self.update_column_count()  # setting table size
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
        print("first cell size:", self.first_cell_size)

    def scroll_query(self):
        pass

    def add_new_row(self):
        if self.current_database is None or not self.databases[self.current_database].column_classes:  # isn't used
            self.error_sound.play()
            return
        self.insert_row_action.blockSignals(True)
        self.databases[self.current_database].add_defaults()
        self.resizeEvent(self.geometry())
        self.query_switch = True
        if self.table_query_end > 1:
            if self.table_query_end == 2:
                self.scrollbar.setMinimum(1)
            self.scrollbar.setMaximum(self.scrollbar.maximum() + 24)
            if self.databases[self.current_database].row_count > self.table_query_end:
                while self.scrollbar.value() != self.scrollbar.maximum():
                    self.scrollbar.setValue(self.scrollbar.maximum())
        self.table.clearSelection()
        self.query_switch = False
        self.insert_row_action.blockSignals(False)
        self.query_database()
        print('new row added')

    def delete_row(self):
        print([obj.text() for obj in self.table.selectedItems()])
        self.scrollbar.setMaximum(self.scrollbar.maximum()
                                  - self.table.verticalHeader().sectionSize(self.table.currentRow()))
        self.databases[self.current_database].delete_row([obj.text() for obj in self.table.selectedItems()],
                                                         self.table_query_start + self.table.currentRow())
        self.resizeEvent(self.geometry())
        self.table.verticalHeader().sectionPressed.emit(self.table.currentRow())

    def add_new_column(self, column: int, name: str):
        if column == 0:
            self.databases[self.current_database].add_column_integer(name)
            self.add_integer_input_widget(name)
        elif column == 1:
            self.databases[self.current_database].add_column_text(name)
            self.add_text_input_widget(name)
        else:
            self.databases[self.current_database].add_column_list(name)
            self.add_text_input_widget(name)
        self.update_column_count()  # does this need to be here?
        self.update_headers()
        self.window4.enter.disconnect()
        self.window4.close()
        self.query_database()  # this is used to put blank objects in newly generated cells so input widgets connect
        self.insert_row_action.setEnabled(True)
        print('new column added')

    def delete_column(self):
        self.information_box_header_layout.itemAt(self.table.currentColumn()).widget().hide()
        self.information_box_widget_layout.itemAt(self.table.currentColumn()).widget().hide()
        self.databases[self.current_database].delete_column(self.table.currentColumn())
        if not self.databases[self.current_database].column_classes:  # if no more columns
            self.databases[self.current_database].row_count = 0
            self.table.setRowCount(0)
            self.insert_row_action.setDisabled(True)
        self.resizeEvent(self.geometry())

    def move_column(self, lIndex, oIndex, nIndex):
        self.table.horizontalHeader().blockSignals(True)
        print(lIndex, oIndex, nIndex)
        self.databases[self.current_database].move_column(oIndex, nIndex)
        self.table.horizontalHeader().moveSection(nIndex, oIndex)
        self.query_database()
        self.update_headers()
        self.table.horizontalHeader().blockSignals(False)
        self.table.horizontalHeader().sectionPressed.emit(nIndex)

    def update_column_count(self):  # why do I do this instead of just updating to the length of the query?
        self.table.setColumnCount(len(self.databases[self.current_database].column_classes))

    def update_row_count(self, count):
        self.table.setRowCount(count)

    def set_scrollbar_max(self):
        if self.current_database is not None:
            self.scrollbar.setMaximum((self.databases[self.current_database].row_count - 1) * 24)
        else:
            self.scrollbar.setMaximum(1)

    def change_current_database(self, db_name: str):
        self.current_database = self.databases_names[db_name]
        self.table_query_start = 1 if self.databases[self.current_database].row_count > 0 else 0
        self.resizeEvent(self.geometry())
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
            self.insert_row_action.setDisabled(True)
        else:
            self.insert_row_action.setEnabled(True)
        print(self.databases[self.current_database].row_count)

    def close_current_database(self):
        self.current_database = None
        self.query_database()
        self.set_scrollbar_max()
        self.insert_new_column.setDisabled(True)
        self.insert_row_action.setDisabled(True)

    def update_headers(self):
        if self.current_database is not None:
            headers = self.databases[self.current_database].get_column_headers()[1:]
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
            if self.databases[self.current_database].column_classes[column].table_name == "Main":
                try:
                    int(new_value)
                except:
                    self.error_label.setText("               Error: Only Valid Integers Are Allowed In Integer Columns")
                    self.error_label.setHidden(False)
                    self.query_database()
                    return
            if new_value is not None:
                new_value = new_value.strip()
            self.databases[self.current_database].update_column(column, self.table_query_start + row,
                                                                self.selected_item, new_value)

    def change_selected(self, text=None):
        self.blockSignals(True)
        if text:
            self.selected_item = text
        elif self.table.currentItem():
            self.selected_item = self.table.currentItem().text()
        else:
            self.selected_item = ''
        self.blockSignals(False)
        print(self.selected_item, text)

        # window controls

    def write_settings(self):
        if self.current_database is not None and self.table.columnCount():
            self.header_sizes[self.databases[self.current_database].name[:-3]] = \
                [self.table.horizontalHeader().sectionSize(i) for i in range(self.table.horizontalHeader().count())]
        settings = QSettings('MyApp', 'DatabaseBuilderApp')
        settings.beginGroup('windowconfig')
        settings.setValue("Database Organiser", self.windowTitle())
        settings.setValue('databases', self.databases)
        settings.setValue('databasenames', self.databases_names)
        settings.setValue('databaseamount', self.database_amount)
        settings.setValue('currentdatabase', self.current_database)
        settings.endGroup()
        settings.beginGroup('tableconfig')
        settings.setValue('columnconfig', self.table.horizontalHeader().saveState())
        settings.setValue('headersizes', self.header_sizes)
        settings.endGroup()

    def read_settings(self):
        settings = QSettings('MyApp', 'DatabaseBuilderApp')
        settings.beginGroup('windowconfig')
        self.setWindowTitle(settings.value("Database Organiser"))
        self.databases_names = settings.value('databasenames')
        self.databases = settings.value('databases')
        self.database_amount = settings.value('databaseamount')
        self.current_database = settings.value('currentdatabase')
        settings.endGroup()
        settings.beginGroup('tableconfig')
        self.header_sizes = settings.value('headersizes')
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

    @staticmethod
    def get_signal(oObject: QObject, strSignalName: str):
        oMetaObj = oObject.metaObject()
        for i in range(oMetaObj.methodCount()):
            oMetaMethod = oMetaObj.method(i)
            if not oMetaMethod.isValid():
                continue
            if oMetaMethod.methodType() == QMetaMethod.MethodType.Signal and \
                    oMetaMethod.name() == strSignalName:
                return oMetaMethod

        return None

    def closeEvent(self, event):
        print(self.databases_names, self.databases, self.current_database)
        self.write_settings()
        for win in [self.window2, self.window3, self.window4, self.window5]:
            if win:
                win.close()
        event.accept()

    def resizeEvent(self, a0: QResizeEvent) -> None:  # Handles app opening query and re-queries with resize
        if not self.information_box.isHidden():  # hiding information box when window resized
            self.table.itemSelectionChanged.emit()
            self.table.clearSelection()
        print("resizeEvent")
        app.processEvents()  # updates geometry by forcing the process of events before grabbing geometry
        count = self.table.geometry().getRect()
        if self.current_database is None:
            self.query_database()
        elif count[3] // 24 > self.databases[self.current_database].row_count:  #  + self.table_query_start - 1
            self.table_query_end = self.databases[self.current_database].row_count \
                if self.databases[self.current_database].row_count > 0 else 0
            self.query_database()
            self.v_scrollbar_resize()
        else:
            self.table_query_end = self.table_query_start + (count[3] // 24 - 1)
            self.query_database()
        if self.table.horizontalHeaderItem(0) is None:  # I don't remember what this is for
            self.update_headers()

    def make_add_database_window(self):
        self.setDisabled(True)
        self.window2 = self.DbNameInputWindow()
        self.window2.show()

    def open_database_window(self):
        self.setDisabled(True)
        if self.current_database is not None and self.table.columnCount():
            self.header_sizes[self.databases[self.current_database].name[:-3]] = \
                [self.table.horizontalHeader().sectionSize(i) for i in range(self.table.horizontalHeader().count())]
        self.window3 = self.OpenDbWindow()
        self.window3.show()

    def open_new_column_window(self):
        if self.current_database is not None:
            self.setDisabled(True)
            self.window4 = self.AddNewColumn()
            self.window4.show()
        else: # shouldn't trigger anymore
            self.error_sound.play()

    def open_search_window(self):
        if self.current_database is not None:
            self.setDisabled(True)
            self.window5 = self.SearchWindow()
            self.window5.show()

    def eventFilter(self, a0: 'QObject', a1: 'QWheelEvent') -> bool:  # this is jank LMAO
        if a1.type() == QEvent.Type.Wheel:
            y = a1.angleDelta().y()
            if y < 0:
                self.scrollbar.setValue(self.scrollbar.value() + 24)
            elif y > 0:
                self.scrollbar.setValue(self.scrollbar.value() - 24)
            self.table.clearSelection()
            return True
        return super(MainWindow, self).eventFilter(a0, a1)

    class MySpinBox(QSpinBox):
        firstClicked = pyqtSignal(str)

        def __init__(self):
            super().__init__()

        def focusInEvent(self, *args, **kwargs):
            window.table.blockSignals(True)
            self.firstClicked.emit(self.cleanText())
            print('first clicked')
            super(window.MySpinBox, self).focusInEvent(*args)

        def focusOutEvent(self, a0: QFocusEvent) -> None:
            window.table.blockSignals(False)
            print('Unfocused')
            super(window.MySpinBox, self).focusOutEvent(a0)

    class MyLineEdit(QLineEdit):
        firstClicked = pyqtSignal(str)

        def __init__(self):
            super().__init__()

        def focusInEvent(self, a0: QFocusEvent) -> None:
            window.table.blockSignals(True)
            self.firstClicked.emit(self.text())
            print('first clicked')
            super(window.MyLineEdit, self).focusInEvent(a0)

        def focusOutEvent(self, a0: QFocusEvent) -> None:
            window.table.blockSignals(False)
            print('Unfocused')
            super(window.MyLineEdit, self).focusOutEvent(a0)

    class MySearchLineEdit(QLineEdit):
        focused = pyqtSignal()

        def __init__(self, w):
            super().__init__()
            self.win = w
            self.switch = True

        def focusInEvent(self, e: QFocusEvent) -> None:
            if self.switch is False:
                print("stacked focusInEvent")
                return
            self.focused.emit()
            self.win.search_table.blockSignals(True)
            print('Focused')
            self.switch = False
            super(window.MySearchLineEdit, self).focusInEvent(e)

        def focusOutEvent(self, e: QFocusEvent) -> None:
            self.win.search_table.blockSignals(False)
            print("Unfocused")
            self.switch = True
            super(window.MySearchLineEdit, self).focusOutEvent(e)

    class EnterKeyFilter(QObject):
        entrkeypressed = pyqtSignal()

        def eventFilter(self, a0: 'QObject', a1: 'QEvent'):
            if a1.type() == QEvent.Type.KeyPress and a1.key() == Qt.Key.Key_Return:
                self.entrkeypressed.emit()
                print('Enter Pressed')
                return True
            return False

    class TableFilter(QObject):
        tabbed = pyqtSignal(int, int)
        selectColumn = pyqtSignal()
        selectRow = pyqtSignal()

        def __init__(self, obj):
            super().__init__()
            self.table = obj
            self.switch = True

        def eventFilter(self, a0: 'QObject', a1: 'QEvent') -> bool:
            if a1.type() == QEvent.Type.KeyPress and a1.key() == Qt.Key.Key_Tab:
                if self.table.currentItem():
                    self.tabbed.emit(self.table.currentRow(), self.table.currentColumn())
                print('Tabbed')
                return True
            elif a1.type() == QEvent.Type.KeyPress and a1.key() == Qt.Key.Key_Space and \
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

    class ContextFilter(QObject):
        openScrollbarContextMenu = pyqtSignal(QPoint)

        def eventFilter(self, a0: 'QObject', a1: 'QEvent'):
            if a0 == window.scrollbar and a1.type() == QEvent.Type.MouseButtonRelease and \
                    a1.button() == Qt.MouseButton.RightButton:
                self.openScrollbarContextMenu.emit(QCursor.pos())
                print("scrollbar context emitted")
            return False

    class HighlightFilter(QObject):  # garbage?
        columnHighlighted = pyqtSignal()

    class DbNameInputWindow(QWidget):
        def __init__(self):
            super().__init__()

            self.setWindowTitle('Create Database')
            self.setStyleSheet('background-color: light grey')
            self.setFixedSize(400, 100)
            window.center_on_mainwindow(self)

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
                    self.enter.clicked.connect(lambda: self.create_database(input_box.text()))
                else:
                    self.enter.disconnect()

        def create_database(self, name):  # needs testing
            window.databases.append(Database(name))
            window.databases_names[name] = window.database_amount
            window.database_amount += 1
            window.change_current_database(name)
            window.insert_new_column.setEnabled(True)
            self.enter.disconnect()
            self.close()

        def closeEvent(self, event) -> None:
            window.setEnabled(True)
            event.accept()

    class OpenDbWindow(QWidget):
        def __init__(self):
            super().__init__()

            self.setWindowTitle("Open Database")
            self.setFixedSize(500, 500)
            window.center_on_mainwindow(self)

            new_db_button = QPushButton("New Database")
            new_db_button.setMaximumWidth(140)
            new_db_button.clicked.connect(self.close)
            new_db_button.clicked.connect(window.make_add_database_window)

            self.spacer = QWidget()
            self.spacer.setMaximumHeight(24)
            self.spacer.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)

            list_view = QListWidget()
            header = QLabel("Select Database:")
            temp_databases = list(window.databases_names.keys())
            temp_databases.reverse()

            try:
                for database in temp_databases:
                    list_view.addItem(database)
            except:
                pass

            list_view.itemDoubleClicked.connect(lambda: current_item())

            enter = QPushButton('Enter', self)
            enter.setFixedWidth(100)

            list_view.itemClicked.connect(lambda: enter_connection())

            def enter_connection():
                enter.clicked.connect(lambda: current_item())
                enter.clicked.connect(self.close)  # <- maybe redundant

            cancel = QPushButton('Cancel', self)
            cancel.setFixedWidth(100)
            cancel.clicked.connect(self.close)

            self.filter = window.EnterKeyFilter()
            list_view.installEventFilter(self.filter)
            self.filter.entrkeypressed.connect(enter.click)

            layout = QVBoxLayout()
            layout2 = QHBoxLayout()
            layout2.addWidget(header)
            layout2.addWidget(self.spacer)
            layout2.addWidget(new_db_button)

            layout3 = QHBoxLayout()
            layout3.addWidget(enter)
            layout3.addWidget(cancel)

            layout.addLayout(layout2)
            layout.addWidget(list_view)
            layout.addLayout(layout3)

            self.setLayout(layout)

            def current_item():
                self.temp = list_view.currentItem()
                self.item = self.temp.text()
                temp = window.databases_names.pop(self.item)
                window.databases_names[self.item] = temp
                window.change_current_database(self.item)
                window.insert_new_column.setEnabled(True)
                self.close()

        def closeEvent(self, event) -> None:
            window.setEnabled(True)
            event.accept()

    class AddNewColumn(QWidget):
        def __init__(self):
            super().__init__()

            self.setWindowTitle("Create New Column")
            self.setFixedSize(400, 115)
            window.center_on_mainwindow(self)

            columns_list = QComboBox()
            columns_list.setPlaceholderText("Column Type...")
            for name in ["Integer Column", "Text Column", "List Column"]:
                columns_list.addItem(name)

            label = QLabel("Column Type:   ")
            label2 = QLabel("Column Name:")

            input_box = QLineEdit()
            input_box.setMaxLength(40)
            input_box.setPlaceholderText("Type Column Name..")

            self.enter = QPushButton("Enter", self)
            self.enter.setFixedWidth(100)

            columns_list.currentIndexChanged.connect(lambda: enter_connection())
            input_box.textChanged.connect(lambda: enter_connection())

            def enter_connection():
                if columns_list.currentIndex() != -1 and input_box.text() != '':
                    self.enter.clicked.connect(lambda: window.add_new_column(columns_list.currentIndex(),
                                                                             input_box.text().strip()))
                else:
                    try:
                        self.enter.disconnect()
                    except TypeError:
                        pass

            cancel = QPushButton('Cancel', self)
            cancel.setFixedWidth(100)
            cancel.clicked.connect(self.close)

            self.filter = window.EnterKeyFilter()
            input_box.installEventFilter(self.filter)
            self.filter.entrkeypressed.connect(self.enter.click)

            layout = QVBoxLayout()
            layout2 = QHBoxLayout()
            layout3 = QHBoxLayout()
            layout4 = QHBoxLayout()
            layout3.addWidget(label)
            layout3.addWidget(columns_list)
            layout4.addWidget(label2)
            layout4.addWidget(input_box)
            layout2.addWidget(self.enter)
            layout2.addWidget(cancel)
            layout3.setAlignment(Qt.AlignmentFlag.AlignLeft)
            layout.addLayout(layout3)
            layout.addLayout(layout4)
            layout.addLayout(layout2)

            self.setLayout(layout)

        def closeEvent(self, event) -> None:
            window.setEnabled(True)
            event.accept()

    class SearchWindow(QWidget):
        def __init__(self):
            super().__init__()

            self.setWindowTitle("Database Search")
            self.resize(700, 500)
            window.center_on_mainwindow(self)
            # setting up search bar and connection to search
            self.search_bar = window.MySearchLineEdit(self)
            self.search_bar.setFixedSize(180, 25)
            self.search_bar.setPlaceholderText("Search")
            self.search_bar.textChanged.connect(self.search_database)
            self.search_bar.textChanged.connect(self.autofill)
            # setting up completer and completer model
            self.completer = QCompleter()
            self.completer_model = QStringListModel()
            self.completer.setModel(self.completer_model)
            self.search_bar.setCompleter(self.completer)
            # setting up table to update database
            self.search_table = QTableWidget()
            self.search_table.setSortingEnabled(True)
            self.search_table.cellChanged.connect(self.update_database)
            self.search_table.itemSelectionChanged.connect(self.change_selected)
            # setting header context menu
            self.search_table.verticalHeader().setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            self.search_table.verticalHeader().customContextMenuRequested.connect(self.open_context)
            # accounting for tab irregularities
            self.tableFilter = window.TableFilter(self.search_table)
            self.search_table.installEventFilter(self.tableFilter)
            self.tableFilter.tabbed.connect(self.update_database)
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
            search_query = window.databases[window.current_database].general_query(search=text)
            if not search_query:  # If nothing is returned, passes search and restores default
                self.search_table.setColumnCount(0)
                self.search_table.setRowCount(0)
                return
            print(search_query)
            self.search_table.setColumnCount(len(search_query[0]))
            self.search_table.setRowCount(len(search_query))
            self.search_table.setHorizontalHeaderLabels(window.databases[window.current_database].get_column_headers())
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
            self.search_table.blockSignals(False)

        def autofill(self, search_text):
            autofill = window.databases[window.current_database].autofill_query(search_text)
            self.completer_model.setStringList([a[0] for a in autofill])
            self.completer.popup().resize(180, 24 * len(autofill))
            print("completer", self.completer_model.stringList())
            self.search_bar.setFocus()

        def update_database(self, row, column):
            window.update_cell(int(self.search_table.item(row, 0).text()) - window.table_query_start, column - 1,
                               self.search_table.currentItem().text() if self.search_table.currentItem() else '')

        def change_selected(self):
            self.blockSignals(True)
            window.change_selected(self.search_table.currentItem().text() if self.search_table.currentItem() else None)
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
            window.scroll_to(row)

        def closeEvent(self, event) -> None:
            window.setEnabled(True)
            window.query_database()
            event.accept()


app = QApplication(sys.argv)

window = MainWindow()
window.show()

app.exec()
