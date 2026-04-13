from PySide6.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QLabel

class TechnicalWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("PageSurface")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        title = QLabel("Technical")
        title.setObjectName("PageHeroTitle")
        subtitle = QLabel("Diagnostics, capability checks, and runtime details for troubleshooting.")
        subtitle.setObjectName("PageHeroSubtitle")
        subtitle.setWordWrap(True)
        layout.addWidget(title)
        layout.addWidget(subtitle)
        
        self.output = QTextEdit()
        self.output.setObjectName("TechnicalLog")
        self.output.setReadOnly(True)
        layout.addWidget(self.output)

    def log(self, message: str):
        self.output.append(message)
