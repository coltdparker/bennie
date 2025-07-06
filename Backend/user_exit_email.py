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
        'spanish': '¡Que tengas un buen camino!',
        'french': 'Bonne route !',
        'chinese': '一路顺风！',
        'japanese': '道中お気をつけて！',
        'german': 'Gute Reise!',
        'italian': 'Buon viaggio!'
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

def create_exit_email_html(user_name: str, user_language: str) -> str:
    """
    Creates the HTML content for the exit email with custom styling.
    """
    greeting = get_language_greeting(user_language)
    language_name = get_language_name(user_language)
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Goodbye from Bennie</title>
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
                    Hi {user_name}! I wanted to reach out one more time to say goodbye and thank you for being part of our {language_name} learning community.
                </p>
            </div>
            
            <!-- Thank you section -->
            <div style="background-color: #E9E2DF; padding: 25px; border-radius: 12px; margin-bottom: 30px;">
                <h3 style="font-family: 'Playfair Display', serif; font-size: 20px; font-weight: 500; color: #1a1a1a; margin: 0 0 15px 0;">
                    Thank You for Learning With Me
                </h3>
                <p style="font-size: 16px; color: #4a4a4a; margin: 0 0 15px 0;">
                    It's been such a pleasure helping you on your {language_name} journey! Every conversation we've had has been special, and I've loved watching your progress and growth.
                </p>
                <p style="font-size: 16px; color: #4a4a4a; margin: 0;">
                    Remember, language learning is a marathon, not a sprint. The foundation you've built with our conversations will stay with you forever!
                </p>
            </div>
            
            <!-- Encouragement to continue -->
            <div style="margin-bottom: 30px;">
                <p style="font-size: 16px; color: #4a4a4a; margin: 0 0 15px 0;">
                    I hope our time together has inspired you to keep exploring {language_name} in your own way. Whether it's through movies, music, books, or conversations with native speakers, every little bit of practice counts.
                </p>
                <p style="font-size: 16px; color: #4a4a4a; margin: 0 0 15px 0;">
                    Don't forget the vocabulary we've covered together - those words are now part of your {language_name} toolkit! Keep using them whenever you can.
                </p>
                <p style="font-size: 16px; color: #4a4a4a; margin: 0;">
                    And remember, my friends ChatGPT, Gemini, and Claude are always there to help you with translations, grammar questions, or just to chat in {language_name} when you need some practice.
                </p>
            </div>
            
            <!-- Come back anytime -->
            <div style="background-color: #f8f8f8; padding: 25px; border-radius: 12px; margin-bottom: 30px; border-left: 4px solid #FA7561;">
                <h3 style="font-family: 'Playfair Display', serif; font-size: 20px; font-weight: 500; color: #1a1a1a; margin: 0 0 15px 0;">
                    You're Always Welcome Back
                </h3>
                <p style="font-size: 16px; color: #4a4a4a; margin: 0 0 15px 0;">
                    Life gets busy, priorities change, and that's totally okay! If you ever want to pick up where we left off or start fresh with a different language, I'll be here with open arms.
                </p>
                <p style="font-size: 16px; color: #4a4a4a; margin: 0;">
                    Just visit our website anytime and sign up again. I'll remember our conversations and we can continue your language journey together!
                </p>
            </div>
            
            <!-- Closing -->
            <div style="text-align: center; margin-top: 40px;">
                <p style="font-size: 18px; color: #FA7561; margin: 0 0 20px 0; font-weight: 500;">
                    Keep practicing and never give up on your dreams!
                </p>
                <p style="font-size: 16px; color: #4a4a4a; margin: 0;">
                    Wishing you all the best in your {language_name} adventures! 🌟
                </p>
            </div>
            
            <!-- Footer -->
            <div style="margin-top: 40px; padding-top: 30px; border-top: 1px solid #d1d1d1; text-align: center;">
                <p style="font-size: 14px; color: #6b6b6b; margin: 0;">
                    With gratitude and warm wishes,<br>
                    <strong>Bennie</strong><br>
                    Your AI Language Learning Friend
                </p>
                <p style="font-size: 12px; color: #6b6b6b; margin: 15px 0 0 0;">
                    P.S. You can always reach out to us at hello@itsbennie.com if you have any questions or just want to say hi!
                </p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html_content

def send_exit_email(user_name: str, user_email: str, user_language: str):
    """
    Sends a personalized exit email to users who unsubscribe.
    
    Args:
        user_name (str): The user's name
        user_email (str): The user's email address
        user_language (str): The language they were learning
    """
    load_dotenv()
    
    # Check if SendGrid API key is loaded
    sendgrid_key = os.getenv("SENDGRID_API_KEY")
    
    if not sendgrid_key:
        print("Error: SENDGRID_API_KEY not found in .env file")
        return False
    
    try:
        # Create HTML content
        html_content = create_exit_email_html(user_name, user_language)
        
        # Create plain text version for email clients that don't support HTML
        plain_text_content = f"""
Goodbye from Bennie

{get_language_greeting(user_language)}

Hi {user_name}! I wanted to reach out one more time to say goodbye and thank you for being part of our {get_language_name(user_language)} learning community.

THANK YOU FOR LEARNING WITH ME:
It's been such a pleasure helping you on your {get_language_name(user_language)} journey! Every conversation we've had has been special, and I've loved watching your progress and growth.

Remember, language learning is a marathon, not a sprint. The foundation you've built with our conversations will stay with you forever!

I hope our time together has inspired you to keep exploring {get_language_name(user_language)} in your own way. Whether it's through movies, music, books, or conversations with native speakers, every little bit of practice counts.

Don't forget the vocabulary we've covered together - those words are now part of your {get_language_name(user_language)} toolkit! Keep using them whenever you can.

And remember, my friends ChatGPT, Gemini, and Claude are always there to help you with translations, grammar questions, or just to chat in {get_language_name(user_language)} when you need some practice.

YOU'RE ALWAYS WELCOME BACK:
Life gets busy, priorities change, and that's totally okay! If you ever want to pick up where we left off or start fresh with a different language, I'll be here with open arms.

Just visit our website anytime and sign up again. I'll remember our conversations and we can continue your language journey together!

Keep practicing and never give up on your dreams! Wishing you all the best in your {get_language_name(user_language)} adventures!

With gratitude and warm wishes,
Bennie
Your AI Language Learning Friend

P.S. You can always reach out to us at hello@itsbennie.com if you have any questions or just want to say hi!
        """
        
        # Create email
        message = Mail(
            from_email='Bennie@itsbennie.com',
            to_emails=user_email,
            subject=f'Goodbye from Bennie - Thank You for Learning {get_language_name(user_language)} With Me 💛',
            html_content=html_content,
            plain_text_content=plain_text_content
        )
        
        # Send email
        print(f"Sending exit email to {user_name} ({user_email})")
        sg = SendGridAPIClient(sendgrid_key)
        response = sg.send(message)
        
        if response.status_code == 202:
            print(f"✓ Exit email sent to {user_name} successfully!")
            return True
        else:
            print(f"⚠ Unexpected status code: {response.status_code}")
            print(f"Response body: {response.body}")
            return False
        
    except Exception as e:
        print(f"Error sending exit email: {e}")
        return False

if __name__ == "__main__":
    print("Sending exit email...")
    # Test the exit email function
    success = send_exit_email(
        user_name="Colt", 
        user_email="coltdparker@gmail.com", 
        user_language="chinese"
    )
    
    if success:
        print("Exit email test completed successfully!")
    else:
        print("Exit email test failed.")
