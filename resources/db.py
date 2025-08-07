# stripe_db_tool/db.py
import uuid

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker, scoped_session
from resources.config import Config
import pandas as pd
from resources.models import Users, Referrals, CommissionTransactions

engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db_session():
    return scoped_session(SessionLocal)


def fetch_users(session):
    """
    Fetch users from the database with specific columns where referee is not None.

    Parameters:
    session (sqlalchemy.orm.session.Session): SQLAlchemy session for database queries.

    Returns:
    pd.DataFrame: DataFrame containing user_id, stripe_customer_id, and referee for users with a non-null referee.

    Raises:
    Exception: If an error occurs during query execution or DataFrame creation.
    """
    try:
        # Query users with non-null referee, selecting specific columns
        users_query = session.query(Users.user_id, Users.stripe_customer_id, Users.referee).filter(
            Users.referee != None)

        # Convert query results to list of dictionaries
        users_data = [
            {
                'user_id': str(user.user_id), # Convert UUID to string
                'stripe_customer_id': user.stripe_customer_id,
                'referee': str(user.referee) # Convert UUID to string, handle None explicitly
            }
            for user in users_query.all()
        ]

        # Create DataFrame
        users_df = pd.DataFrame(users_data)

        # Handle empty result
        if users_data:
            return users_df
        else:
            # Return empty DataFrame with correct columns
            return pd.DataFrame(columns=['user_id', 'stripe_customer_id', 'referee'])

    except Exception as e:
        raise ValueError(f"Error fetching users: {str(e)}")


def fetch_commission_rates(session):
    """
    Fetch user_id and commission from the referrals table in the database.

    Parameters:
    session (sqlalchemy.orm.session.Session): SQLAlchemy session for database queries.

    Returns:
    pd.DataFrame: DataFrame containing user_id and commission for all records in the referrals table.

    Raises:
    Exception: If an error occurs during query execution or DataFrame creation.
    """
    try:
        # Query referrals table, selecting user_id and commission columns
        referrals_query = session.query(Referrals.user_id, Referrals.commission)

        # Convert query results to list of dictionaries
        referrals_data = [
            {
                'user_id': str(referral.user_id),  # Convert UUID to string
                'commission': referral.commission
            }
            for referral in referrals_query.all()
        ]

        # Create DataFrame
        referrals_df = pd.DataFrame(referrals_data)

        # Handle empty result
        if referrals_data:
            return referrals_df
        else:
            # Return empty DataFrame with correct columns
            return pd.DataFrame(columns=['user_id', 'commission'])

    except Exception as e:
        raise ValueError(f"Error fetching commission rates: {str(e)}")


def write_df_to_CommissionTransactions(session, df):
    """
    Write a pandas DataFrame to the commission_transactions table, handling PK conflicts
    by updating only differing columns. Columns not in the DataFrame are not modified.

    Parameters:
    session (sqlalchemy.orm.session.Session): SQLAlchemy session for database operations.
    df (pd.DataFrame): DataFrame with data to write, containing a subset of table columns.

    Returns:
    dict: Summary of operations (e.g., {'inserted': n, 'updated': m, 'errors': k}).

    Raises:
    ValueError: If the DataFrame is missing 'charge_id' or contains invalid columns.
    """

    # Get table columns from the model
    table_columns = {c.name for c in CommissionTransactions.__table__.columns}
    df_columns = set(df.columns)
    invalid_columns = df_columns - table_columns
    if invalid_columns:
        raise ValueError(f"DataFrame contains invalid columns: {invalid_columns}")

    # Track operations
    result = {'inserted': 0, 'updated': 0, 'errors': 0}

    try:
        for _, row in df.iterrows():
            # Convert row to dictionary and handle UUID and datetime types
            row_dict = row.to_dict()
            for key, value in row_dict.items():
                if isinstance(value, str) and key in {'user_id', 'referee'}:
                    try:
                        row_dict[key] = uuid.UUID(value)
                    except (ValueError, TypeError):
                        row_dict[key] = None
                elif isinstance(value, pd.Timestamp):
                    row_dict[key] = value.to_pydatetime()
                elif pd.isna(value):
                    row_dict[key] = None

            # Check if record exists using ORM mapping
            existing = session.execute(
                select(CommissionTransactions).where(CommissionTransactions.charge_id == row_dict['charge_id'])
            ).scalar_one_or_none()  # This needs adjustment to return the full object

            # Corrected: Use .one_or_none() to get the full model instance
            existing_query = select(CommissionTransactions).where(CommissionTransactions.charge_id == row_dict['charge_id'])
            existing = session.execute(existing_query).one_or_none()

            if existing:
                # Compare existing record with DataFrame row
                updates = {
                    col: row_dict[col]
                    for col in df_columns
                    if col != 'charge_id' and getattr(existing[0], col) != row_dict.get(col)  # Access the model instance
                }
                if updates:
                    session.execute(
                        CommissionTransactions.__table__.update()
                        .where(CommissionTransactions.charge_id == row_dict['charge_id'])
                        .values(**updates)
                    )
                    result['updated'] += 1
            else:
                # Insert new record with only DataFrame columns
                insert_data = {
                    col: row_dict.get(col)
                    for col in df_columns
                }
                session.add(CommissionTransactions(**insert_data))
                result['inserted'] += 1

        # Commit the transaction
        session.commit()

    except Exception as e:
        session.rollback()
        result['errors'] += 1
        raise ValueError(f"Error writing DataFrame to database: {str(e)}")

    return result


def update_isactive_in_users(session, df, logger):
    """
    Update the 'isactive' column in the users table based on the provided DataFrame.

    Parameters:
    session (sqlalchemy.orm.session.Session): SQLAlchemy session for database operations.
    df (pd.DataFrame): DataFrame with 'user_id' (str) and 'active' (bool) columns.
    logger (GcpLogger): Logger instance for logging operations.

    Returns:
    dict: Summary of operations (e.g., {'updated': n, 'skipped': m, 'errors': k}).

    Raises:
    ValueError: If the DataFrame is missing required columns or contains invalid data.
    """
    required_columns = {'user_id', 'active'}
    if not required_columns.issubset(df.columns):
        raise ValueError(f"DataFrame is missing required columns: {required_columns - set(df.columns)}")

    # Track operations
    result = {'updated': 0, 'skipped': 0, 'errors': 0}

    logger.info("Starting update of 'isactive' in users table.")

    try:
        for _, row in df.iterrows():
            try:
                user_id_str = row['user_id']
                active_status = row['active']

                # Validate and convert user_id to UUID
                try:
                    user_id_uuid = uuid.UUID(user_id_str)
                except (ValueError, TypeError):
                    logger.warning(f"Invalid user_id format: {user_id_str}. Skipping.")
                    result['errors'] += 1
                    continue

                # Check if the user exists
                existing_query = select(Users).where(Users.user_id == user_id_uuid)
                existing = session.execute(existing_query).scalar_one_or_none()

                if existing:
                    # Update only if the status differs
                    if existing.isactive != active_status:
                        session.execute(
                            Users.__table__.update()
                            .where(Users.user_id == user_id_uuid)
                            .values(isactive=active_status)
                        )
                        result['updated'] += 1
                        logger.debug(f"Updated isactive to {active_status} for user_id: {user_id_str}.")
                    else:
                        result['skipped'] += 1
                        logger.debug(f"No change needed for user_id: {user_id_str}.")
                else:
                    logger.warning(f"User not found for user_id: {user_id_str}. Skipping.")
                    result['skipped'] += 1
            except Exception as e:
                logger.error(f"Error processing row for user_id {user_id_str}: {str(e)}")
                result['errors'] += 1

        # Commit the transaction
        session.commit()
        logger.info(f"Completed update: {result}")
    except Exception as e:
        session.rollback()
        logger.error(f"Transaction rollback due to error: {str(e)}")
        raise ValueError(f"Error updating isactive in users table: {str(e)}")

    return result


def read_CommissionTransactions_to_df(session, logger):
    """
    Read all data from the commission_transactions table into a pandas DataFrame.

    Parameters:
    session (sqlalchemy.orm.session.Session): SQLAlchemy session for database operations.
    logger: Logger object for logging information and errors.

    Returns:
    pd.DataFrame: DataFrame containing all data from the table with column names matching the table schema.

    Raises:
    ValueError: If there is an error reading from the database.
    """
    try:
        # Construct the SELECT statement using the ORM model
        stmt = select(CommissionTransactions)

        # Execute the query and load results into a DataFrame
        df = pd.read_sql(stmt, session.connection())

        logger.info(f"Successfully read {len(df)} rows from commission_transactions table.")

        return df
    except Exception as e:
        logger.error(f"Error reading from database: {str(e)}")
        raise ValueError(f"Error reading from database: {str(e)}")