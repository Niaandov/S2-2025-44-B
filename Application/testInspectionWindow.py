"""
This file is just a tester file to help trouble shoot the inspection task
 it can be deleted once the inspection task is implmented with the windowRender.py
"""
from PyQt5.QtWidgets import QApplication
import sys
from inspectionTask import inspectionTask

if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Create a test inspection task
    task = inspectionTask(errorRateVal=0.1, speed=2000, acceptedRange=12)

    # Show the window
    task.renderWindow.show()

    # Start the task
    # task.startTask()

    sys.exit(app.exec_())
