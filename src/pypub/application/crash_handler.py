import sys
import traceback
import logging
from PySide6.QtWidgets import QMessageBox, QApplication

logger = logging.getLogger("pypub.crash_handler")

def global_exception_handler(exctype, value, tb):
    """
    Captura exceções globais (não tratadas) no Qt e Python thread principal.
    Evita que o programa capote no shell nativo do Windows sem aviso.
    """
    logger.critical("Uncaught Exception", exc_info=(exctype, value, tb))
    
    err_msg = "".join(traceback.format_exception(exctype, value, tb))
    
    if QApplication.instance():
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Critical)
        msg_box.setWindowTitle("PyPub - Fatal Error")
        msg_box.setText("An unexpected error occurred.")
        msg_box.setInformativeText(str(value))
        msg_box.setDetailedText(err_msg)
        msg_box.exec()
    
    sys.__excepthook__(exctype, value, tb)
