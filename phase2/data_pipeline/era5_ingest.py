from utils.logger import get_logger

logger = get_logger()

def fetch_data():
    logger.info("Dry-run: fetching ERA5 data...")
    return {"data": "era5_dummy"}
