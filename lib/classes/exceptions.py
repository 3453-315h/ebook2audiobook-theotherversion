#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Custom exception classes for ebook2audiobook project
Provides specific exception types for better error handling and debugging
"""

from typing import Any, Optional, Dict, List
import traceback
import logging
from enum import Enum

# Configure logging for exceptions
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('ebook2audiobook_exceptions.log')
    ]
)

class ErrorSeverity(Enum):
    """Enumeration for error severity levels"""
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4
    INFO = 5

class ErrorCategory(Enum):
    """Enumeration for error categories"""
    SYSTEM = "system"
    CONFIGURATION = "configuration"
    DEPENDENCY = "dependency"
    PROCESSING = "processing"
    VALIDATION = "validation"
    NETWORK = "network"
    MEMORY = "memory"
    FILE_OPERATION = "file_operation"
    TTS_ENGINE = "tts_engine"
    AUDIO_PROCESSING = "audio_processing"

class Ebook2AudiobookException(Exception):
    """
    Base exception class for all ebook2audiobook exceptions
    Provides standardized error handling and logging
    """

    def __init__(self, message: str, severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                 category: ErrorCategory = ErrorCategory.SYSTEM,
                 original_exception: Optional[Exception] = None,
                 context: Optional[Dict[str, Any]] = None):
        self.message = message
        self.severity = severity
        self.category = category
        self.original_exception = original_exception
        self.context = context or {}
        self.timestamp = None  # Will be set when logged

        # Build full error message
        full_message = self._build_error_message()
        super().__init__(full_message)

        # Log the exception immediately
        self._log_exception()

    def _build_error_message(self) -> str:
        """Build a comprehensive error message with context"""
        base_msg = f"[{self.severity.name}] {self.category.value.upper()}: {self.message}"

        if self.context:
            context_str = ", ".join(f"{k}={v}" for k, v in self.context.items())
            base_msg += f" | Context: {context_str}"

        if self.original_exception:
            base_msg += f" | Original: {type(self.original_exception).__name__}: {str(self.original_exception)}"

        return base_msg

    def _log_exception(self) -> None:
        """Log the exception with appropriate severity"""
        import datetime
        self.timestamp = datetime.datetime.now().isoformat()

        log_methods = {
            ErrorSeverity.CRITICAL: logging.critical,
            ErrorSeverity.HIGH: logging.error,
            ErrorSeverity.MEDIUM: logging.warning,
            ErrorSeverity.LOW: logging.info,
            ErrorSeverity.INFO: logging.info
        }

        log_method = log_methods.get(self.severity, logging.error)

        # Log the full error message
        log_method(self._build_error_message())

        # Log traceback if available
        if self.original_exception:
            traceback_str = "".join(traceback.format_exception(type(self.original_exception),
                                                               self.original_exception,
                                                               self.original_exception.__traceback__))
            logging.debug(f"Traceback for {self.category.value} error:\n{traceback_str}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for serialization"""
        return {
            'timestamp': self.timestamp,
            'message': self.message,
            'severity': self.severity.name,
            'category': self.category.value,
            'original_exception': str(self.original_exception) if self.original_exception else None,
            'context': self.context,
            'type': type(self).__name__
        }

    def __str__(self) -> str:
        return self._build_error_message()

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.message!r}, severity={self.severity!r}, category={self.category!r})"

class ConfigurationError(Ebook2AudiobookException):
    """Exception for configuration-related errors"""

    def __init__(self, message: str, severity: ErrorSeverity = ErrorSeverity.HIGH,
                 original_exception: Optional[Exception] = None, context: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            severity=severity,
            category=ErrorCategory.CONFIGURATION,
            original_exception=original_exception,
            context=context
        )

class DependencyError(Ebook2AudiobookException):
    """Exception for missing or incompatible dependencies"""

    def __init__(self, message: str, severity: ErrorSeverity = ErrorSeverity.CRITICAL,
                 original_exception: Optional[Exception] = None, context: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            severity=severity,
            category=ErrorCategory.DEPENDENCY,
            original_exception=original_exception,
            context=context
        )

class ProcessingError(Ebook2AudiobookException):
    """Exception for processing-related errors"""

    def __init__(self, message: str, severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                 original_exception: Optional[Exception] = None, context: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            severity=severity,
            category=ErrorCategory.PROCESSING,
            original_exception=original_exception,
            context=context
        )

class ValidationError(Ebook2AudiobookException):
    """Exception for validation failures"""

    def __init__(self, message: str, severity: ErrorSeverity = ErrorSeverity.LOW,
                 original_exception: Optional[Exception] = None, context: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            severity=severity,
            category=ErrorCategory.VALIDATION,
            original_exception=original_exception,
            context=context
        )

class NetworkError(Ebook2AudiobookException):
    """Exception for network-related errors"""

    def __init__(self, message: str, severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                 original_exception: Optional[Exception] = None, context: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            severity=severity,
            category=ErrorCategory.NETWORK,
            original_exception=original_exception,
            context=context
        )

class MemoryError(Ebook2AudiobookException):
    """Exception for memory-related errors"""

    def __init__(self, message: str, severity: ErrorSeverity = ErrorSeverity.HIGH,
                 original_exception: Optional[Exception] = None, context: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            severity=severity,
            category=ErrorCategory.MEMORY,
            original_exception=original_exception,
            context=context
        )

class FileOperationError(Ebook2AudiobookException):
    """Exception for file operation errors"""

    def __init__(self, message: str, severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                 original_exception: Optional[Exception] = None, context: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            severity=severity,
            category=ErrorCategory.FILE_OPERATION,
            original_exception=original_exception,
            context=context
        )

class TTSEngineError(Ebook2AudiobookException):
    """Exception for TTS engine-specific errors"""

    def __init__(self, message: str, engine_name: str, severity: ErrorSeverity = ErrorSeverity.HIGH,
                 original_exception: Optional[Exception] = None, context: Optional[Dict[str, Any]] = None):
        context = context or {}
        context['engine_name'] = engine_name
        super().__init__(
            message=message,
            severity=severity,
            category=ErrorCategory.TTS_ENGINE,
            original_exception=original_exception,
            context=context
        )

class AudioProcessingError(Ebook2AudiobookException):
    """Exception for audio processing errors"""

    def __init__(self, message: str, severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                 original_exception: Optional[Exception] = None, context: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            severity=severity,
            category=ErrorCategory.AUDIO_PROCESSING,
            original_exception=original_exception,
            context=context
        )

class ExceptionHandler:
    """
    Centralized exception handler for the application
    Provides methods to handle different types of exceptions consistently
    """

    @staticmethod
    def handle_exception(exception: Exception, context: Optional[Dict[str, Any]] = None) -> None:
        """
        Handle any exception and convert to appropriate custom exception if needed
        """
        context = context or {}

        if isinstance(exception, Ebook2AudiobookException):
            # Already a custom exception, just log it
            logging.error(f"Handled custom exception: {exception}")
            return

        # Convert common exceptions to custom ones
        exception_type = type(exception).__name__

        if exception_type in ('FileNotFoundError', 'PermissionError', 'IsADirectoryError'):
            FileOperationError(
                message=f"File operation failed: {str(exception)}",
                original_exception=exception,
                context=context
            )
        elif exception_type in ('MemoryError', 'OutOfMemoryError'):
            MemoryError(
                message=f"Memory error occurred: {str(exception)}",
                original_exception=exception,
                context=context
            )
        elif exception_type in ('ConnectionError', 'TimeoutError', 'HTTPError'):
            NetworkError(
                message=f"Network error occurred: {str(exception)}",
                original_exception=exception,
                context=context
            )
        elif exception_type in ('ValueError', 'TypeError', 'AttributeError'):
            ValidationError(
                message=f"Validation error: {str(exception)}",
                original_exception=exception,
                context=context
            )
        elif exception_type in ('ImportError', 'ModuleNotFoundError'):
            DependencyError(
                message=f"Dependency error: {str(exception)}",
                original_exception=exception,
                context=context
            )
        else:
            # Generic handling for other exceptions
            Ebook2AudiobookException(
                message=f"Unexpected error: {str(exception)}",
                severity=ErrorSeverity.HIGH,
                original_exception=exception,
                context=context
            )

    @staticmethod
    def wrap_function_call(func, *args, **kwargs) -> Any:
        """
        Wrapper to handle exceptions from function calls consistently
        """
        try:
            return func(*args, **kwargs)
        except Exception as e:
            ExceptionHandler.handle_exception(e, {'function': func.__name__, 'args': args, 'kwargs': kwargs})
            raise  # Re-raise after handling

    @staticmethod
    def get_exception_context(exception: Ebook2AudiobookException) -> Dict[str, Any]:
        """
        Extract context information from an exception
        """
        if not isinstance(exception, Ebook2AudiobookException):
            return {}

        return {
            'timestamp': exception.timestamp,
            'message': exception.message,
            'severity': exception.severity.name,
            'category': exception.category.value,
            'context': exception.context,
            'original_exception': str(exception.original_exception) if exception.original_exception else None
        }

def safe_execute(func, default_return=None, *args, **kwargs) -> Any:
    """
    Safe execution wrapper that catches exceptions and returns default value
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        ExceptionHandler.handle_exception(e, {'function': func.__name__})
        return default_return

def validate_and_execute(validator_func, main_func, *args, **kwargs) -> Any:
    """
    Execute a function only if validation passes
    """
    try:
        if validator_func(*args, **kwargs):
            return main_func(*args, **kwargs)
        else:
            raise ValidationError("Validation failed before execution")
    except Exception as e:
        ExceptionHandler.handle_exception(e)
        raise