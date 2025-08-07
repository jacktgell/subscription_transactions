# stripe_db_tool/main.py
from resources.db import get_db_session
from resources.logger import get_logger
from update_active_status.update_active_status import update_active_status
from update_commision_transactions_db.update_commision_transactions import update_commision_transactions_df
from update_redis.update_redis import update_redis


def main(logger):
    logger.info(f"Entering main function")
    session = get_db_session()

    try:
        update_active_status(session, logger)
    except Exception as e:
        logger.error(f"Error update_active_status(): {str(e)}")

    try:
        update_commision_transactions_df(session, logger)
    except Exception as e:
        logger.error(f"Error update_commision_transactions_df(): {str(e)}")

    try:
        update_redis(session, logger)
    except Exception as e:
        logger.error(f"Error update_redis(): {str(e)}")

    logger.info(f"session closing")
    session.close()
    logger.info(f"Program complete")


if __name__ == "__main__":
    logger = get_logger('Subscription_transactions')
    main(logger)