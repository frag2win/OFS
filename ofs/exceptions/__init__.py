"""OFS Custom Exceptions.

This module defines custom exception classes for OFS operations.
All exceptions inherit from the base OFSError class.
"""


class OFSError(Exception):
    """Base exception for all OFS errors.
    
    All OFS-specific exceptions should inherit from this class.
    """
    pass


class RepositoryNotFoundError(OFSError):
    """Repository not initialized or not found.
    
    Raised when an operation requires an initialized repository
    but none exists at the specified path.
    """
    pass


class RepositoryExistsError(OFSError):
    """Repository already exists.
    
    Raised when trying to initialize a repository that already exists.
    """
    pass


class ObjectNotFoundError(OFSError):
    """Object not found in object store.
    
    Raised when attempting to retrieve an object by hash
    that doesn't exist in the store.
    """
    pass


class CorruptionError(OFSError):
    """Data corruption detected.
    
    Raised when verification fails due to hash mismatch
    or invalid data format.
    """
    pass


class CommitError(OFSError):
    """Commit operation failed.
    
    Raised when a commit cannot be created, such as
    when the staging area is empty.
    """
    pass


class CommitNotFoundError(OFSError):
    """Commit not found.
    
    Raised when attempting to load or reference a commit
    that doesn't exist.
    """
    pass


class IndexError(OFSError):
    """Index operation failed.
    
    Raised when reading or writing the staging index fails.
    """
    pass


class CheckoutError(OFSError):
    """Checkout operation failed.
    
    Raised when unable to restore working directory to a commit state.
    """
    pass


class FileTooLargeError(OFSError):
    """File exceeds size limit.
    
    Raised when attempting to add a file larger than the maximum
    allowed size (default: 100MB).
    """
    pass


class VerificationError(OFSError):
    """Repository verification failed.
    
    Raised when repository integrity checks detect problems.
    """
    pass
