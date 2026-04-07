from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QSizePolicy, QGroupBox, QSpinBox, QGridLayout, QCheckBox
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

def add_label_to_input(input_field: QWidget, label: str) -> QWidget:
    label_layout = QVBoxLayout()
    label_widget = QLabel(label)
    label_font = QFont()
    label_font.setPointSize(8)
    label_font.setBold(True)
    label_widget.setFont(label_font)
    label_layout.addWidget(label_widget)
    label_layout.setAlignment(label_widget, Qt.AlignmentFlag.AlignHCenter)
    label_layout.addWidget(input_field)
    label_layout.setAlignment(input_field, Qt.AlignmentFlag.AlignHCenter)
    label_layout.setSpacing(8)
    label_layout.setContentsMargins(0, 0, 0, 0)

    combo_widget = QWidget()
    combo_widget.setContentsMargins(0, 0, 0, 0)
    combo_widget.setLayout(label_layout)
    combo_widget.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

    return combo_widget
