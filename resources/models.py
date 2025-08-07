# stripe_db_tool/models.py
from sqlalchemy import Column, Integer, Float, String, DateTime, Text, ForeignKey, Boolean, Date
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import uuid

Base = declarative_base()

class Users(Base):
    __tablename__ = 'users'
    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(120), unique=True, nullable=False)
    password_hash = Column(String(128), nullable=False)
    signup_date = Column(Date, nullable=False)
    isactive = Column(Boolean, nullable=False, default=False)
    active_till = Column(Date, nullable=True)
    apikey = Column(String, nullable=True)
    apisecret = Column(String, nullable=True)
    passphrase = Column(String, nullable=True)
    verification_token = Column(String(64), nullable=True)
    verification_code = Column(String(6), nullable=True)
    veri_token_exp = Column(DateTime, nullable=True)
    verified = Column(Boolean, nullable=False, default=False)
    exchange = Column(String, nullable=True)
    active_symbols = Column(JSONB, nullable=False, default=lambda: {})
    strategy = Column(JSONB, nullable=False, default=lambda: {})
    stripe_customer_id = Column(String(255), nullable=True)
    stripe_subscription_id = Column(String(255), nullable=True)
    referee = Column(UUID(as_uuid=True), nullable=True)
    cancel_at_period_end = Column(Boolean, nullable=False, default=False)

class CommissionTransactions(Base):
    __tablename__ = 'commission_transactions'

    charge_id = Column(String(50), primary_key=True, nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.user_id'), nullable=True)
    referee = Column(UUID(as_uuid=True), nullable=True)
    customer_id = Column(String(50), nullable=True)
    email = Column(String(255), nullable=True)
    amount = Column(Float, nullable=True)
    currency = Column(String(3), nullable=True)
    status = Column(String(50), nullable=True)
    notes = Column(Text, nullable=True)
    disputed = Column(Boolean, nullable=True)
    dispute = Column(Text, nullable=True)
    refunded = Column(Boolean, nullable=True)
    created = Column(DateTime, nullable=True)
    description = Column(Text, nullable=True)
    payment_method = Column(String(20), nullable=True)
    last4 = Column(String(4), nullable=True)
    matures_on = Column(DateTime, nullable=True)
    commission_amount = Column(Float, nullable=True)
    commission_paid = Column(Boolean, nullable=False, default=False)
    commission_paid_tx_id = Column(Text, nullable=False, default='')

class Referrals(Base):
    __tablename__ = 'referrals'
    user_id = Column(UUID(as_uuid=True), primary_key=True)
    referral_link = Column(String(50), unique=True, nullable=False)
    referrals = Column(JSONB, nullable=False, default=lambda: {})
    commission = Column(Float, nullable=False, default=0.25)
    discount = Column(Float, nullable=False, default=0.05)