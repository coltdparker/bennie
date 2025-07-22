import os
from dotenv import load_dotenv
from supabase import create_client
from openai import OpenAI
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import logging
from typing import List, Dict
import sys
import datetime

# --- CONFIG ---
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")

if not (SUPABASE_URL and SUPABASE_KEY and OPENAI_API_KEY and SENDGRID_API_KEY):
    print("Missing required environment variables.")
    sys.exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
openai_client = OpenAI(api_key=OPENAI_API_KEY)
logger = logging.getLogger(__name__)

# --- LEVEL TO SEMESTER MAPPING ---
def level_to_semester(level: int) -> tuple[int, str]:
    if level <= 12:
        return 1, "Absolute beginner. Greetings, basic phrases, simple questions. Equivalent to first semester college language student."
    elif level <= 25:
        return 2, "Beginner. Simple present tense, basic questions, daily life topics. Equivalent to second semester."
    elif level <= 37:
        return 3, "Lower intermediate. Past/future tense, more vocabulary, short stories. Equivalent to third semester."
    elif level <= 50:
        return 4, "Intermediate. Complex sentences, opinions, short essays. Equivalent to fourth semester."
    elif level <= 62:
        return 5, "Upper intermediate. Argumentation, abstract topics, intro to literature. Equivalent to fifth semester."
    elif level <= 75:
        return 6, "Advanced. Advanced readings, idioms, cultural nuance. Equivalent to sixth semester."
    elif level <= 87:
        return 7, "Very advanced. Academic/professional topics, debates, research. Equivalent to seventh semester."
    else:
        return 8, "Near-native. Literature, advanced writing, slang, full fluency. Equivalent to eighth (final) semester."

# --- FETCH USER DATA ---
def get_user_context(user_email: str) -> Dict:
    # Get auth user first
    auth_user = supabase.auth.admin.get_user_by_email(user_email)
    if not auth_user:
        raise ValueError(f"User not found: {user_email}")
    
    # Get user profile
    resp = supabase.table("users").select("auth_user_id, name, target_language, proficiency_level").eq("auth_user_id", auth_user.id).execute()
    if not resp.data:
        raise ValueError(f"User profile not found: {user_email}")
    return resp.data[0]

def get_last_n_bennie_emails(auth_user_id: str, n: int = 3) -> List[Dict]:
    resp = supabase.table("email_history").select("id, content, created_at").eq("auth_user_id", auth_user_id).eq("is_from_bennie", True).order("created_at", desc=True).limit(n).execute()
    return resp.data or []

def get_last_n_user_replies(auth_user_id: str, n: int = 3) -> List[Dict]:
    resp = supabase.table("email_history").select("id, content, created_at").eq("auth_user_id", auth_user_id).eq("is_from_bennie", False).order("created_at", desc=True).limit(n).execute()
    return resp.data or []

def analyze_reply_length(replies: List[Dict]) -> tuple[float, str]:
    """Calculate average reply length and provide feedback."""
    if not replies:
        return 0, "No replies to analyze yet."
    
    lengths = [len(r["content"].split()) for r in replies]
    avg_len = sum(lengths) / len(lengths)
    
    if avg_len < 20:
        feedback = "Try to write a bit more in your replies - aim for at least 3-4 sentences!"
    elif avg_len < 40:
        feedback = "Good length! Keep practicing with these medium-length responses."
    else:
        feedback = "Excellent detailed responses! Your thorough practice will speed up your learning."
    
    return avg_len, feedback

def estimate_reply_level(replies: List[Dict]) -> tuple[int, int, str]:
    """Estimate user's current level based on replies."""
    if not replies:
        return 1, 1, "Just starting out!"
    
    # Simple estimation based on reply length and complexity
    total_score = 0
    for reply in replies:
        words = reply["content"].split()
        length_score = min(len(words) / 10, 10)  # Cap at 100 words
        unique_words = len(set(words))
        vocab_score = min(unique_words / 5, 10)  # Cap at 50 unique words
        total_score += (length_score + vocab_score) / 2
    
    avg_score = (total_score / len(replies)) * 5  # Scale to 0-100
    level = max(1, min(int(avg_score), 100))  # Ensure between 1-100
    semester, desc = level_to_semester(level)
    
    return level, semester, desc

def get_vocab_from_bennie_emails(bennie_emails: List[Dict]) -> List[str]:
    """Extract vocabulary words from Bennie's emails."""
    vocab = []
    for email in bennie_emails:
        content = email["content"]
        # Look for vocabulary sections at the end of emails
        if "Vocabulary:" in content or "New words:" in content:
            vocab_section = content.split("Vocabulary:")[-1].split("New words:")[-1]
            vocab.extend([line.strip() for line in vocab_section.split("\n") if line.strip()])
    return vocab

def get_progress_tracker(auth_user_id: str, user_replies: List[Dict], bennie_emails: List[Dict]) -> str:
    """Generate a progress tracking summary."""
    try:
        # Count total interactions
        total_replies = len(user_replies)
        total_bennie = len(bennie_emails)
        
        # Get reply rate
        if total_bennie > 0:
            reply_rate = (total_replies / total_bennie) * 100
        else:
            reply_rate = 0
        
        # Get streak info
        current_streak = 0
        last_reply_date = None
        if user_replies:
            last_reply_date = datetime.datetime.fromisoformat(user_replies[0]["created_at"].replace("Z", "+00:00"))
            current_date = datetime.datetime.now(datetime.timezone.utc)
            days_since_last = (current_date - last_reply_date).days
            
            if days_since_last <= 2:  # Consider it active if replied in last 2 days
                current_streak = 1
                for i in range(1, len(user_replies)):
                    prev_date = datetime.datetime.fromisoformat(user_replies[i]["created_at"].replace("Z", "+00:00"))
                    if (last_reply_date - prev_date).days <= 2:
                        current_streak += 1
                        last_reply_date = prev_date
                    else:
                        break
        
        return f"You've replied to {reply_rate:.0f}% of Bennie's emails (that's {total_replies} out of {total_bennie}). Current response streak: {current_streak} days!"
        
    except Exception as e:
        logger.error(f"Error generating progress tracker: {e}")
        return "Keep practicing consistently to see your progress tracked here!"

# --- BUILD PROMPT FOR CHATGPT ---
def build_evaluation_prompt(user, bennie_emails, user_replies, avg_len, len_feedback, reply_level, semester, semester_desc, vocab, progress_tracker):
    return f"""
You are Bennie, a friendly and encouraging AI language learning coach who has been emailing back and forth with the user who send these emails. Write a weekly evaluation email in ENGLISH to the user below. Be upbeat, supportive, and helpful. Use the following structure:

1. Friendly greeting and encouragement.
2. Motivational progress tracker: {progress_tracker}
3. Vocabulary recap: List the new words from the last 3 Bennie emails (with definitions).
4. Evaluation of the user's replies: Give specific examples of things they did well and things to improve. Be positive and not nitpicky.
5. Quick proficiency evaluation: Their average reply level this week was {reply_level}/100, which is equivalent to semester {semester} out of 8. ({semester_desc})
6. Email length feedback: Their average reply was {avg_len:.1f} words. {len_feedback}
7. Friendly closing and encouragement for the coming week.

User info:
- Name: {user['name']}
- Target language: {user['target_language']}

Bennie emails (last 3):
{chr(10).join([e['content'] for e in bennie_emails])}

User replies (last 3):
{chr(10).join([r['content'] for r in user_replies])}

Vocabulary recap:
{chr(10).join(vocab) if vocab else 'No new words found.'}
"""

# --- SEND EMAIL ---
def send_evaluation_email(user_email: str, subject: str, html_content: str, plain_content: str, auth_user_id: str = None):
    message = Mail(
        from_email='Bennie@itsbennie.com',
        to_emails=user_email,
        subject=subject,
        html_content=html_content,
        plain_text_content=plain_content
    )
    sg = SendGridAPIClient(SENDGRID_API_KEY)
    response = sg.send(message)
    if response.status_code == 202:
        print(f"✓ Evaluation email sent to {user_email}")
        # Log to email_history with is_evaluation=True if auth_user_id is provided
        if auth_user_id is not None:
            try:
                supabase.table("email_history").insert({
                    "auth_user_id": auth_user_id,
                    "content": plain_content,
                    "is_from_bennie": True,
                    "is_evaluation": True,
                    "difficulty_level": 1  # Evaluation emails are in English
                }).execute()
            except Exception as e:
                print(f"⚠️ Failed to log evaluation email to history: {e}")
    else:
        print(f"⚠️ Failed to send email: {response.status_code}")
        print(response.body)

# --- MAIN FUNCTION FOR SCHEDULER/IMPORT ---
def send_weekly_evaluation_email(user_email: str):
    user = get_user_context(user_email)
    auth_user_id = user["auth_user_id"]
    bennie_emails = get_last_n_bennie_emails(auth_user_id, 3)
    user_replies = get_last_n_user_replies(auth_user_id, 3)
    avg_len, len_feedback = analyze_reply_length(user_replies)
    reply_level, semester, semester_desc = estimate_reply_level(user_replies)
    vocab = get_vocab_from_bennie_emails(bennie_emails)
    progress_tracker = get_progress_tracker(auth_user_id, user_replies, bennie_emails)
    prompt = build_evaluation_prompt(user, bennie_emails, user_replies, avg_len, len_feedback, reply_level, semester, semester_desc, vocab, progress_tracker)

    # Get response from OpenAI
    resp = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=700,
        temperature=0.7
    )
    email_text = resp.choices[0].message.content
    html_content = f"<html><body style='font-family: Arial, sans-serif; line-height: 1.6;'>{email_text.replace(chr(10), '<br>')}</body></html>"
    send_evaluation_email(user_email, "Your Weekly Language Progress with Bennie!", html_content, email_text, auth_user_id=auth_user_id)

# --- CLI ENTRY POINT ---
def main():
    if len(sys.argv) < 2:
        print("Usage: python send_weekly_evaluation_email.py user@example.com")
        sys.exit(1)
    user_email = sys.argv[1]
    send_weekly_evaluation_email(user_email)

if __name__ == "__main__":
    main() 