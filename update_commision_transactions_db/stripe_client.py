import stripe
import pandas as pd
from typing import Optional

from resources.config import Config

def get_data_as_df(logger, customer_id: Optional[str] = None) -> pd.DataFrame:
    """
    Retrieve payment-related data for a Stripe customer and return it as a DataFrame.

    Args:
        customer_id (str, optional): The Stripe customer ID (e.g., 'cus_Sg6HZ5yF4go4v1').
                                   If None, fetches data for all customers.

    Returns:
        pandas.DataFrame: A DataFrame containing customer payment data, including pre-discount amount.

    Raises:
        stripe.error.StripeError: If the Stripe API call fails.
        ValueError: If the customer_id is invalid or not found.
    """
    try:
        # Set Stripe API key (ensure Config.STRIPE_SECRET_KEY is defined)
        stripe.api_key = Config.STRIPE_SECRET_KEY

        # Initialize an empty list to store payment data
        payment_data = []

        if customer_id:
            # Fetch specific customer data
            try:
                customer = stripe.Customer.retrieve(customer_id)
            except stripe.error.InvalidRequestError as e:
                logger.error(f"Invalid customer ID {customer_id}: {str(e)}")
                raise ValueError(f"Customer ID {customer_id} not found or invalid")

            # Fetch charges (successful payments) for the customer
            charges = stripe.Charge.list(customer=customer_id)

            # Combine customer and payment data
            for charge in charges.auto_paging_iter():
                # Initialize pre-discount amount as the charge amount

                payment_info = {
                    'customer_id': customer.id,
                    'email': customer.email,
                    'charge_id': charge.id,
                    'amount': charge.amount / 100.0,
                    'currency': charge.currency.upper(),
                    'status': charge.status,
                    'disputed': charge.disputed,
                    'dispute': charge.dispute,
                    'refunded': charge.refunded,
                    'created': pd.to_datetime(charge.created, unit='s'),
                    'description': charge.description,
                    'payment_method': charge.payment_method_details.card.brand if charge.payment_method_details else None,
                    'last4': charge.payment_method_details.card.last4 if charge.payment_method_details else None
                }
                payment_data.append(payment_info)

            # If no charges, still include customer info
            if not payment_data:
                payment_data.append({
                    'customer_id': customer.id,
                    'email': customer.email,
                    'charge_id': None,
                    'amount': None,
                    'currency': None,
                    'status': None,
                    'disputed': None,
                    'dispute': None,
                    'refunded': None,
                    'created': None,
                    'description': None,
                    'payment_method': None,
                    'last4': None
                })

        else:
            # Fetch all customers if no customer_id is provided
            customers = stripe.Customer.list()
            for customer in customers.auto_paging_iter():
                # Fetch charges for each customer
                charges = stripe.Charge.list(customer=customer.id)
                for charge in charges.auto_paging_iter():

                    payment_info = {
                        'customer_id': customer.id,
                        'email': customer.email,
                        'charge_id': charge.id,
                        'amount': charge.amount / 100.0,
                        'currency': charge.currency.upper(),
                        'status': charge.status,
                        'disputed': charge.disputed,
                        'dispute': charge.dispute,
                        'refunded': charge.refunded,
                        'created': pd.to_datetime(charge.created, unit='s'),
                        'description': charge.description,
                        'payment_method': charge.payment_method_details.card.brand if charge.payment_method_details else None,
                        'last4': charge.payment_method_details.card.last4 if charge.payment_method_details else None
                    }
                    payment_data.append(payment_info)

                # If no charges, still include customer info
                if not charges.data:
                    payment_data.append({
                        'customer_id': customer.id,
                        'email': customer.email,
                        'charge_id': None,
                        'amount': None,
                        'currency': None,
                        'status': None,
                        'disputed': None,
                        'dispute': None,
                        'refunded': None,
                        'created': None,
                        'description': None,
                        'payment_method': None,
                        'last4': None
                    })

        # Convert to DataFrame
        df = pd.DataFrame(payment_data)
        return df

    except stripe.error.StripeError as e:
        logger.error(f"Stripe API error: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise