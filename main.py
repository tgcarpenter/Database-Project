import sys

from PyQt6.QtWidgets import QApplication

from DatabaseprojectGUI import MainWindow
from CustomStyle import *

if __name__ == '__main__':

    app = QApplication(sys.argv)

    app.setStyle(MyStyle())

    window = MainWindow()
    window.show()

    app.exec()
