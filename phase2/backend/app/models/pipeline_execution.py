"""
Pipeline execution tracking models

Tracks automated pipeline runs, data quality metrics, and source ingestion status.
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, ARRAY, Numeric, Date, ForeignKey, JSON
from sqlalchemy.sql import func
from app.core.database import Base


class PipelineExecution(Base):
    """Track pipeline execution runs"""
    __tablename__ = "pipeline_executions"
    
    id = Column(String, primary_key=True)  # UUID
    execution_type = Column(String, nullable=False)  # 'scheduled' | 'manual'
    status = Column(String, nullable=False)  # 'running' | 'completed' | 'failed'
    started_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    
    # Ingestion metrics
    records_fetched = Column(Integer, default=0)
    records_stored = Column(Integer, default=0)
    sources_succeeded = Column(ARRAY(String), default=[])
    sources_failed = Column(ARRAY(String), default=[])
    
    # Forecast metrics
    forecasts_generated = Column(Integer, default=0)
    recommendations_created = Column(Integer, default=0)
    
    # Error tracking
    error_message = Column(Text, nullable=True)
    error_traceback = Column(Text, nullable=True)
    
    def __repr__(self):
        return f"<PipelineExecution(id='{self.id}', status='{self.status}', type='{self.execution_type}')>"


class DataQualityMetrics(Base):
    """Track data quality metrics per source"""
    __tablename__ = "data_quality_metrics"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    execution_id = Column(String, ForeignKey("pipeline_executions.id", ondelete="CASCADE"), nullable=False)
    source = Column(String, nullable=False)
    checked_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    
    # Quality metrics
    total_records = Column(Integer, nullable=False)
    missing_values_count = Column(Integer, default=0)
    out_of_range_count = Column(Integer, default=0)
    data_gaps_count = Column(Integer, default=0)
    quality_score = Column(Numeric(3, 2), nullable=True)  # 0.00 to 1.00
    
    # Anomalies
    anomalies = Column(JSON, nullable=True)  # List of detected anomalies
    
    def __repr__(self):
        return f"<DataQualityMetrics(source='{self.source}', score={self.quality_score})>"


class SourceIngestionTracking(Base):
    """Track last successful ingestion date per source"""
    __tablename__ = "source_ingestion_tracking"
    
    source = Column(String, primary_key=True)
    last_successful_date = Column(Date, nullable=False)
    last_execution_id = Column(String, ForeignKey("pipeline_executions.id", ondelete="SET NULL"), nullable=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<SourceIngestionTracking(source='{self.source}', last_date={self.last_successful_date})>"
