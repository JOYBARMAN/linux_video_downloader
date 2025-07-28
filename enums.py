from enum import Enum


class DownloadType(Enum):
    AUDIO = "audio"
    VIDEO = "video"


class DownloadStatus(Enum):
    """Enum to represent download status."""

    NOT_STARTED = "Not Started Yet"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"
    FAILED = "Failed"
