# Bennie Database Setup Guide

This guide will help you set up the PostgreSQL database for Bennie on Railway.

## 🚀 Quick Start

### 1. Railway Setup

1. **Create a Railway account** at [railway.app](https://railway.app)
2. **Create a new project** in Railway
3. **Add a PostgreSQL service** to your project:
   - Click "New Service" → "Database" → "PostgreSQL"
   - Railway will automatically provide a `DATABASE_URL` environment variable

### 2. Environment Variables

Railway will automatically set these environment variables:
- `DATABASE_URL` - PostgreSQL connection string
- `PORT` - Port for the application (Railway sets this automatically)

You'll need to add these manually in Railway's environment variables:
- `OPENAI_API_KEY` - Your OpenAI API key
- `SENDGRID_API_KEY` - Your SendGrid API key
- `DEBUG` - Set to "true" for development, "false" for production

### 3. Deploy to Railway

1. **Connect your GitHub repository** to Railway
2. **Deploy the application** - Railway will automatically detect the Python app
3. **Run database setup** (see below)

## 📊 Database Schema

The database includes the following tables:

### Users Table
- `id` - Primary key
- `email` - User's email address (unique)
- `name` - User's full name
- `nickname` - Optional nickname
- `target_language` - Language they're learning (enum)
- `proficiency_level` - Current level (1-100)
- `auth_provider` - How they signed up (Google, email, custom)
- `topics_of_interest` - JSON field for learning preferences
- `learning_goal` - User's learning objective
- `email_schedule` - JSON field for email preferences
- `is_active` - Account status
- `created_at`, `updated_at` - Timestamps

### Messages Table
- `id` - Primary key
- `user_id` - Foreign key to users
- `content` - Message content
- `is_from_bennie` - Boolean (true if from Bennie, false if from user)
- `language` - Language of the message
- `vocabulary_words` - JSON array of new words
- `difficulty_level` - Message difficulty (1-100)
- `created_at`, `read_at` - Timestamps

### Email Logs Table
- `id` - Primary key
- `user_id` - Foreign key to users
- `email_type` - Type of email (welcome, practice, exit)
- `subject` - Email subject
- `content` - Email content
- `sendgrid_message_id` - SendGrid tracking ID
- `status` - Email status (sent, delivered, bounced, failed)
- `sent_at` - Timestamp

### Email Schedules Table
- `id` - Primary key
- `user_id` - Foreign key to users
- `day_of_week` - 0=Monday, 1=Tuesday, etc.
- `time_of_day` - "08:00" format
- `is_active` - Whether this schedule is active
- `next_send_at` - Next scheduled send time

### User Progress Table
- `id` - Primary key
- `user_id` - Foreign key to users
- `current_level` - Current proficiency level
- `total_messages_sent` - Count of user messages
- `total_messages_received` - Count of Bennie messages
- `vocabulary_words_learned` - Count of learned words
- `streak_days` - Current activity streak
- `longest_streak` - Longest streak achieved

### Vocabulary Words Table
- `id` - Primary key
- `user_id` - Foreign key to users
- `word` - The vocabulary word
- `definition` - Word definition
- `language` - Language of the word
- `is_learned` - Whether user has learned it
- `times_encountered` - How many times seen
- `created_at`, `last_encountered` - Timestamps

## 🛠️ Local Development Setup

### Prerequisites
- Python 3.8+
- PostgreSQL installed locally
- pip

### Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd Bennie
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   Create a `.env` file:
   ```env
   DATABASE_URL=postgresql://username:password@localhost:5432/bennie_db
   OPENAI_API_KEY=your_openai_key
   SENDGRID_API_KEY=your_sendgrid_key
   DEBUG=true
   ```

4. **Set up local PostgreSQL**
   ```bash
   # Create database
   createdb bennie_db
   
   # Or using psql
   psql -c "CREATE DATABASE bennie_db;"
   ```

5. **Initialize the database**
   ```bash
   python setup_database.py
   ```

6. **Run the application**
   ```bash
   python main.py
   ```

## 📝 Database Operations

### Creating a User
```python
from database.crud import UserCRUD
from database.models import LanguageEnum

user = UserCRUD.create_user(
    db=session,
    email="user@example.com",
    name="John Doe",
    target_language=LanguageEnum.SPANISH
)
```

### Sending Scheduled Emails
```python
from database.email_scheduler import run_scheduled_emails

# This will send emails to all users scheduled for the current time
results = run_scheduled_emails()
```

### Getting User Messages
```python
from database.crud import MessageCRUD

messages = MessageCRUD.get_user_messages(db=session, user_id=1, limit=10)
```

## 🔄 Database Migrations

### Creating a Migration
```bash
# After making changes to models
alembic revision --autogenerate -m "Description of changes"
```

### Applying Migrations
```bash
# Apply all pending migrations
alembic upgrade head

# Apply specific migration
alembic upgrade <revision_id>

# Rollback one migration
alembic downgrade -1
```

### Migration Status
```bash
# Check current migration status
alembic current

# View migration history
alembic history
```

## 📧 Email Scheduling

The system automatically sends emails based on user schedules:

- **Default Schedule**: Monday, Wednesday, Friday at 8:00 AM
- **Customizable**: Users can set their own schedules
- **Time Zones**: All times are in UTC (you may want to add timezone support)

### Running Scheduled Emails

1. **Automatically**: Set up a cron job or Railway cron service
2. **Manually**: Call the API endpoint `/api/emails/send-scheduled`
3. **Programmatically**: Use `run_scheduled_emails()` function

## 🔧 Troubleshooting

### Database Connection Issues
- Check that `DATABASE_URL` is set correctly
- Verify PostgreSQL is running
- Check firewall settings

### Migration Issues
- Ensure all dependencies are installed
- Check that the database exists
- Verify user permissions

### Email Sending Issues
- Check SendGrid API key
- Verify email templates
- Check user email addresses

## 📈 Monitoring

### Database Health
- Use Railway's built-in monitoring
- Check the `/health` endpoint
- Monitor email sending logs

### Performance
- Monitor query performance
- Check connection pool usage
- Track email delivery rates

## 🔒 Security Considerations

1. **Environment Variables**: Never commit API keys to version control
2. **Database Access**: Use connection pooling and prepared statements
3. **Email Validation**: Validate all email addresses
4. **Rate Limiting**: Implement rate limiting for API endpoints
5. **Input Validation**: Validate all user inputs

## 🚀 Production Deployment

1. **Set up Railway PostgreSQL**
2. **Configure environment variables**
3. **Deploy the application**
4. **Run database migrations**
5. **Set up monitoring**
6. **Configure email scheduling**

## 📞 Support

If you encounter issues:
1. Check the logs in Railway dashboard
2. Verify environment variables
3. Test database connection
4. Check API endpoints

---

For more information, see the main [README.md](README.md) file. 