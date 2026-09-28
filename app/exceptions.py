from fastapi import HTTPException, status


class WalletNotFoundError(HTTPException):
    """Кошелёк не найден."""

    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Wallet not found",
        )


class InsufficientFundsError(HTTPException):
    """Недостаточно средств для списания."""

    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Insufficient funds",
        )