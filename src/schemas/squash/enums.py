import enum


class MatchFormat(str, enum.Enum):
    SINGLES = "singles"
    DOUBLES = "doubles"


class MatchStatus(str, enum.Enum):
    # Arranged but not started
    SCHEDULED = "scheduled"
    # Being scored game by game
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


PLAYERS_PER_SIDE = {MatchFormat.SINGLES: 1, MatchFormat.DOUBLES: 2}
