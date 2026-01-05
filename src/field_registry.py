from enum import Enum
from dataclasses import dataclass
from typing import Optional, Callable, Any


class FieldType(Enum):
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    IMAGEORVIDEO = "image_or_video"
    NUMERIC = "numeric"
    SONGPREVIEW = "songpreview"

    def displayName(self):
        display_names = {
            FieldType.TEXT: "Text",
            FieldType.IMAGE: "Image",
            FieldType.VIDEO: "Video",
            FieldType.AUDIO: "Audio",
            FieldType.IMAGEORVIDEO: "Image or Video",
            FieldType.NUMERIC: "Number",
            FieldType.SONGPREVIEW: "Song Preview"
        }
        return display_names[self] or str(self)
    
    def isFilePath(self):
        return self in [FieldType.IMAGE, FieldType.IMAGEORVIDEO, FieldType.AUDIO, FieldType.SONGPREVIEW]


class SimFileFormat(Enum):
    SM = "sm"   # StepMania .sm files
    SSC = "ssc"  # StepMania .ssc files
    # DWI = "dwi"  # DanceWith Intensity files


@dataclass
class FieldDefinition:
    internal_name: str  # Name in SimfileMetadata class (e.g., 'title')
    display_name: str   # Name shown to user (e.g., 'Title')
    
    field_type: FieldType
    
    supported_formats: set[SimFileFormat]
    
    description: Optional[str] = None  # Tooltip/help text
    placeholder: Optional[str] = None  # Placeholder text for empty fields
    validator: Optional[Callable[[Any], bool]] = None  # Validation function
    default_value: Any = ""
    
    def is_supported_for_format(self, format_type: SimFileFormat) -> bool:
        """Check if this field is supported for a given file format."""
        return format_type in self.supported_formats
    
    def is_supported_for_file(self, file_path: str) -> bool:
        """Check if this field is supported based on file extension."""
        ext = file_path.lower().split('.')[-1]
        
        format_map = {
            'sm': SimFileFormat.SM,
            'ssc': SimFileFormat.SSC,
            # 'dwi': FileFormat.DWI
        }
        
        file_format = format_map.get(ext)
        if not file_format:
            return False
        
        return self.is_supported_for_format(file_format)
    
    def validate(self, value: Any) -> bool:
        """Validate a value for this field."""
        if self.validator:
            return self.validator(value)
        return True

@dataclass
class FieldGroup:
    display_name: str
    fields: list[FieldDefinition]

class FieldRegistry:
    """
    Central registry of all editable fields.
    
    This is the SINGLE PLACE where fields are defined.
    Everything else queries this registry.
    """
    
    SSC_ONLY = {SimFileFormat.SSC}
    SM_AND_SSC = {SimFileFormat.SM, SimFileFormat.SSC}
    
    CHART_FIELDS = [
        FieldDefinition(
            internal_name='title',
            display_name='Title',
            field_type=FieldType.TEXT,
            supported_formats=SM_AND_SSC,
            description='Song title',
            placeholder='Enter song title'
        ),
        FieldDefinition(
            internal_name='subtitle',
            display_name='Subtitle',
            field_type=FieldType.TEXT,
            supported_formats=SM_AND_SSC,
            description='Song subtitle (optional)',
            placeholder='Enter subtitle (optional)'
        ),
        FieldDefinition(
            internal_name='artist',
            display_name='Artist',
            field_type=FieldType.TEXT,
            supported_formats=SM_AND_SSC,
            description='Song artist/composer',
            placeholder='Enter artist name'
        ),
        FieldDefinition(
            internal_name='genre',
            display_name='Genre',
            field_type=FieldType.TEXT,
            supported_formats=SM_AND_SSC,
            description='Music genre',
            placeholder='e.g. Rock, Pop, Electronic'
        ),
        FieldDefinition(
            internal_name='origin',
            display_name='Origin',
            field_type=FieldType.TEXT,
            supported_formats=SSC_ONLY,
            description='Song origin',
            placeholder='e.g. IIDX, Sound Voltex...'
        ),
        FieldDefinition(
            internal_name='credit',
            display_name='Credit',
            field_type=FieldType.TEXT,
            supported_formats=SM_AND_SSC,
            description='Chart author/stepper credit',
            placeholder='Chart created by...'
        ),
        
        # Transliteration fields
        FieldDefinition(
            internal_name='titletranslit',
            display_name='Title (Romanized)',
            field_type=FieldType.TEXT,
            supported_formats=SM_AND_SSC,
            description='transliterated title',
            placeholder='Romanized title'
        ),
        FieldDefinition(
            internal_name='subtitletranslit',
            display_name='Subtitle (Romanized)',
            field_type=FieldType.TEXT,
            supported_formats=SM_AND_SSC,
            description='transliterated subtitle',
            placeholder='Romanized subtitle'
        ),
        FieldDefinition(
            internal_name='artisttranslit',
            display_name='Artist (Romanized)',
            field_type=FieldType.TEXT,
            supported_formats=SM_AND_SSC,
            description='transliterated artist name',
            placeholder='Romanized artist'
        ),
    ]

    IMAGE_FIELDS = [
        FieldDefinition(
            internal_name='banner',
            display_name='Banner',
            field_type=FieldType.IMAGEORVIDEO,
            supported_formats=SM_AND_SSC,
            description='Banner image (long horizontal image)'
        ),
        FieldDefinition(
            internal_name='background',
            display_name='Background',
            field_type=FieldType.IMAGE,
            supported_formats=SM_AND_SSC,
            description='Background image shown during gameplay'
        ),
        FieldDefinition(
            internal_name='cdtitle',
            display_name='CD Title',
            field_type=FieldType.IMAGE,
            supported_formats=SM_AND_SSC,
            description='Small CD title graphic'
        ),
        FieldDefinition(
            internal_name='jacket',
            display_name='Jacket',
            field_type=FieldType.IMAGE,
            supported_formats=SSC_ONLY,
            description='Album jacket/cover art'
        ),
    ]

    AUDIO_FIELDS = [
        FieldDefinition(
            internal_name='samplestart',
            display_name='Sample Start',
            field_type=FieldType.NUMERIC,
            supported_formats=SM_AND_SSC,
            description='Sample Start (seconds)'
        ),
        FieldDefinition(
            internal_name='samplelength',
            display_name='Sample Length',
            field_type=FieldType.NUMERIC,
            supported_formats=SM_AND_SSC,
            description='Sample Length (seconds)'
        ),
        FieldDefinition(
            internal_name='music',
            display_name='Music',
            field_type=FieldType.SONGPREVIEW,
            supported_formats=SM_AND_SSC,
            description='Song Name'
        ),
    ]

    ALL_FIELDS = CHART_FIELDS + IMAGE_FIELDS + AUDIO_FIELDS

    FIELD_GROUPS: list[FieldGroup] = [
        FieldGroup(display_name="Simfile Details", fields=CHART_FIELDS),
        FieldGroup(display_name="Images and Videos", fields=IMAGE_FIELDS),
        FieldGroup(display_name="Song Preview", fields=AUDIO_FIELDS)
    ]
    
    # Build lookup dictionaries for fast access
    _by_internal_name = {field.internal_name: field for field in ALL_FIELDS}
    _by_display_name = {field.display_name: field for field in ALL_FIELDS}
    
    @classmethod
    def get_field(cls, internal_name: str) -> Optional[FieldDefinition]:
        """Get field definition by internal name."""
        return cls._by_internal_name.get(internal_name)
    
    @classmethod
    def get_field_by_display_name(cls, display_name: str) -> Optional[FieldDefinition]:
        """Get field definition by display name."""
        return cls._by_display_name.get(display_name)
    
    @classmethod
    def get_all_fields(cls) -> list[FieldDefinition]:
        """Get all field definitions."""
        return cls.ALL_FIELDS.copy()
    
    @classmethod
    def get_fields_for_field_type(cls, field_type: FieldType):
        return [f for f in cls.ALL_FIELDS if f.field_type == field_type]
    
    @classmethod
    def get_fields_for_format(cls, format_type: SimFileFormat) -> list[FieldDefinition]:
        """Get all fields supported by a given format."""
        return [f for f in cls.ALL_FIELDS if f.is_supported_for_format(format_type)]
    
    @classmethod
    def get_fields_for_file(cls, file_path: str) -> list[FieldDefinition]:
        """Get all fields supported by a file based on its extension."""
        return [f for f in cls.ALL_FIELDS if f.is_supported_for_file(file_path)]
    
    @classmethod
    def get_internal_names(cls) -> list[str]:
        """Get list of all internal field names."""
        return [f.internal_name for f in cls.ALL_FIELDS]
    
    @classmethod
    def get_text_field_names(cls) -> list[str]:
        """Get list of text field internal names."""
        return [f.internal_name for f in cls.get_fields_for_field_type(FieldType.TEXT)]
    
    @classmethod
    def get_image_field_names(cls) -> list[str]:
        """Get list of image field internal names."""
        return [f.internal_name for f in cls.get_fields_for_field_type(FieldType.IMAGE)]
    
    @classmethod
    def is_field_editable(cls, internal_name: str, file_path: str) -> bool:
        """
        Check if a field is editable for a given file.
        
        Args:
            internal_name: The internal field name
            file_path: Path to the simfile
            
        Returns:
            True if the field can be edited for this file format
        """
        field = cls.get_field(internal_name)
        if not field:
            return False
        
        return field.is_supported_for_file(file_path)
