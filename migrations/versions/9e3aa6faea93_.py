"""empty message

Revision ID: 9e3aa6faea93
Revises: 
Create Date: 2018-12-06 17:54:01.654641

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9e3aa6faea93'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('user')
    op.drop_table('modbus_address')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('modbus_address',
    sa.Column('start_address', sa.TEXT(length=80), nullable=False),
    sa.Column('qty', sa.TEXT(length=80), nullable=True),
    sa.Column('function_code', sa.TEXT(length=80), nullable=True),
    sa.PrimaryKeyConstraint('start_address')
    )
    op.create_table('user',
    sa.Column('email', sa.VARCHAR(length=80), nullable=False),
    sa.Column('password', sa.VARCHAR(length=80), nullable=True),
    sa.PrimaryKeyConstraint('email'),
    sa.UniqueConstraint('email')
    )
    # ### end Alembic commands ###