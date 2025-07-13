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
    resp = supabase.table("users").select("id, name, target_language, proficiency_level").eq("email", user_email).execute()
    if not resp.data:
        raise ValueError(f"User not found: {user_email}")
    return resp.data[0]

def get_last_n_bennie_emails(user_id: int, n: int = 3) -> List[Dict]:
    resp = supabase.table("email_history").select("id, content, created_at").eq("user_id", user_id).eq("is_from_bennie", True).order("created_at", desc=True).limit(n).execute()
    return resp.data or []

def get_last_n_user_replies(user_id: int, n: int = 3) -> List[Dict]:
    resp = supabase.table("email_history").select("id, content, created_at").eq("user_id", user_id).eq("is_from_bennie", False).order("created_at", desc=True).limit(n).execute()
    return resp.data or []

# --- ANALYSIS HELPERS ---
def analyze_reply_length(replies: List[Dict]) -> tuple[float, str]:
    if not replies:
        return 0, "No replies this week."
    avg_len = sum(len(r["content"].split()) for r in replies) / len(replies)
    if avg_len <= 15:
        feedback = "Your replies were quite short (1-2 sentences). Try to write a bit more each time—longer emails will help you improve much faster!"
    elif avg_len <= 40:
        feedback = "Your replies were a good length. Keep adding detail and practicing!"
    else:
        feedback = "Your replies were impressively detailed! This is fantastic for your progress."
    return avg_len, feedback

def estimate_reply_level(replies: List[Dict]) -> tuple[int, int, str]:
    # Use OpenAI to estimate the average level of the user's replies (1-100)
    if not replies:
        return 0, 1, "No replies to evaluate."
    joined = "\n---\n".join([r["content"] for r in replies])
    prompt = f"""
You are a language teacher. Read the following student email replies and estimate their average proficiency on a scale of 1-100 (1=absolute beginner, 100=near-native). Only output the number.

{joined}
"""
    resp = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=5,
        temperature=0
    )
    try:
        level = int("".join([c for c in resp.choices[0].message.content if c.isdigit()]))
    except Exception:
        level = 1
    semester, desc = level_to_semester(level)
    return level, semester, desc

def get_vocab_from_bennie_emails(emails: List[Dict]) -> List[str]:
    # Extract lines with definitions (simple heuristic)
    vocab = []
    for email in emails:
        lines = email["content"].splitlines()
        for line in lines:
            if (":" in line or "-" in line) and ("(" in line and ")" in line):
                vocab.append(line.strip())
    return vocab

def get_progress_tracker(user_id: int, replies: List[Dict], bennie_emails: List[Dict]) -> str:
    # Example: streak, reply rate, new words learned
    streak = 0
    today = datetime.datetime.utcnow().date()
    for i in range(7):
        day = today - datetime.timedelta(days=i)
        if any(r["created_at"].startswith(str(day)) for r in replies):
            streak += 1
        else:
            break
    reply_rate = len(replies)
    new_words = len(get_vocab_from_bennie_emails(bennie_emails))
    return f"You replied to {reply_rate} out of 3 emails this week. Your current reply streak is {streak} days. You learned {new_words} new words!"

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
def send_evaluation_email(user_email: str, subject: str, html_content: str, plain_content: str, user_id: int = None):
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
        # Log to email_history with is_evaluation=True if user_id is provided
        if user_id is not None:
            try:
                supabase.table("email_history").insert({
                    "user_id": user_id,
                    "content": plain_content,
                    "is_from_bennie": True,
                    "is_evaluation": True
                }).execute()
            except Exception as e:
                print(f"⚠️ Failed to log evaluation email to history: {e}")
    else:
        print(f"⚠️ Failed to send email: {response.status_code}")
        print(response.body)

# --- MAIN FUNCTION FOR SCHEDULER/IMPORT ---
def send_weekly_evaluation_email(user_email: str):
    user = get_user_context(user_email)
    user_id = user["id"]
    bennie_emails = get_last_n_bennie_emails(user_id, 3)
    user_replies = get_last_n_user_replies(user_id, 3)
    avg_len, len_feedback = analyze_reply_length(user_replies)
    reply_level, semester, semester_desc = estimate_reply_level(user_replies)
    vocab = get_vocab_from_bennie_emails(bennie_emails)
    progress_tracker = get_progress_tracker(user_id, user_replies, bennie_emails)
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
    send_evaluation_email(user_email, "Your Weekly Language Progress with Bennie!", html_content, email_text, user_id=user_id)

# --- CLI ENTRY POINT ---
def main():
    if len(sys.argv) < 2:
        print("Usage: python send_weekly_evaluation_email.py user@example.com")
        sys.exit(1)
    user_email = sys.argv[1]
    send_weekly_evaluation_email(user_email)

if __name__ == "__main__":
    main() 