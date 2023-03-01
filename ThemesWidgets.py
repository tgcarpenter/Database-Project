from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QGridLayout, QPushButton, QLabel, QSizePolicy, \
    QStyleOptionButton, QStylePainter, QColorDialog, QMessageBox, QApplication, QFrame
from PyQt6.QtGui import QColor, QPalette, QPainterPath, QPainter, QPen, QBrush, QLinearGradient, QRadialGradient
from PyQt6.QtCore import Qt, QSettings, QPointF

from CustomStyle import MyChangingPalette
from DatabaseprojectGUI import MainWindow
from UniversalFunctions import get_signal
from MyWidgets import MyColorDialog


class EditThemes(QWidget):

    def __init__(self, window):
        super().__init__()
        # Stored Variables
        self.window = window

        self.setWindowTitle("Themes")
        self.setFixedSize(900, 700)

        self.cur_theme = None

        self.temp_background = QColor()
        self.temp_text = QColor()
        self.temp_highlight = QColor()

        # Font
        font = QLabel().font()
        font.setUnderline(True)

        # labels
        themes_label = QLabel("Themes:")
        themes_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        themes_label.setFont(font)
        dark_label = QLabel("Dark")
        dark_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        light_label = QLabel("Light")
        light_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        custom_themes_label = QLabel("Custom Themes:")
        custom_themes_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        custom_themes_label.setFont(font)
        color_options_label = QLabel("Color Options:")
        color_options_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        color_options_label.setFont(font)
        background_label = QLabel("Background")
        background_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        text_label = QLabel("Text")
        text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        highlight_label = QLabel("Highlight")
        highlight_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Palette and Preview Window
        self.preview_palette = MyChangingPalette(preview=True)

        self.window_preview = MainWindow()
        self.window_preview.setAutoFillBackground(True)
        self.window_preview.setFixedSize(600, 300)
        self.window_preview.setDisabled(True)
        self.window_preview.setPalette(self.preview_palette)

        self.background_button = EditColorButton(self)
        self.text_button = EditColorButton(self)
        self.highlight_button = EditColorButton(self)

        self.dark_theme = ThemeButton(self)
        self.light_theme = ThemeButton(self, True)
        self.custom_themes = [ThemeButton(self), ThemeButton(self), ThemeButton(self),
                              ThemeButton(self, True), ThemeButton(self, True), ThemeButton(self, True)]

        # Custom Color Dialog
        self.dialog = MyColorDialog()
        self.dialog.setOption(QColorDialog.ColorDialogOption.DontUseNativeDialog, True)

        # Buttons
        apply = QPushButton("&Apply")
        apply.setFixedWidth(108)
        apply.pressed.connect(self.apply_palette)

        cancel = QPushButton("Cancel")
        cancel.setFixedWidth(108)
        cancel.pressed.connect(self.load_from_temps)

        restore_defaults = QPushButton("&Reset Themes")
        restore_defaults.setFixedWidth(108)
        restore_defaults.pressed.connect(self.load_default_themes)

        # Reading Saved Themes
        try:
            self.readThemes()
        except:
            pass

        # setting initial selection
        self.dark_theme.set_preview()

        # Spacer/Seperator Objects
        self.spacer = QWidget()
        self.spacer.setMaximumHeight(170)
        self.spacer.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)

        spacer = QWidget()
        spacer.setFixedHeight(250)
        spacer.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)

        s = QWidget()
        s.setFixedHeight(20)
        s.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)

        seperator = QFrame()
        seperator.setFrameShape(QFrame.Shape.VLine)
        seperator.setLineWidth(1)

        # setting layouts in order of depth (top left to bottom right ish)
        default_themes_layout = QGridLayout()
        default_themes_layout.addWidget(dark_label, 1, 1)
        default_themes_layout.addWidget(light_label, 1, 2)
        default_themes_layout.addWidget(self.dark_theme, 2, 1)
        default_themes_layout.addWidget(self.light_theme, 2, 2)

        custom_themes_layout = QGridLayout()
        for i, theme in enumerate(self.custom_themes):
            custom_themes_layout.addWidget(theme, i // 3, i - 3 if i > 2 else i)

        themes_layout = QVBoxLayout()
        themes_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        themes_layout.addWidget(self.spacer)
        themes_layout.addWidget(themes_label)
        themes_layout.addLayout(default_themes_layout)
        themes_layout.addWidget(custom_themes_label)
        themes_layout.addLayout(custom_themes_layout)
        themes_layout.addWidget(s)
        themes_layout.addWidget(restore_defaults)
        themes_layout.setAlignment(restore_defaults, Qt.AlignmentFlag.AlignCenter)
        themes_layout.addWidget(spacer)

        colors_layout = QGridLayout()
        colors_layout.setHorizontalSpacing(50)
        colors_layout.setVerticalSpacing(8)
        colors_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        colors_layout.addWidget(background_label, 0, 1)
        colors_layout.addWidget(text_label, 0, 2)
        colors_layout.addWidget(highlight_label, 0, 3)
        colors_layout.addWidget(self.background_button, 1, 1)
        colors_layout.setAlignment(self.background_button, Qt.AlignmentFlag.AlignCenter)
        colors_layout.addWidget(self.text_button, 1, 2)
        colors_layout.setAlignment(self.text_button, Qt.AlignmentFlag.AlignCenter)
        colors_layout.addWidget(self.highlight_button, 1, 3)
        colors_layout.setAlignment(self.highlight_button, Qt.AlignmentFlag.AlignCenter)

        button_layout = QHBoxLayout()
        button_layout.addWidget(apply)
        button_layout.addWidget(cancel)

        value_layout = QVBoxLayout()
        value_layout.addWidget(s)
        value_layout.addWidget(self.dialog.color_shower)
        value_layout.addWidget(s)
        value_layout.addLayout(button_layout)

        dialog_layout = QHBoxLayout()
        dialog_layout.addWidget(self.dialog)
        dialog_layout.setAlignment(self.dialog, Qt.AlignmentFlag.AlignBaseline)
        dialog_layout.addLayout(value_layout)

        preview_and_colors_layout = QVBoxLayout()
        preview_and_colors_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        preview_and_colors_layout.addWidget(self.window_preview)
        preview_and_colors_layout.addWidget(color_options_label)
        preview_and_colors_layout.addLayout(colors_layout)
        preview_and_colors_layout.addLayout(dialog_layout)

        layout = QHBoxLayout()
        layout.addLayout(themes_layout)
        layout.addWidget(spacer)
        layout.addWidget(seperator)
        layout.addLayout(preview_and_colors_layout)

        self.setLayout(layout)

    # Handles changing colors in preview and color options
    def show_color_options(self, theme):
        self.set_palette_colors(theme, self.preview_palette)
        self.window_preview.table.horizontalHeader().sectionPressed.emit(0)

        b, t, h = theme.getColors()

        self.background_button.setTheme(theme, b)
        self.text_button.setTheme(theme, t)
        self.highlight_button.setTheme(theme, h)
        # handling exception for default palettes
        if theme in (self.dark_theme, self.light_theme):
            self.dialog.blockSignals(True)
        else:
            self.dialog.blockSignals(False)
        self.background_button.connectToDialog()
        self.cur_theme = theme

    def set_palette_colors(self, theme, palette):
        palette.setShadeColors(theme.background_color)
        palette.setBackgroundColors(theme.background_color)
        palette.setHighlightColor(theme.highlight_color)
        palette.setTextColor(theme.text_color)
        self.window_preview.setPalette(self.preview_palette)

    def apply_palette(self):
        settings = QSettings(r'settings.ini', QSettings.Format.IniFormat)
        settings.beginGroup("themes")
        settings.setValue("palette", [self.preview_palette.background, self.preview_palette.text,
                                      self.preview_palette.highlight])
        settings.endGroup()
        self.set_palette_colors(self.cur_theme, self.preview_palette)
        self.set_palette_colors(self.cur_theme, QApplication.style().changing_palette)
        QApplication.style().update_palette()
        self.window_preview.repaint()

    def store_temps(self, theme):
        for color, temp in zip(theme.getColors(), [self.temp_background, self.temp_text, self.temp_highlight]):
            r, g, b, a = color.getRgb()
            temp.setRgb(r, g, b, a)

    def load_from_temps(self):
        for color, temp in zip(self.cur_theme.getColors(), [self.temp_background, self.temp_text, self.temp_highlight]):
            r, g, b, a = temp.getRgb()
            color.setRgb(r, g, b, a)
        self.show_color_options(self.cur_theme)
        self.repaint()
        self.apply_palette()

    def saveThemes(self):
        settings = QSettings(r'settings.ini', QSettings.Format.IniFormat)
        settings.beginGroup("themes")
        settings.setValue("customthemes", [[theme.background_color, theme.text_color, theme.highlight_color]
                                           for theme in self.custom_themes])
        settings.endGroup()

    def readThemes(self):
        settings = QSettings(r'settings.ini', QSettings.Format.IniFormat)
        settings.beginGroup("themes")
        themes = settings.value("customthemes")
        for colors, theme in zip(themes, self.custom_themes):
            r, g, b, a = colors[0].getRgb()
            theme.background_color.setRgb(r, g, b, a)
            theme.text_color = colors[1]
            theme.highlight_color = colors[2]
        settings.endGroup()

    def load_default_themes(self):
        if self.cur_theme:
            ret = QMessageBox.question(self, "Reset Themes",
                                       "Would you like to reset themes to default?",
                                       QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel)
            if ret == QMessageBox.StandardButton.Cancel:
                return

        for theme in self.custom_themes[:3]:
            theme.set_dark()
            theme.repaint()

        for theme in self.custom_themes[3:]:
            theme.set_light()
            theme.repaint()

        self.dark_theme.set_preview()

    def closeEvent(self, event) -> None:
        ret = QMessageBox.question(self, "Save",
                                   "Would you like to save themes before closing?",
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No |
                                   QMessageBox.StandardButton.Cancel)
        if ret == QMessageBox.StandardButton.Cancel:
            event.ignore()
            return
        elif ret == QMessageBox.StandardButton.Yes:
            self.saveThemes()
        self.window.setEnabled(True)
        event.accept()


class ColorButton(QPushButton):

    def __init__(self, color=QColor(Qt.GlobalColor.black)):
        super().__init__()
        self.setFixedSize(50, 50)
        self.check = False

        self.button_color = color

    def paintEvent(self, a0) -> None:
        option = QStyleOptionButton()
        self.initStyleOption(option)
        painter = QStylePainter(self)

        fill = QRadialGradient(QPointF(self.rect().center()), 25, QPointF(self.rect().center()))
        fill.setColorAt(0.0, self.button_color)
        fill.setColorAt(1.0, self.button_color.lighter(110))
        path = self.draw_circle(option.rect)
        path.setFillRule(Qt.FillRule.WindingFill)

        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.fillPath(path, fill)

        painter.save()
        pen = QPen(Qt.GlobalColor.black, 2)
        if self.check:
            pen = QPen(Qt.GlobalColor.darkRed, 2)
        painter.setPen(pen)
        painter.drawPath(path)

        painter.restore()

    @staticmethod
    def draw_circle(rect, highlight=False):
        x1, y1, x2, y2 = rect.getRect()
        radius = (x2 / 2) - 1.5
        if highlight:
            radius = (x2 / 2) - 3

        path = QPainterPath()
        path.addRoundedRect(x1 + 1, y1 + 1, x2 - 2, y2 - 2, radius, radius, Qt.SizeMode.RelativeSize)

        return path


class ThemeButton(ColorButton):

    def __init__(self, window, light=False):
        self.win = window

        self.background_color = QColor()
        self.text_color = QColor()
        self.highlight_color = QColor()

        if light:
            self.set_light()
        else:
            self.set_dark()
        super().__init__(self.background_color)

        self.clicked.connect(self.set_preview)

    def set_light(self):
        self.background_color.setRgb(240, 240, 250)
        self.text_color.setRgb(0, 0, 0)
        self.highlight_color.setRgb(0, 144, 238)

    def set_dark(self):
        self.background_color.setRgb(50, 50, 58)
        self.text_color.setRgb(240, 238, 243)
        self.highlight_color.setRgb(70, 80, 180)

    def set_preview(self):
        for button in self.win.custom_themes + [self.win.dark_theme, self.win.light_theme]:  # changes visual drawn
            button.check = False
            button.repaint()
        self.check = True
        self.repaint()
        self.win.store_temps(self)
        self.win.show_color_options(self)

    def getColors(self):
        return self.background_color, self.text_color, self.highlight_color


class EditColorButton(ColorButton):

    def __init__(self, window):
        super().__init__()
        self.win = window
        self.clicked.connect(self.connectToDialog)
        self.cur_theme = None

    def set_color(self, color):
        r, g, b, a = color.getRgb()
        self.button_color.setRgb(r, g, b, a)
        self.repaint()
        self.cur_theme.repaint()
        self.win.set_palette_colors(self.cur_theme, self.win.preview_palette)

    def setTheme(self, theme, color):
        self.cur_theme = theme
        self.button_color = color
        self.repaint()

    def connectToDialog(self):
        for button in [self.win.background_button, self.win.text_button, self.win.highlight_button]:  # changes visual
            button.check = False
            button.repaint()
        self.check = True
        self.repaint()
        if self.win.dialog.isSignalConnected(get_signal(self.win.dialog, "currentColorChanged")):
            self.win.dialog.currentColorChanged.disconnect()
        self.test()
        self.win.dialog.setCurrentColor(self.button_color)

    def test(self):
        self.win.dialog.currentColorChanged.connect(self.set_color)
