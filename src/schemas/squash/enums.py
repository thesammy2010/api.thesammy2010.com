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


class RallyDecision(str, enum.Enum):
    """The referee's call when a player appeals for interference."""

    # Replayed, with no point to either side and the same server
    LET = "let"
    # The point to the player who appealed
    STROKE = "stroke"
    # The appeal turned down, so the point to their opponent
    NO_LET = "no_let"


PLAYERS_PER_SIDE = {MatchFormat.SINGLES: 1, MatchFormat.DOUBLES: 2}
