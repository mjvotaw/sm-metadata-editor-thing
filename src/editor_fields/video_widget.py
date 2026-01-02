from PyQt6.QtCore import Qt, QUrl, pyqtSignal
from PyQt6.QtWidgets import QWidget, QLabel, QHBoxLayout, QVBoxLayout, QPushButton, QSizePolicy
from PyQt6.QtMultimedia import QMediaPlayer, QMediaMetaData
from PyQt6.QtMultimediaWidgets import QVideoWidget
import os
from typing import Optional

class VideoWidget(QWidget):
    
    dimensionsChanged = pyqtSignal(int, int) # width, height

    def __init__(self, parent=None):
        super().__init__(parent)
        self.filepath: Optional[str] = None
        self.is_playing: bool = False
        self.video_duration = 0
        self.video_height = None
        self.video_width = None

        self.setup_ui()
        self.setMouseTracking(True)
    
    def setup_ui(self):
        """Set up the video player UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.video_container = QWidget()
        self.video_container.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )
        
        container_layout = QVBoxLayout(self.video_container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        
        # Video widget
        self.video_widget = QVideoWidget()
        self.video_widget.setAspectRatioMode(Qt.AspectRatioMode.KeepAspectRatio)

        self.video_widget.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )
        container_layout.addWidget(self.video_widget)
        
        controls_layout = QHBoxLayout()
        # Play button overlay
        self.play_button = QPushButton("▶")
        self.play_button.setFixedSize(40, 40)
        self.play_button.clicked.connect(self._toggle_playback)
        
        self.time_label = QLabel("--:--/--:--")
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        controls_layout.addWidget(self.play_button)
        controls_layout.addWidget(self.time_label, 1)

        layout.addWidget(self.video_container, 1)
        layout.addLayout(controls_layout)

        self.media_player = QMediaPlayer()
        self.media_player.setVideoOutput(self.video_widget)
        
        self.media_player.playbackStateChanged.connect(self._on_playback_state_changed)
        self.media_player.durationChanged.connect(self._on_duration_changed)
        self.media_player.positionChanged.connect(self._on_position_changed)
        self.media_player.metaDataChanged.connect(self._on_metadata_changed)

        self.media_player.setLoops(573)
        self.setLayout(layout)
    
    
    def load_video(self, filepath: str) -> bool:
        """
        Load a video file.
        Returns True if successful, False otherwise.
        """
        if not filepath or not os.path.exists(filepath):
            return False
        
        self.filepath = filepath
        self.media_player.setSource(QUrl.fromLocalFile(filepath))
        # self.media_player.setPosition(0)
        
        return True
    
    def clear(self):
        """Clear the video and reset state."""
        self.media_player.stop()
        self.media_player.setSource(QUrl())
        self.filepath = None
        self.is_playing = False
        self.video_width = None
        self.video_height = None
        self.video_duration = 0
        self.play_button.setText("▶")
    
    def _toggle_playback(self):
        """Toggle between play and pause."""
        if self.is_playing:
            self.media_player.pause()
        else:
            self.media_player.setPosition(0)
            self.media_player.play()
    
    def _on_playback_state_changed(self, state):
        """Update UI based on playback state."""
        from PyQt6.QtMultimedia import QMediaPlayer
        
        if state == QMediaPlayer.PlaybackState.PlayingState:
            self.is_playing = True
            self.play_button.setText("⏸")
        else:
            self.is_playing = False
            self.play_button.setText("▶")    
    
    def _on_duration_changed(self, duration_ms):
        self.video_duration = duration_ms / 1000
        self.update_time_display(self.media_player.position())

    def _on_position_changed(self, position_ms):
        position = position_ms / 1000
        self.update_time_display(position)
        pass

    def _on_metadata_changed(self):
        resolution = self.media_player.metaData().value(QMediaMetaData.Key.Resolution)
        
        if resolution:
            self.video_width = resolution.width()
            self.video_height = resolution.height()
            self.dimensionsChanged.emit(self.video_width, self.video_height)


    def update_time_display(self, current_seconds: float):
        current_mins = int(current_seconds // 60)
        current_secs = int(current_seconds % 60)
        
        duration_mins = int(self.video_duration // 60)
        duration_secs = int(self.video_duration % 60)
        
        time_str = f"{current_mins:02d}:{current_secs:02d}/{duration_mins:02d}:{duration_secs:02d}"
        self.time_label.setText(time_str)

    def hasHeightForWidth(self) -> bool:
        return self.video_width is not None
    
    def heightForWidth(self, width: int) -> int:
        if self.video_width is not None and self.video_height is not None:
            return int(width * (self.video_height / self.video_width))
        return 0