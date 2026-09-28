import asyncio
import uuid

import pytest
from httpx import AsyncClient

from app import crud


@pytest.mark.asyncio(loop_scope="session")
async def test_get_wallet_balance(client: AsyncClient, session_factory):
    async with session_factory() as session:
        wallet = await crud.create_wallet(session, balance=500)
        wallet_id = wallet.id

    response = await client.get(f"/api/v1/wallets/{wallet_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(wallet_id)
    assert float(data["balance"]) == 500.0


@pytest.mark.asyncio(loop_scope="session")
async def test_get_wallet_not_found(client: AsyncClient):
    response = await client.get(f"/api/v1/wallets/{uuid.uuid4()}")
    assert response.status_code == 404


@pytest.mark.asyncio(loop_scope="session")
async def test_deposit(client: AsyncClient, session_factory):
    async with session_factory() as session:
        wallet = await crud.create_wallet(session, balance=0)
        wallet_id = wallet.id

    response = await client.post(
        f"/api/v1/wallets/{wallet_id}/operation",
        json={"operation_type": "DEPOSIT", "amount": 1000},
    )

    assert response.status_code == 200
    assert float(response.json()["balance"]) == 1000.0


@pytest.mark.asyncio(loop_scope="session")
async def test_withdraw(client: AsyncClient, session_factory):
    async with session_factory() as session:
        wallet = await crud.create_wallet(session, balance=1000)
        wallet_id = wallet.id

    response = await client.post(
        f"/api/v1/wallets/{wallet_id}/operation",
        json={"operation_type": "WITHDRAW", "amount": 300},
    )

    assert response.status_code == 200
    assert float(response.json()["balance"]) == 700.0


@pytest.mark.asyncio(loop_scope="session")
async def test_withdraw_insufficient_funds(
    client: AsyncClient, session_factory
):
    async with session_factory() as session:
        wallet = await crud.create_wallet(session, balance=100)
        wallet_id = wallet.id

    response = await client.post(
        f"/api/v1/wallets/{wallet_id}/operation",
        json={"operation_type": "WITHDRAW", "amount": 500},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Insufficient funds"


@pytest.mark.asyncio(loop_scope="session")
async def test_operation_invalid_amount(
    client: AsyncClient, session_factory
):
    async with session_factory() as session:
        wallet = await crud.create_wallet(session, balance=0)
        wallet_id = wallet.id

    response = await client.post(
        f"/api/v1/wallets/{wallet_id}/operation",
        json={"operation_type": "DEPOSIT", "amount": -10},
    )

    assert response.status_code == 422


@pytest.mark.asyncio(loop_scope="session")
async def test_concurrent_deposits(client: AsyncClient, session_factory):
    async with session_factory() as session:
        wallet = await crud.create_wallet(session, balance=0)
        wallet_id = wallet.id

    async def deposit():
        return await client.post(
            f"/api/v1/wallets/{wallet_id}/operation",
            json={"operation_type": "DEPOSIT", "amount": 100},
        )

    results = await asyncio.gather(*(deposit() for _ in range(20)))
    assert all(r.status_code == 200 for r in results)

    response = await client.get(f"/api/v1/wallets/{wallet_id}")
    assert float(response.json()["balance"]) == 2000.0


@pytest.mark.asyncio(loop_scope="session")
async def test_concurrent_withdraw_never_negative(
    client: AsyncClient, session_factory
):
    async with session_factory() as session:
        wallet = await crud.create_wallet(session, balance=1000)
        wallet_id = wallet.id

    async def withdraw():
        return await client.post(
            f"/api/v1/wallets/{wallet_id}/operation",
            json={"operation_type": "WITHDRAW", "amount": 100},
        )

    results = await asyncio.gather(*(withdraw() for _ in range(20)))
    ok = [r for r in results if r.status_code == 200]
    failed = [r for r in results if r.status_code == 400]

    assert len(ok) == 10
    assert len(failed) == 10

    response = await client.get(f"/api/v1/wallets/{wallet_id}")
    assert float(response.json()["balance"]) == 0.0