from PyQt6.QtGui import QPalette, QColor, QPen, QPainterPath, QPainter, QLinearGradient, QPixmap, \
    qGray
from PyQt6.QtCore import Qt, QRectF, pyqtSignal, QSettings, QRect, QPointF
from PyQt6.QtWidgets import QStyle, QProxyStyle, QWidget, QGraphicsDropShadowEffect, QToolTip, QApplication

import platform


class MyChangingPalette(QPalette):

    def __init__(self, preview=False, background=None, text=None, highlight=None):
        super().__init__()

        self.preview = preview
        self.light = False

        self.background = QColor(50, 50, 58)
        self.text = QColor(240, 238, 243)
        self.highlight = QColor(70, 80, 180)

        self.setShadeColors(self.background)
        self.setBackgroundColors(self.background)
        self.setTextColor(self.text)
        self.setHighlightColor(self.highlight)

    def setColorRoleForColorGroups(self, role, color):
        f, l = self.setFactors(color)
        for i in range(len(QPalette.ColorGroup)):
            self.setColor(QPalette.ColorGroup(i), role, color)
        if not self.preview:
            self.setColor(QPalette.ColorGroup.Disabled, role, color.lighter(l))

    def setBackgroundColors(self, color):
        f, l = self.setFactors(color)
        self.setColorRoleForColorGroups(QPalette.ColorRole.Window, color)
        self.setColorRoleForColorGroups(QPalette.ColorRole.Base, color.lighter(f))
        self.setColorRoleForColorGroups(QPalette.ColorRole.Button, color)
        self.setColorRoleForColorGroups(QPalette.ColorRole.ToolTipBase, color.lighter(l))
        self.background = color

    def setTextColor(self, color):
        f, l = self.setFactors(color)
        if (sum(color.getRgb()[:3]) < 400) == (sum(self.highlight.getRgb()[:3]) < 400):
            print(color.getRgb())
            r, g, b = color.getRgb()[:3]
            self.setColorRoleForColorGroups(QPalette.ColorRole.HighlightedText, QColor(255 - r, 255 - g, 255 - b))
        else:
            self.setColorRoleForColorGroups(QPalette.ColorRole.HighlightedText, color)
        self.setColorRoleForColorGroups(QPalette.ColorRole.Text, color)
        self.setColorRoleForColorGroups(QPalette.ColorRole.ButtonText, color)
        self.setColorRoleForColorGroups(QPalette.ColorRole.WindowText, color)
        self.setColorRoleForColorGroups(QPalette.ColorRole.ToolTipText, color)
        self.setColorRoleForColorGroups(QPalette.ColorRole.PlaceholderText, color.lighter(f))
        self.text = color

    def setHighlightColor(self, color):
        self.setColorRoleForColorGroups(QPalette.ColorRole.Highlight, color)
        self.highlight = color

    def setShadeColors(self, color: QColor):
        f, l = self.setFactors(color)
        self.setBrush(QPalette.ColorRole.Light, color.lighter(f))
        self.setBrush(QPalette.ColorRole.Midlight, color)
        self.setBrush(QPalette.ColorRole.Mid, color.lighter(l))
        self.setBrush(QPalette.ColorRole.Dark, color.lighter(l).lighter(l))
        self.setBrush(QPalette.ColorRole.Shadow, color.lighter(l).lighter(l).lighter(l))

    def setFactors(self, color):
        f = 50
        l = 150
        if sum(color.getRgb()[:3]) < 400:
            self.light = False
            return f, l
        else:
            self.light = True
            return l, f


class MyStyle(QProxyStyle):

    def __init__(self):
        super().__init__("Fusion")
        self.changing_palette = MyChangingPalette()

        settings = QSettings(r'settings.ini', QSettings.Format.IniFormat)
        settings.beginGroup("themes")
        if settings.value("palette"):
            colors = settings.value("palette")
            self.changing_palette.setShadeColors(colors[0])
            self.changing_palette.setBackgroundColors(colors[0])
            self.changing_palette.setHighlightColor(colors[2])
            self.changing_palette.setTextColor(colors[1])
        settings.endGroup()

        self.update_palette()

    def drawPrimitive(self, element, option: 'QStyleOption',
                      painter: QPainter, widget: QWidget) -> None:
        if element == QStyle.PrimitiveElement.PE_PanelTipLabel:

            widget.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
            widget.setWindowFlag(Qt.WindowType.FramelessWindowHint, True)
            widget.setPalette(self.changing_palette)

            rect = QRect(0, 0, option.rect.width(), option.rect.height())
            background = self.button_color(option.palette)
            gradient_start = background.lighter(130)
            gradient_stop = background.darker(102)
            gradient = QLinearGradient(QPointF(rect.topLeft()), QPointF(rect.bottomLeft()))

            self.set_gradient(gradient, option, gradient_start, gradient_stop)

            edge = background.darker()

            x, y, width, height = option.rect.getRect()

            path = self.rounded_corner(option.rect)

            painter.save()
            painter.fillPath(path, gradient)

            if sum(background.getRgb()[:3]) < 400:
                pen = QPen(background.lighter(125), 3)

                painter.setPen(pen)
                painter.drawLine(x + 3, y + height - 1, x - 3 + width, y + height - 1)

                pen = QPen(background.lighter(115), 3)

                painter.setClipPath(path)

                painter.setPen(pen)
                painter.drawPath(path)

            pen = QPen(edge, 2)

            painter.setPen(pen)
            painter.drawPath(path)

            if platform.system() == "Windows":

                path = self.rounded_corner(option.rect, False)

                painter.setPen(pen)
                painter.drawPath(path)

            painter.restore()

        elif element == QStyle.PrimitiveElement.PE_PanelMenu:

            background = self.changing_palette.background

            edge = background.lighter(115)

            path = QPainterPath()
            path.addRect(QRectF(option.rect))

            painter.save()
            painter.fillPath(path, background)

            pen = QPen(background.lighter(115), 1)

            painter.setClipPath(path)

            painter.setPen(pen)
            painter.drawPath(path)

            pen = QPen(edge, 1)

            painter.setPen(pen)
            painter.drawPath(path)

            painter.restore()

        elif element == QStyle.PrimitiveElement.PE_PanelLineEdit \
                and widget.parent().objectName() == "qt_scrollarea_viewport":

            rect = QRect(0, 0, option.rect.width(), option.rect.height())
            rect.setTop(rect.top() + 1)
            button_color = self.button_color(option.palette)
            gradient_start = button_color.lighter(115)
            gradient_stop = button_color.darker(102)
            gradient = QLinearGradient(QPointF(rect.topLeft()), QPointF(rect.bottomLeft()))

            self.set_gradient(gradient, option, gradient_start, gradient_stop)

            painter.save()
            painter.fillRect(rect, gradient)

            painter.restore()

        else:
            super().drawPrimitive(element, option, painter, widget)

    @staticmethod
    def merged_colors(color1: QColor, color2: QColor, factor=50):
        maxFactor = 100
        tmp = color1
        tmp.setRed((tmp.red() * factor) // maxFactor + (color2.red() * (maxFactor - factor)) // maxFactor)
        tmp.setGreen((tmp.green() * factor) // maxFactor + (color2.green() * (maxFactor - factor)) // maxFactor)
        tmp.setBlue((tmp.blue() * factor) // maxFactor + (color2.blue() * (maxFactor - factor)) // maxFactor)

        return tmp

    @staticmethod
    def button_color(palette):
        color = palette.button().color()
        val = qGray(color.rgb())
        color = color.lighter(100 + max(1, (180 - val) // 6))
        color.setHsv(color.hue(), round(color.saturation() * .75), color.value())

        return color

    def set_gradient(self, gradient, option, start, stop):
        if option.palette.window().gradient():
            gradient.setStops(option.palette.window().gradient().stops())
        else:
            midColor1 = self.merged_colors(start, stop, 60)
            midColor2 = self.merged_colors(start, stop, 40)
            gradient.setColorAt(0, start)
            gradient.setColorAt(.5, midColor1)
            gradient.setColorAt(.501, midColor2)
            gradient.setColorAt(.92, stop)
            gradient.setColorAt(1, stop.darker(104))

    @staticmethod
    def rounded_corner(rect, corner=True):

        x1, y1, x2, y2 = rect.getRect()

        path = QPainterPath()
        path.moveTo(x2, y1 + 2)
        path.lineTo(x2 - 2, y1)
        path.lineTo(x1 + 2, y1)
        path.lineTo(x1, y1 + 2)
        path.lineTo(x1, y2 - 2)
        path.lineTo(x1 + 2, y2)
        if corner and platform.system() == "Windows":
            path.lineTo(x2, y2)
        else:
            path.lineTo(x2 - 2, y2)
            path.lineTo(x2, y2 - 2)

        path.closeSubpath()

        return path

    def update_palette(self):
        QApplication.setPalette(self.changing_palette)

