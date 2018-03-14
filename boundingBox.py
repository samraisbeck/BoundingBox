"""
This program is for getting images ready for the training/testing of a
neural network for object detection with bounding boxes.
It allows the user to open a set of images, classify each one, and put a
bounding box around the object of interest (OOI).
Then, a CSV file can be saved. Partly finished sets can be saved and loaded to
be finished at a later time.
Finally, once all images are manually classified and bounded, a TFRecord file
can be generated, which can be used for the training of a neural network.

As of January 19 2018 it only works when one OOI is in the picture. This will
be updated.
- SR
"""

import sys, os, csv
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
import matplotlib.patches as patches
import matplotlib.image as mimg
import PyQt5.QtWidgets as QtW
import PyQt5.QtCore as QtC
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from math import floor
from subprocess import Popen
from widgetClassify import WidgetClassify

class MainControl(QtW.QMainWindow):
    def __init__(self):
        super(MainControl, self).__init__()
        self.isSaved = True
        self.images = []
        self.boundBoxes = []
        self.textLabels = []
        self.isDrawing = False
        self._index = 0
        self.startPos = (0, 0)
        self.endPos = (0, 0)
        self.tags = []
        self.classes = []
        self.uniqueClasses = []
        self.wh = []
        self.initUI()
        self.connectFigureEvents()
        self.exportMessages = ['',
                              'There was an error trying to match class names to '\
                              'ID numbers. Check in config/classDict.yaml that it is set '\
                              'up to match your classifications in the corresponding csv.',
                              'There was an error reading config/classDict.yaml. Check it to make sure '\
                              'that it is formatted correctly.',
                              'Could not find config/classDict.yaml. Make sure it exists and is '\
                              'in the right place.']
        self.classifyWindow = WidgetClassify()
        self.classifyWindow.ClassifySelection.connect(self.editClass, QtC.Qt.QueuedConnection)

    @property
    def index(self): return self._index

    @index.setter
    def index(self, val):
        """ It's more convenient to have index like this, so that the buttons
        can easily be updated if the index is at the limits. """
        self._index = val
        if self.boundBox != None:
            self.boundBox.remove()
        self.buttonPrev.setEnabled(self._index > 0)
        self.buttonNext.setEnabled(self._index < len(self.images)-1)

    def initUI(self):
        grid = QtW.QGridLayout()
        button = QtW.QPushButton('Select Image(s)', parent=self)
        button.clicked.connect(self.selectImages)
        grid.addWidget(button, 0, 0)
        hbox = QtW.QHBoxLayout()
        self.buttonPrev = QtW.QPushButton('Previous', parent=self)
        self.buttonPrev.clicked.connect(self.previousImage)
        self.buttonPrev.setShortcut('Backspace')
        self.buttonPrev.setEnabled(False)
        hbox.addWidget(self.buttonPrev, 10)
        self.buttonNext = QtW.QPushButton('  Next  ', parent=self)
        self.buttonNext.clicked.connect(self.nextImage)
        self.buttonNext.setShortcut('Return')
        self.buttonNext.setEnabled(False)
        hbox.addWidget(self.buttonNext, 10)
        label = QtW.QLabel('Seek Image:', parent=self)
        hbox.addWidget(label, 1)
        self.seekEdit = QtW.QLineEdit(parent=self)
        self.seekEdit.setText('1')
        hbox.addWidget(self.seekEdit, 1)
        button = QtW.QPushButton('Go!', parent=self)
        button.clicked.connect(self.seekImage)
        hbox.addWidget(button, 3)
        grid.addLayout(hbox, 1, 0)
        hbox = QtW.QHBoxLayout()
        button = QtW.QPushButton(' Save Info to File ', parent=self)
        button.clicked.connect(self.save)
        hbox.addWidget(button)
        button = QtW.QPushButton('Export TFRecord File', parent=self)
        if not os.path.exists('generateTFRecord.py'):
            button.setEnabled(False)
        button.clicked.connect(self.exportTFRecord)
        hbox.addWidget(button)
        button = QtW.QPushButton('Load Info from File', parent=self)
        button.clicked.connect(self.load)
        hbox.addWidget(button)
        grid.addLayout(hbox, 2, 0)
        self.fig = plt.figure()
        self.ax = self.fig.add_subplot(111)
        self.boundBox = None
        self.canvas = FigureCanvas(self.fig)
        grid.addWidget(self.canvas, 3, 0)
        button = QtW.QPushButton('Remove Last Bounding Box', parent=self)
        button.clicked.connect(self.removeLast)
        button.setShortcut('Delete')
        grid.addWidget(button, 4, 0)
        Qw = QtW.QWidget()
        Qw.setLayout(grid)
        self.setCentralWidget(Qw)
        self.setWindowTitle('Image Prep for TF Object Detection API')
        self.show()

    def updateImage(self):
        self.ax.clear()
        img = mimg.imread(self.images[self.index])
        self.ax.imshow(img)
        for i in range(len(self.boundBoxes[self.index])):
            self.ax.add_patch(self.boundBoxes[self.index][i])
            textElement = self.ax.text(self.textLabels[self.index][i].get_position()[0], self.textLabels[self.index][i].get_position()[1],
                                       self.textLabels[self.index][i].get_text(), bbox=dict(facecolor='white', alpha=0.5))
            self.textLabels[self.index][i] = textElement
        title = 'Image '+str(self.index+1)+'/'+str(len(self.images))
        self.ax.set_title(title)
        self.wh[self.index] = (int(round(self.ax.get_xlim()[1])), int(round(self.ax.get_ylim()[0])))
        self.canvas.draw()


    def selectImages(self):
        if not self.isSaved:
            reply = self.savePrompt()
            if reply == True:
                self.save()
            elif reply == None:
                return
        try:
            temp = self.images
            self.images = QtW.QFileDialog.getOpenFileNames(self, 'Select a file to load', os.path.realpath(__file__))[0]
            if len(self.images) == 0:
                self.images = temp
                return
            if len(self.boundBoxes) > 0:
                for i in range(len(self.boundBoxes[self.index])):
                    self.boundBoxes[self.index][i].remove()
                    self.textLabels[self.index][i].remove()
            self.tags = []
            self.classes = []
            self.wh = []
            self.boundBoxes = []
            self.textLabels = []
            for __ in range(len(self.images)):
                self.tags.append([]) #(sp tuple, ep tuple)
                self.classes.append([])
                self.wh.append((0, 0)) #(width, height)
                self.boundBoxes.append([])
                self.textLabels.append([])
            self.index = 0
            self.updateImage()
            self.isSaved = False
            print (self.images)
            return
        except:
            raise
            print('Something went wrong! Make sure you selected a valid image.')
            return

    def previousImage(self):
        self.index -= 1
        for i in range(len(self.boundBoxes[self.index+1])):
            self.boundBoxes[self.index+1][i].remove()
            self.textLabels[self.index+1][i].remove()
        self.updateImage()

    def nextImage(self):
        self.index += 1
        for i in range(len(self.boundBoxes[self.index-1])):
            self.boundBoxes[self.index-1][i].remove()
            self.textLabels[self.index-1][i].remove()
        self.updateImage()

    def seekImage(self):
        try:
            num = int(self.seekEdit.text())-1
            if (num <= -1):
                raise
            temp = self.index
            self.index = num
            for i in range(len(self.boundBoxes[temp])):
                self.boundBoxes[temp][i].remove()
                self.textLabels[temp][i].remove()
            self.updateImage()
        except:
            box = QtW.QMessageBox(QtW.QMessageBox.Critical, 'Error', 'You must enter a '\
                                  'valid integer in the range of 1 to <number of images>. Also make '\
                                  'sure you have loaded some images.', parent=self)
            box.exec_()
            return


    def editClass(self, label):
        if label not in self.uniqueClasses:
            query = QtW.QMessageBox.question(self, 'New Entry?', '"'+label+'" is a new class. Please confirm: is this correct?', QtW.QMessageBox.Yes | QtW.QMessageBox.No)
            if query == QtW.QMessageBox.Yes:
                self.uniqueClasses.append(label)
        self.classes[self.index].append(label)
        textElement = self.ax.text(self.startPos[0], self.startPos[1], label, bbox=dict(facecolor='white', alpha=0.5))
        self.textLabels[self.index].append(textElement)
        self.canvas.draw()

    def onPress(self, event):
        self.startPos = (floor(event.xdata), floor(event.ydata))

    def onUp(self, event):
        self.isSaved = False
        self.endPos = (floor(event.xdata), floor(event.ydata))
        temp = (min(self.startPos[0], self.endPos[0]), min(self.startPos[1], self.endPos[1]))
        self.endPos = (max(self.startPos[0], self.endPos[0]), max(self.startPos[1], self.endPos[1]))
        self.startPos = temp
        self.tags[self.index].append((self.startPos, self.endPos))
        self.boundBoxes[self.index].append(patches.Rectangle(self.tags[self.index][-1][0], self.tags[self.index][-1][1][0]-self.tags[self.index][-1][0][0],
                                          self.tags[self.index][-1][1][1]-self.tags[self.index][-1][0][1], fill=False, linewidth=2))
        self.ax.add_patch(self.boundBoxes[self.index][-1])
        self.canvas.draw()
        self.classifyWindow.exec()

    def removeLast(self):
        try:
            box = self.boundBoxes[self.index].pop()
            text = self.textLabels[self.index].pop()
            self.classes[self.index].pop()
            self.tags[self.index].pop()
        except IndexError:
            box = QtW.QMessageBox(QtW.QMessageBox.Critical, 'Error', 'There are no '\
                                  'bounding boxes to remove.', parent=self)
            box.exec_()
            return
        box.remove()
        text.remove()
        self.canvas.draw()
        self.isSaved = False

    def connectFigureEvents(self):
        self.fig.canvas.mpl_connect('button_press_event', self.onPress)
        self.fig.canvas.mpl_connect('button_release_event', self.onUp)

    def save(self):
        if len(self.images) == 0:
            box = QtW.QMessageBox(QtW.QMessageBox.Critical, 'Error', 'You must load '\
                                  'some images to be able to save data.', parent=self)
            box.exec_()
            return
        filename = QtW.QFileDialog.getSaveFileName(self, 'Save your file', os.path.dirname(os.path.realpath(__file__))+os.sep+'data',
                                                              'Microsoft Excel Comma Separated Values File (*.csv)')[0]
        if filename == '':
            return
        try:
            fcsv = open(filename, 'w')
        except PermissionError:
            box = QtW.QMessageBox(QtW.QMessageBox.Critical, 'Error', 'Permission Error: '\
                                  'the file is being used somewhere else. Close it then try again.', parent=self)
            box.exec_()
            return
        writer = csv.writer(fcsv)
        writer.writerow(['filename', 'width', 'height', 'class', 'xmin', 'ymin', 'xmax', 'ymax'])
        for i in range(len(self.images)):
            if len(self.tags[i]) != 0:
                for j in range(len(self.tags[i])):
                    writer.writerow([self.images[i], self.wh[i][0], self.wh[i][1], self.classes[i][j], \
                                     self.tags[i][j][0][0], self.tags[i][j][0][1], self.tags[i][j][1][0], self.tags[i][j][1][1]])
            else:
                writer.writerow([self.images[i], self.wh[i][0], self.wh[i][1], 0, 0, 0, 0, 0])
            writer.writerow(['###'])
        fcsv.close()
        self.isSaved = True
        return filename

    def load(self):
        if not self.isSaved:
            reply = self.savePrompt()
            if reply == True:
                self.save()
            elif reply == None:
                return
        filename = QtW.QFileDialog.getOpenFileName(self, 'Open a file', os.path.dirname(os.path.realpath(__file__))+os.sep+'data',
                                                   'Microsoft Excel Comma Separated Values File (*.csv)')[0]
        if filename == '':
            return
        self.images = []
        self.tags = []
        tempTags = []
        self.classes = []
        tempClasses = []
        self.wh = []
        tempWh = []
        newImage = True
        cnt = 0
        if len(self.boundBoxes) > 0:
            for i in range(len(self.boundBoxes[self.index])):
                self.boundBoxes[self.index][i].remove()
                self.textLabels[self.index][i].remove()
        self.boundBoxes = []
        self.textLabels = []
        self.uniqueClasses = []
        tempBoxes = []
        tempLabels = []
        reader = csv.reader(open(filename, 'r'))
        next(reader)
        for line in reader:
            if len(line) == 0:
                continue
            elif line[0] == '':
                continue
            elif line[0] == '###':
                newImage = True
                self.tags.append(tempTags)
                self.boundBoxes.append(tempBoxes)
                self.textLabels.append(tempLabels)
                self.classes.append(tempClasses)
                tempTags = []
                tempClasses = []
                tempBoxes = []
                tempLabels = []
                continue
            if newImage:
                self.images.append(line[0])
                self.wh.append((line[1],line[2]))
                newImage = False
            if line[3] == '0':
                # This means that the image hasn't been classified yet
                tempTags = []
                tempClasses = []
                tempBoxes = []
                tempLabels = []
            else:
                tempClasses.append(line[3])
                if line[3] not in self.uniqueClasses:
                    self.uniqueClasses.append(line[3])
                tempTags.append(((int(line[4]), int(line[5])), (int(line[6]), int(line[7]))))
                tempBoxes.append(patches.Rectangle(tempTags[-1][0], tempTags[-1][1][0]-tempTags[-1][0][0],
                                                         tempTags[-1][1][1]-tempTags[-1][0][1], fill=False, linewidth=2))
                tempLabels.append(self.ax.text(tempTags[-1][0][0], tempTags[-1][0][1], tempClasses[-1], bbox=dict(facecolor='white', alpha=0.5)))
                tempLabels[-1].remove()
        self.index = 0
        self.updateImage()
        return filename

    def exportTFRecord(self):
        for i in range(len(self.images)):
            if len(self.tags[i]) == 0:
                box = QtW.QMessageBox(QtW.QMessageBox.Critical, 'Error', 'You must finish '\
                                      'inputting all bounding boxes and classify every image '\
                                      'before creating the TFRecord file. You may choose to save '\
                                      'your progress and come back later to create the TFRecord.', parent=self)
                box.exec_()
                return
        fName = self.save() # we save a new csv to ensure that we export the current version
        if fName == None:
            return
        fName = fName[:-4]
        args = [sys.executable, 'generateTFRecord.py', '--dataLoc='+fName]
        recordProc = Popen(args, cwd = os.path.dirname(os.path.realpath(__file__)))
        recordProc.wait() # Wait for the TFRecord to be created
        err = recordProc.returncode
        # A few different outcomes
        if err == 0:
            box = QtW.QMessageBox(QtW.QMessageBox.Information, 'Info', 'Finished creating '\
                                  'the record file: '+fName+'.record', parent=self)
            box.exec_()
            print ('\nFinished creating record file: '+fName+'.record\n')
        else:
            box = QtW.QMessageBox(QtW.QMessageBox.Critical, 'Error', self.exportMessages[err], parent=self)
            box.exec_()
            print ('\n'+self.exportMessages[err]+'\n')

    def savePrompt(self):
        query = QtW.QMessageBox.question(self, 'Question', 'Save your progress?', QtW.QMessageBox.Yes | QtW.QMessageBox.No | QtW.QMessageBox.Cancel)
        if query == QtW.QMessageBox.Yes:
            return True
        elif query == QtW.QMessageBox.No:
            return False
        else:
            return None

    def closeEvent(self, event):
        if not self.isSaved:
            reply = self.savePrompt()
            if reply == True:
                self.save()
            elif reply == None:
                event.ignore()
                return
        super(MainControl, self).closeEvent(event)


if __name__ == '__main__':
    app = QtW.QApplication(sys.argv)
    mw = MainControl()
    sys.exit(app.exec_())
