import os
import json
import pandas as pd
from google.cloud import bigquery, secretmanager
import tempfile
import streamlit as st
from google.oauth2 import service_account
from google.api_core import retry
from pathlib import Path

# register json
# os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "auth/frf_gcp.json"


class GCPManager:
    def __init__(self, project_id="933479348828"):
        """Initialize GCP Manager with credentials"""
        self.project_id = project_id
        self.credentials = None
        self.setup_credentials()

    def setup_credentials(self):
        """Setup GCP credentials with multiple fallback options"""
        errors = []

        # Try all credential sources
        try:
            # 1. Check environment variable
            if self._try_environment_credentials():
                return
            errors.append("Environment credentials not found")

            # 2. Check Streamlit secrets
            if self._try_streamlit_secrets():
                return
            errors.append("Streamlit secrets not found")

            # 3. Check local credentials file
            if self._try_local_credentials():
                return
            errors.append("Local credentials not found")

            # 4. Try Secret Manager with default credentials
            if self._try_secret_manager():
                return
            errors.append("Secret Manager access failed")

            # If all attempts fail, raise detailed error
            raise Exception("\n".join(errors))

        except Exception as e:
            self._handle_setup_error(e, errors)

    def _try_environment_credentials(self):
        """Try to use credentials from environment variable"""
        if "GOOGLE_APPLICATION_CREDENTIALS" in os.environ:
            try:
                credentials = service_account.Credentials.from_service_account_file(
                    os.environ["GOOGLE_APPLICATION_CREDENTIALS"],
                    scopes=[
                        "https://www.googleapis.com/auth/bigquery",
                        "https://www.googleapis.com/auth/drive.readonly",
                    ],
                )
                self.credentials = credentials
                return True
            except Exception:
                return False
        return False

    def _try_streamlit_secrets(self):
        """Try to get credentials from Streamlit secrets"""
        try:
            if hasattr(st.secrets, "gcp_service_account"):
                credentials_dict = st.secrets.gcp_service_account
                credentials = service_account.Credentials.from_service_account_info(
                    credentials_dict,
                    scopes=[
                        "https://www.googleapis.com/auth/bigquery",
                        "https://www.googleapis.com/auth/drive.readonly",
                    ],
                )
                self.credentials = credentials
                self._setup_temp_credentials(credentials_dict)
                return True
        except Exception:
            return False
        return False

    def _try_local_credentials(self):
        """Try to find credentials in common local paths"""
        possible_paths = [
            Path.home() / ".config/gcloud/application_default_credentials.json",
            Path.home() / ".config/gcloud/credentials.json",
            Path("credentials.json"),
            Path("service-account.json"),
        ]

        for path in possible_paths:
            try:
                if path.exists():
                    credentials = service_account.Credentials.from_service_account_file(
                        str(path), scopes=["https://www.googleapis.com/auth/bigquery"]
                    )
                    self.credentials = credentials
                    return True
            except Exception:
                continue
        return False

    @retry.Retry(predicate=retry.if_exception_type(Exception))
    def _try_secret_manager(self):
        """Try to get credentials from Secret Manager"""
        try:
            # Try to use default credentials for initial Secret Manager access
            client = secretmanager.SecretManagerServiceClient()
            name = f"projects/{self.project_id}/secrets/sa-secret/versions/latest"
            response = client.access_secret_version(request={"name": name})
            credentials_dict = json.loads(response.payload.data.decode("UTF-8"))

            credentials = service_account.Credentials.from_service_account_info(
                credentials_dict, scopes=["https://www.googleapis.com/auth/bigquery"]
            )
            self.credentials = credentials
            self._setup_temp_credentials(credentials_dict)
            return True
        except Exception as e:
            st.warning(f"Could not access Secret Manager: {str(e)}")
            return False

    def _setup_temp_credentials(self, credentials_dict):
        """Setup temporary credentials file"""
        try:
            temp_cred_path = os.path.join(
                tempfile.gettempdir(), "temp_credentials.json"
            )
            with open(temp_cred_path, "w") as f:
                json.dump(credentials_dict, f)
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = temp_cred_path
        except Exception as e:
            st.warning(f"Failed to setup temporary credentials: {str(e)}")

    def _handle_setup_error(self, error, errors):
        """Handle credential setup errors with detailed feedback"""
        error_message = "Failed to setup GCP credentials.\n\nDetailed errors:"
        for err in errors:
            error_message += f"\n- {err}"

        st.error(error_message)
        st.info(
            "Please ensure proper credentials are configured in one of the following ways:"
        )
        st.info("1. Set GOOGLE_APPLICATION_CREDENTIALS environment variable")
        st.info("2. Configure credentials in Streamlit secrets.toml")
        st.info("3. Place credentials file in ~/.config/gcloud/")
        st.info("4. Set up Secret Manager with service account credentials")
        raise Exception("No valid credentials found") from error

    @retry.Retry()
    def fetch_allowed_emails(self):
        """Fetch allowed emails from BigQuery with retry logic"""
        if not self.credentials:
            raise Exception("Credentials not properly initialized")

        try:
            # Initialize BigQuery client
            client = bigquery.Client(
                project=self.project_id, credentials=self.credentials
            )

            # Define the query to fetch emails
            query = """
                SELECT email
                FROM `frf-chatbot.auth.allowed_emails`
            """

            # Execute query and convert to DataFrame
            df = client.query(query).to_dataframe()

            return df["email"].tolist()

        except Exception as e:
            st.error(f"Error fetching allowed emails from BigQuery: {str(e)}")
            return []

    def cleanup(self):
        """Cleanup temporary files"""
        temp_cred_path = os.path.join(tempfile.gettempdir(), "temp_credentials.json")
        if os.path.exists(temp_cred_path):
            os.remove(temp_cred_path)
