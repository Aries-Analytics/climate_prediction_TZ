"""add pipeline tracking tables

Revision ID: 005
Revises: 004
Create Date: 2024-11-26

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade():
    # Create pipeline_executions table
    op.create_table(
        'pipeline_executions',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('execution_type', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('duration_seconds', sa.Integer(), nullable=True),
        sa.Column('records_fetched', sa.Integer(), server_default='0'),
        sa.Column('records_stored', sa.Integer(), server_default='0'),
        sa.Column('sources_succeeded', postgresql.ARRAY(sa.String()), server_default='{}'),
        sa.Column('sources_failed', postgresql.ARRAY(sa.String()), server_default='{}'),
        sa.Column('forecasts_generated', sa.Integer(), server_default='0'),
        sa.Column('recommendations_created', sa.Integer(), server_default='0'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('error_traceback', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_pipeline_executions_status', 'pipeline_executions', ['status'])
    op.create_index('ix_pipeline_executions_started_at', 'pipeline_executions', ['started_at'])
    
    # Create data_quality_metrics table
    op.create_table(
        'data_quality_metrics',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('execution_id', sa.String(), nullable=False),
        sa.Column('source', sa.String(), nullable=False),
        sa.Column('checked_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('total_records', sa.Integer(), nullable=False),
        sa.Column('missing_values_count', sa.Integer(), server_default='0'),
        sa.Column('out_of_range_count', sa.Integer(), server_default='0'),
        sa.Column('data_gaps_count', sa.Integer(), server_default='0'),
        sa.Column('quality_score', sa.Numeric(3, 2), nullable=True),
        sa.Column('anomalies', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(['execution_id'], ['pipeline_executions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_data_quality_metrics_execution_id', 'data_quality_metrics', ['execution_id'])
    op.create_index('ix_data_quality_metrics_source', 'data_quality_metrics', ['source'])
    
    # Create source_ingestion_tracking table
    op.create_table(
        'source_ingestion_tracking',
        sa.Column('source', sa.String(), nullable=False),
        sa.Column('last_successful_date', sa.Date(), nullable=False),
        sa.Column('last_execution_id', sa.String(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['last_execution_id'], ['pipeline_executions.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('source')
    )


def downgrade():
    op.drop_table('source_ingestion_tracking')
    op.drop_table('data_quality_metrics')
    op.drop_table('pipeline_executions')
