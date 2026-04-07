import warnings
from PySide6.QtWidgets import QApplication, QStyleFactory
from DAQ.AXIOM.MainPanel import MainPanel


# Suppress UserWarnings
warnings.filterwarnings("ignore", category=UserWarning)

if __name__ == '__main__':
    app = QApplication()
    app.setStyle(QStyleFactory.create('Fusion'))
    window = MainPanel()
    window.show()

    app.aboutToQuit.connect(
        window.cleanup_exit
        # window.stop_temperature_thread
        )

    try:
        app.exec()
    except BaseException as error:
        window.cleanup_exit()
        raise error
