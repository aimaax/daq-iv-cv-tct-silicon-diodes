from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QCheckBox, QDialogButtonBox
)

class CloseEventDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Exit Confirmation")
        self.setMinimumWidth(350)

        layout = QVBoxLayout()
        layout.addWidget(QLabel("<b>Are you sure you want to close the application?</b>"))

        self.copy_checkbox = QCheckBox("Copy/Sync all csv files to Particulars Analysis Git Repo")
        self.overwrite_checkbox = QCheckBox("Overwrite current files (takes longer time)")
        layout.addWidget(self.copy_checkbox)
        layout.addWidget(self.overwrite_checkbox)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Yes | QDialogButtonBox.StandardButton.No)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)