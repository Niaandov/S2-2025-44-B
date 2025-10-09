from PyQt5.QtWidgets import QApplication
import sys
from inspectionTask import inspectionTask

if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Create a test inspection task
    task = inspectionTask(errorRateVal=0.1, speed=100)

    # Show the window
    task.renderWindow.show()

    # Start the task
    # task.startTask()

    sys.exit(app.exec_())
