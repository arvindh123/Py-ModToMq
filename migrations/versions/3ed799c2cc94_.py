"""empty message

Revision ID: 3ed799c2cc94
Revises: a3e42dce9813
Create Date: 2018-12-12 16:22:37.444241

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3ed799c2cc94'
down_revision = 'a3e42dce9813'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('write_mod_registers')
    op.drop_table('sub_mqtt_topics')
    op.drop_table('modbus_parameters')
    op.drop_table('all_status')
    op.drop_table('modbus_address')
    op.drop_table('pub_mqtt_topics')
    op.drop_table('mqtt_parameters')
    op.drop_table('user')
    op.drop_table('read_mod_registers')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('read_mod_registers',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('name', sa.VARCHAR(length=80), nullable=True),
    sa.Column('address', sa.INTEGER(), nullable=True),
    sa.Column('qty', sa.INTEGER(), nullable=True),
    sa.Column('unit', sa.INTEGER(), nullable=True),
    sa.Column('pub_topic_id', sa.INTEGER(), nullable=True),
    sa.ForeignKeyConstraint(['pub_topic_id'], ['pub_mqtt_topics.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('address'),
    sa.UniqueConstraint('name')
    )
    op.create_table('user',
    sa.Column('email', sa.VARCHAR(length=80), nullable=False),
    sa.Column('password', sa.VARCHAR(length=80), nullable=True),
    sa.PrimaryKeyConstraint('email'),
    sa.UniqueConstraint('email')
    )
    op.create_table('mqtt_parameters',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('mqtt_ip', sa.VARCHAR(length=80), nullable=True),
    sa.Column('mqtt_port', sa.INTEGER(), nullable=True),
    sa.Column('mqtt_user_name', sa.VARCHAR(length=80), nullable=True),
    sa.Column('mqtt_password', sa.VARCHAR(length=80), nullable=True),
    sa.Column('mqtt_access_token', sa.VARCHAR(length=80), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('mqtt_ip')
    )
    op.create_table('pub_mqtt_topics',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('topic', sa.VARCHAR(length=150), nullable=True),
    sa.Column('qos', sa.INTEGER(), nullable=True),
    sa.Column('retain', sa.BOOLEAN(), nullable=True),
    sa.CheckConstraint('retain IN (0, 1)'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('topic')
    )
    op.create_table('modbus_address',
    sa.Column('name', sa.VARCHAR(length=80), nullable=False),
    sa.Column('start_address', sa.VARCHAR(length=80), nullable=True),
    sa.Column('qty', sa.VARCHAR(length=80), nullable=True),
    sa.Column('function_code', sa.VARCHAR(length=80), nullable=True),
    sa.PrimaryKeyConstraint('name'),
    sa.UniqueConstraint('name')
    )
    op.create_table('all_status',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('mqtt_status', sa.VARCHAR(length=80), nullable=True),
    sa.Column('modbus_status', sa.VARCHAR(length=80), nullable=True),
    sa.Column('last_sent_data', sa.VARCHAR(length=80), nullable=True),
    sa.Column('last_sent_data_ts', sa.VARCHAR(length=80), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('modbus_parameters',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('modbus_ip', sa.VARCHAR(length=80), nullable=True),
    sa.Column('modbus_port', sa.INTEGER(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('modbus_ip')
    )
    op.create_table('sub_mqtt_topics',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('topic', sa.VARCHAR(length=150), nullable=True),
    sa.Column('qos', sa.INTEGER(), nullable=True),
    sa.Column('retain', sa.BOOLEAN(), nullable=True),
    sa.CheckConstraint('retain IN (0, 1)'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('topic')
    )
    op.create_table('write_mod_registers',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('address', sa.INTEGER(), nullable=True),
    sa.Column('qty', sa.INTEGER(), nullable=True),
    sa.Column('unit', sa.INTEGER(), nullable=True),
    sa.Column('sub_topic_id', sa.INTEGER(), nullable=True),
    sa.ForeignKeyConstraint(['sub_topic_id'], ['sub_mqtt_topics.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('address')
    )
    # ### end Alembic commands ###
