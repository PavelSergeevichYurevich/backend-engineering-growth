from decimal import Decimal

from sqlalchemy import select

from lesson0203.models import Account, IdempotencyRecords
from lesson0203 import services as services_module



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

def test_create_order_201(client, test_db):
    payload = {
        'user_id': 1,
        'amount': 100,
        'currency': 'RUB',
        'idempotency_key': 'test-key-1',
    }

    response = client.post(url='/orders/', json=payload)
    stmnt = select(IdempotencyRecords).where(IdempotencyRecords.idempotency_key == 'test-key-1')
    record = test_db.execute(stmnt).scalar_one_or_none()
    assert record is not None
    assert record.request_hash == '1:100:RUB'
    order_id = record.order_id
    assert response.status_code == 201
    assert response.json()['order_id'] == order_id  

def test_create_order_200(client, test_db):
    payload = {
        'user_id': 1,
        'amount': 100,
        'currency': 'RUB',
        'idempotency_key': 'test-key-2',
    }

    response1 = client.post(url='/orders/', json=payload)
    response2 = client.post(url='/orders/', json=payload)

    assert response1.status_code == 201
    assert response2.status_code == 200
    assert response1.json()['order_id'] == response2.json()['order_id']

def test_create_order_idempotency_key_conflict(client, test_db):
    payload1 = {
        'user_id': 1,
        'amount': 100,
        'currency': 'RUB',
        'idempotency_key': 'test-key-3',
    }
    payload2 = {
        'user_id': 1,
        'amount': 200,
        'currency': 'RUB',
        'idempotency_key': 'test-key-3',
    }

    response1 = client.post(url='/orders/', json=payload1)
    response2 = client.post(url='/orders/', json=payload2)

    assert response1.status_code == 201
    assert response2.status_code == 409
    assert response2.json()['detail'] == 'Idempotency key conflict'

def test_get_order_cache_miss_writes_cache(client, monkeypatch):
    payload = {
        'user_id': 1,
        'amount': 100,
        'currency': 'RUB',
        'idempotency_key': 'test-key-3',
    }
    response = client.post(url='/orders/', json=payload)
    assert response.status_code == 201
    order_id = response.json()['order_id']

    monkeypatch.setattr(services_module, 'get_order_from_cache', lambda _order_id: None)

    captured = {}
    def fake_set_order_cache(_order_id, _order_data):
        captured['order_id'] = _order_id
        captured['order_data'] = _order_data

    monkeypatch.setattr(services_module, 'set_order_cache', fake_set_order_cache)

    response = client.get(url=f'/orders/{order_id}')
    assert response.status_code == 200
    assert response.json()['order_id'] == order_id
    assert response.json()['user_id'] == 1
    assert response.json()['amount'] == '100.00'
    assert response.json()['currency'] == 'RUB'

    assert captured['order_id'] == order_id
    assert captured['order_data']['order_id'] == order_id

def test_get_order_cache_hit_skips_db(client, test_db, monkeypatch):
    payload = {
        'user_id': 1,
        'amount': 100,
        'currency': 'RUB',
        'idempotency_key': 'test-key-3',
    }
    response = client.post(url='/orders/', json=payload)
    assert response.status_code == 201
    order_id = response.json()['order_id']

    cached_payload = {
        'order_id': order_id,
        'user_id': 1,
        'amount': '100',
        'currency': 'RUB'
    }

    monkeypatch.setattr(services_module, 'get_order_from_cache', lambda _order_id: cached_payload)

    calls = {'set_cache': 0}
    def spy_set_order_cache(_order_id, _order_data):
        calls['set_cache'] += 1

    monkeypatch.setattr(services_module, 'set_order_cache', spy_set_order_cache)

    def fail_if_db_read(*args, **kwargs):
        raise AssertionError('DB should not be called on cache hit')

    monkeypatch.setattr(test_db, 'execute', fail_if_db_read)

    response = client.get(url=f'/orders/{order_id}')
    assert response.status_code == 200
    assert response.json() == cached_payload
    assert calls['set_cache'] == 0

def test_create_order_invalidates_cache_on_created(client, monkeypatch):
    payload = {
        'user_id': 1,
        'amount': 100,
        'currency': 'RUB',
        'idempotency_key': 'test-key-3',
    }
    calls = {'count': 0, 'order_id': None}
    def spy_plus_calls(order_id):
        calls['count'] += 1
        calls['order_id'] = order_id
    monkeypatch.setattr(services_module, 'on_order_created', spy_plus_calls)

    response = client.post(url='/orders/', json=payload)
    assert response.status_code == 201
    assert response.json()['order_id'] is not None
    assert calls['count'] == 1
    assert calls['order_id'] == response.json()['order_id']


