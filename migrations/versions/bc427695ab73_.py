"""empty message

Revision ID: bc427695ab73
Revises: 57753368c586
Create Date: 2019-07-26 23:27:55.813591

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'bc427695ab73'
down_revision = '57753368c586'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('transaction', sa.Column('ticket_qrode', sa.String(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('transaction', 'ticket_qrode')
    # ### end Alembic commands ###