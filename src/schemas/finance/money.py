import decimal
from typing import Annotated

from pydantic import PlainSerializer

# Held as a Decimal so that totals add up exactly, but sent as a JSON number
# rather than Pydantic's default of a string, like every other amount the API
# returns.
Money = Annotated[
    decimal.Decimal,
    PlainSerializer(float, return_type=float, when_used="json"),
]
