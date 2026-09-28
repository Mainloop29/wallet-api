import uuid
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class OperationType(str, Enum):
    """Тип операции над кошельком."""

    DEPOSIT = "DEPOSIT"
    WITHDRAW = "WITHDRAW"


class WalletOperationRequest(BaseModel):
    """Тело запроса на изменение баланса."""

    operation_type: OperationType
    amount: Decimal = Field(gt=0, max_digits=20, decimal_places=2)


class WalletResponse(BaseModel):
    """Ответ с информацией о кошельке."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    balance: Decimal