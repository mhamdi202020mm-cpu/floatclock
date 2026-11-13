"""FloatClock entry point (single-instance)."""
import sys

from PySide6.QtNetwork import QLocalServer, QLocalSocket
from PySide6.QtWidgets import QApplication

SERVER_NAME = "FloatClock-single-instance-v1"


def main() -> int:
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("FloatClock.App")
        except Exception:
            pass

    app = QApplication(sys.argv)
    app.setApplicationName("FloatClock")
    app.setQuitOnLastWindowClosed(False)

    # Already running? -> ask the existing instance to show itself, then exit.
    sock = QLocalSocket()
    sock.connectToServer(SERVER_NAME)
    if sock.waitForConnected(300):
        sock.write(b"show")
        sock.flush()
        sock.waitForBytesWritten(300)
        sock.disconnectFromServer()
        return 0

    from core.alarm_manager import AlarmManager
    from core.settings import Settings
    from core.sound import SoundPlayer
    from ui.main_window import MainWindow
    from ui.theme import STYLE

    app.setStyleSheet(STYLE)
    settings = Settings()
    alarms = AlarmManager()
    sound = SoundPlayer()
    window = MainWindow(settings, alarms, sound)

    QLocalServer.removeServer(SERVER_NAME)  # clear a stale socket from a crash
    server = QLocalServer()
    server.listen(SERVER_NAME)

    def on_connection():
        conn = server.nextPendingConnection()
        if conn:
            conn.disconnected.connect(conn.deleteLater)
            window.show_and_raise()
            conn.disconnectFromServer()

    server.newConnection.connect(on_connection)

    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
