import enum


class UserRole(str, enum.Enum):
    """Roles for user authorization."""

    ADMIN = "admin"
    USER = "user"


class UserStatus(str, enum.Enum):
    """Lifecycle status of a user account."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"


class VerificationTypeEnum(str, enum.Enum):
    """Types of verification tokens."""

    LOGIN = "login"
    INITIAL_VERIFICATION = "initial_verification"
    PASSWORD_RESET = "password_reset"
