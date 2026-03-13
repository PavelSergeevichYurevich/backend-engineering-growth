from decimal import Decimal

from sqlalchemy import select

from lesson0203.models import Account


def test_forced_failure(client, test_db):
    payload = {
        'from_account_id': 1,
        'to_account_id': 2,
        'amount': 300,
        'currency': 'RUB',
        'forced_failure': True,
    }

    balance1 = test_db.execute(select(Account).where(Account.id == 1)).scalar_one().balance
    balance2 = test_db.execute(select(Account).where(Account.id == 2)).scalar_one().balance

    response = client.post(url='/transfer/', json=payload)
    assert response.status_code == 500
    assert response.json()['detail'] == 'test'

    balance1_after = test_db.get(Account, 1).balance
    balance2_after = test_db.get(Account, 2).balance

    assert balance1 == balance1_after
    assert balance2 == balance2_after

def test_insufficient_funds(client, test_db):
    payload = {
        'from_account_id': 1,
        'to_account_id': 2,
        'amount': 3000,
        'currency': 'RUB',
        'forced_failure': False
    }

    balance1 = test_db.execute(select(Account).where(Account.id == 1)).scalar_one().balance
    balance2 = test_db.execute(select(Account).where(Account.id == 2)).scalar_one().balance

    response = client.post(url='/transfer/', json=payload)
    assert response.status_code == 409
    assert response.json()['detail'] == 'Not enough money'

    balance1_after = test_db.get(Account, 1).balance
    balance2_after = test_db.get(Account, 2).balance

    assert balance1 == balance1_after
    assert balance2 == balance2_after
def test_successful_transfer(client, test_db):
    payload = {
        'from_account_id': 1,
        'to_account_id': 2,
        'amount': 300,
        'currency': 'RUB',
        'forced_failure': False
    }

    balance1 = test_db.execute(select(Account).where(Account.id == 1)).scalar_one().balance
    balance2 = test_db.execute(select(Account).where(Account.id == 2)).scalar_one().balance

    response = client.post(url='/transfer/', json=payload)
    assert response.status_code == 201
    assert response.json()['transfer_id'] is not None
    test_db.expire_all()

    balance1_after = test_db.get(Account, 1).balance
    balance2_after = test_db.get(Account, 2).balance

    assert balance1 - Decimal('300.00') == balance1_after
    assert balance2 + Decimal('300.00') == balance2_after
