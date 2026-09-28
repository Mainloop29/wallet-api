import uuid
from decimal import Decimal

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import InsufficientFundsError, WalletNotFoundError
from app.models import Wallet
from app.schemas import OperationType


async def get_wallet(
    session: AsyncSession, wallet_id: uuid.UUID
) -> Wallet:
    """Вернуть кошелёк или бросить 404."""
    wallet = await session.get(Wallet, wallet_id)
    if wallet is None:
        raise WalletNotFoundError()
    return wallet


async def create_wallet(
    session: AsyncSession, balance: Decimal = Decimal("0")
) -> Wallet:
    """Создать новый кошелёк (используется в тестах/сидинге)."""
    wallet = Wallet(balance=balance)
    session.add(wallet)
    await session.commit()
    await session.refresh(wallet)
    return wallet


async def apply_operation(
    session: AsyncSession,
    wallet_id: uuid.UUID,
    operation_type: OperationType,
    amount: Decimal,
) -> Wallet:
    """
    Изменить баланс кошелька.

    Использует SELECT ... FOR UPDATE, чтобы параллельные операции
    над одним кошельком выполнялись последовательно. Также проверка
    достаточности средств выполняется в одной транзакции с изменением,
    что защищает от отрицательного баланса.
    """
    async with session.begin():
        result = await session.execute(
            select(Wallet)
            .where(Wallet.id == wallet_id)
            .with_for_update()
        )
        wallet = result.scalar_one_or_none()

        if wallet is None:
            raise WalletNotFoundError()

        if operation_type == OperationType.DEPOSIT:
            new_balance = wallet.balance + amount
        else:
            if wallet.balance < amount:
                raise InsufficientFundsError()
            new_balance = wallet.balance - amount

        await session.execute(
            update(Wallet)
            .where(Wallet.id == wallet_id)
            .values(balance=new_balance)
        )

    await session.refresh(wallet)
    return wallet