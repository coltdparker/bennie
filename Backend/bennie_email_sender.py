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
        # Get auth user first
        auth_user = supabase.auth.admin.get_user_by_email(user_email)
        
        if not auth_user:
            logger.error(f"User not found: {user_email}")
            raise ValueError(f"User not found: {user_email}")
        
        # Get user profile
        user_response = supabase.table("users").select(
            "auth_user_id, name, target_language, proficiency_level, topics_of_interest, learning_goal"
        ).eq("auth_user_id", auth_user.id).execute()
        
        if not user_response.data:
            logger.error(f"User profile not found for auth_user_id: {auth_user.id}")
            raise ValueError(f"User profile not found: {user_email}")
        
        user = user_response.data[0]
        
        # Get recent email history (last 20 messages)
        history_response = supabase.table("email_history").select(
            "content, is_from_bennie, created_at"
        ).eq("auth_user_id", user["auth_user_id"]).order("created_at", desc=True).limit(20).execute()
        
        email_history = history_response.data if history_response.data else []
        
        return {
            "auth_user_id": user["auth_user_id"],
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

def analyze_topic_diversity(email_history: List[Dict]) -> Tuple[List[str], bool, List[str]]:
    """
    Analyze email history to determine topic diversity and suggest new vs repeated topics.
    Enhanced version that better tracks topics and enforces variety.
    
    Args:
        email_history (List[Dict]): List of recent email history
        
    Returns:
        Tuple[List[str], bool, List[str]]: (recent_topics, should_use_new_topic, available_interests)
    """
    # Extract topics from recent Bennie emails (last 10 messages)
    recent_bennie_emails = [
        email["content"] for email in email_history 
        if email["is_from_bennie"] and email["content"]
    ][:10]
    
    # Better topic extraction using keyword detection
    recent_topics = []
    topic_keywords = {
        'food': ['comida', 'cocinar', 'restaurante', 'cena', 'almuerzo', 'desayuno', 'manger', 'cuisine', 'dîner', 'déjeuner', 'petit-déjeuner', '食物', '做饭', '餐厅', '晚餐', '午餐', '早餐', '食べ物', '料理', 'レストラン', '夕食', '昼食', '朝食', 'Essen', 'kochen', 'Restaurant', 'Abendessen', 'Mittagessen', 'Frühstück', 'cibo', 'cucinare', 'ristorante', 'cena', 'pranzo', 'colazione'],
        'travel': ['viaje', 'vacaciones', 'turismo', 'ciudad', 'país', 'voyage', 'vacances', 'tourisme', 'ville', 'pays', '旅行', '假期', '旅游', '城市', '国家', '旅行', '休暇', '観光', '都市', '国', 'Reise', 'Urlaub', 'Tourismus', 'Stadt', 'Land', 'viaggio', 'vacanze', 'turismo', 'città', 'paese'],
        'work': ['trabajo', 'oficina', 'proyecto', 'reunión', 'travail', 'bureau', 'projet', 'réunion', '工作', '办公室', '项目', '会议', '仕事', 'オフィス', 'プロジェクト', '会議', 'Arbeit', 'Büro', 'Projekt', 'Meeting', 'lavoro', 'ufficio', 'progetto', 'riunione'],
        'family': ['familia', 'hijos', 'padres', 'hermanos', 'famille', 'enfants', 'parents', 'frères', '家庭', '孩子', '父母', '兄弟', '家族', '子供', '親', '兄弟', 'Familie', 'Kinder', 'Eltern', 'Geschwister', 'famiglia', 'figli', 'genitori', 'fratelli'],
        'hobbies': ['hobby', 'deportes', 'música', 'arte', 'lectura', 'passe-temps', 'sports', 'musique', 'art', 'lecture', '爱好', '运动', '音乐', '艺术', '阅读', '趣味', 'スポーツ', '音楽', '芸術', '読書', 'Hobby', 'Sport', 'Musik', 'Kunst', 'Lesen', 'hobby', 'sport', 'musica', 'arte', 'lettura'],
        'technology': ['tecnología', 'computadora', 'internet', 'aplicación', 'technologie', 'ordinateur', 'internet', 'application', '技术', '电脑', '互联网', '应用程序', '技術', 'コンピューター', 'インターネット', 'アプリケーション', 'Technologie', 'Computer', 'Internet', 'Anwendung', 'tecnologia', 'computer', 'internet', 'applicazione'],
        'weather': ['clima', 'lluvia', 'sol', 'frío', 'calor', 'temps', 'pluie', 'soleil', 'froid', 'chaud', '天气', '雨', '太阳', '冷', '热', '天気', '雨', '太陽', '寒い', '暑い', 'Wetter', 'Regen', 'Sonne', 'kalt', 'warm', 'tempo', 'pioggia', 'sole', 'freddo', 'caldo']
    }
    
    for email in recent_bennie_emails:
        email_lower = email.lower()
        for topic, keywords in topic_keywords.items():
            if any(keyword in email_lower for keyword in keywords):
                recent_topics.append(topic)
                break
    
    # Get user interests from the most recent email context
    user_interests = []
    if email_history:
        # Try to extract interests from the most recent user context
        # This is a simplified approach - in practice, you'd get this from user profile
        pass
    
    # Decide whether to use new topic (70% chance for variety, 30% to repeat)
    should_use_new_topic = random.random() < 0.7
    
    # If we have too many recent topics of the same type, force new topic
    if len(recent_topics) >= 3:
        topic_counts = {}
        for topic in recent_topics[-3:]:  # Last 3 topics
            topic_counts[topic] = topic_counts.get(topic, 0) + 1
        if any(count >= 2 for count in topic_counts.values()):
            should_use_new_topic = True
    
    return recent_topics, should_use_new_topic, user_interests

def parse_user_interests(interests_string: str) -> List[str]:
    """
    Parse user interests string into a list of distinct topics.
    Handles various formats: comma-separated, semicolon-separated, etc.
    """
    if not interests_string:
        return []
    
    # Split by common separators and clean up
    separators = [',', ';', '|', '\n']
    interests = [interests_string]
    
    for sep in separators:
        new_interests = []
        for interest in interests:
            new_interests.extend([i.strip() for i in interest.split(sep) if i.strip()])
        interests = new_interests
    
    # Remove duplicates and empty strings
    unique_interests = list(set([interest.lower() for interest in interests if interest]))
    
    # Map common variations to standard topics
    topic_mapping = {
        'food': ['food', 'cooking', 'cuisine', 'restaurant', 'dining', 'cooking', 'baking'],
        'travel': ['travel', 'tourism', 'vacation', 'trip', 'adventure', 'exploring'],
        'work': ['work', 'job', 'career', 'business', 'office', 'profession'],
        'family': ['family', 'kids', 'children', 'parents', 'siblings', 'home'],
        'hobbies': ['hobby', 'hobbies', 'sports', 'music', 'art', 'reading', 'gaming', 'photography'],
        'technology': ['technology', 'tech', 'computer', 'internet', 'software', 'gadgets'],
        'weather': ['weather', 'climate', 'outdoors', 'nature', 'environment'],
        'culture': ['culture', 'history', 'traditions', 'customs', 'heritage'],
        'health': ['health', 'fitness', 'exercise', 'wellness', 'medical'],
        'education': ['education', 'learning', 'study', 'school', 'university', 'courses']
    }
    
    # Map interests to standard topics
    mapped_interests = []
    for interest in unique_interests:
        for topic, keywords in topic_mapping.items():
            if any(keyword in interest for keyword in keywords):
                mapped_interests.append(topic)
                break
        else:
            # If no mapping found, keep the original interest
            mapped_interests.append(interest)
    
    return list(set(mapped_interests))

def get_next_topic(user_interests: List[str], recent_topics: List[str], should_use_new_topic: bool) -> str:
    """
    Determine the next topic to use based on user interests and recent history.
    """
    if not user_interests:
        # Fallback topics if no interests specified
        fallback_topics = ['daily life', 'weather', 'hobbies', 'food', 'work', 'family']
        return random.choice(fallback_topics)
    
    if should_use_new_topic:
        # Choose a topic from interests that hasn't been used recently
        available_topics = [topic for topic in user_interests if topic not in recent_topics[-3:]]
        if available_topics:
            return random.choice(available_topics)
        else:
            # If all interests have been used recently, choose the least recent one
            for topic in user_interests:
                if topic not in recent_topics[-2:]:
                    return topic
            # If everything is too recent, force a different angle
            return random.choice(user_interests)
    else:
        # Repeat a topic but with a different angle
        if recent_topics:
            return random.choice(recent_topics[-2:])  # Choose from last 2 topics
        else:
            return random.choice(user_interests)

# Map proficiency level (1-100) to college semester (1-8) and description
def level_to_semester(level: int) -> tuple[int, str]:
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

def get_vocabulary_guidance(proficiency_level: int, target_language: str) -> str:
    """
    Generate specific vocabulary guidance based on proficiency level.
    This provides concrete examples without needing large vocab lists.
    """
    if proficiency_level <= 12:
        return f"""
VOCABULARY GUIDANCE FOR ABSOLUTE BEGINNER (Level {proficiency_level}/100):
- Use only the most basic words: greetings, simple verbs (ser/estar, tener, hacer), basic nouns (casa, trabajo, familia)
- Avoid complex vocabulary, idioms, or advanced grammar
- Stick to present tense only
- Use simple sentence structures: Subject + Verb + Object
- Maximum 1-2 new vocabulary words per email
- Focus on survival vocabulary: basic needs, simple questions, everyday objects
"""
    elif proficiency_level <= 25:
        return f"""
VOCABULARY GUIDANCE FOR BEGINNER (Level {proficiency_level}/100):
- Use basic everyday vocabulary: daily activities, common objects, simple emotions
- Include some basic adjectives and adverbs
- Can use simple past tense occasionally
- Avoid complex verb conjugations or subjunctive mood
- Maximum 2-3 new vocabulary words per email
- Focus on practical, frequently-used words
"""
    elif proficiency_level <= 37:
        return f"""
VOCABULARY GUIDANCE FOR LOWER INTERMEDIATE (Level {proficiency_level}/100):
- Use intermediate vocabulary: hobbies, work-related terms, cultural topics
- Can include some idiomatic expressions (but explain them)
- Use past and future tenses
- Include some compound sentences
- Maximum 3-4 new vocabulary words per email
- Can introduce abstract concepts but keep them simple
"""
    elif proficiency_level <= 50:
        return f"""
VOCABULARY GUIDANCE FOR INTERMEDIATE (Level {proficiency_level}/100):
- Use intermediate-advanced vocabulary: opinions, preferences, experiences
- Can include more complex sentence structures
- Use subjunctive mood occasionally
- Include cultural references and idioms
- Maximum 4-5 new vocabulary words per email
- Can discuss abstract topics but provide context
"""
    else:
        return f"""
VOCABULARY GUIDANCE FOR ADVANCED (Level {proficiency_level}/100):
- Use advanced vocabulary: complex topics, nuanced expressions, cultural depth
- Can include sophisticated grammar structures
- Use idioms and cultural references freely
- Maximum 5-6 new vocabulary words per email
- Can discuss abstract, complex topics
"""

def create_enhanced_prompt(user_context: Dict, recent_topics: List[str], should_use_new_topic: bool, next_topic: str = None) -> str:
    """
    Create an enhanced prompt with comprehensive user context and better topic/vocabulary control.
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

    # Enhanced topic guidance with better variety control
    topic_guidance = f"""
TOPIC GUIDANCE:
- Recent topics discussed: {', '.join(recent_topics) if recent_topics else 'None yet'}
- Should introduce new topic: {'Yes' if should_use_new_topic else 'No'}
- SELECTED TOPIC FOR THIS EMAIL: {next_topic if next_topic else 'Choose from interests'}
- Topic variety rule: If the same topic appears in 2+ recent emails, you MUST choose a different topic
- Available interests to choose from: {user_context['topics_of_interest']}
- If new topic: Chose a random topic that you are interested in!  Be creative!  Bennie is very adventurous and has a wide range of interesting experiences.  Be creative and make something fun and unique up that will expand our user's vocabulary!
- If repeating topic: Choose a completely different angle or situation
- Topic rotation: Cycle through their interests evenly over time
- Avoid topic repetition: Don't discuss the same specific topic within 5 emails
- IMPORTANT: Focus your email content around the selected topic: {next_topic}
"""

    # Enhanced vocabulary guidance
    vocab_guidance = get_vocabulary_guidance(user_context['proficiency_level'], user_context['target_language'])

    # Language and content requirements
    requirements = f"""
REQUIREMENTS:
- Write entirely in {user_context['target_language']}
- {vocab_guidance}
- Keep message to 3-4 sentences
- Include 2-3 new vocabulary words appropriate for their level
- End with an engaging question that invites a response
- Keep tone friendly, encouraging, and conversational
- End the email with a culturally appropriate closing and Bennie's name, in the target language:
  - Spanish: "Con cariño, Bennie"
  - French: "Avec amitié, Bennie"
  - Mandarin: "祝好 (Zhù hǎo), Bennie"
  - Japanese: "ベニーより (Bennie yori)"
  - German: "Viele Grüße, Bennie"
  - Italian: "Con affetto, Bennie"
- Add vocabulary definitions at the bottom after signature
- DO NOT mention their learning goals or proficiency level in the email
- Focus on natural conversation, not explicit teaching
- IMPORTANT: Use vocabulary that matches their exact level - don't overestimate their abilities
"""

    # Combine all sections
    full_prompt = f"""{bennie_identity}

{user_info}

{topic_guidance}

{vocab_guidance}

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
        
        # Analyze topic diversity and get user interests
        logger.info("Analyzing topic diversity...")
        recent_topics, should_use_new_topic, _ = analyze_topic_diversity(user_context["email_history"])
        
        # Parse user interests for better topic management
        logger.info("Parsing user interests...")
        user_interests = parse_user_interests(user_context['topics_of_interest'])
        
        # Get the next topic to use
        next_topic = get_next_topic(user_interests, recent_topics, should_use_new_topic)
        logger.info(f"Selected topic: {next_topic}")
        
        # Create enhanced prompt
        logger.info("Creating enhanced prompt...")
        enhanced_prompt = create_enhanced_prompt(user_context, recent_topics, should_use_new_topic, next_topic)
        
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
                    "auth_user_id": user_context["auth_user_id"],
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


