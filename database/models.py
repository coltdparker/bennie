from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

Base = declarative_base()

class LanguageEnum(enum.Enum):
    SPANISH = "spanish"
    FRENCH = "french"
    MANDARIN = "mandarin"
    JAPANESE = "japanese"
    GERMAN = "german"
    ITALIAN = "italian"

class AuthProviderEnum(enum.Enum):
    GOOGLE = "google"
    EMAIL = "email"
    CUSTOM = "custom"

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    nickname = Column(String(100))
    
    # Language learning preferences
    target_language = Column(Enum(LanguageEnum), nullable=False)
    proficiency_level = Column(Integer, default=1)  # 1-100 scale
    
    # Authentication
    auth_provider = Column(Enum(AuthProviderEnum), default=AuthProviderEnum.EMAIL)
    auth_provider_id = Column(String(255))  # For OAuth providers
    password_hash = Column(String(255))  # For custom login
    
    # Learning preferences
    topics_of_interest = Column(Text)  # JSON string or comma-separated
    learning_goal = Column(Text)
    target_proficiency = Column(Integer, default=50)  # Goal level 1-100
    
    # Email preferences
    email_schedule = Column(JSON, default={
        "monday": True,
        "wednesday": True,
        "friday": True,
        "preferred_time": "08:00"  # 24-hour format
    })
    
    # Account status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    verification_token = Column(String(255))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True))
    
    # Relationships
    messages = relationship("Message", back_populates="user")
    email_logs = relationship("EmailLog", back_populates="user")
    
    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', name='{self.name}')>"

class Message(Base):
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Message content
    content = Column(Text, nullable=False)
    is_from_bennie = Column(Boolean, default=False)  # True if from Bennie, False if from user
    
    # Language and context
    language = Column(Enum(LanguageEnum), nullable=False)
    vocabulary_words = Column(JSON)  # List of new words introduced
    difficulty_level = Column(Integer)  # 1-100 scale
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    read_at = Column(DateTime(timezone=True))
    
    # Relationships
    user = relationship("User", back_populates="messages")
    
    def __repr__(self):
        return f"<Message(id={self.id}, user_id={self.user_id}, is_from_bennie={self.is_from_bennie})>"

class EmailLog(Base):
    __tablename__ = "email_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Email details
    email_type = Column(String(50), nullable=False)  # 'welcome', 'practice', 'exit', etc.
    subject = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    
    # SendGrid response
    sendgrid_message_id = Column(String(255))
    status = Column(String(50))  # 'sent', 'delivered', 'bounced', 'failed'
    
    # Timestamps
    sent_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="email_logs")
    
    def __repr__(self):
        return f"<EmailLog(id={self.id}, user_id={self.user_id}, email_type='{self.email_type}')>"

class EmailSchedule(Base):
    __tablename__ = "email_schedules"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Schedule details
    day_of_week = Column(Integer, nullable=False)  # 0=Monday, 1=Tuesday, etc.
    time_of_day = Column(String(5), nullable=False)  # "08:00" format
    is_active = Column(Boolean, default=True)
    
    # Next scheduled send
    next_send_at = Column(DateTime(timezone=True))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<EmailSchedule(id={self.id}, user_id={self.user_id}, day={self.day_of_week}, time='{self.time_of_day}')>"

class UserProgress(Base):
    __tablename__ = "user_progress"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Progress tracking
    current_level = Column(Integer, nullable=False)  # 1-100
    total_messages_sent = Column(Integer, default=0)
    total_messages_received = Column(Integer, default=0)
    vocabulary_words_learned = Column(Integer, default=0)
    
    # Engagement metrics
    last_activity = Column(DateTime(timezone=True))
    streak_days = Column(Integer, default=0)  # Consecutive days of activity
    longest_streak = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<UserProgress(id={self.id}, user_id={self.user_id}, level={self.current_level})>"

class VocabularyWord(Base):
    __tablename__ = "vocabulary_words"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Word details
    word = Column(String(255), nullable=False)
    definition = Column(Text, nullable=False)
    language = Column(Enum(LanguageEnum), nullable=False)
    
    # Learning status
    is_learned = Column(Boolean, default=False)
    times_encountered = Column(Integer, default=1)
    last_encountered = Column(DateTime(timezone=True), server_default=func.now())
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<VocabularyWord(id={self.id}, word='{self.word}', language='{self.language}')>" 