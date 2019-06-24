"""Added account table

Revision ID: e13042e34ee0
Revises: e6d94e9207ba
Create Date: 2019-06-19 00:59:37.524547

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e13042e34ee0'
down_revision = 'e6d94e9207ba'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('users', sa.Column('user', sa.String(length=20), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('users', 'user')
    # ### end Alembic commands ###
