from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import json

from .models import User, Message, EmailLog, EmailSchedule, UserProgress, VocabularyWord, LanguageEnum, AuthProviderEnum

# User CRUD operations
class UserCRUD:
    @staticmethod
    def create_user(
        db: Session,
        email: str,
        name: str,
        target_language: LanguageEnum,
        nickname: Optional[str] = None,
        auth_provider: AuthProviderEnum = AuthProviderEnum.EMAIL,
        auth_provider_id: Optional[str] = None,
        password_hash: Optional[str] = None
    ) -> User:
        """Create a new user."""
        db_user = User(
            email=email,
            name=name,
            nickname=nickname,
            target_language=target_language,
            auth_provider=auth_provider,
            auth_provider_id=auth_provider_id,
            password_hash=password_hash
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        # Create initial progress record
        progress = UserProgress(user_id=db_user.id, current_level=1)
        db.add(progress)
        db.commit()
        
        return db_user
    
    @staticmethod
    def get_user_by_email(db: Session, email: str) -> Optional[User]:
        """Get user by email address."""
        return db.query(User).filter(User.email == email).first()
    
    @staticmethod
    def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
        """Get user by ID."""
        return db.query(User).filter(User.id == user_id).first()
    
    @staticmethod
    def update_user_profile(
        db: Session,
        user_id: int,
        **kwargs
    ) -> Optional[User]:
        """Update user profile information."""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return None
        
        for key, value in kwargs.items():
            if hasattr(user, key):
                setattr(user, key, value)
        
        db.commit()
        db.refresh(user)
        return user
    
    @staticmethod
    def update_proficiency_level(db: Session, user_id: int, new_level: int) -> bool:
        """Update user's proficiency level."""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False
        
        user.proficiency_level = max(1, min(100, new_level))
        db.commit()
        return True

# Message CRUD operations
class MessageCRUD:
    @staticmethod
    def create_message(
        db: Session,
        user_id: int,
        content: str,
        language: LanguageEnum,
        is_from_bennie: bool = False,
        vocabulary_words: Optional[List[str]] = None,
        difficulty_level: Optional[int] = None
    ) -> Message:
        """Create a new message."""
        db_message = Message(
            user_id=user_id,
            content=content,
            language=language,
            is_from_bennie=is_from_bennie,
            vocabulary_words=vocabulary_words or [],
            difficulty_level=difficulty_level
        )
        db.add(db_message)
        db.commit()
        db.refresh(db_message)
        return db_message
    
    @staticmethod
    def get_user_messages(
        db: Session,
        user_id: int,
        limit: int = 50,
        offset: int = 0
    ) -> List[Message]:
        """Get messages for a user with pagination."""
        return db.query(Message).filter(
            Message.user_id == user_id
        ).order_by(
            Message.created_at.desc()
        ).offset(offset).limit(limit).all()
    
    @staticmethod
    def get_conversation_history(
        db: Session,
        user_id: int,
        days: int = 30
    ) -> List[Message]:
        """Get recent conversation history."""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        return db.query(Message).filter(
            and_(
                Message.user_id == user_id,
                Message.created_at >= cutoff_date
            )
        ).order_by(Message.created_at.asc()).all()

# Email Log CRUD operations
class EmailLogCRUD:
    @staticmethod
    def log_email(
        db: Session,
        user_id: int,
        email_type: str,
        subject: str,
        content: str,
        sendgrid_message_id: Optional[str] = None,
        status: str = "sent"
    ) -> EmailLog:
        """Log an email that was sent."""
        db_email_log = EmailLog(
            user_id=user_id,
            email_type=email_type,
            subject=subject,
            content=content,
            sendgrid_message_id=sendgrid_message_id,
            status=status
        )
        db.add(db_email_log)
        db.commit()
        db.refresh(db_email_log)
        return db_email_log
    
    @staticmethod
    def get_user_email_logs(
        db: Session,
        user_id: int,
        limit: int = 50
    ) -> List[EmailLog]:
        """Get email logs for a user."""
        return db.query(EmailLog).filter(
            EmailLog.user_id == user_id
        ).order_by(
            EmailLog.sent_at.desc()
        ).limit(limit).all()

# Email Schedule CRUD operations
class EmailScheduleCRUD:
    @staticmethod
    def create_schedule(
        db: Session,
        user_id: int,
        day_of_week: int,
        time_of_day: str
    ) -> EmailSchedule:
        """Create an email schedule for a user."""
        db_schedule = EmailSchedule(
            user_id=user_id,
            day_of_week=day_of_week,
            time_of_day=time_of_day
        )
        db.add(db_schedule)
        db.commit()
        db.refresh(db_schedule)
        return db_schedule
    
    @staticmethod
    def get_user_schedules(db: Session, user_id: int) -> List[EmailSchedule]:
        """Get all email schedules for a user."""
        return db.query(EmailSchedule).filter(
            EmailSchedule.user_id == user_id
        ).all()
    
    @staticmethod
    def get_schedules_for_time(
        db: Session,
        day_of_week: int,
        time_of_day: str
    ) -> List[EmailSchedule]:
        """Get all schedules for a specific time."""
        return db.query(EmailSchedule).filter(
            and_(
                EmailSchedule.day_of_week == day_of_week,
                EmailSchedule.time_of_day == time_of_day,
                EmailSchedule.is_active == True
            )
        ).all()
    
    @staticmethod
    def update_schedule(
        db: Session,
        schedule_id: int,
        **kwargs
    ) -> Optional[EmailSchedule]:
        """Update an email schedule."""
        schedule = db.query(EmailSchedule).filter(
            EmailSchedule.id == schedule_id
        ).first()
        if not schedule:
            return None
        
        for key, value in kwargs.items():
            if hasattr(schedule, key):
                setattr(schedule, key, value)
        
        db.commit()
        db.refresh(schedule)
        return schedule

# User Progress CRUD operations
class UserProgressCRUD:
    @staticmethod
    def get_progress(db: Session, user_id: int) -> Optional[UserProgress]:
        """Get user progress."""
        return db.query(UserProgress).filter(
            UserProgress.user_id == user_id
        ).first()
    
    @staticmethod
    def update_progress(
        db: Session,
        user_id: int,
        **kwargs
    ) -> Optional[UserProgress]:
        """Update user progress."""
        progress = db.query(UserProgress).filter(
            UserProgress.user_id == user_id
        ).first()
        if not progress:
            return None
        
        for key, value in kwargs.items():
            if hasattr(progress, key):
                setattr(progress, key, value)
        
        db.commit()
        db.refresh(progress)
        return progress
    
    @staticmethod
    def increment_messages_sent(db: Session, user_id: int) -> bool:
        """Increment the count of messages sent by user."""
        progress = db.query(UserProgress).filter(
            UserProgress.user_id == user_id
        ).first()
        if not progress:
            return False
        
        progress.total_messages_sent += 1
        progress.last_activity = datetime.utcnow()
        db.commit()
        return True
    
    @staticmethod
    def increment_messages_received(db: Session, user_id: int) -> bool:
        """Increment the count of messages received by user."""
        progress = db.query(UserProgress).filter(
            UserProgress.user_id == user_id
        ).first()
        if not progress:
            return False
        
        progress.total_messages_received += 1
        progress.last_activity = datetime.utcnow()
        db.commit()
        return True

# Vocabulary Word CRUD operations
class VocabularyWordCRUD:
    @staticmethod
    def add_vocabulary_word(
        db: Session,
        user_id: int,
        word: str,
        definition: str,
        language: LanguageEnum
    ) -> VocabularyWord:
        """Add a new vocabulary word for a user."""
        # Check if word already exists for this user
        existing_word = db.query(VocabularyWord).filter(
            and_(
                VocabularyWord.user_id == user_id,
                VocabularyWord.word == word,
                VocabularyWord.language == language
            )
        ).first()
        
        if existing_word:
            # Increment encounter count
            existing_word.times_encountered += 1
            existing_word.last_encountered = datetime.utcnow()
            db.commit()
            db.refresh(existing_word)
            return existing_word
        
        # Create new word
        db_word = VocabularyWord(
            user_id=user_id,
            word=word,
            definition=definition,
            language=language
        )
        db.add(db_word)
        db.commit()
        db.refresh(db_word)
        return db_word
    
    @staticmethod
    def get_user_vocabulary(
        db: Session,
        user_id: int,
        language: Optional[LanguageEnum] = None
    ) -> List[VocabularyWord]:
        """Get vocabulary words for a user."""
        query = db.query(VocabularyWord).filter(
            VocabularyWord.user_id == user_id
        )
        
        if language:
            query = query.filter(VocabularyWord.language == language)
        
        return query.order_by(VocabularyWord.last_encountered.desc()).all()
    
    @staticmethod
    def mark_word_learned(
        db: Session,
        word_id: int,
        user_id: int
    ) -> bool:
        """Mark a vocabulary word as learned."""
        word = db.query(VocabularyWord).filter(
            and_(
                VocabularyWord.id == word_id,
                VocabularyWord.user_id == user_id
            )
        ).first()
        
        if not word:
            return False
        
        word.is_learned = True
        db.commit()
        return True 