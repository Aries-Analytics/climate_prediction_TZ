"""Initial schema

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create users table
    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(length=50), nullable=False),
        sa.Column('email', sa.String(length=100), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('role', sa.String(length=20), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('last_login', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_users_username', 'users', ['username'], unique=True)
    op.create_index('idx_users_email', 'users', ['email'], unique=True)

    # Create locations table
    op.create_table('locations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('latitude', sa.Float(), nullable=False),
        sa.Column('longitude', sa.Float(), nullable=False),
        sa.Column('region', sa.String(length=50), nullable=True),
        sa.Column('population', sa.Integer(), nullable=True),
        sa.Column('climate_zone', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_locations_name', 'locations', ['name'], unique=True)

    # Create climate_data table
    op.create_table('climate_data',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('location_lat', sa.Numeric(10, 6), nullable=True),
        sa.Column('location_lon', sa.Numeric(10, 6), nullable=True),
        sa.Column('temperature_avg', sa.Numeric(5, 2), nullable=True),
        sa.Column('rainfall_mm', sa.Numeric(7, 2), nullable=True),
        sa.Column('ndvi', sa.Numeric(4, 3), nullable=True),
        sa.Column('enso_index', sa.Numeric(5, 3), nullable=True),
        sa.Column('iod_index', sa.Numeric(5, 3), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_climate_date', 'climate_data', ['date'])

    # Create trigger_events table
    op.create_table('trigger_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('trigger_type', sa.String(length=50), nullable=False),
        sa.Column('confidence', sa.Numeric(4, 3), nullable=True),
        sa.Column('severity', sa.Numeric(4, 3), nullable=True),
        sa.Column('payout_amount', sa.Numeric(10, 2), nullable=True),
        sa.Column('location_lat', sa.Numeric(10, 6), nullable=True),
        sa.Column('location_lon', sa.Numeric(10, 6), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_trigger_date', 'trigger_events', ['date'])
    op.create_index('idx_trigger_type', 'trigger_events', ['trigger_type'])

    # Create model_metrics table
    op.create_table('model_metrics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('model_name', sa.String(length=50), nullable=False),
        sa.Column('experiment_id', sa.String(length=100), nullable=True),
        sa.Column('r2_score', sa.Numeric(6, 4), nullable=True),
        sa.Column('rmse', sa.Numeric(10, 4), nullable=True),
        sa.Column('mae', sa.Numeric(10, 4), nullable=True),
        sa.Column('mape', sa.Numeric(6, 4), nullable=True),
        sa.Column('training_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('data_start_date', sa.Date(), nullable=True),
        sa.Column('data_end_date', sa.Date(), nullable=True),
        sa.Column('hyperparameters', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_metrics_model', 'model_metrics', ['model_name'])
    op.create_index('idx_metrics_training_date', 'model_metrics', ['training_date'])

    # Create model_predictions table
    op.create_table('model_predictions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('model_name', sa.String(length=50), nullable=False),
        sa.Column('prediction_date', sa.Date(), nullable=False),
        sa.Column('target_date', sa.Date(), nullable=False),
        sa.Column('predicted_value', sa.Numeric(10, 4), nullable=True),
        sa.Column('actual_value', sa.Numeric(10, 4), nullable=True),
        sa.Column('confidence_lower', sa.Numeric(10, 4), nullable=True),
        sa.Column('confidence_upper', sa.Numeric(10, 4), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_predictions_model', 'model_predictions', ['model_name'])
    op.create_index('idx_predictions_target_date', 'model_predictions', ['target_date'])

    # Create audit_logs table
    op.create_table('audit_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('resource', sa.String(length=100), nullable=True),
        sa.Column('details', sa.JSON(), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_audit_user', 'audit_logs', ['user_id'])
    op.create_index('idx_audit_action', 'audit_logs', ['action'])
    op.create_index('idx_audit_created', 'audit_logs', ['created_at'])


def downgrade() -> None:
    op.drop_table('locations')
    op.drop_table('audit_logs')
    op.drop_table('model_predictions')
    op.drop_table('model_metrics')
    op.drop_table('trigger_events')
    op.drop_table('climate_data')
    op.drop_table('users')
