"""
Entry point for Pipeline Monitoring Service

Exposes metrics and health check endpoints for pipeline monitoring.
"""
import os
import sys
import logging
from flask import Flask, jsonify, Response

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)


@app.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint
    
    Returns system health status including data freshness and pipeline state.
    """
    try:
        from app.core.database import SessionLocal
        from app.services.pipeline.monitoring import MonitoringService
        
        db = SessionLocal()
        try:
            monitoring = MonitoringService(db)
            health_status = monitoring.get_health_status()
            
            response = {
                'status': health_status.status,
                'last_execution': health_status.last_execution.isoformat() if health_status.last_execution else None,
                'data_freshness_days': health_status.data_freshness_days,
                'forecast_freshness_days': health_status.forecast_freshness_days,
                'failed_sources': health_status.failed_sources,
                'message': health_status.message
            }
            
            # Return appropriate HTTP status code
            status_code = 200
            if health_status.status == 'degraded':
                status_code = 200  # Still operational
            elif health_status.status == 'unhealthy':
                status_code = 503  # Service unavailable
            
            return jsonify(response), status_code
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Health check failed: {e}", exc_info=True)
        return jsonify({
            'status': 'unhealthy',
            'message': f'Health check error: {str(e)}'
        }), 503


@app.route('/metrics', methods=['GET'])
def metrics():
    """
    Prometheus metrics endpoint
    
    Returns pipeline metrics in Prometheus text format.
    """
    try:
        from app.core.database import SessionLocal
        from app.services.pipeline.monitoring import MonitoringService
        
        db = SessionLocal()
        try:
            monitoring = MonitoringService(db)
            metrics_dict = monitoring.get_metrics()
            
            # Format as Prometheus text
            prometheus_text = monitoring.format_prometheus_metrics(metrics_dict)
            
            return Response(prometheus_text, mimetype='text/plain')
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Metrics endpoint failed: {e}", exc_info=True)
        return Response(f"# Error: {str(e)}", mimetype='text/plain'), 500


@app.route('/status', methods=['GET'])
def status():
    """
    Pipeline status endpoint
    
    Returns current pipeline execution status and recent history.
    """
    try:
        from app.core.database import SessionLocal
        from app.models.pipeline_execution import PipelineExecution
        from sqlalchemy import desc
        
        db = SessionLocal()
        try:
            # Get last 10 executions
            executions = db.query(PipelineExecution).order_by(
                desc(PipelineExecution.started_at)
            ).limit(10).all()
            
            history = []
            for execution in executions:
                history.append({
                    'execution_id': execution.id,
                    'execution_type': execution.execution_type,
                    'status': execution.status,
                    'started_at': execution.started_at.isoformat(),
                    'completed_at': execution.completed_at.isoformat() if execution.completed_at else None,
                    'duration_seconds': execution.duration_seconds,
                    'records_stored': execution.records_stored,
                    'forecasts_generated': execution.forecasts_generated,
                    'sources_succeeded': execution.sources_succeeded,
                    'sources_failed': execution.sources_failed,
                    'error_message': execution.error_message
                })
            
            return jsonify({
                'current_status': executions[0].status if executions else 'idle',
                'execution_history': history
            })
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Status endpoint failed: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


def main():
    """Main entry point for monitoring service"""
    logger.info("Starting Pipeline Monitoring Service")
    
    # Load configuration
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        logger.error("DATABASE_URL environment variable not set")
        sys.exit(1)
    
    metrics_port = int(os.getenv('MONITORING_METRICS_PORT', '9090'))
    health_port = int(os.getenv('MONITORING_HEALTH_PORT', '8080'))
    
    logger.info(f"Configuration:")
    logger.info(f"  Metrics port: {metrics_port}")
    logger.info(f"  Health check port: {health_port}")
    
    # Run Flask app
    # Note: In production, use a proper WSGI server like gunicorn
    # For now, using Flask's built-in server for simplicity
    try:
        # Use health_port for all endpoints
        logger.info(f"Starting monitoring service on port {health_port}")
        app.run(host='0.0.0.0', port=health_port, debug=False)
        
    except Exception as e:
        logger.error(f"Monitoring service failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
