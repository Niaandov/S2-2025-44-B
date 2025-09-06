import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton, QLineEdit, 
    QVBoxLayout, QHBoxLayout, QCheckBox, QSlider, QComboBox
)
from PyQt5.QtCore import Qt


class MainOCSWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Observer Control System")
        self.setGeometry(100, 100, 900, 500)

        # Central Widget & Main Layout
        centralWidget = QWidget(self)        
        self.setCentralWidget(centralWidget)
        mainLayout = QVBoxLayout(centralWidget)

        # === Title Bar ===
        self.titleLabel = QLabel("Observer Control System")
        self.titleLabel.setFixedHeight(20)
        titleLayout = QVBoxLayout()
        titleLayout.addWidget(self.titleLabel)
        mainLayout.addLayout(titleLayout)

        # === Middle Layout ===
        middleLayout = QHBoxLayout()

        # Session Info
        sessionLayout = self.create_session_info()
        middleLayout.addLayout(sessionLayout)

        # Tasks (Sorting, Packaging, Inspection)
        middleLayout.addLayout(self.create_task_section("SORTING"))
        middleLayout.addLayout(self.create_task_section("PACKAGING"))
        middleLayout.addLayout(self.create_task_section("INSPECTION"))

        # Stretch evenly
        for i in range(4):
            middleLayout.setStretch(i, 1)

        mainLayout.addLayout(middleLayout)

        sortERResult = 9
        sortThruResult= 9
        sortCorResult = 9

        packERResult = 9
        packThruResult=9
        packCorResult = 9

        inspERResult = 9
        inspThruResult= 9
        inspCorResult = 9

        partAvgCon = 2.0
        partAcc = 87




        # === Bottom Layout (Results) ===
        bottomLayout = QHBoxLayout()
        bottomLayout.addLayout(self.create_result_section("SORTING", sortERResult, sortThruResult, sortCorResult))
        bottomLayout.addLayout(self.create_result_section("PACKAGING", packERResult, packThruResult, packCorResult))
        bottomLayout.addLayout(self.create_result_section("INSPECTION", inspERResult, inspThruResult, inspCorResult))
        bottomLayout.addLayout(self.create_participant_results(partAvgCon, partAcc))
        mainLayout.addLayout(bottomLayout)


    # --- Helper: Session Info Layout ---
    def create_session_info(self):
        layout = QVBoxLayout()

        # Traffic lights
        lightsLayout = QHBoxLayout()
        for color in ["green", "yellow", "red"]:
            btn = QPushButton()
            btn.setStyleSheet(
                f"background-color: {color}; min-width: 40px; min-height: 40px;"
                "max-width: 40px; max-height: 40px;"
            )
            lightsLayout.addWidget(btn)
        layout.addLayout(lightsLayout)

        # Session name input
        nameLayout = QHBoxLayout()
        self.sessionName = QLineEdit(placeholderText="Session Name")
        saveBtn = QPushButton("SAVE")
        nameLayout.addWidget(self.sessionName)
        nameLayout.addWidget(saveBtn)
        layout.addLayout(nameLayout)

        # Session file input
        fileLayout = QHBoxLayout()
        self.sessionFile = QLineEdit(placeholderText="Session File")
        loadBtn = QPushButton("LOAD")
        fileLayout.addWidget(self.sessionFile)
        fileLayout.addWidget(loadBtn)
        layout.addLayout(fileLayout)

        return layout

    # --- Helper: Task Section (Sorting/Packaging/Inspection) ---
    def create_task_section(self, title):
        layout = QVBoxLayout()
        layout.addWidget(QLabel(title))
        layout.addWidget(QCheckBox("Enable"))

        sliders = [
            ("Speed", QSlider(Qt.Horizontal)),
            ("Base Error Rate", QSlider(Qt.Horizontal)),
            ("Bins", QSlider(Qt.Horizontal)),
        ]

        for label, widget in sliders:
            layout.addWidget(QLabel(label))
            layout.addWidget(widget)

        # Distractions combo
        layout.addWidget(QLabel("Distractions"))
        distCombo = QComboBox()
        distCombo.addItems(["None", "Low", "Medium", "High"])
        layout.addWidget(distCombo)

        return layout

    # --- Helper: Results Section (Task results) ---
    def create_result_section(self, title, er, thru, cor):
        layout = QVBoxLayout()
        layout.addWidget(QLabel(title))

        for label_text, value in [
            ("Error Rate (errors/min)", er),
            ("Throughput (items/min)", thru),
            ("Corrections (# of clicks)", cor),
        ]:
            layout.addWidget(QLabel(label_text))
            layout.addWidget(QLabel(str(value)))

        return layout

    # --- Helper: Participant Results ---
    def create_participant_results(self, avgCon, acc):
        layout = QVBoxLayout()
        layout.addWidget(QLabel("PARTICIPANT"))

        layout.addWidget(QLabel("Avg. Connection Time (s)"))
        layout.addWidget(QLabel(f"{avgCon}s"))

        layout.addWidget(QLabel("Accuracy (%)"))
        layout.addWidget(QLabel(f"{acc}%"))

        return layout


# --- Run the App ---
def main():
    app = QApplication(sys.argv)
    window = MainOCSWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
