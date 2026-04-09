"""add_music_media_types

Revision ID: c8a3f91b2e04
Revises: b1345f835923
Create Date: 2026-04-08 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c8a3f91b2e04"
down_revision: Union[str, None] = "b1345f835923"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add mbid column to MediaItem
    with op.batch_alter_table("MediaItem", schema=None) as batch_op:
        batch_op.add_column(sa.Column("mbid", sa.String(), nullable=True))

    # Create Artist table
    op.create_table(
        "Artist",
        sa.Column(
            "id",
            sa.Integer(),
            sa.ForeignKey("MediaItem.id", ondelete="CASCADE"),
            nullable=False,
            primary_key=True,
        ),
        sa.Column(
            "subscribed",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
        sa.Column("last_checked_at", sa.DateTime(), nullable=True),
    )

    # Create Album table
    op.create_table(
        "Album",
        sa.Column(
            "id",
            sa.Integer(),
            sa.ForeignKey("MediaItem.id", ondelete="CASCADE"),
            nullable=False,
            primary_key=True,
        ),
        sa.Column(
            "parent_id",
            sa.Integer(),
            sa.ForeignKey("Artist.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("label", sa.String(), nullable=True),
        sa.Column("total_tracks", sa.Integer(), nullable=True),
    )

    # Create Track table
    op.create_table(
        "Track",
        sa.Column(
            "id",
            sa.Integer(),
            sa.ForeignKey("MediaItem.id", ondelete="CASCADE"),
            nullable=False,
            primary_key=True,
        ),
        sa.Column(
            "parent_id",
            sa.Integer(),
            sa.ForeignKey("Album.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("track_number", sa.Integer(), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("isrc", sa.String(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("Track")
    op.drop_table("Album")
    op.drop_table("Artist")

    with op.batch_alter_table("MediaItem", schema=None) as batch_op:
        batch_op.drop_column("mbid")
