import sys

from PyQt6.QtWidgets import QApplication

from DatabaseprojectGUI import MainWindow
from CustomStyle import *


app = QApplication(sys.argv)

app.setStyle(MyStyle())

window = MainWindow()
window.show()

app.exec()
