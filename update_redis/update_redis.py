import json
import logging
import uuid
import numpy as np
import redis
from resources.db import read_CommissionTransactions_to_df
from resources.config import Config


def update_redis(session, logger: logging.Logger):
    """
    Update Redis with aggregated commission data after reading and modifying the commission transactions DataFrame.

    Parameters:
    session: SQLAlchemy session for database operations.
    logger: Logger object for logging information and errors.
    """
    # Retrieve Redis configuration
    redis_host = Config.REDIS_HOST
    redis_port = Config.REDIS_PORT
    redis_db = Config.REDIS_DB
    redis_password = Config.REDIS_PASSWORD

    # Establish Redis connection
    try:
        r = redis.Redis(host=redis_host, port=redis_port, db=redis_db, password=redis_password, decode_responses=True)
        r.ping()  # Test connection
        logger.info("Successfully connected to Redis.")
    except redis.ConnectionError as e:
        logger.error(f"Failed to connect to Redis: {str(e)}")
        raise ConnectionError(f"Failed to connect to Redis: {str(e)}")

    # Read DataFrame from database
    try:
        commission_transactions_df = read_CommissionTransactions_to_df(session, logger)
        logger.info(f"Successfully read {len(commission_transactions_df)} rows from commission_transactions table.")
    except ValueError as e:
        logger.error(f"Error reading DataFrame from database: {str(e)}")
        raise

    # Get unique referees (used as user_ids)
    user_ids = list(commission_transactions_df['referee'].unique())
    logger.info(f"Identified {len(user_ids)} unique referees.")

    # Process and store data for each unique referee
    for user_id in user_ids:
        temp_df = commission_transactions_df[commission_transactions_df['referee'] == user_id]
        total_commissions = temp_df['commission_amount'].sum()
        pending_commissions = temp_df[temp_df['commission_paid'] == False]['commission_amount'].sum()
        total_commissions_paid_out = total_commissions - pending_commissions

        data = {
            'total_commissions_paid_out': total_commissions_paid_out,
            'pending_commissions': pending_commissions,
            'total_commissions': total_commissions
        }

        key = str(user_id)
        try:
            r.set(key, json.dumps(data))
            logger.info(f"Successfully stored data for key '{key}' in Redis.")
        except Exception as e:
            logger.error(f"Error storing data for key '{key}' in Redis: {str(e)}")
            raise ValueError(f"Error storing data for key '{key}': {str(e)}")
