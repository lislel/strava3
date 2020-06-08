"""added oauth info

Revision ID: e1dc65927ddf
Revises: 99aef733233a
Create Date: 2020-06-08 19:40:06.899671

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e1dc65927ddf'
down_revision = '99aef733233a'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('user', sa.Column('access_token', sa.String(length=128), nullable=True))
    op.add_column('user', sa.Column('expires_at', sa.Integer(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('user', 'expires_at')
    op.drop_column('user', 'access_token')
    # ### end Alembic commands ###
