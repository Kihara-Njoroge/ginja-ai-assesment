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


class ClaimStatus(str, enum.Enum):
    """Status of a health insurance claim."""

    PENDING = "pending"
    APPROVED = "approved"
    PARTIAL = "partial"
    REJECTED = "rejected"


class MemberStatus(str, enum.Enum):
    """Status of an insurance member."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
