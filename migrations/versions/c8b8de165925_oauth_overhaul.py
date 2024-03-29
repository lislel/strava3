"""oauth overhaul

Revision ID: c8b8de165925
Revises: 941d40c2f486
Create Date: 2020-12-21 18:55:02.088002

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c8b8de165925'
down_revision = '941d40c2f486'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('user', sa.Column('code', sa.String(length=128), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('user', 'code')
    # ### end Alembic commands ###
