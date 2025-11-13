from utils.logger import get_logger

logger = get_logger()

def fetch_data():
    logger.info("Dry-run: fetching NASA POWER data...")
    # Return dummy dataframe placeholder
    return {"data": "nasa_dummy"}
