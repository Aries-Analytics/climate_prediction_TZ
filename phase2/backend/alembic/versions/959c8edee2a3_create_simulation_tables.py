"""create_simulation_tables

Revision ID: 959c8edee2a3
Revises: 0f6c61d64299
Create Date: 2026-01-21 18:27:39.059770

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '959c8edee2a3'
down_revision = '0f6c61d64299'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create simulation_runs table
    op.create_table(
        'simulation_runs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('location_id', sa.Integer(), nullable=False),
        sa.Column('location_name', sa.String(100), nullable=False),
        sa.Column('start_year', sa.Integer(), nullable=False),
        sa.Column('end_year', sa.Integer(), nullable=False),
        sa.Column('farmer_count', sa.Integer(), nullable=False),
        sa.Column('crop_type', sa.String(50), nullable=False),
        sa.Column('annual_premium_per_farmer', sa.Float()),
        sa.Column('drought_payout_rate', sa.Float()),
        sa.Column('flood_payout_rate', sa.Float()),
        sa.Column('crop_failure_payout_rate', sa.Float()),
        sa.Column('status', sa.String(20)),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('total_triggers', sa.Integer()),
        sa.Column('total_claims', sa.Integer()),
        sa.Column('total_premiums_collected', sa.Float()),
        sa.Column('total_payouts', sa.Float()),
        sa.Column('loss_ratio', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['location_id'], ['locations.id'], )
    )
    op.create_index('ix_simulation_runs_id', 'simulation_runs', ['id'])
    op.create_index('ix_simulation_runs_status', 'simulation_runs', ['status'])
    
    # Create simulated_farmers table
    op.create_table(
        'simulated_farmers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('simulation_id', sa.Integer(), nullable=False),
        sa.Column('farmer_code', sa.String(20), nullable=False),
        sa.Column('village', sa.String(100), nullable=False),
        sa.Column('hectares', sa.Float(), nullable=False),
        sa.Column('premium_paid', sa.Float(), nullable=False),
        sa.Column('coverage_amount', sa.Float(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['simulation_id'], ['simulation_runs.id'], )
    )
    op.create_index('ix_simulated_farmers_id', 'simulated_farmers', ['id'])
    
    # Create simulated_triggers table
    op.create_table(
        'simulated_triggers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('simulation_id', sa.Integer(), nullable=False),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('month', sa.Integer(), nullable=False),
        sa.Column('trigger_type', sa.String(50), nullable=False),
        sa.Column('trigger_date', sa.Date(), nullable=False),
        sa.Column('observed_value', sa.Float(), nullable=False),
        sa.Column('threshold_value', sa.Float(), nullable=False),
        sa.Column('deviation', sa.Float(), nullable=False),
        sa.Column('severity', sa.String(20), nullable=False),
        sa.Column('phenology_stage', sa.String(50), nullable=True),
        sa.Column('farmers_affected', sa.Integer()),
        sa.Column('payout_per_farmer', sa.Float()),
        sa.Column('total_payout', sa.Float()),
        sa.Column('external_validation', sa.Text(), nullable=True),
        sa.Column('validated', sa.String(10)),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['simulation_id'], ['simulation_runs.id'], )
    )
    op.create_index('ix_simulated_triggers_id', 'simulated_triggers', ['id'])
    
    # Create simulated_claims table
    op.create_table(
        'simulated_claims',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('simulation_id', sa.Integer(), nullable=False),
        sa.Column('farmer_id', sa.Integer(), nullable=False),
        sa.Column('trigger_id', sa.Integer(), nullable=False),
        sa.Column('claim_code', sa.String(30), nullable=False),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('trigger_type', sa.String(50), nullable=False),
        sa.Column('payout_amount', sa.Float(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['simulation_id'], ['simulation_runs.id'], ),
        sa.ForeignKeyConstraint(['farmer_id'], ['simulated_farmers.id'], ),
        sa.ForeignKeyConstraint(['trigger_id'], ['simulated_triggers.id'], )
    )
    op.create_index('ix_simulated_claims_id', 'simulated_claims', ['id'])


def downgrade() -> None:
    op.drop_table('simulated_claims')
    op.drop_table('simulated_triggers')
    op.drop_table('simulated_farmers')
    op.drop_table('simulation_runs')
