from utils.logger import get_logger

logger = get_logger()

def run(features):
    logger.info("Dry-run: training model...")
    model = "dummy_model"
    metrics = {"accuracy": 1.0}
    return model, metrics
