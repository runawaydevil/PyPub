class PyPubError(Exception):
    """Base exception for PyPub domain errors."""
    pass

class IndieAuthError(PyPubError):
    """Raised when authentication fails."""
    pass

class DiscoveryError(PyPubError):
    """Raised when endpoint discovery fails."""
    pass

class MicropubError(PyPubError):
    """Raised when interacting with Micropub endpoint fails."""
    pass

class MediaUploadError(PyPubError):
    """Raised when uploading media fails."""
    pass
