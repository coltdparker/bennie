# using SendGrid's Python Library
# https://github.com/sendgrid/sendgrid-python
import os
from dotenv import load_dotenv
import sendgrid
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from openai import OpenAI
import logging
from supabase import create_client, Client
from typing import List, Dict, Optional, Tuple
import random
import json

logger = logging.getLogger(__name__)

load_dotenv()

# Initialize Supabase client
SUPABASE_URL: str = os.getenv("SUPABASE_URL")
SUPABASE_KEY: str = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    logger.error("Missing required environment variables: SUPABASE_URL or SUPABASE_KEY")
    raise ValueError("Missing required environment variables")

try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    logger.info("Supabase client initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Supabase client: {e}")
    raise

# Convert text to HTML format for proper email display
def text_to_html(text):
    """Convert plain text to HTML, preserving line breaks"""
    # Replace newlines with HTML line breaks
    html_text = text.replace('\n', '<br>\n')
    # Wrap in basic HTML structure
    return f"""
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        {html_text}
    </body>
    </html>
    """

def get_email_subject(user_language: str) -> str:
    """
    Returns the appropriate email subject line based on the selected language.
    
    Args:
        language (str): The language code (spanish, french, mandarin, japanese, german, italian)
    
    Returns:
        str: The email subject line in both English and the target language
    """
    user_language = user_language.lower()
    language_subjects = {
        'spanish': 'Spanish Learning Email from Bennie! - Correo de aprendizaje de español',
        'french': 'French Learning Email from Bennie! - E-mail d\'apprentissage du français',
        'mandarin': 'Chinese Learning Email from Bennie! - 中文学习邮件',
        'japanese': 'Japanese Learning Email from Bennie! - 日本語学習メール',
        'german': 'German Learning Email from Bennie! - Deutsch-Lern-E-Mail',
        'italian': 'Italian Learning Email from Bennie! - E-mail di apprendimento dell\'italiano'
    }
    
    # Convert to lowercase and remove any extra whitespace for robust matching
    language_clean = user_language.lower().strip()
    
    if language_clean in language_subjects:
        return language_subjects[language_clean]
    else:
        # General fallback case for unsupported languages
        return f'Language Learning Email from Bennie! {user_language.title()} Learning Email'

def get_user_context(user_email: str) -> Dict:
    """
    Fetch comprehensive user context from the database.
    
    Args:
        user_email (str): User's email address
        
    Returns:
        Dict: User context including profile and preferences
    """
    try:
        # Get user profile
        user_response = supabase.table("users").select(
            "id, name, target_language, proficiency_level, topics_of_interest, learning_goal"
        ).eq("email", user_email).execute()
        
        if not user_response.data:
            logger.error(f"User not found: {user_email}")
            raise ValueError(f"User not found: {user_email}")
        
        user = user_response.data[0]
        
        # Get recent email history (last 20 messages)
        history_response = supabase.table("email_history").select(
            "content, is_from_bennie, created_at"
        ).eq("user_id", user["id"]).order("created_at", desc=True).limit(20).execute()
        
        email_history = history_response.data if history_response.data else []
        
        return {
            "user_id": user["id"],
            "name": user["name"],
            "target_language": user["target_language"],
            "proficiency_level": user["proficiency_level"] or 1,
            "topics_of_interest": user["topics_of_interest"] or "",
            "learning_goal": user["learning_goal"] or "",
            "email_history": email_history
        }
        
    except Exception as e:
        logger.error(f"Error fetching user context: {e}")
        raise

def analyze_topic_diversity(email_history: List[Dict]) -> Tuple[List[str], bool]:
    """
    Analyze email history to determine topic diversity and suggest new vs repeated topics.
    
    Args:
        email_history (List[Dict]): List of recent email history
        
    Returns:
        Tuple[List[str], bool]: (recent_topics, should_use_new_topic)
    """
    # Extract topics from recent Bennie emails (last 7 messages)
    recent_bennie_emails = [
        email["content"] for email in email_history 
        if email["is_from_bennie"] and email["content"]
    ][:7]
    
    # Simple topic extraction (this could be enhanced with NLP)
    recent_topics = []
    for email in recent_bennie_emails:
        # Extract potential topics from email content
        # This is a simplified approach - could be enhanced with better NLP
        lines = email.lower().split('\n')
        for line in lines:
            if any(keyword in line for keyword in ['today', 'yesterday', 'weekend', 'morning', 'evening', 'afternoon']):
                # Extract the main activity/topic from the line
                words = line.split()
                if len(words) > 3:
                    recent_topics.append(' '.join(words[:5]))  # First 5 words as topic
                break
    
    # Decide whether to use new topic (50% chance) or repeat an old one
    should_use_new_topic = random.random() < 0.5
    
    return recent_topics, should_use_new_topic

# Map proficiency level (1-100) to college semester (1-8) and description
def level_to_semester(level: int) -> (int, str):
    """
    Map a proficiency level (1-100) to a college semester (1-8) and provide a description for prompt context.
    """
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

def create_enhanced_prompt(user_context: Dict, recent_topics: List[str], should_use_new_topic: bool) -> str:
    """
    Create an enhanced prompt with comprehensive user context.
    """
    # Bennie's personality and purpose
    bennie_identity = """You are Bennie, a warm, enthusiastic, and encouraging AI language learning friend. You have a playful personality and love sharing your daily experiences. You're genuinely excited about helping people learn languages and you treat each user like a close friend. You're curious about their lives and always ask engaging questions to keep the conversation flowing."""

    # User context section
    semester, semester_desc = level_to_semester(user_context['proficiency_level'])
    user_info = f"""
USER CONTEXT:
- Name: {user_context['name']}
- Target Language: {user_context['target_language']}
- Proficiency Level: {user_context['proficiency_level']}/100
- Learning Goal: {user_context['learning_goal']}
- Interests: {user_context['topics_of_interest']}

SEMESTER CONTEXT:
- The user's proficiency level of {user_context['proficiency_level']}/100 is equivalent to a college language learner in semester {semester} out of 8.
- {semester_desc}
- Tailor your vocabulary, grammar, and topics to what a student would be expected to handle at this semester.
"""

    # Topic guidance
    topic_guidance = f"""
TOPIC GUIDANCE:
- Recent topics discussed: {', '.join(recent_topics) if recent_topics else 'None yet'}
- Should introduce new topic: {'Yes' if should_use_new_topic else 'No'}
- If new topic: Choose something related to their interests: {user_context['topics_of_interest']}
- If repeating topic: Choose a different angle or situation from their interests
- Avoid repeating the exact same topic within 7 messages
"""

    # Language and content requirements
    requirements = f"""
REQUIREMENTS:
- Write entirely in {user_context['target_language']}
- Adjust complexity for level {user_context['proficiency_level']}/100 (see semester context above)
- Keep message to 3-4 sentences
- Include 2-3 new vocabulary words appropriate for their level
- End with an engaging question that invites a response
- Keep tone friendly, encouraging, and conversational
- Include signature: "Con cariño, Bennie" (Spanish) / "Avec amitié, Bennie" (French) / etc.
- Add vocabulary definitions at the bottom after signature
- DO NOT mention their learning goals or proficiency level in the email
- Focus on natural conversation, not explicit teaching
"""

    # Combine all sections
    full_prompt = f"""{bennie_identity}

{user_info}

{topic_guidance}

{requirements}

Write your email now:"""

    return full_prompt

# ==========================================
# Enhanced version with comprehensive user context
def send_language_learning_email(user_email: str):
    """
    Enhanced version with comprehensive user context and topic diversity.
    
    Args:
        user_email (str): User's email address
    """
    load_dotenv()
    
    # Check if API keys are loaded
    openai_key = os.getenv("OPENAI_API_KEY")
    sendgrid_key = os.getenv("SENDGRID_API_KEY")
    
    # Masked API key logging
    def mask_key(key):
        if not key or len(key) < 8:
            return "(not set or too short)"
        return f"{key[:4]}...{key[-4:]}"
    
    logger.info(f"send_language_learning_email called for user_email={user_email}")
    logger.info(f"OPENAI_API_KEY (masked): {mask_key(openai_key)}")
    logger.info(f"SENDGRID_API_KEY (masked): {mask_key(sendgrid_key)}")
    
    if not openai_key:
        logger.error("Error: OPENAI_API_KEY not found in .env file")
        raise RuntimeError("OPENAI_API_KEY not found in .env file")
    
    if not sendgrid_key:
        logger.error("Error: SENDGRID_API_KEY not found in .env file")
        raise RuntimeError("SENDGRID_API_KEY not found in .env file")
    
    try:
        # Get comprehensive user context
        logger.info("Fetching user context...")
        user_context = get_user_context(user_email)
        
        # Analyze topic diversity
        logger.info("Analyzing topic diversity...")
        recent_topics, should_use_new_topic = analyze_topic_diversity(user_context["email_history"])
        
        # Create enhanced prompt
        logger.info("Creating enhanced prompt...")
        enhanced_prompt = create_enhanced_prompt(user_context, recent_topics, should_use_new_topic)
        
        # Log before OpenAI client initialization
        import openai as openai_module
        logger.info(f"OpenAI package version: {getattr(openai_module, '__version__', 'unknown')}")
        logger.info("About to initialize OpenAI client...")
        client = OpenAI(api_key=openai_key)
        
        # Get response from OpenAI with enhanced context
        logger.info("Getting response from OpenAI with enhanced context...")
        completion = client.chat.completions.create(
            model="gpt-4o", 
            messages=[
                {
                    "role": "system",
                    "content": "You are Bennie, a warm and enthusiastic AI language learning friend. You write natural, conversational emails in the user's target language, sharing your daily experiences while helping them learn. You're encouraging, curious, and genuinely interested in their lives."
                },
                {
                    "role": "user",
                    "content": enhanced_prompt
                }
            ],
            max_tokens=600,
            temperature=0.8
        )
        
        # Print usage information
        model_rate = 0.0000025 # $/token
        usage = completion.usage
        total_usage = usage.total_tokens
        estimated_cost = total_usage * model_rate
        logger.info(f"📊 OpenAI Usage: {usage.prompt_tokens} prompt tokens, {usage.completion_tokens} completion tokens, {usage.total_tokens} total tokens. Estimated cost = ${estimated_cost}")

        bennies_response = completion.choices[0].message.content
        logger.info("✓ Got response from OpenAI")
        logger.info(f"Response length: {len(bennies_response)} characters")
        
        # Convert to HTML
        html_content = text_to_html(bennies_response)
        
        # Create email
        message = Mail(
            from_email='Bennie@itsbennie.com',
            to_emails=user_email,
            subject=get_email_subject(user_language=user_context["target_language"]),
            html_content=html_content,
            plain_text_content=bennies_response
        )
        
        # Send email
        logger.info(f"Sending email to {user_context['name']} <{user_email}>")
        sg = SendGridAPIClient(sendgrid_key)
        response = sg.send(message)
        
        if response.status_code == 202:
            logger.info(f"✓ Email sent to {user_context['name']} successfully!")
            logger.info(f"Check your inbox for the {user_context['target_language']} learning email!")
            
            # Save email to history
            try:
                supabase.table("email_history").insert({
                    "user_id": user_context["user_id"],
                    "content": bennies_response,
                    "is_from_bennie": True,
                    "difficulty_level": user_context["proficiency_level"]
                }).execute()
                logger.info("✓ Email saved to history")
            except Exception as e:
                logger.error(f"Failed to save email to history: {e}")
                
        else:
            logger.error(f"⚠ Unexpected status code: {response.status_code}")
            logger.error(f"Response body: {response.body}")
            raise RuntimeError(f"SendGrid error: {response.status_code} {response.body}")
        
    except Exception as e:
        logger.error(f"Error in send_language_learning_email: {e}")
        raise

# Legacy function for backward compatibility
def send_language_learning_email_legacy(user_name: str, user_email: str, user_language: str, user_level: int):
    """
    Legacy version for backward compatibility - redirects to new function.
    """
    logger.warning("Using legacy function - consider updating to use send_language_learning_email(user_email)")
    return send_language_learning_email(user_email)

if __name__ == "__main__":
    print("Sending email with enhanced language learning content...")
    # Test with a user email
    send_language_learning_email("coltdparker@gmail.com") 


