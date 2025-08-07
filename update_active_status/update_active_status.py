import pandas as pd
import stripe

from resources.db import fetch_users, update_isactive_in_users
from resources.config import Config
import time

def update_active_status(session, logger):

    df_users = fetch_users(session)
    df_users = df_users.drop(columns=['referee'])
    df_users = df_users.dropna(subset=['stripe_customer_id'])
    df_users['active'] = False

    stripe.api_key = Config.STRIPE_SECRET_KEY

    for index, row in df_users.iterrows():
        customer_id = row['stripe_customer_id']
        try:
            # Check for any active subscriptions
            time.sleep(0.1)
            subscriptions = stripe.Subscription.list(
                customer=customer_id
            )

            logger.debug(f"customer_id={customer_id}: Length subscriptions={len(subscriptions)}")

            for data in subscriptions.data:
                if data.get('status') == 'active':
                    logger.debug(f"customer_id={customer_id}: {data.get('status')}")
                    df_users.at[index, 'active'] = True
                else:
                    logger.debug(f"customer_id={customer_id}: {data.get('status')}")

        except stripe.error.StripeError as e:
            logger.error(f"Stripe API error for customer {customer_id}: {str(e)}")
            df_users.at[index, 'active'] = False
        except Exception as e:
            logger.error(f"Unexpected error checking subscription for customer {customer_id}: {str(e)}")
            df_users.at[index, 'active'] = False

    df_users = df_users.drop(columns=['stripe_customer_id'])

    update_isactive_in_users(session, df_users, logger)

    logger.info("Completed updating active subscription statuses.")