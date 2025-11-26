"""add forecast tables

Revision ID: 004
Revises: 003
Create Date: 2025-11-24

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade():
    # Create forecasts table
    op.create_table(
        'forecasts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('forecast_date', sa.Date(), nullable=False),
        sa.Column('target_date', sa.Date(), nullable=False),
        sa.Column('horizon_months', sa.Integer(), nullable=False),
        sa.Column('trigger_type', sa.String(length=50), nullable=False),
        sa.Column('probability', sa.Numeric(precision=5, scale=4), nullable=False),
        sa.Column('confidence_lower', sa.Numeric(precision=5, scale=4), nullable=False),
        sa.Column('confidence_upper', sa.Numeric(precision=5, scale=4), nullable=False),
        sa.Column('model_version', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('forecast_date', 'target_date', 'trigger_type', name='uq_forecast_date_target_type')
    )
    
    # Create indexes for forecasts
    op.create_index('idx_forecasts_created', 'forecasts', ['created_at'])
    op.create_index('idx_forecasts_probability', 'forecasts', ['probability'])
    op.create_index('idx_forecasts_target', 'forecasts', ['target_date', 'trigger_type'])
    op.create_index(op.f('ix_forecasts_forecast_date'), 'forecasts', ['forecast_date'])
    op.create_index(op.f('ix_forecasts_id'), 'forecasts', ['id'])
    op.create_index(op.f('ix_forecasts_target_date'), 'forecasts', ['target_date'])
    op.create_index(op.f('ix_forecasts_trigger_type'), 'forecasts', ['trigger_type'])

    # Create forecast_recommendations table
    op.create_table(
        'forecast_recommendations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('forecast_id', sa.Integer(), nullable=False),
        sa.Column('recommendation_text', sa.String(), nullable=False),
        sa.Column('priority', sa.String(length=20), nullable=False),
        sa.Column('action_timeline', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['forecast_id'], ['forecasts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for forecast_recommendations
    op.create_index(op.f('ix_forecast_recommendations_forecast_id'), 'forecast_recommendations', ['forecast_id'])
    op.create_index(op.f('ix_forecast_recommendations_id'), 'forecast_recommendations', ['id'])

    # Create forecast_validation table
    op.create_table(
        'forecast_validation',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('forecast_id', sa.Integer(), nullable=False),
        sa.Column('actual_trigger_id', sa.Integer(), nullable=True),
        sa.Column('was_correct', sa.Integer(), nullable=False),
        sa.Column('probability_error', sa.Numeric(precision=5, scale=4), nullable=True),
        sa.Column('brier_score', sa.Numeric(precision=5, scale=4), nullable=True),
        sa.Column('validated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['actual_trigger_id'], ['trigger_events.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['forecast_id'], ['forecasts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for forecast_validation
    op.create_index('idx_validation_forecast', 'forecast_validation', ['forecast_id'])
    op.create_index('idx_validation_trigger', 'forecast_validation', ['actual_trigger_id'])
    op.create_index(op.f('ix_forecast_validation_id'), 'forecast_validation', ['id'])


def downgrade():
    # Drop tables in reverse order (due to foreign key constraints)
    op.drop_index(op.f('ix_forecast_validation_id'), table_name='forecast_validation')
    op.drop_index('idx_validation_trigger', table_name='forecast_validation')
    op.drop_index('idx_validation_forecast', table_name='forecast_validation')
    op.drop_table('forecast_validation')
    
    op.drop_index(op.f('ix_forecast_recommendations_id'), table_name='forecast_recommendations')
    op.drop_index(op.f('ix_forecast_recommendations_forecast_id'), table_name='forecast_recommendations')
    op.drop_table('forecast_recommendations')
    
    op.drop_index(op.f('ix_forecasts_trigger_type'), table_name='forecasts')
    op.drop_index(op.f('ix_forecasts_target_date'), table_name='forecasts')
    op.drop_index(op.f('ix_forecasts_id'), table_name='forecasts')
    op.drop_index(op.f('ix_forecasts_forecast_date'), table_name='forecasts')
    op.drop_index('idx_forecasts_target', table_name='forecasts')
    op.drop_index('idx_forecasts_probability', table_name='forecasts')
    op.drop_index('idx_forecasts_created', table_name='forecasts')
    op.drop_table('forecasts')
