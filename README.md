# BoundingBox
Program to put bounding boxes around objects in images, save as CSV and export as TFRecord (for TensorFlow)

This was made with Python 3.6.3

## Installation

Clone this repository (or download the zip), make sure Python 3 is properly installed (the python.exe and /Scripts locations are specified in the environment variable PATH), open a command prompt and do `pip install -r requirements.txt`. Or install each package manually:

`pip install numpy`

`pip install PyQt5`

`pip install matplotlib`

If `pip` doesn't work correctly, it is likely because you did not add your ..PythonXX/Scripts directory to your PATH (where XX is the version number, so Python36 for Python 3.6.x).

## Usage

Run `boundingBox.py`. This opens the GUI. Select the images you want (don't select a folder, use Shift+Click to select multiple image files). You can also load a previously saved set of images by hitting "Load Info from File" and selecting the `.csv`. Remember that the images must be in the same location as they were when the `.csv` was saved.

Now you can begin bounding the objects in each image, and putting a label on them. If the label is new, it will ask you to confirm that this label is correct (to avoid typos). More than one bounding box is allowed on each image, and it doesn't matter which corner you start drawing your box.

To draw a box, left-click and hold where one corner will be, and drag the mouse down to the diagonally opposite corner, and let go (i.e go from top-left to bottom-right, or bottom-left to top-right, etc...)

If you make a mistake (i.e typo, put a box in the wrong place), click the Delete key or hit the "Remove Last Bounding Box" button. Bounding boxes can be removed at any time. For example, if you finish 200 images and realize the first bounding box is wrong, you can just go back to that image and remove the box and put a new one in.

Hitting Enter scrolls forward through images, Backspace scrolls backward (or you can push the buttons).  

If you wish to save, hit Save Info, and name the file. This will save a `.csv` file. You can come back to it later by loading it in.

Remember, the way you bound the areas of interest must be consistent throughout the dataset! This is important when you begin to train a model, so it can recognize identifying features.

#### To Do

Add in `generateTFRecord.py` and a tensorflow module check.
