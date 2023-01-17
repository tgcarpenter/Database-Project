from PyQt6.QtCore import QSize
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtWidgets import QToolBar, QWidget, QSizePolicy, QMenu, QPushButton


class OptionBar(QToolBar):
    def __init__(self, window):
        super().__init__()
        self.setFixedHeight(50)

        self.open_database_action = QAction("Open Database")
        self.open_database_action.triggered.connect(window.open_database_window)

        self.new_database_action = QAction("New Database")
        self.new_database_action.triggered.connect(window.make_add_database_window)

        self.addAction(self.new_database_action)
        self.addSeparator()
        self.addAction(self.open_database_action)

        self.toolbar = QToolBar()
        self.toolbar.setIconSize(QSize(40, 40))

        window.addToolBar(self)


class ToolBar(QToolBar):
    def __init__(self, window):
        super().__init__()
        self.setIconSize(QSize(40, 40))
        self.instantiate_icons()
        self.insert_new_column = QAction(self.insert_column_icon, "Insert New Column", self)
        self.insert_new_column.triggered.connect(window.open_new_column_window)
        if window.current_database is None:
            self.insert_new_column.setDisabled(True)

        self.delete_cur_column = QAction(self.delete_column_icon, "Delete Current Column", self)
        self.delete_cur_column.triggered.connect(window.delete_column)
        self.delete_cur_column.setDisabled(True)

        self.insert_row_action = QAction(self.insert_row_icon, 'Insert New Row', self)
        self.insert_row_action.triggered.connect(window.add_new_row)
        if window.current_database is None \
                or (window.current_database is not None and not window.databases[window.current_database].column_classes):
            self.insert_row_action.setDisabled(True)

        self.delete_cur_row = QAction(self.delete_row_icon, "Delete Selected Row", self)
        self.delete_cur_row.triggered.connect(window.delete_row)
        self.delete_cur_row.setDisabled(True)

        self.search_button = QAction(self.search_icon, "Search Database", self)
        self.search_button.triggered.connect(window.open_search_window)

        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        spacer2 = QWidget()
        spacer2.setFixedWidth(50)

        self.addAction(self.insert_new_column)
        self.addAction(self.insert_row_action)
        self.addSeparator()
        self.addAction(self.delete_cur_column)
        self.addAction(self.delete_cur_row)
        self.addSeparator()
        self.addWidget(spacer)
        self.addSeparator()
        self.addAction(self.search_button)
        self.addWidget(spacer2)

        window.addToolBar(self)

    def instantiate_icons(self):
        self.insert_row_icon = QIcon("New Row Graphic.PNG")
        self.insert_column_icon = QIcon("New Column Graphic 2.PNG")
        self.delete_column_icon = QIcon("Delete Column Graphic")
        self.delete_row_icon = QIcon("Delete Row Graphic")
        self.search_icon = QIcon("Search Graphic")


class ContextMenus(QMenu):
    def __init__(self, window, toolbar, menu):
        super().__init__(window)

        if menu == "h_header":
            self.sColumn_action = QAction("&Select Column", self)

            self.addAction(self.sColumn_action)
            self.addSeparator()
            self.addAction(toolbar.insert_new_column)
            self.addAction(toolbar.delete_cur_column)

        elif menu == "v_header":
            self.sRow_action = QAction("&Select Row", self)

            self.addAction(self.sRow_action)
            self.addSeparator()
            self.addAction(toolbar.insert_row_action)
            self.addAction(toolbar.delete_cur_row)

        elif menu == "table":
            self.tSColumn_action = QAction("&Select Column", self)
            self.tSColumn_action.triggered.connect(lambda: window.table.horizontalHeader().sectionPressed.
                                              emit(window.table.currentColumn()))

            self.tSRow_action = QAction("&Select Row", self)
            self.tSRow_action.triggered.connect(
                lambda: window.table.verticalHeader().sectionPressed.emit(window.table.currentRow()))

            self.addAction(self.tSColumn_action)
            self.addSeparator()
            self.addAction(self.tSRow_action)


class FileMenu(QMenu):
    def __init__(self, window):
        super().__init__()
        self.setTitle("File")

        self.add_db_action = QAction("&New", self)
        self.add_db_action.triggered.connect(window.make_add_database_window)

        self.open_db_action = QAction("&Open", self)
        self.open_db_action.triggered.connect(window.open_database_window)

        self.save_action = QAction("&Save", self)
        self.save_action.triggered.connect(window.write_settings)

        self.close_action = QAction("Close", self)
        self.close_action.triggered.connect(window.close_current_database)

        # adding actions
        self.addAction(self.add_db_action)
        self.addAction(self.open_db_action)
        self.addAction(self.save_action)
        self.addSeparator()
        self.addAction(self.close_action)


class EditMenu(QMenu):
    def __init__(self, window):
        super().__init__()
        self.setTitle("Edit")

        hot_keys = QAction("Hot Keys", self)
        hot_keys.triggered.connect(window.open_hotkeys_window)

        self.addAction(hot_keys)


class HideButton(QPushButton):
    def __init__(self, obj, direction="left"):
        super().__init__()
        directions = {"left": "<", "right": ">", "up": "^", "down": "∨"}
        self.setText(directions[direction])
        self.setToolTip("Hide Window")
        self.setFixedSize(18, 18)
        self.clicked.connect(obj.hide)

