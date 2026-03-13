from sqlalchemy import TIMESTAMP, Column, ForeignKey, Integer, Numeric, Text, func
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class Account(Base):
    __tablename__ = 'accounts'

    id = Column(Integer, primary_key=True)
    balance = Column(Numeric(18, 2), nullable=False)
    currency = Column(Text, nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    outgoing_transfers = relationship(
        'Transfer',
        foreign_keys='Transfer.from_account_id',
        back_populates='from_account',
    )
    incoming_transfers = relationship(
        'Transfer',
        foreign_keys='Transfer.to_account_id',
        back_populates='to_account',
    )


class Transfer(Base):
    __tablename__ = 'transfers'

    id = Column(Integer, primary_key=True)
    from_account_id = Column(Integer, ForeignKey('accounts.id'), nullable=False)
    to_account_id = Column(Integer, ForeignKey('accounts.id'), nullable=False)
    amount = Column(Numeric(18, 2), nullable=False)
    currency = Column(Text, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())

    from_account = relationship(
        'Account', foreign_keys=[from_account_id], back_populates='outgoing_transfers'
    )
    to_account = relationship(
        'Account', foreign_keys=[to_account_id], back_populates='incoming_transfers'
    )
