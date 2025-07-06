import os
from dotenv import load_dotenv
import sendgrid
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

load_dotenv()

def get_language_greeting(user_language: str) -> str:
    """
    Returns a fun greeting in the user's target language.
    
    Args:
        user_language (str): The language code (spanish, french, chinese, japanese, german, italian)
    
    Returns:
        str: A greeting in the target language
    """
    language_greetings = {
        'spanish': '¡Hola! ¿Cómo estás?',
        'french': 'Salut ! Comment ça va ?',
        'chinese': '你好！你最近好吗？',
        'japanese': 'こんにちは！お元気ですか？',
        'german': 'Hallo! Wie geht es dir?',
        'italian': 'Ciao! Come stai?'
    }
    
    language_clean = user_language.lower().strip()
    return language_greetings.get(language_clean, f'Hello! How are you? (Learning {user_language.title()})')

def get_language_name(user_language: str) -> str:
    """
    Returns the proper name of the language.
    """
    language_names = {
        'spanish': 'Spanish',
        'french': 'French',
        'chinese': 'Mandarin Chinese',
        'japanese': 'Japanese',
        'german': 'German',
        'italian': 'Italian'
    }
    
    language_clean = user_language.lower().strip()
    return language_names.get(language_clean, user_language.title())

def create_welcome_email_html(user_name: str, user_language: str, user_token: str = None) -> str:
    """
    Creates the HTML content for the welcome email with custom styling.
    """
    greeting = get_language_greeting(user_language)
    language_name = get_language_name(user_language)
    
    # Generate onboarding URL with token
    onboarding_url = f"https://itsbennie.com/onboard?token={user_token}" if user_token else "https://itsbennie.com/onboard?token=USER_TOKEN_PLACEHOLDER"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Welcome to Bennie!</title>
    </head>
    <body style="margin: 0; padding: 0; font-family: 'Inter', Arial, sans-serif; background-color: #f8f8f8; color: #1a1a1a; line-height: 1.6;">
        <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; padding: 40px 20px;">
            <!-- Header -->
            <div style="text-align: center; margin-bottom: 40px;">
                <h1 style="font-family: 'Playfair Display', serif; font-size: 32px; font-weight: 600; color: #FA7561; margin: 0 0 10px 0;">
                    Bennie
                </h1>
                <div style="width: 60px; height: 3px; background-color: #FA7561; margin: 0 auto;"></div>
            </div>
            
            <!-- Greeting -->
            <div style="margin-bottom: 30px;">
                <h2 style="font-family: 'Playfair Display', serif; font-size: 24px; font-weight: 500; color: #1a1a1a; margin: 0 0 15px 0;">
                    {greeting}
                </h2>
                <p style="font-size: 16px; color: #4a4a4a; margin: 0;">
                    Hi {user_name}! I'm Bennie, your new AI language learning friend. I'm so excited to help you on your journey to fluency in {language_name}! 🌟
                </p>
            </div>
            
            <!-- How it works -->
            <div style="background-color: #E9E2DF; padding: 25px; border-radius: 12px; margin-bottom: 30px;">
                <h3 style="font-family: 'Playfair Display', serif; font-size: 20px; font-weight: 500; color: #1a1a1a; margin: 0 0 15px 0;">
                    How Our Language Journey Works
                </h3>
                <p style="font-size: 16px; color: #4a4a4a; margin: 0 0 15px 0;">
                    I'll be sending you friendly emails every Monday, Wednesday, and Friday in {language_name}. Each email will include:
                </p>
                <ul style="font-size: 16px; color: #4a4a4a; margin: 0 0 15px 0; padding-left: 20px;">
                    <li style="margin-bottom: 8px;">Natural conversations about my day and interesting topics</li>
                    <li style="margin-bottom: 8px;">2-3 new vocabulary words with definitions to expand your knowledge</li>
                    <li style="margin-bottom: 8px;">Questions that encourage you to respond and practice</li>
                </ul>
                <p style="font-size: 16px; color: #4a4a4a; margin: 0;">
                    <strong>Pro tip:</strong> Don't worry if you don't understand every word! Use my friends ChatGPT, Gemini, or Claude to look up words and ask questions. My goal is to help you be consistent in engaging with {language_name} on steady rhythms.
                </p>
            </div>
            
            <!-- Encouragement -->
            <div style="margin-bottom: 30px;">
                <p style="font-size: 16px; color: #4a4a4a; margin: 0 0 15px 0;">
                    I absolutely love helping engaged learners like you grow fluent through consistent practice and engagement. Every response you send helps me understand your progress and tailor our conversations to your level.
                </p>
                <p style="font-size: 16px; color: #4a4a4a; margin: 0;">
                    When you reply to my emails, I'll review your responses to track your improvements over time and adjust our conversations accordingly. It's like having a personal language coach who remembers everything about your learning journey!
                </p>
            </div>
            
            <!-- Closing -->
            <div style="text-align: center; margin-top: 40px;">
                <p style="font-size: 18px; color: #FA7561; margin: 0 0 20px 0; font-weight: 500;">
                    I can't wait to start chatting with you!
                </p>
                <p style="font-size: 16px; color: #4a4a4a; margin: 0 0 30px 0;">
                    Your first {language_name} email will arrive soon. Get ready for some fun conversations! 🚀
                </p>
                
                <!-- Onboarding Button -->
                <div style="margin: 30px 0;">
                    <a href="{onboarding_url}" style="display: inline-block; background-color: #FA7561; color: white; text-decoration: none; padding: 15px 30px; border-radius: 8px; font-weight: 500; font-size: 16px; transition: background-color 0.3s ease;">
                        🎯 Help Bennie Get to Know You Better
                    </a>
                </div>
                
                <p style="font-size: 14px; color: #6b6b6b; margin: 0;">
                    (This helps me personalize your learning experience!)
                </p>
            </div>
            
            <!-- Footer -->
            <div style="margin-top: 40px; padding-top: 30px; border-top: 1px solid #d1d1d1; text-align: center;">
                <p style="font-size: 14px; color: #6b6b6b; margin: 0;">
                    With love and excitement,<br>
                    <strong>Bennie</strong><br>
                    Your AI Language Learning Friend
                </p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html_content

def send_welcome_email(user_name: str, user_email: str, user_language: str, user_token: str = None):
    """
    Sends a personalized welcome email to new users.
    
    Args:
        user_name (str): The user's name
        user_email (str): The user's email address
        user_language (str): The language they want to learn
    """
    load_dotenv()
    
    # Check if SendGrid API key is loaded
    sendgrid_key = os.getenv("SENDGRID_API_KEY")
    
    if not sendgrid_key:
        print("Error: SENDGRID_API_KEY not found in .env file")
        return False
    
    try:
        # Create HTML content
        html_content = create_welcome_email_html(user_name, user_language, user_token)
        
        # Create plain text version for email clients that don't support HTML
        plain_text_content = f"""
Welcome to Bennie!

{get_language_greeting(user_language)}

Hi {user_name}! I'm Bennie, your new AI language learning friend. I'm so excited to help you on your journey to fluency in {get_language_name(user_language)}!

HOW OUR LANGUAGE JOURNEY WORKS:
I'll be sending you friendly emails every Monday, Wednesday, and Friday in {get_language_name(user_language)}. Each email will include:
- Natural conversations about my day and interesting topics
- 2-3 new vocabulary words with definitions to expand your knowledge
- Questions that encourage you to respond and practice

Pro tip: Don't worry if you don't understand every word! Use my friends ChatGPT, Gemini, or Claude to look up words and ask questions. My goal is to help you be consistent in engaging with {get_language_name(user_language)} on steady rhythms.

I absolutely love helping engaged learners like you grow fluent through consistent practice and engagement. Every response you send helps me understand your progress and tailor our conversations to your level.

When you reply to my emails, I'll review your responses to track your improvements over time and adjust our conversations accordingly. It's like having a personal language coach who remembers everything about your learning journey!

I can't wait to start chatting with you! Your first {get_language_name(user_language)} email will arrive soon. Get ready for some fun conversations!

With love and excitement,
Bennie
Your AI Language Learning Friend
        """
        
        # Create email
        message = Mail(
            from_email='Bennie@itsbennie.com',
            to_emails=user_email,
            subject=f'Welcome to Bennie! Your {get_language_name(user_language)} Learning Journey Begins 🌟',
            html_content=html_content,
            plain_text_content=plain_text_content
        )
        
        # Send email
        print(f"Sending welcome email to {user_name} ({user_email})")
        sg = SendGridAPIClient(sendgrid_key)
        response = sg.send(message)
        
        if response.status_code == 202:
            print(f"✓ Welcome email sent to {user_name} successfully!")
            return True
        else:
            print(f"⚠ Unexpected status code: {response.status_code}")
            print(f"Response body: {response.body}")
            return False
        
    except Exception as e:
        print(f"Error sending welcome email: {e}")
        return False

if __name__ == "__main__":
    print("Sending welcome email...")
    # Test the welcome email function
    success = send_welcome_email(
        user_name="Colt", 
        user_email="coltdparker@gmail.com", 
        user_language="italian",
        user_token="test_token_123"
    )
    
    if success:
        print("Welcome email test completed successfully!")
    else:
        print("Welcome email test failed.")
