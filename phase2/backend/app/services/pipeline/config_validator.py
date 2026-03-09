"""
Configuration Validator

Validates pipeline configuration values including cron expressions,
port numbers, and retry attempt counts.
"""
import re
from typing import NamedTuple


class ValidationResult(NamedTuple):
    is_valid: bool
    error_message: str | None = None


class ConfigValidator:
    """Validates pipeline configuration values."""

    # Valid ranges for field values
    _MIN_PORT = 1024
    _MAX_PORT = 65535
    _MIN_RETRY = 1
    _MAX_RETRY = 10

    # Cron field validators: (min, max) for each of the 5 fields
    _CRON_RANGES = [
        (0, 59),   # minute
        (0, 23),   # hour
        (1, 31),   # day-of-month
        (1, 12),   # month
        (0, 7),    # day-of-week (0 and 7 both = Sunday)
    ]

    def validate_cron_expression(self, expression: str) -> ValidationResult:
        """
        Validate a cron expression (5-field standard format).

        Returns ValidationResult with is_valid=False and an error_message
        for invalid expressions.
        """
        if not expression or not expression.strip():
            return ValidationResult(
                is_valid=False,
                error_message="cron schedule expression must not be empty"
            )

        parts = expression.strip().split()
        if len(parts) != 5:
            return ValidationResult(
                is_valid=False,
                error_message=(
                    f"Invalid cron schedule: expected 5 fields, got {len(parts)}"
                )
            )

        for i, (field, (low, high)) in enumerate(zip(parts, self._CRON_RANGES)):
            result = self._validate_cron_field(field, low, high)
            if not result.is_valid:
                return ValidationResult(
                    is_valid=False,
                    error_message=f"Invalid cron schedule field {i + 1}: {result.error_message}"
                )

        return ValidationResult(is_valid=True)

    def _validate_cron_field(self, field: str, low: int, high: int) -> ValidationResult:
        """Validate a single cron field against its allowed range."""
        if field == "*":
            return ValidationResult(is_valid=True)

        # Step values: */n or start/n
        if "/" in field:
            parts = field.split("/", 1)
            if len(parts) != 2:
                return ValidationResult(
                    is_valid=False,
                    error_message=f"invalid step expression '{field}'"
                )
            base, step = parts
            try:
                step_val = int(step)
                if step_val <= 0:
                    raise ValueError
            except ValueError:
                return ValidationResult(
                    is_valid=False,
                    error_message=f"step value must be a positive integer in '{field}'"
                )
            if base != "*":
                try:
                    base_val = int(base)
                    if not (low <= base_val <= high):
                        raise ValueError
                except ValueError:
                    return ValidationResult(
                        is_valid=False,
                        error_message=f"base value out of range [{low}-{high}] in '{field}'"
                    )
            return ValidationResult(is_valid=True)

        # Range: n-m
        if "-" in field:
            parts = field.split("-", 1)
            try:
                a, b = int(parts[0]), int(parts[1])
                if not (low <= a <= high and low <= b <= high and a <= b):
                    raise ValueError
                return ValidationResult(is_valid=True)
            except (ValueError, IndexError):
                return ValidationResult(
                    is_valid=False,
                    error_message=f"invalid range '{field}' (allowed {low}-{high})"
                )

        # List: n,m,...
        if "," in field:
            for val in field.split(","):
                result = self._validate_cron_field(val.strip(), low, high)
                if not result.is_valid:
                    return result
            return ValidationResult(is_valid=True)

        # Plain integer
        try:
            val = int(field)
            if low <= val <= high:
                return ValidationResult(is_valid=True)
            return ValidationResult(
                is_valid=False,
                error_message=f"value {val} out of range [{low}-{high}]"
            )
        except ValueError:
            return ValidationResult(
                is_valid=False,
                error_message=f"invalid cron field value '{field}'"
            )

    def validate_port(self, port: int) -> ValidationResult:
        """
        Validate a network port number.

        Valid range: 1024–65535 (unprivileged ports).
        """
        if not isinstance(port, int):
            return ValidationResult(
                is_valid=False,
                error_message=f"port must be an integer, got {type(port).__name__}"
            )
        if self._MIN_PORT <= port <= self._MAX_PORT:
            return ValidationResult(is_valid=True)
        return ValidationResult(
            is_valid=False,
            error_message=(
                f"port {port} is out of valid range "
                f"[{self._MIN_PORT}-{self._MAX_PORT}]"
            )
        )

    def validate_retry_attempts(self, attempts: int) -> ValidationResult:
        """
        Validate retry attempt count.

        Valid range: 1–10.
        """
        if not isinstance(attempts, int):
            return ValidationResult(
                is_valid=False,
                error_message=f"retry attempts must be an integer, got {type(attempts).__name__}"
            )
        if self._MIN_RETRY <= attempts <= self._MAX_RETRY:
            return ValidationResult(is_valid=True)
        return ValidationResult(
            is_valid=False,
            error_message=(
                f"retry attempts {attempts} out of valid range "
                f"[{self._MIN_RETRY}-{self._MAX_RETRY}]"
            )
        )
