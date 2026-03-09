"""
Google Earth Engine Authentication Utility

Supports two auth paths — both Docker-friendly:

1. Service Account (preferred for servers / Docker):
   Set in .env:
     GEE_SERVICE_ACCOUNT=your-sa@project.iam.gserviceaccount.com
     GEE_PRIVATE_KEY_FILE=/app/secrets/gee-service-account.json

   Mount the JSON key in docker-compose:
     volumes:
       - ./secrets/gee-service-account.json:/app/secrets/gee-service-account.json:ro

2. User credentials (local dev only):
   Run once on the machine:
     earthengine authenticate
   This creates ~/.config/earthengine/credentials which is already
   volume-mounted in docker-compose.dev.yml.

No interactive browser session is required with Option 1.
"""
import os
import logging

logger = logging.getLogger(__name__)


def initialize_gee(project_id: str = "climate-prediction-using-ml") -> bool:
    """
    Initialize Google Earth Engine using service account or user credentials.

    Args:
        project_id: GCP project ID with Earth Engine API enabled.

    Returns:
        True if initialization succeeded, False otherwise.
    """
    try:
        import ee
    except ImportError:
        logger.warning("earthengine-api not installed. Run: pip install earthengine-api")
        return False

    try:
        from dotenv import load_dotenv
        load_dotenv()

        project_id = os.getenv("GOOGLE_CLOUD_PROJECT", project_id)
        service_account = os.getenv("GEE_SERVICE_ACCOUNT")
        key_file = os.getenv("GEE_PRIVATE_KEY_FILE")

        # Path 1: Service account credentials (Docker-friendly, no browser)
        if service_account and key_file:
            if not os.path.exists(key_file):
                logger.error(
                    f"GEE_PRIVATE_KEY_FILE={key_file} not found. "
                    f"Mount the service account JSON key into the container."
                )
                return False
            credentials = ee.ServiceAccountCredentials(service_account, key_file)
            ee.Initialize(credentials=credentials, project=project_id)
            logger.info(f"GEE initialized via service account: {service_account}")
            return True

        # Path 2: User/ADC credentials (~/.config/earthengine/credentials)
        ee.Initialize(project=project_id)
        logger.info(f"GEE initialized via user credentials (project: {project_id})")
        return True

    except Exception as e:
        logger.warning(f"GEE initialization failed: {e}")
        if not os.getenv("GEE_SERVICE_ACCOUNT"):
            logger.info(
                "To enable GEE in Docker without browser auth:\n"
                "  1. Create a GCP service account with Earth Engine API access\n"
                "  2. Download the JSON key to phase2/secrets/gee-service-account.json\n"
                "  3. Add to .env on the server:\n"
                "       GEE_SERVICE_ACCOUNT=<sa-email>\n"
                "       GEE_PRIVATE_KEY_FILE=/app/secrets/gee-service-account.json\n"
                "  4. Redeploy: ./scripts/deploy.sh shadow-run --update"
            )
        return False
