from sqlalchemy import select

from lesson0203.models import Account


def test_forced_failure(client, test_db):
    payload = {
        "from_account_id": 1,
        "to_account_id": 2,
        "amount": 300,
        "currency": "RUB",
        "forced_failure": True,
    }

    balance1 = test_db.execute(select(Account).where(Account.id == 1)).scalar_one().balance
    balance2 = test_db.execute(select(Account).where(Account.id == 2)).scalar_one().balance

    response = client.post(url="/transfer/", json=payload)
    assert response.status_code == 500
    assert response.json()["detail"] == "test"

    balance1_after = test_db.get(Account, 1).balance
    balance2_after = test_db.get(Account, 2).balance

    assert balance1 == balance1_after
    assert balance2 == balance2_after
