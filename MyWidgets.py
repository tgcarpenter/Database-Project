from PyQt6.QtWidgets import QComboBox, QLineEdit, QSpinBox, QCompleter, QColorDialog, QWidget, QHeaderView, \
    QStyleOptionFrame, QStyle
from PyQt6.QtCore import Qt, QStringListModel, pyqtSignal, QPoint, QEvent, QObject
from PyQt6.QtGui import QFocusEvent, QPainter, QPaintEvent, QCursor


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
            com = com[:len(pre)].casefold()
            if pref[::-1] == com:
                self.lineEdit().setSelection(len(text), len(pre) * -1)
            self.lineEdit().insert(", " + completion)
        self.item = self.lineEdit().text()

    def focusInEvent(self, *args, **kwargs):
        self.window.table.blockSignals(True)
        self.firstClicked.emit(self.lineEdit().text())
        self.item = self.lineEdit().text()
        print('first clicked')
        super(MyComboBox, self).focusInEvent(*args)

    def focusOutEvent(self, a0: QFocusEvent) -> None:
        self.window.table.blockSignals(False)
        print('Unfocused')
        super(MyComboBox, self).focusOutEvent(a0)

    class InComboEdit(QLineEdit):
        def __init__(self, combo):
            super().__init__()
            self.combo = combo
            self.editingFinished.connect(self.set_item)

        def set_item(self):
            self.combo.item = self.text()
            self.combo.currentTextChanged.emit('')
            self.window.change_selected(self.text())


class MySpinBox(QSpinBox):
    firstClicked = pyqtSignal(str, name="firstClicked")

    def __init__(self, window):
        super().__init__()
        self.window = window

    def focusInEvent(self, *args, **kwargs):
        self.window.table.blockSignals(True)
        self.firstClicked.emit(self.cleanText())
        print('first clicked')
        super(MySpinBox, self).focusInEvent(*args)

    def focusOutEvent(self, a0: QFocusEvent) -> None:
        self.window.table.blockSignals(False)
        print('Unfocused')
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

    def set_autofill(self):
        autofill = self.window.databases[self.window.current_database].list_column_query(self.name)
        self.completer_modal.setStringList([str(a[0]) for a in autofill])

    def focusInEvent(self, a0: QFocusEvent) -> None:
        self.window.table.blockSignals(True)
        self.firstClicked.emit(self.text())
        super(MyLineEdit, self).focusInEvent(a0)

    def focusOutEvent(self, a0: QFocusEvent) -> None:
        self.window.table.blockSignals(False)
        print('Unfocused')
        super(MyLineEdit, self).focusOutEvent(a0)


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
        print('Focused')
        self.switch = False
        super(MySearchLineEdit, self).focusInEvent(e)

    def focusOutEvent(self, e: QFocusEvent) -> None:
        self.search_win.search_table.blockSignals(False)
        print("Unfocused")
        self.switch = True
        super(MySearchLineEdit, self).focusOutEvent(e)


class MyColorDialog(QColorDialog):

    def __init__(self):
        super().__init__()

        for child in self.findChildren(QWidget):
            classname = child.metaObject().className()
            if classname not in ("QColorPicker", "QColorLuminancePicker", "QColorShower", "QDialogButtonBox",
                                 "QLabel", "QSpinBox", "QLineEdit"):
                child.hide()
            if classname == "QLabel":
                print(child.text())
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
        self.edit.setText(self.model().headerData(section_index, Qt.Orientation.Horizontal))
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
