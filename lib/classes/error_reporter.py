#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Centralized Error Reporting System for ebook2audiobook
Provides standardized error reporting, logging, and user feedback
"""

import os
import json
import logging
import traceback
import datetime
import platform
import socket
import uuid
from typing import Any, Dict, List, Optional, Union, Callable
from enum import Enum
from pathlib import Path

# Import custom exceptions
from lib.classes.exceptions import (
    Ebook2AudiobookException, ErrorSeverity, ErrorCategory,
    ConfigurationError, DependencyError, ProcessingError,
    ValidationError, NetworkError, MemoryError,
    FileOperationError, TTSEngineError, AudioProcessingError
)

class ReportFormat(Enum):
    """Enumeration for report formats"""
    JSON = "json"
    TEXT = "text"
    MARKDOWN = "markdown"
    HTML = "html"
    CONSOLE = "console"

class ReportDestination(Enum):
    """Enumeration for report destinations"""
    CONSOLE = "console"
    FILE = "file"
    GUI = "gui"
    API = "api"
    ALL = "all"

class ErrorReport:
    """
    Standardized error report structure
    """

    def __init__(self, exception: Ebook2AudiobookException, context: Optional[Dict[str, Any]] = None):
        self.exception = exception
        self.context = context or {}
        self.report_id = str(uuid.uuid4())
        self.timestamp = datetime.datetime.now().isoformat()
        self.system_info = self._collect_system_info()

    def _collect_system_info(self) -> Dict[str, Any]:
        """Collect system information for error context"""
        return {
            'platform': platform.system(),
            'platform_version': platform.version(),
            'python_version': platform.python_version(),
            'hostname': socket.gethostname(),
            'timestamp': self.timestamp,
            'report_id': self.report_id
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert error report to dictionary"""
        report = {
            'report_id': self.report_id,
            'timestamp': self.timestamp,
            'exception': self.exception.to_dict(),
            'context': self.context,
            'system_info': self.system_info,
            'type': 'error_report'
        }
        return report

    def to_json(self, indent: int = 2) -> str:
        """Convert error report to JSON string"""
        return json.dumps(self.to_dict(), indent=indent)

    def to_text(self) -> str:
        """Convert error report to formatted text"""
        lines = [
            f"=== ERROR REPORT {self.report_id} ===",
            f"Timestamp: {self.timestamp}",
            f"Severity: {self.exception.severity.name}",
            f"Category: {self.exception.category.value}",
            f"Message: {self.exception.message}",
            f"System: {self.system_info['platform']} {self.system_info['platform_version']}",
            f"Python: {self.system_info['python_version']}",
            f"Host: {self.system_info['hostname']}",
            "=== CONTEXT ===",
        ]

        for key, value in self.context.items():
            lines.append(f"{key}: {value}")

        if self.exception.original_exception:
            lines.extend([
                "=== ORIGINAL EXCEPTION ===",
                f"Type: {type(self.exception.original_exception).__name__}",
                f"Message: {str(self.exception.original_exception)}"
            ])

        return "\n".join(lines)

    def to_markdown(self) -> str:
        """Convert error report to Markdown format"""
        md_lines = [
            f"# Error Report: {self.report_id}",
            f"**Timestamp:** `{self.timestamp}`",
            f"**Severity:** `{self.exception.severity.name}`",
            f"**Category:** `{self.exception.category.value}`",
            f"**Message:** {self.exception.message}",
            "",
            "## System Information",
            f"- **Platform:** {self.system_info['platform']} {self.system_info['platform_version']}",
            f"- **Python:** {self.system_info['python_version']}",
            f"- **Host:** {self.system_info['hostname']}",
            "",
            "## Context"
        ]

        for key, value in self.context.items():
            md_lines.append(f"- **{key}:** {value}")

        if self.exception.original_exception:
            md_lines.extend([
                "",
                "## Original Exception",
                f"- **Type:** {type(self.exception.original_exception).__name__}",
                f"- **Message:** {str(self.exception.original_exception)}"
            ])

        return "\n".join(md_lines)

    def to_html(self) -> str:
        """Convert error report to HTML format"""
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Error Report: {self.report_id}</title>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; padding: 20px; color: #333; }}
        .error-header {{ background-color: #f8d7da; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
        .error-title {{ color: #721c24; font-size: 1.5em; }}
        .section {{ margin: 20px 0; }}
        .section-title {{ font-weight: bold; color: #495057; border-bottom: 1px solid #dee2e6; padding-bottom: 5px; }}
        .context-item {{ margin: 5px 0; }}
        .severity-critical {{ color: #721c24; background-color: #f8d7da; padding: 2px 8px; border-radius: 3px; }}
        .severity-high {{ color: #856404; background-color: #fff3cd; padding: 2px 8px; border-radius: 3px; }}
        .severity-medium {{ color: #842029; background-color: #f8d7da; padding: 2px 8px; border-radius: 3px; }}
        .severity-low {{ color: #0c5460; background-color: #d1ecf1; padding: 2px 8px; border-radius: 3px; }}
    </style>
</head>
<body>
    <div class="error-header">
        <div class="error-title">Error Report: {self.report_id}</div>
        <div>Timestamp: {self.timestamp}</div>
    </div>

    <div class="section">
        <div class="section-title">Error Details</div>
        <div><strong>Severity:</strong> <span class="severity-{self.exception.severity.name.lower()}">{self.exception.severity.name}</span></div>
        <div><strong>Category:</strong> {self.exception.category.value}</div>
        <div><strong>Message:</strong> {self.exception.message}</div>
    </div>

    <div class="section">
        <div class="section-title">System Information</div>
        <div><strong>Platform:</strong> {self.system_info['platform']} {self.system_info['platform_version']}</div>
        <div><strong>Python:</strong> {self.system_info['python_version']}</div>
        <div><strong>Host:</strong> {self.system_info['hostname']}</div>
    </div>

    <div class="section">
        <div class="section-title">Context Information</div>
        {''.join(f'<div class="context-item"><strong>{key}:</strong> {value}</div>' for key, value in self.context.items())}
    </div>
"""
        if self.exception.original_exception:
            html += f"""
    <div class="section">
        <div class="section-title">Original Exception</div>
        <div><strong>Type:</strong> {type(self.exception.original_exception).__name__}</div>
        <div><strong>Message:</strong> {str(self.exception.original_exception)}</div>
    </div>
"""

        html += """
</body>
</html>
"""
        return html

class ErrorReporter:
    """
    Centralized error reporter for the application
    Handles standardized error reporting across different destinations
    """

    def __init__(self, app_name: str = "ebook2audiobook"):
        self.app_name = app_name
        self.error_log_dir = os.path.join("logs", "errors")
        self.report_log_dir = os.path.join("logs", "reports")
        self._ensure_log_dirs_exist()

        # Configure logging
        self._configure_logging()

        # Error statistics
        self.error_stats = {
            'total_errors': 0,
            'by_severity': {severity.name: 0 for severity in ErrorSeverity},
            'by_category': {category.value: 0 for category in ErrorCategory},
            'recent_errors': []
        }

    def _ensure_log_dirs_exist(self) -> None:
        """Ensure log directories exist"""
        try:
            os.makedirs(self.error_log_dir, exist_ok=True)
            os.makedirs(self.report_log_dir, exist_ok=True)
        except Exception as e:
            print(f"Warning: Could not create log directories: {e}")

    def _configure_logging(self) -> None:
        """Configure logging for error reporting"""
        # Create logs directory if it doesn't exist
        logs_dir = "logs"
        os.makedirs(logs_dir, exist_ok=True)

        # Configure file handlers
        error_log_path = os.path.join(self.error_log_dir, "errors.log")
        report_log_path = os.path.join(self.report_log_dir, "reports.log")

        # Set up logging configuration
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(message)s",
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler(error_log_path),
                logging.FileHandler(report_log_path)
            ]
        )

    def report_error(self, exception: Union[Ebook2AudiobookException, Exception],
                    context: Optional[Dict[str, Any]] = None,
                    destinations: List[ReportDestination] = None) -> ErrorReport:
        """
        Report an error through standardized channels
        """
        # Convert standard exceptions to custom ones if needed
        if not isinstance(exception, Ebook2AudiobookException):
            from lib.classes.exceptions import ExceptionHandler
            ExceptionHandler.handle_exception(exception, context)
            # Create a generic error report
            error_report = ErrorReport(
                Ebook2AudiobookException(
                    message=str(exception),
                    severity=ErrorSeverity.HIGH,
                    category=ErrorCategory.SYSTEM,
                    original_exception=exception,
                    context=context
                ),
                context
            )
        else:
            error_report = ErrorReport(exception, context)

        # Update statistics
        self._update_error_stats(error_report)

        # Report to specified destinations
        destinations = destinations or [ReportDestination.ALL]

        if ReportDestination.ALL in destinations or ReportDestination.CONSOLE in destinations:
            self._report_to_console(error_report)

        if ReportDestination.ALL in destinations or ReportDestination.FILE in destinations:
            self._report_to_file(error_report)

        if ReportDestination.ALL in destinations or ReportDestination.GUI in destinations:
            self._report_to_gui(error_report)

        return error_report

    def _update_error_stats(self, error_report: ErrorReport) -> None:
        """Update error statistics"""
        self.error_stats['total_errors'] += 1
        self.error_stats['by_severity'][error_report.exception.severity.name] += 1
        self.error_stats['by_category'][error_report.exception.category.value] += 1

        # Keep only last 100 errors
        self.error_stats['recent_errors'].append({
            'timestamp': error_report.timestamp,
            'report_id': error_report.report_id,
            'severity': error_report.exception.severity.name,
            'category': error_report.exception.category.value,
            'message': error_report.exception.message
        })
        if len(self.error_stats['recent_errors']) > 100:
            self.error_stats['recent_errors'].pop(0)

    def _report_to_console(self, error_report: ErrorReport) -> None:
        """Report error to console"""
        severity_colors = {
            ErrorSeverity.CRITICAL: '\033[91m',  # Red
            ErrorSeverity.HIGH: '\033[93m',     # Yellow
            ErrorSeverity.MEDIUM: '\033[95m',   # Purple
            ErrorSeverity.LOW: '\033[94m',      # Blue
            ErrorSeverity.INFO: '\033[92m'      # Green
        }

        reset_color = '\033[0m'

        # Get appropriate color for severity
        color = severity_colors.get(error_report.exception.severity, reset_color)

        # Format console output
        console_output = f"""
{color}=== {self.app_name.upper()} ERROR REPORT ==={reset_color}
{color}Report ID: {error_report.report_id}{reset_color}
{color}Timestamp: {error_report.timestamp}{reset_color}
{color}Severity: {error_report.exception.severity.name}{reset_color}
{color}Category: {error_report.exception.category.value}{reset_color}
{color}Message: {error_report.exception.message}{reset_color}

{color}System: {error_report.system_info['platform']} {error_report.system_info['platform_version']}{reset_color}
{color}Python: {error_report.system_info['python_version']}{reset_color}

{color}Context:{reset_color}
"""
        for key, value in error_report.context.items():
            console_output += f"  {key}: {value}\n"

        if error_report.exception.original_exception:
            console_output += f"""
{color}Original Exception:{reset_color}
  Type: {type(error_report.exception.original_exception).__name__}
  Message: {str(error_report.exception.original_exception)}
"""

        print(console_output)

        # Also log to Python logging system
        logging.error(f"Error reported: {error_report.report_id} - {error_report.exception.message}")

    def _report_to_file(self, error_report: ErrorReport) -> None:
        """Report error to file"""
        try:
            # Create report file
            report_file = os.path.join(
                self.report_log_dir,
                f"error_report_{error_report.report_id}.json"
            )

            # Write JSON report
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(error_report.to_dict(), f, indent=2)

            # Also write text version
            text_report_file = os.path.join(
                self.report_log_dir,
                f"error_report_{error_report.report_id}.txt"
            )

            with open(text_report_file, 'w', encoding='utf-8') as f:
                f.write(error_report.to_text())

            logging.info(f"Error report saved to: {report_file}")

        except Exception as e:
            logging.error(f"Failed to save error report to file: {e}")

    def _report_to_gui(self, error_report: ErrorReport) -> None:
        """Report error to GUI (if available)"""
        try:
            # Check if gradio is available
            import gradio as gr

            # Create error message for GUI
            error_message = f"""
**Error Report: {error_report.report_id}**

**Severity:** {error_report.exception.severity.name}
**Category:** {error_report.exception.category.value}
**Message:** {error_report.exception.message}

**System:** {error_report.system_info['platform']} | Python: {error_report.system_info['python_version']}
**Timestamp:** {error_report.timestamp}
"""

            # Add context if available
            if error_report.context:
                error_message += "\n**Context:**\n"
                for key, value in error_report.context.items():
                    error_message += f"- {key}: {value}\n"

            # Show error in GUI
            if hasattr(gr, 'Error'):
                gr.Error(error_message)
            elif hasattr(gr, 'Warning'):
                gr.Warning(error_message)
            else:
                print(f"GUI Error: {error_message}")

        except ImportError:
            # Gradio not available, fall back to console
            logging.warning("Gradio not available for GUI error reporting")
        except Exception as e:
            logging.error(f"Failed to report error to GUI: {e}")

    def get_error_stats(self) -> Dict[str, Any]:
        """Get current error statistics"""
        return self.error_stats.copy()

    def generate_error_summary(self, format: ReportFormat = ReportFormat.TEXT) -> str:
        """Generate a summary of recent errors"""
        stats = self.error_stats

        if format == ReportFormat.JSON:
            return json.dumps(stats, indent=2)
        elif format == ReportFormat.MARKDOWN:
            summary = [
                f"# Error Statistics for {self.app_name}",
                f"**Total Errors:** {stats['total_errors']}",
                "",
                "## By Severity",
                "```",
                "\n".join(f"{severity}: {count}" for severity, count in stats['by_severity'].items()),
                "```",
                "",
                "## By Category",
                "```",
                "\n".join(f"{category}: {count}" for category, count in stats['by_category'].items()),
                "```",
                "",
                "## Recent Errors (last 10)",
                "\n".join([
                    f"- **{error['timestamp']}** [{error['severity']}] {error['message']}"
                    for error in stats['recent_errors'][-10:]
                ])
            ]
            return "\n".join(summary)
        else:  # TEXT format
            summary = [
                f"Error Statistics for {self.app_name}",
                f"Total Errors: {stats['total_errors']}",
                "",
                "By Severity:",
                "\n".join(f"  {severity}: {count}" for severity, count in stats['by_severity'].items()),
                "",
                "By Category:",
                "\n".join(f"  {category}: {count}" for category, count in stats['by_category'].items()),
                "",
                "Recent Errors (last 10):",
                "\n".join([
                    f"  {error['timestamp']} [{error['severity']}] {error['message']}"
                    for error in stats['recent_errors'][-10:]
                ])
            ]
            return "\n".join(summary)

    def clear_error_stats(self) -> None:
        """Clear error statistics"""
        self.error_stats = {
            'total_errors': 0,
            'by_severity': {severity.name: 0 for severity in ErrorSeverity},
            'by_category': {category.value: 0 for category in ErrorCategory},
            'recent_errors': []
        }

class ErrorReportingMiddleware:
    """
    Middleware for integrating error reporting into application flow
    """

    def __init__(self, error_reporter: ErrorReporter):
        self.error_reporter = error_reporter

    def wrap_function(self, func: Callable) -> Callable:
        """
        Wrap a function to automatically report errors
        """
        def wrapped_function(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Ebook2AudiobookException as e:
                # Report the error and re-raise
                self.error_reporter.report_error(e, {'function': func.__name__})
                raise
            except Exception as e:
                # Convert to custom exception and report
                context = {'function': func.__name__, 'args': args, 'kwargs': kwargs}
                custom_exception = Ebook2AudiobookException(
                    message=f"Error in {func.__name__}: {str(e)}",
                    severity=ErrorSeverity.HIGH,
                    original_exception=e,
                    context=context
                )
                self.error_reporter.report_error(custom_exception)
                raise custom_exception
        return wrapped_function

    def wrap_async_function(self, func: Callable) -> Callable:
        """
        Wrap an async function to automatically report errors
        """
        async def wrapped_async_function(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Ebook2AudiobookException as e:
                # Report the error and re-raise
                self.error_reporter.report_error(e, {'function': func.__name__})
                raise
            except Exception as e:
                # Convert to custom exception and report
                context = {'function': func.__name__, 'args': args, 'kwargs': kwargs}
                custom_exception = Ebook2AudiobookException(
                    message=f"Error in {func.__name__}: {str(e)}",
                    severity=ErrorSeverity.HIGH,
                    original_exception=e,
                    context=context
                )
                self.error_reporter.report_error(custom_exception)
                raise custom_exception
        return wrapped_async_function

    def report_and_continue(self, func: Callable, default_return: Any = None) -> Callable:
        """
        Wrap a function to report errors but continue execution with default return
        """
        def wrapped_function(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                context = {'function': func.__name__, 'args': args, 'kwargs': kwargs}
                self.error_reporter.report_error(e, context)
                return default_return
        return wrapped_function

# Global error reporter instance
global_error_reporter = ErrorReportingMiddleware(ErrorReporter())

def report_error(exception: Union[Ebook2AudiobookException, Exception],
                context: Optional[Dict[str, Any]] = None) -> ErrorReport:
    """
    Global function to report errors using the default error reporter
    """
    return global_error_reporter.error_reporter.report_error(exception, context)

def wrap_function(func: Callable) -> Callable:
    """
    Global function to wrap functions with error reporting
    """
    return global_error_reporter.wrap_function(func)

def wrap_async_function(func: Callable) -> Callable:
    """
    Global function to wrap async functions with error reporting
    """
    return global_error_reporter.wrap_async_function(func)

def report_and_continue(func: Callable, default_return: Any = None) -> Callable:
    """
    Global function to wrap functions that should continue after errors
    """
    return global_error_reporter.report_and_continue(func, default_return)

def get_error_stats() -> Dict[str, Any]:
    """
    Get global error statistics
    """
    return global_error_reporter.error_reporter.get_error_stats()

def generate_error_summary(format: ReportFormat = ReportFormat.TEXT) -> str:
    """
    Generate global error summary
    """
    return global_error_reporter.error_reporter.generate_error_summary(format)