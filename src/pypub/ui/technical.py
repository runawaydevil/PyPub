from PySide6.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QLabel

class TechnicalWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("<h2>Technical Inspection</h2>"))
        
        self.output = QTextEdit()
        self.output.setReadOnly(True)
        layout.addWidget(self.output)

    def log(self, message: str):
        self.output.append(message)
