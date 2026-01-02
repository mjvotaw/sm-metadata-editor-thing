# audio_preview.py
from PyQt6.QtCore import Qt, QUrl, QTimer
from PyQt6.QtWidgets import QWidget, QLabel, QHBoxLayout, QVBoxLayout, QPushButton, QSizePolicy, QSlider
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from pathlib import Path
from typing import Optional
from .base_field_widget import BaseFieldWidget
from src.field_registry import FieldDefinition

class AudioPreviewWidget(BaseFieldWidget):

    FADE_OUT_DURATION_MS = 500  # Adjust this to match ITGmania
    
    def __init__(self, field: FieldDefinition, *args, **kwargs):
        self.audio_filepath: Optional[str] = None
        self.sample_start_seconds: float = 0.0
        self.sample_length_seconds: float = 15.0  # Default preview length
        
        # Playback state
        self.is_playing = False
        self.is_fading = False
        self.volume = 0.5
        
        # Setup audio player
        self.audio_output = QAudioOutput()
        self.media_player = QMediaPlayer()
        self.media_player.setAudioOutput(self.audio_output)

        super().__init__(field, *args, **kwargs)
        # Timers
        self.position_timer = QTimer(self)
        self.fade_timer = QTimer(self)

        self.connect_signals()
        self.show_placeholder()
    
    def setup_ui(self, field_def: FieldDefinition):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        controls_layout = QHBoxLayout()
        self.label = QLabel(field_def.display_name + ":")

        self.play_button = QPushButton("▶")  # Play symbol
        self.play_button.setFixedSize(40, 40)
        self.play_button.setEnabled(False)
        
        # Time label
        self.time_label = QLabel("--:--/--:--")
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        controls_layout.addWidget(self.play_button)
        controls_layout.addWidget(self.time_label, 1)
        
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setSingleStep(1)
        self.volume_slider.setValue(50)

        layout.addWidget(self.label)
        layout.addLayout(controls_layout)
        layout.addWidget(self.volume_slider, 0, alignment=Qt.AlignmentFlag.AlignRight)
        self.setLayout(layout)
    

    def connect_signals(self):
        self.play_button.clicked.connect(self.toggle_playback)
        
        self.media_player.positionChanged.connect(self.on_position_changed)
        self.media_player.playbackStateChanged.connect(self.on_playback_state_changed)
        self.media_player.errorOccurred.connect(self.on_error)
        
        self.position_timer.timeout.connect(self.check_position)
        self.fade_timer.timeout.connect(self.update_fade)

        self.volume_slider.valueChanged.connect(self.update_volume)
    

    def update_time_display(self, current_seconds: float):
        """
        Update the time label with current position.
        
        Args:
            current_seconds: Current position relative to sample start
        """
        # Format current time
        current_mins = int(current_seconds // 60)
        current_secs = int(current_seconds % 60)
        
        # Format duration
        duration_mins = int(self.sample_length_seconds // 60)
        duration_secs = int(self.sample_length_seconds % 60)
        
        time_str = f"{current_mins:02d}:{current_secs:02d}/{duration_mins:02d}:{duration_secs:02d}"
        self.time_label.setText(time_str)
    
    def on_position_changed(self, position_ms):
        """Handle media player position changes (for UI updates)."""
        # The check_position method already handles time display
        pass
    
    def on_playback_state_changed(self, state):
        """Handle playback state changes."""
        if state == QMediaPlayer.PlaybackState.StoppedState:
            self.play_button.setText("▶")
            self.position_timer.stop()
            self.fade_timer.stop()
    
    def on_error(self, error, error_string):
        """Handle media player errors."""
        print(f"Audio playback error: {error_string}")
        self.show_placeholder()
        self.time_label.setText("Playback error")
    
    def clear(self):
        """Clear current audio and show placeholder."""
        self.stop()
        self.audio_filepath = None
        self.show_placeholder()


    def show_placeholder(self):
        """Show placeholder state when no audio loaded."""
        self.play_button.setEnabled(False)
        self.play_button.setText("▶")
        self.time_label.setText("--:--/--:--")
        self.time_label.setStyleSheet("color: #666666; font-style: italic;")
    
    def set_value(self, filepath: str, sample_start: float = 0.0, sample_length: float = 15.0):
        """
        Load an audio file and set the sample parameters.
        
        Args:
            filepath: Path to the audio file
            sample_start: Start time in seconds for the sample
            sample_length: Duration in seconds of the sample
        """
        if not filepath:
            self.show_placeholder()
            return
        
        # Resolve absolute path
        filepath = str(Path(filepath).resolve())
        
        # Check if file exists
        if not Path(filepath).exists():
            self.show_placeholder()
            self.time_label.setText("File not found")
            return
        
        # Store parameters
        self.audio_filepath = filepath
        self.sample_start_seconds = sample_start
        self.sample_length_seconds = sample_length
        
        # Load media
        media_url = QUrl.fromLocalFile(filepath)
        self.media_player.setSource(media_url)
        
        # Enable controls
        self.play_button.setEnabled(True)
        self.time_label.setStyleSheet("")
        
        # Update time display
        self.update_time_display(0)
    
    def toggle_playback(self):
        """Toggle between play and pause."""
        if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.pause()
        else:
            self.play()
    
    def play(self):
        """Start playback from sample start position."""
        if not self.audio_filepath:
            return
        
        start_ms = int(self.sample_start_seconds * 1000)
        self.media_player.setPosition(start_ms)
        self.audio_output.setVolume(self.volume)
        self.is_fading = False
        self.media_player.play()
        self.position_timer.start(50)
        self.play_button.setText("⏸")
    
    def pause(self):
        """Pause playback."""
        self.media_player.pause()
        self.position_timer.stop()
        self.fade_timer.stop()
        self.is_fading = False
        self.play_button.setText("▶")
    
    def stop(self):
        """Stop playback completely."""
        self.media_player.stop()
        self.position_timer.stop()
        self.fade_timer.stop()
        self.is_fading = False
        self.audio_output.setVolume(self.volume)
        self.play_button.setText("▶")
        self.update_time_display(0)

    def update_volume(self, volume: int):

        self.volume = volume * 0.01
        if self.is_fading:
            self.update_fade()
        else:
            self.audio_output.setVolume(self.volume)

    def check_position(self):
        """
        Check current playback position and handle looping.
        Called regularly by position_timer.
        """
        current_pos_ms = self.media_player.position()
        current_pos_seconds = current_pos_ms / 1000.0
        
        # Calculate sample end position
        sample_end_seconds = self.sample_start_seconds + self.sample_length_seconds
        
        # Calculate fade start position (FADE_OUT_DURATION_MS before end)
        fade_start_seconds = sample_end_seconds - (self.FADE_OUT_DURATION_MS / 1000.0)
        
        # Check if we should start fading
        if current_pos_seconds >= fade_start_seconds and not self.is_fading:
            self.start_fade_out()
        
        # Check if we've reached the end (loop point)
        if current_pos_seconds >= sample_end_seconds:
            self.loop_sample()
        
        # Update time display
        relative_time = current_pos_seconds - self.sample_start_seconds
        self.update_time_display(relative_time)
    
    def loop_sample(self):
        """Loop back to the start of the sample."""
        # Seek back to sample start
        start_ms = int(self.sample_start_seconds * 1000)
        self.media_player.setPosition(start_ms)
        
        # Reset fade state and volume
        self.is_fading = False
        self.fade_timer.stop()
        self.audio_output.setVolume(self.volume)

    
    def start_fade_out(self):
        """Begin fading out the audio volume."""
        if self.is_fading:
            return
        
        self.is_fading = True
        self.fade_start_time = self.media_player.position()
        
        # Start fade timer (update every 20ms for smooth fade)
        self.fade_timer.start(20)
    
    def update_fade(self):
        """
        Update volume during fade-out.
        Uses linear fade from current volume to 0.
        """
        if not self.is_fading:
            return
        
        # Calculate fade progress (0.0 to 1.0)
        current_time = self.media_player.position()
        elapsed_ms = current_time - self.fade_start_time
        progress = min(1.0, elapsed_ms / self.FADE_OUT_DURATION_MS)
        
        # Calculate new volume (linear fade)
        new_volume = self.volume * (1.0 - progress)
        self.audio_output.setVolume(max(0.0, new_volume))