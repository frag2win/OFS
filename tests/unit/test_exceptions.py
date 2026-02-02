"""Tests for custom exception classes."""

import pytest
from ofs.exceptions import (
    OFSError,
    RepositoryNotFoundError,
    RepositoryExistsError,
    ObjectNotFoundError,
    CorruptionError,
    CommitError,
    CommitNotFoundError,
    IndexError,
    CheckoutError,
    FileTooLargeError,
    VerificationError,
)


class TestOFSError:
    """Tests for base OFSError exception."""
    
    def test_ofs_error_is_exception(self):
        """OFSError should inherit from Exception."""
        assert issubclass(OFSError, Exception)
    
    def test_ofs_error_can_be_raised(self):
        """OFSError can be raised and caught."""
        with pytest.raises(OFSError):
            raise OFSError("Test error")
    
    def test_ofs_error_message(self):
        """OFSError stores message correctly."""
        error = OFSError("Custom message")
        assert str(error) == "Custom message"


class TestRepositoryErrors:
    """Tests for repository-related exceptions."""
    
    def test_repository_not_found_error_inheritance(self):
        """RepositoryNotFoundError should inherit from OFSError."""
        assert issubclass(RepositoryNotFoundError, OFSError)
    
    def test_repository_not_found_error(self):
        """RepositoryNotFoundError with path."""
        error = RepositoryNotFoundError("Repository not found at /some/path")
        assert "/some/path" in str(error)
    
    def test_repository_exists_error_inheritance(self):
        """RepositoryExistsError should inherit from OFSError."""
        assert issubclass(RepositoryExistsError, OFSError)
    
    def test_repository_exists_error(self):
        """RepositoryExistsError with path."""
        error = RepositoryExistsError("Repository already exists at /existing/path")
        assert "/existing/path" in str(error)


class TestObjectErrors:
    """Tests for object-related exceptions."""
    
    def test_object_not_found_error_inheritance(self):
        """ObjectNotFoundError should inherit from OFSError."""
        assert issubclass(ObjectNotFoundError, OFSError)
    
    def test_object_not_found_error(self):
        """ObjectNotFoundError with hash."""
        error = ObjectNotFoundError("Object not found: abc123def456")
        assert "abc123def456" in str(error)
    
    def test_corruption_error_inheritance(self):
        """CorruptionError should inherit from OFSError."""
        assert issubclass(CorruptionError, OFSError)
    
    def test_corruption_error(self):
        """CorruptionError with details."""
        error = CorruptionError("Hash mismatch detected")
        assert "Hash mismatch" in str(error)


class TestIndexErrors:
    """Tests for index-related exceptions."""
    
    def test_index_error_inheritance(self):
        """IndexError should inherit from OFSError."""
        assert issubclass(IndexError, OFSError)
    
    def test_index_error(self):
        """IndexError with details."""
        error = IndexError("Invalid JSON in index file")
        assert "Invalid JSON" in str(error)


class TestCommitErrors:
    """Tests for commit-related exceptions."""
    
    def test_commit_error_inheritance(self):
        """CommitError should inherit from OFSError."""
        assert issubclass(CommitError, OFSError)
    
    def test_commit_error(self):
        """CommitError with details."""
        error = CommitError("Nothing to commit")
        assert "Nothing to commit" in str(error)
    
    def test_commit_not_found_error_inheritance(self):
        """CommitNotFoundError should inherit from OFSError."""
        assert issubclass(CommitNotFoundError, OFSError)
    
    def test_commit_not_found_error(self):
        """CommitNotFoundError with commit ID."""
        error = CommitNotFoundError("Commit 003 not found")
        assert "003" in str(error)


class TestCheckoutError:
    """Tests for checkout exceptions."""
    
    def test_checkout_error_inheritance(self):
        """CheckoutError should inherit from OFSError."""
        assert issubclass(CheckoutError, OFSError)
    
    def test_checkout_error(self):
        """CheckoutError with details."""
        error = CheckoutError("Failed to restore working directory")
        assert "Failed to restore" in str(error)


class TestFileSizeError:
    """Tests for file size exceptions."""
    
    def test_file_too_large_error_inheritance(self):
        """FileTooLargeError should inherit from OFSError."""
        assert issubclass(FileTooLargeError, OFSError)
    
    def test_file_too_large_error(self):
        """FileTooLargeError with details."""
        error = FileTooLargeError("File exceeds 100MB limit")
        assert "100MB" in str(error)


class TestVerificationError:
    """Tests for verification exceptions."""
    
    def test_verification_error_inheritance(self):
        """VerificationError should inherit from OFSError."""
        assert issubclass(VerificationError, OFSError)
    
    def test_verification_error(self):
        """VerificationError with details."""
        error = VerificationError("Repository integrity check failed")
        assert "integrity check failed" in str(error)


class TestExceptionHandling:
    """Tests for exception handling patterns."""
    
    def test_catch_by_base_class(self):
        """All OFS exceptions can be caught by OFSError."""
        exceptions = [
            RepositoryNotFoundError("test"),
            RepositoryExistsError("test"),
            ObjectNotFoundError("test"),
            CorruptionError("test"),
            CommitError("test"),
            CommitNotFoundError("test"),
            IndexError("test"),
            CheckoutError("test"),
            FileTooLargeError("test"),
            VerificationError("test"),
        ]
        
        for exc in exceptions:
            with pytest.raises(OFSError):
                raise exc
    
    def test_exceptions_are_distinct(self):
        """Each exception type is distinct and can be caught specifically."""
        with pytest.raises(RepositoryNotFoundError):
            raise RepositoryNotFoundError("test")
        
        with pytest.raises(ObjectNotFoundError):
            raise ObjectNotFoundError("test")
        
        with pytest.raises(CommitNotFoundError):
            raise CommitNotFoundError("test")
