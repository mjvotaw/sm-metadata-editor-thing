from PyQt6.QtCore import QObject, QEvent


class IgnoreWheelFilter(QObject):
    
    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.Wheel:
            if not obj.hasFocus():
                event.ignore()
                return True  # Event handled - ignore
        return super().eventFilter(obj, event)