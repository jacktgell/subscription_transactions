import pandas as pd

from resources.db import write_df_to_CommissionTransactions, fetch_commission_rates, fetch_users
from update_commision_transactions_db.stripe_client import get_data_as_df


def update_commision_transactions_df(session, logger):

    logger.info("Starting update of commission transactions.")

    df_users = fetch_users(session)
    logger.debug(f"Fetched {len(df_users)} users.")

    commission_df = fetch_commission_rates(session)
    logger.debug(f"Fetched {len(commission_df)} commission rates.")

    columns = [
        'user_id', 'referee', 'customer_id', 'email', 'charge_id', 'amount', 'currency', 'status',
        'disputed', 'dispute', 'refunded', 'created', 'description', 'payment_method', 'last4'
    ]
    referals_df = pd.DataFrame(columns=columns)

    for index, user_row in df_users.iterrows():
        try:
            if user_row['stripe_customer_id']:
                df_payments = get_data_as_df(logger, user_row['stripe_customer_id'])
                df_payments['user_id'] = user_row['user_id']
                df_payments['referee'] = user_row['referee']
                referals_df = pd.concat([referals_df, df_payments], ignore_index=True)
                logger.debug(f"Processed payments for user {user_row['user_id']} with {len(df_payments)} entries.")
        except Exception as e:
            logger.error(f"Error fetching payments for user {user_row.get('user_id', 'unknown')}: {str(e)}")
            raise ValueError(f"Error fetching users: {str(e)}")

    logger.info(f"Collected {len(referals_df)} referral payments entries.")

    referals_df['matures_on'] = referals_df['created'] + pd.Timedelta(days=90)
    logger.debug("Added 'matures_on' column to referrals DataFrame.")

    for index, user_row in commission_df.iterrows():
        # Create a mask for rows where referee matches user_row['user_id']
        mask = referals_df['referee'] == user_row['user_id']

        # Further filter to exclude rows with disputes or refunds
        valid_commission_mask = mask & (referals_df['dispute'].isna()) & (referals_df['refunded'] != True)

        referals_df.loc[valid_commission_mask, 'commission_amount'] = (
                referals_df.loc[valid_commission_mask, 'amount'] * user_row['commission']
        )

        # Set commission_amount to 0.0 for disputed or refunded rows in the matched subset
        invalid_commission_mask = mask & ((referals_df['dispute'].notna()) | (referals_df['refunded'] == True) |
                    (referals_df['status'] != 'succeeded'))
        referals_df.loc[invalid_commission_mask, 'commission_amount'] = 0.0

        logger.debug(f"Calculated commissions for referee {user_row['user_id']}.")

    referals_df['disputed'] = referals_df['disputed'].astype(bool)
    referals_df['refunded'] = referals_df['refunded'].astype(bool)
    referals_df = referals_df[referals_df['charge_id'].notna()]

    logger.info("Writing updated DataFrame to CommissionTransactions.")
    write_df_to_CommissionTransactions(session, referals_df)

    logger.info("Completed update of commission transactions.")