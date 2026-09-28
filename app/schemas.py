import uuid
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class OperationType(str, Enum):

    DEPOSIT = "DEPOSIT"
    WITHDRAW = "WITHDRAW"


class WalletOperationRequest(BaseModel):

    operation_type: OperationType
    amount: Decimal = Field(gt=0, max_digits=20, decimal_places=2)


class WalletResponse(BaseModel):

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    balance: Decimal