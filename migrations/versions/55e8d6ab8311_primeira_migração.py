"""primeira migração

Revision ID: 55e8d6ab8311
Revises: 531d77b27108
Create Date: 2025-06-17 00:18:44.433969

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '55e8d6ab8311'
down_revision = '531d77b27108'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('daily_analytics',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('restaurant_id', sa.Integer(), nullable=True),
    sa.Column('date', sa.Date(), nullable=False),
    sa.Column('total_visits', sa.Integer(), nullable=True),
    sa.Column('total_item_views', sa.Integer(), nullable=True),
    sa.Column('total_reservations', sa.Integer(), nullable=True),
    sa.Column('total_people', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['restaurant_id'], ['restaurant.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('daily_analytics')
    # ### end Alembic commands ###
