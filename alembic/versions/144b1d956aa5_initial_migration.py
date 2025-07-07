"""Initial migration

Revision ID: 144b1d956aa5
Revises: 
Create Date: 2025-07-06 20:59:06.736532

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '144b1d956aa5'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create enum types only if they do not exist
    op.execute("""
    DO $$
    BEGIN
        IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'languageenum') THEN
            CREATE TYPE languageenum AS ENUM ('spanish', 'french', 'mandarin', 'japanese', 'german', 'italian');
        END IF;
    END$$;
    """)
    op.execute("""
    DO $$
    BEGIN
        IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'authproviderenum') THEN
            CREATE TYPE authproviderenum AS ENUM ('google', 'email', 'custom');
        END IF;
    END$$;
    """)
    
    # Create users table
    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('nickname', sa.String(length=100), nullable=True),
        sa.Column('target_language', postgresql.ENUM('spanish', 'french', 'mandarin', 'japanese', 'german', 'italian', name='languageenum'), nullable=False),
        sa.Column('proficiency_level', sa.Integer(), nullable=True),
        sa.Column('auth_provider', postgresql.ENUM('google', 'email', 'custom', name='authproviderenum'), nullable=True),
        sa.Column('auth_provider_id', sa.String(length=255), nullable=True),
        sa.Column('password_hash', sa.String(length=255), nullable=True),
        sa.Column('topics_of_interest', sa.Text(), nullable=True),
        sa.Column('learning_goal', sa.Text(), nullable=True),
        sa.Column('target_proficiency', sa.Integer(), nullable=True),
        sa.Column('email_schedule', sa.JSON(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('is_verified', sa.Boolean(), nullable=True),
        sa.Column('verification_token', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_login', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    
    # Create messages table
    op.create_table('messages',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('is_from_bennie', sa.Boolean(), nullable=True),
        sa.Column('language', postgresql.ENUM('spanish', 'french', 'mandarin', 'japanese', 'german', 'italian', name='languageenum'), nullable=False),
        sa.Column('vocabulary_words', sa.JSON(), nullable=True),
        sa.Column('difficulty_level', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('read_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_messages_id'), 'messages', ['id'], unique=False)
    
    # Create email_logs table
    op.create_table('email_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('email_type', sa.String(length=50), nullable=False),
        sa.Column('subject', sa.String(length=255), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('sendgrid_message_id', sa.String(length=255), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('sent_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_email_logs_id'), 'email_logs', ['id'], unique=False)
    
    # Create email_schedules table
    op.create_table('email_schedules',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('day_of_week', sa.Integer(), nullable=False),
        sa.Column('time_of_day', sa.String(length=5), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('next_send_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_email_schedules_id'), 'email_schedules', ['id'], unique=False)
    
    # Create user_progress table
    op.create_table('user_progress',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('current_level', sa.Integer(), nullable=False),
        sa.Column('total_messages_sent', sa.Integer(), nullable=True),
        sa.Column('total_messages_received', sa.Integer(), nullable=True),
        sa.Column('vocabulary_words_learned', sa.Integer(), nullable=True),
        sa.Column('last_activity', sa.DateTime(timezone=True), nullable=True),
        sa.Column('streak_days', sa.Integer(), nullable=True),
        sa.Column('longest_streak', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_progress_id'), 'user_progress', ['id'], unique=False)
    
    # Create vocabulary_words table
    op.create_table('vocabulary_words',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('word', sa.String(length=255), nullable=False),
        sa.Column('definition', sa.Text(), nullable=False),
        sa.Column('language', postgresql.ENUM('spanish', 'french', 'mandarin', 'japanese', 'german', 'italian', name='languageenum'), nullable=False),
        sa.Column('is_learned', sa.Boolean(), nullable=True),
        sa.Column('times_encountered', sa.Integer(), nullable=True),
        sa.Column('last_encountered', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_vocabulary_words_id'), 'vocabulary_words', ['id'], unique=False)


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_index(op.f('ix_vocabulary_words_id'), table_name='vocabulary_words')
    op.drop_table('vocabulary_words')
    op.drop_index(op.f('ix_user_progress_id'), table_name='user_progress')
    op.drop_table('user_progress')
    op.drop_index(op.f('ix_email_schedules_id'), table_name='email_schedules')
    op.drop_table('email_schedules')
    op.drop_index(op.f('ix_email_logs_id'), table_name='email_logs')
    op.drop_table('email_logs')
    op.drop_index(op.f('ix_messages_id'), table_name='messages')
    op.drop_table('messages')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_table('users')
    
    # Drop enum types
    op.execute("DROP TYPE IF EXISTS languageenum CASCADE;")
    op.execute("DROP TYPE IF EXISTS authproviderenum CASCADE;") 