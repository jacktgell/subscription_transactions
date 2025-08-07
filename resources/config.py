# stripe_db_tool/config.py
from dotenv import load_dotenv
from google.cloud import secretmanager
from google.api_core.exceptions import GoogleAPIError
import os

load_dotenv()

def get_secret(secret_id, project_id):
    try:
        client = secretmanager.SecretManagerServiceClient()
        name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
        response = client.access_secret_version(request={"name": name})
        secret = response.payload.data.decode("UTF-8")
        print(f"Successfully fetched secret {secret_id}")
        return secret
    except GoogleAPIError as e:
        print(f"Error fetching secret {secret_id}: {str(e)}")
        raise

class Config:
    PROJECT_ID = os.getenv('PROJECT_ID')
    DB_SECRET_ID = os.getenv('DB_SECRET_ID')
    DB_USER = os.getenv('DB_USER')
    DB_HOST = os.getenv('DB_HOST')
    DB_PORT = os.getenv('DB_PORT')
    DB_NAME = os.getenv('DB_NAME')

    REDIS_HOST = os.getenv('REDIS_HOST')
    REDIS_PORT = os.getenv('REDIS_PORT')
    REDIS_DB = os.getenv('REDIS_DB')
    REDIS_PASSWORD = os.getenv('REDIS_PASSWORD')

    DB_PASSWORD = get_secret(DB_SECRET_ID, PROJECT_ID) if DB_SECRET_ID and PROJECT_ID else os.getenv('DB_PASSWORD')
    STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY')  # Use environment variable directly
    SQLALCHEMY_DATABASE_URI = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False