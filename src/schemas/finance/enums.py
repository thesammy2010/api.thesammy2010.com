import enum


class PaymentMethodKind(str, enum.Enum):
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    CASH = "cash"
    # Settled through a shared ledger such as Splitwise, so the amount is only
    # this side's share of what was spent
    SHARED_EXPENSE = "shared_expense"
    TRANSIT_CARD = "transit_card"
    OTHER = "other"


class TimeOfDay(str, enum.Enum):
    MORNING = "morning"
    AFTERNOON = "afternoon"
    EVENING = "evening"
    NIGHT = "night"
    # Bought online, where the time of day doesn't say anything
    ONLINE = "online"


class TransactionRelation(str, enum.Enum):
    """How a spend relates to the one it belongs to."""

    # Charged on top of it, such as a foreign transaction fee
    FEE = "fee"
    # Money back for it, with a negative amount
    REFUND = "refund"
    OTHER = "other"
