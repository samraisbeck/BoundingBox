import sys, os, csv
import PyQt5.QtWidgets as QtW
import PyQt5.QtCore as QtC


class WidgetClassify(QtW.QDialog):
    ClassifySelection = QtC.Signal(str)
    def __init__(self, last=None):
        super(WidgetClassify, self).__init__()
        self.lastClass = last
        self.initUI()

    def initUI(self):
        grid = QtW.QGridLayout()
        hbox = QtW.QHBoxLayout()
        label = QtW.QLabel('Classification:', parent=self)
        hbox.addWidget(label)
        self.edit = QtW.QLineEdit(parent=self)
        if self.lastClass != None:
            self.edit.setText(self.lastClass)
        self.edit.returnPressed.connect(self.classify)
        hbox.addWidget(self.edit)
        grid.addLayout(hbox, 1, 0)
        label = QtW.QLabel('Press Enter to classify!', parent=self)
        grid.addWidget(label, 2, 0)
        self.setWindowTitle('Classification')
        self.setLayout(grid)

    def classify(self):
        self.ClassifySelection.emit(self.edit.text())
        self.hide()

    def closeEvent(self, event):
        self.ClassifySelection.emit(self.edit.text())
        super(WidgetClassify, self).closeEvent(event)
