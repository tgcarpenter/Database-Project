from PyQt6.QtWidgets import QComboBox, QLineEdit, QSpinBox, QCompleter, QColorDialog, QWidget, QHeaderView, \
    QStyleOptionFrame, QStyle, QTableView, QAbstractItemView
from PyQt6.QtCore import Qt, QStringListModel, pyqtSignal, QPoint, QEvent, QObject, QModelIndex, QAbstractItemModel, \
    QAbstractTableModel, QVariant, QSortFilterProxyModel, QTimer
from PyQt6.QtGui import QFocusEvent, QPainter, QPaintEvent, QCursor, QWheelEvent, QResizeEvent


class MyTableItem:
    def __init__(self, table):
        self.table = table
        self.row = None
        self.column = None

    def setValues(self, row, column):
        self.row = row
        self.column = column

    def setText(self, text):
        self.table.setData(self.row, self.column, text)


class MyComboBox(QComboBox):
    firstClicked = pyqtSignal(str, name="firstClicked")

    def __init__(self, name, window):
        super().__init__()
        self.name = f"[_{name}]"
        self.item = ''
        self.window = window
        self.setEditable(True)
        self.activated.connect(self.insert_completion)
        self.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.setLineEdit(self.InComboEdit(self))
        self.tableUpdater = MyTableItem(window.table)

    def set_autofill(self):
        self.clear()
        autofill = self.window.databases[self.window.current_database].list_column_query(self.name)
        self.addItems([str(a[0]) for a in autofill])

    def insert_completion(self, completion):
        self.lineEdit().blockSignals(True)
        self.lineEdit().setText(self.item)
        self.lineEdit().blockSignals(False)
        completion = self.itemText(completion)
        self.lineEdit().end(False)
        text = self.lineEdit().text()
        if not text:
            self.lineEdit().insert(completion)
        elif completion == text:
            return
        else:
            pre = ''
            for char in text[::-1]:
                if char != ",":
                    pre += char
                else:
                    pre += ","
                    break
            pref = pre.strip().casefold()
            com = ", " + completion
            com = com[:len(pref)].casefold()
            if pref[::-1] == com or pref[::-1] == com.strip():
                self.lineEdit().setSelection(len(text), len(pre) * -1)
            self.lineEdit().insert(", " + completion)
        self.item = self.lineEdit().text()

    def focusInEvent(self, *args, **kwargs):
        self.window.table.blockSignals(True)
        self.firstClicked.emit(self.lineEdit().text())
        self.item = self.lineEdit().text()
        # print('first clicked')
        super(MyComboBox, self).focusInEvent(*args)

    def focusOutEvent(self, a0: QFocusEvent) -> None:
        self.window.table.blockSignals(False)
        # print('Unfocused')
        super(MyComboBox, self).focusOutEvent(a0)

    def wheelEvent(self, a0: QWheelEvent) -> None:
        return

    class InComboEdit(QLineEdit):
        def __init__(self, combo):
            super().__init__()
            self.combo = combo
            self.editingFinished.connect(self.set_item)

        def set_item(self):
            self.combo.item = self.text()
            self.combo.currentTextChanged.emit('')
            self.combo.window.change_selected(self.text())

        def wheelEvent(self, a0: QWheelEvent) -> None:
            return


class MySpinBox(QSpinBox):
    firstClicked = pyqtSignal(str, name="firstClicked")

    def __init__(self, window):
        super().__init__()
        self.window = window
        self.tableUpdater = MyTableItem(window.table)

    def focusInEvent(self, *args, **kwargs):
        self.window.table.blockSignals(True)
        self.firstClicked.emit(self.cleanText())
        # print('first clicked')
        super(MySpinBox, self).focusInEvent(*args)

    def focusOutEvent(self, a0: QFocusEvent) -> None:
        self.window.table.blockSignals(False)
        # print('Unfocused')
        super(MySpinBox, self).focusOutEvent(a0)


class MyLineEdit(QLineEdit):
    firstClicked = pyqtSignal(str, name="firstClicked")

    def __init__(self, name, window):
        super().__init__()
        self.name = f"[_{name}]"
        self.window = window
        self.completer_modal = QStringListModel()
        self.completer = QCompleter()
        self.completer.setModel(self.completer_modal)
        self.completer.setCompletionMode(QCompleter.CompletionMode.InlineCompletion)
        self.completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.setCompleter(self.completer)
        self.tableUpdater = MyTableItem(window.table)

    def set_autofill(self):
        autofill = self.window.databases[self.window.current_database].list_column_query(self.name)
        self.completer_modal.setStringList([str(a[0]) for a in autofill])

    def focusInEvent(self, a0: QFocusEvent) -> None:
        self.window.table.blockSignals(True)
        self.firstClicked.emit(self.text())
        super(MyLineEdit, self).focusInEvent(a0)

    def focusOutEvent(self, a0: QFocusEvent) -> None:
        self.window.table.blockSignals(False)
        # print('Unfocused')
        super(MyLineEdit, self).focusOutEvent(a0)

    def wheelEvent(self, a0: QWheelEvent) -> None:
        return


class MySearchTable(QTableView):
    cellChanged = pyqtSignal(int, int, name="cellChanged")
    itemSelectionChanged = pyqtSignal(name="itemSelectionChanged")

    def __init__(self):
        super(MySearchTable, self).__init__()
        self.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.verticalHeader().setMinimumSectionSize(24)
        self.setSortingEnabled(True)
        self.mainModel = MySearchTableModel(self)
        self.setModel(self.mainModel)
        self.setEditTriggers(QAbstractItemView.EditTrigger.DoubleClicked)

    def emitItemChanged(self, index: QModelIndex):
        self.cellChanged.emit(index.row(), index.column())

    def setModel(self, model: QAbstractItemModel) -> None:
        model.dataChanged.connect(self.emitItemChanged)
        super().setModel(model)
        self.selectionModel().selectionChanged.connect(self.itemSelectionChanged.emit)

    def currentItem(self):
        return self.model().data(self.currentIndex(), Qt.ItemDataRole.DisplayRole)

    def setHorizontalHeaderLabels(self, labels: list):  # sets all labels up to length of "labels" excluding extras
        self.model().setHeaderData(0, Qt.Orientation.Horizontal, labels)

    def setVerticalHeaderLabels(self, labels: list):
        self.model().setHeaderData(0, Qt.Orientation.Vertical, labels)

    def verticalHeaderLabel(self, index) -> str:
        return self.model().headerData(index, Qt.Orientation.Vertical, Qt.ItemDataRole.DisplayRole)

    def horizontalHeaderLabel(self, index) -> str:
        return self.model().headerData(index, Qt.Orientation.Horizontal, Qt.ItemDataRole.DisplayRole)

    def setAllData(self, data: list):
        self.model().setAllData(data)
        for i in range(50 if 50 > self.model().rowCount() else self.model().rowCount()):
            self.resizeRowToContents(i)

    def setData(self, row, column, value):
        self.model().setData(self.model().index(row, column), value, Qt.ItemDataRole.EditRole)

    def getData(self, row: int, column: int) -> str:
        return self.model().data(self.model().index(row, column), Qt.ItemDataRole.DisplayRole)

    def clearData(self):
        self.model().setAllData(list())


class MySearchTableModel(QAbstractTableModel):
    allDataLoaded = pyqtSignal(name="allDataLoaded")

    def __init__(self, parent=None):
        super().__init__(parent)
        self.tableData = []
        self.hHeaderData = []
        self.vHeaderData = []
        self.rowAmount = 0
        self.columnAmount = 0
        self.loaded = False

    def rowCount(self, parent: QModelIndex = ...) -> int:
        return self.rowAmount

    def columnCount(self, parent: QModelIndex = ...) -> int:
        return self.columnAmount

    def data(self, index: QModelIndex, role: int = ...):
        if not index.isValid():
            print(index.row(), index.column())
            return QVariant()
        if index.row() >= self.rowAmount or index.row() < 0:
            return QVariant()
        match role:
            case Qt.ItemDataRole.DisplayRole:
                #print(index.row(), index.column())
                return self.tableData[index.row()][index.column()]
            case Qt.ItemDataRole.EditRole:
                return self.tableData[index.row()][index.column()]

        return QVariant()

    def setData(self, index: QModelIndex, value, role: int = ...) -> bool:
        if role == Qt.ItemDataRole.EditRole:
            if not self.checkIndex(index):
                return False
            if type(value) != str:
                value = value.toString()
            self.tableData[index.row()][index.column()] = value
            self.dataChanged.emit(index, index, [Qt.ItemDataRole.DisplayRole])
            return True
        return False

    def sort(self, column: int, order: Qt.SortOrder = ...) -> None:
        self.tableData.sort(reverse=order.value, key=lambda x: x[column] if x[column] else str())
        self.setHeaderData(0, Qt.Orientation.Vertical, [r[0] for r in self.tableData])
        self.parent().blockSignals(True)
        self.dataChanged.emit(self.createIndex(0, 0), self.createIndex(self.rowAmount - 1, self.columnAmount - 1),
                              [Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole])
        self.parent().blockSignals(False)

    def setAllData(self, data: list) -> bool:
        self.rowAmount = len(data)
        self.columnAmount = len(data[0]) if len(data) > 0 else 0
        if self.rowAmount == 0:
            self.beginResetModel()
        self.tableData = [list(d) for d in data]
        if self.rowAmount == 0:
            self.endResetModel()
        if len(self.hHeaderData) >= self.columnAmount:
            while len(self.hHeaderData) != self.columnAmount:
                self.hHeaderData.pop()
        else:
            while len(self.hHeaderData) != self.columnAmount:
                self.hHeaderData.append('')
        if len(self.vHeaderData) >= self.rowAmount:
            while len(self.vHeaderData) != self.rowAmount:
                self.vHeaderData.pop()
        else:
            while len(self.vHeaderData) != self.rowAmount:
                self.vHeaderData.append('')
        self.dataChanged.emit(self.createIndex(0, 0), self.createIndex(self.rowAmount - 1, self.columnAmount - 1),
                              [Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole])
        self.loadedRows = 50 if 50 > self.rowAmount else self.rowAmount
        self.startBackgroundTimer()
        return True

    def setHeaderData(self, section: int, orientation: Qt.Orientation, value, role: int = ...) -> bool:
        if type(value) == list:
            l = True
        elif type(value) != str:
            value = value.toString()
            l = False
        else:
            l = False
        if orientation == Qt.Orientation.Horizontal:
            if l:
                for i in range(len(value)):
                    if i > len(self.hHeaderData) - 1:
                        break
                    self.hHeaderData[i] = value[i]
                self.headerDataChanged.emit(orientation, 0, len(value) - 1 if len(
                    value) <= self.columnAmount else self.columnAmount - 1)
            else:
                self.hHeaderData[section] = value
                self.headerDataChanged.emit(orientation, section, section)
            return True
        elif orientation == Qt.Orientation.Vertical:
            if l:
                for i in range(len(value)):
                    if i > len(self.vHeaderData) - 1:
                        break
                    self.vHeaderData[i] = value[i]
                self.headerDataChanged.emit(orientation, 0, len(value) - 1 if len(
                    value) <= self.rowAmount else self.rowAmount - 1)
            else:
                self.vHeaderData[section] = value
                self.headerDataChanged.emit(orientation, section, section)
            return True

        return False

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = ...):
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                return self.hHeaderData[section] if section < len(self.hHeaderData) else QVariant()
            else:
                return self.vHeaderData[section]if section < len(self.vHeaderData) else QVariant()

        return QVariant()

    def backgroundLoadRow(self):
        if not self.loaded:
            self.resizeRow()

    def startBackgroundTimer(self):
        timer = QTimer(self)
        timer.timeout.connect(self.backgroundLoadRow)
        self.allDataLoaded.connect(timer.stop)
        timer.start(0)

    def resizeRow(self):
        if self.rowAmount > self.loadedRows:
            self.parent().blockSignals(True)
            self.parent().resizeRowToContents(self.loadedRows)
            self.parent().blockSignals(False)
            self.loadedRows += 1
        else:
            self.loaded = True
            self.allDataLoaded.emit()

    def insertRow(self, row: int, parent: QModelIndex = ...) -> bool:
        self.beginInsertRows(QModelIndex(), row, row)
        self.tableData.insert(row, [str() for i in range(self.columnAmount)])
        self.vHeaderData.insert(row, str(self.rowAmount + 1))
        self.endInsertRows()
        self.rowAmount += 1
        return True

    def removeRow(self, row: int, parent: QModelIndex = ...) -> bool:
        self.beginRemoveRows(QModelIndex(), row, row)
        self.tableData.pop(row)
        self.vHeaderData.pop(row)
        self.endRemoveRows()
        self.rowAmount -= 1
        return True

    def insertColumn(self, column: int, parent: QModelIndex = ...) -> bool:
        self.beginInsertColumns(QModelIndex(), column, column)
        for row in self.tableData:
            row.insert(column, str())
        self.hHeaderData.insert(column, str())
        self.endInsertColumns()
        self.columnAmount += 1
        return True

    def removeColumn(self, column: int, parent: QModelIndex = ...) -> bool:
        self.beginRemoveColumns(QModelIndex(), column, column)
        for row in self.tableData:  # this is expensive
            row.pop(column)
        self.hHeaderData.pop(column)
        self.endRemoveColumns()
        self.columnAmount -= 1
        return True

    def flags(self, index: QModelIndex) -> Qt.ItemFlag:
        if not index.isValid():
            return Qt.ItemFlag.ItemIsEnabled
        return super().flags(index) | Qt.ItemFlag.ItemIsEditable


class MySearchLineEdit(QLineEdit):
    focused = pyqtSignal(name="focused")

    def __init__(self, w):
        super().__init__()
        self.search_win = w
        self.switch = True

    def focusInEvent(self, e: QFocusEvent) -> None:
        if self.switch is False:
            print("stacked focusInEvent")
            return
        self.focused.emit()
        self.search_win.search_table.blockSignals(True)
        # print('Focused')
        self.switch = False
        super(MySearchLineEdit, self).focusInEvent(e)

    def focusOutEvent(self, e: QFocusEvent) -> None:
        self.search_win.search_table.blockSignals(False)
        # print("Unfocused")
        self.switch = True
        super(MySearchLineEdit, self).focusOutEvent(e)


class MyTable(QTableView):
    cellChanged = pyqtSignal(int, int, name="cellChanged")
    itemSelectionChanged = pyqtSignal(name="itemSelectionChanged")
    cellEntered = pyqtSignal(int, int, name="cellEntered")

    def __init__(self, parent=None):
        super(MyTable, self).__init__(parent)
        self.setWordWrap(True)
        self.setMouseTracking(True)

        self.setModel(MyTableModel(self))

        self.setHorizontalHeader(MyHHeaderView(self))
        self.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)

        self.verticalHeader().setMinimumSectionSize(24)
        self.verticalHeader().setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        #self.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)

        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.entered.connect(self.emitCellEntered)

    def emitItemChanged(self, index: QModelIndex):
        self.cellChanged.emit(index.row(), index.column())

    def emitCellEntered(self, index: QModelIndex):
        self.cellEntered.emit(index.row(), index.column())

    def setModel(self, model: QAbstractItemModel) -> None:
        model.dataChanged.connect(self.emitItemChanged)
        super().setModel(model)
        self.selectionModel().selectionChanged.connect(self.itemSelectionChanged.emit)

    def currentColumn(self):
        return self.currentIndex().column()

    def currentRow(self):
        return self.currentIndex().row()

    def columnCount(self):
        return self.model().columnCount()

    def setColumnCount(self, count: int):
        while count > self.model().columnCount():
            self.model().insertColumn(self.model().columnCount())
        while count < self.model().columnCount():
            self.model().removeColumn(self.model().columnCount() - 1)

    def rowCount(self):
        return self.model().rowCount()

    def setRowCount(self, count: int):
        while count > self.model().rowCount():
            self.model().insertRow(self.model().rowCount())
        while count < self.model().rowCount():
            self.model().removeRow(self.model().rowCount() - 1)

    def itemAt(self, point: QPoint):  # TODO check if this works
        return self.model().data(self.indexAt(point), Qt.ItemDataRole.DisplayRole)

    def insertColumn(self, section: int):
        self.model().insertColumn(section)

    def removeColumn(self, section: int):
        self.model().removeColumn(section)

    def insertRow(self, section: int):
        self.model().insertRow(section)
        self.resizeRowToContents(section)

    def removeRow(self, row: int):
        self.model().removeRow(row)

    def loadRow(self):
        self.blockSignals(True)
        self.model().loadRow()
        self.blockSignals(False)

    def getEmptyRows(self):
        return self.model().getEmptyRows()

    def setData(self, row, column, value):
        self.model().setData(self.model().index(row, column), value, Qt.ItemDataRole.EditRole)

    def setRowData(self, row: int, data: list):
        self.model().setRowData(row, data)

    def setAllData(self, data: list):
        self.model().setAllData(data)
        for i in range(50 if 50 > self.rowCount() else self.rowCount()):
            self.resizeRowToContents(i)

    def getData(self, row: int, column: int) -> str:
        return self.model().data(self.model().index(row, column), Qt.ItemDataRole.DisplayRole)

    def selectedItems(self):
        return [self.model().data(index, Qt.ItemDataRole.DisplayRole) for index in self.selectedIndexes()]

    def verticalHeaderItem(self, section: int) -> str:
        return self.model().headerData(section, Qt.Orientation.Vertical, Qt.ItemDataRole.DisplayRole)

    def horizontalHeaderItem(self, section: int) -> str:
        return self.model().headerData(section, Qt.Orientation.Horizontal, Qt.ItemDataRole.DisplayRole)

    def setHorizontalHeaderItem(self, section: int, item: str):
        self.model().setHeaderData(section, Qt.Orientation.Horizontal, item)

    def setHorizontalHeaderLabels(self, labels: list):  # sets all labels up to length of "labels" excluding extras
        self.model().setHeaderData(0, Qt.Orientation.Horizontal, labels)

    def setVerticalHeaderLabels(self, labels: list):
        self.model().setHeaderData(0, Qt.Orientation.Vertical, labels)

    def item(self, row, column) -> str:  # TODO same as 'getData'
        return self.model().data(self.model().index(row, column), Qt.ItemDataRole.DisplayRole)
        pass

    def currentItem(self):
        return self.model().data(self.currentIndex(), Qt.ItemDataRole.DisplayRole)


class MyTableModel(MySearchTableModel):
    def __init__(self, parent):
        super().__init__(parent)

    def setRowData(self, row: int, rowData: list):
        if row < len(self.tableData):
            self.tableData[row] = rowData[1:]
            self.dataChanged.emit(self.createIndex(row, 0), self.createIndex(row, self.columnAmount - 1),
                                  [Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole])

    def setAllData(self, data: list) -> bool:
        self.parent().blockSignals(True)
        self.loaded = False
        self.rowAmount = len(data)
        self.columnAmount = len(data[0]) - 1 if len(data) > 0 else 0
        if self.rowAmount == 0:
            self.beginResetModel()
        self.tableData = [list(d[1:]) for d in data]
        if self.rowAmount == 0:
            self.endResetModel()
        if len(self.hHeaderData) >= self.columnAmount:
            while len(self.hHeaderData) != self.columnAmount:
                self.hHeaderData.pop()
        else:
            while len(self.hHeaderData) != self.columnAmount:
                self.hHeaderData.append('')
        self.dataChanged.emit(self.createIndex(0, 0), self.createIndex(self.rowAmount - 1, self.columnAmount - 1),
                              [Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole])
        self.headerDataChanged.emit(Qt.Orientation.Vertical, 0, self.rowAmount - 1)
        self.loadedRows = 50 if 50 > self.rowAmount else self.rowAmount
        self.startBackgroundTimer()
        self.parent().blockSignals(False)
        return True

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = ...):
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                return self.hHeaderData[section] if section < len(self.hHeaderData) else QVariant()
            else:
                return section + 1

        return QVariant()

    def getEmptyRows(self):
        del_rows = []

        for row in range(len(self.tableData) - 1, -1, -1):
            if all([x is None for x in self.tableData[row][1:]]):
                del_rows.append(row + 1)

        return del_rows

    def insertRow(self, row: int, parent: QModelIndex = ...) -> bool:
        self.beginInsertRows(QModelIndex(), row, row)
        self.tableData.insert(row, [str() for i in range(self.columnAmount)])
        self.endInsertRows()
        self.rowAmount += 1
        return True

    def removeRow(self, row: int, parent: QModelIndex = ...) -> bool:
        self.beginRemoveRows(QModelIndex(), row, row)
        self.tableData.pop(row)
        self.endRemoveRows()
        self.rowAmount -= 1
        return True


class MyColorDialog(QColorDialog):

    def __init__(self):
        super().__init__()

        for child in self.findChildren(QWidget):
            classname = child.metaObject().className()
            if classname not in ("QColorPicker", "QColorLuminancePicker", "QColorShower", "QDialogButtonBox",
                                 "QLabel", "QSpinBox", "QLineEdit"):
                child.hide()
            if classname == "QLabel":
                # print(child.text())
                if child.text() in ("&Basic colors", "&Custom colors"):
                    child.hide()

            if classname == "QColorShower":
                self.color_shower = child


class MyHHeaderView(QHeaderView):
    headerLabelChanged = pyqtSignal(int, str)

    def __init__(self, parent):
        super().__init__(Qt.Orientation.Horizontal, parent)
        self.cur_index = 0
        # settings flags
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.setSectionsMovable(True)
        self.setSectionsClickable(True)
        # setting up lineedit
        self.edit = MyFloatingLineEdit(
            self.viewport())  # if you set it to be a popup it effectively maps to global
        # connecting signals
        self.sectionDoubleClicked.connect(self.edit_header)
        self.edit.editingFinished.connect(self.update_label)

    def edit_header(self, section_index):
        geometry = self.edit.geometry()
        geometry.setWidth(self.sectionSize(section_index) - 3)
        geometry.moveLeft(self.sectionViewportPosition(section_index))
        self.edit.setGeometry(geometry)
        self.edit.setText(self.model().headerData(section_index, Qt.Orientation.Horizontal, Qt.ItemDataRole.DisplayRole))
        self.edit.setHidden(False)
        self.edit.blockSignals(False)
        self.edit.setFocus()
        self.edit.selectAll()
        self.cur_index = section_index

    def update_label(self):
        self.edit.blockSignals(True)
        self.edit.hide()
        text = self.edit.text()
        self.model().setHeaderData(self.cur_index, self.orientation(), text)
        self.headerLabelChanged.emit(self.cur_index, text)


class MyFloatingLineEdit(QLineEdit):

    def __init__(self, parent):
        super().__init__(parent=parent)
        self.setFrame(False)
        self.setFixedHeight(18)
        self.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.blockSignals(True)
        self.hide()


class MyWorker(QObject):

    def __init__(self, container):
        super().__init__()
        self.container = container
        print(self.container)
