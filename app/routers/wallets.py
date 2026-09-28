import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud
from app.database import get_session
from app.schemas import (
    WalletOperationRequest,
    WalletResponse,
)

router = APIRouter(prefix="/api/v1/wallets", tags=["wallets"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]


@router.get(
    "/{wallet_id}",
    response_model=WalletResponse,
    summary="Получить баланс кошелька",
)
async def get_wallet_balance(
    wallet_id: uuid.UUID,
    session: SessionDep,
) -> WalletResponse:
    wallet = await crud.get_wallet(session, wallet_id)
    return WalletResponse.model_validate(wallet)


@router.post(
    "/{wallet_id}/operation",
    response_model=WalletResponse,
    status_code=status.HTTP_200_OK,
    summary="Изменить баланс кошелька",
)
async def wallet_operation(
    wallet_id: uuid.UUID,
    payload: WalletOperationRequest,
    session: SessionDep,
) -> WalletResponse:
    wallet = await crud.apply_operation(
        session=session,
        wallet_id=wallet_id,
        operation_type=payload.operation_type,
        amount=payload.amount,
    )
    return WalletResponse.model_validate(wallet)