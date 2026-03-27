# Mini Production Checklist

## Transactions
- [x] Transfer uses a single transaction with rollback on failure
- [x] Service layer owns commit/rollback boundaries
- [ ] Add one negative test for transfer DB error path with explicit assertion on unchanged balances

## Idempotency
- [x] Unique `idempotency_key` persisted
- [x] Replay path (`200`) and conflict path (`409`) implemented
- [ ] Add concurrency test for two parallel requests with same idempotency key

## Cache
- [x] Cache-aside for `GET /orders/{order_id}`
- [x] Cache invalidation called on order create
- [x] Cache miss/hit tests added with mocks
- [ ] Add test for stale cache prevention after update flow (if update endpoint added)

## DB Performance
- [x] `GET /orders` supports `limit`
- [x] Index for user orders query exists
- [ ] Capture and document EXPLAIN plan before/after index (PostgreSQL run)

## Logging
- [x] Logging bootstrap exists
- [ ] Add log statements for order create/replay/conflict paths
- [ ] Add log statements for transfer success/failure and cache hit/miss

## API/Docs
- [ ] Add response schemas for all endpoints
- [ ] Add error response examples in README
- [ ] Document local run (FastAPI + Redis) commands in README

## Final Readiness
- [ ] All tests green
- [ ] No mixed transport logic in repositories
- [ ] No TODO/FIXME left in critical flows
