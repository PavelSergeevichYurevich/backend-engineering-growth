# Lesson0203 Mini Production Project

## Goal
Build a small backend service with production-minded behavior:
- transactional correctness
- idempotent writes
- Redis cache for reads
- structured logging
- clear architecture boundaries

## Stack
- FastAPI
- SQLAlchemy
- SQLite/PostgreSQL
- Redis

## Architecture
- `routes.py`: HTTP layer (request/response/status codes only)
- `services.py`: business use-cases and transaction boundaries
- `repositories.py`: DB access only (select/insert/update), no HTTP concerns
- `cache.py`: Redis cache primitives (get/set/invalidate)
- `models.py`: ORM models + DB indexes

## Core Flows
1. `POST /transfer/`
- validates request
- runs single transaction for debit/credit/transfer record
- full rollback on any error

2. `POST /orders/`
- idempotent order creation by `idempotency_key`
- returns `201` for created, `200` for replay, `409` for conflict

3. `GET /orders/{order_id}`
- cache-aside read: cache hit -> return; miss -> DB read + cache set

4. `GET /orders?user_id=...&limit=...`
- user orders list
- sorted by newest first
- limited result set

## Logging Plan
Use INFO logs with stable event names and key fields:
- `order.created` (order_id, user_id, idempotency_key)
- `order.replayed` (order_id, idempotency_key)
- `order.conflict` (idempotency_key)
- `transfer.completed` (transfer_id, from_account_id, to_account_id, amount)
- `transfer.failed` (reason)
- `order.cache.hit` / `order.cache.miss` (order_id)

## Next Steps
Follow `MINI_PROD_CHECKLIST.md` and complete all unchecked items.
