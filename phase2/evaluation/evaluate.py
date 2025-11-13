from utils.logger import get_logger

logger = get_logger()

def generate_report(model, metrics):
    logger.info(f"Dry-run: evaluating model {model} with metrics {metrics}")
