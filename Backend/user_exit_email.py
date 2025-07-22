import os
from dotenv import load_dotenv
import sendgrid
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from supabase import create_client

load_dotenv()

def get_language_name(language_code: str) -> str:
    """
    Convert language code to proper name.
    
    Args:
        language_code (str): The language code (spanish, french, mandarin, japanese, german, italian)
    
    Returns:
        str: The proper name of the language
    """
    language_names = {
        'spanish': 'Spanish',
        'french': 'French',
        'mandarin': 'Mandarin Chinese',
        'chinese': 'Mandarin Chinese',  # For backward compatibility
        'japanese': 'Japanese',
        'german': 'German',
        'italian': 'Italian'
    }
    return language_names.get(language_code.lower().strip(), language_code.title())

def get_language_greeting(language_code: str) -> str:
    """
    Get a farewell greeting in the target language.
    
    Args:
        language_code (str): The language code
    
    Returns:
        str: A farewell greeting in the target language
    """
    greetings = {
        'spanish': '¡Hasta luego y gracias por todo!',
        'french': 'Au revoir et merci pour tout !',
        'mandarin': '再见，谢谢你的一切！',
        'chinese': '再见，谢谢你的一切！',  # For backward compatibility
        'japanese': 'さようなら、すべてに感謝します！',
        'german': 'Auf Wiedersehen und danke für alles!',
        'italian': 'Arrivederci e grazie di tutto!'
    }
    return greetings.get(language_code.lower().strip(), 'Goodbye and thank you for everything!')

def create_exit_email_html(user_name: str, language: str) -> str:
    """Create HTML content for exit email."""
    return f"""
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="text-align: center; margin-bottom: 30px;">
            <h1 style="color: #FA7561;">Goodbye from Bennie</h1>
            <p style="font-size: 1.2em; color: #141414;">{get_language_greeting(language)}</p>
        </div>

        <p>Hi {user_name}! I wanted to reach out one more time to say goodbye and thank you for being part of our {get_language_name(language)} learning community.</p>

        <div style="background-color: #E9E2DF; padding: 20px; border-radius: 8px; margin: 20px 0;">
            <h2 style="color: #FA7561; margin-top: 0;">THANK YOU FOR LEARNING WITH ME:</h2>
            <p>It's been such a pleasure helping you on your {get_language_name(language)} journey! Every conversation we've had has been special, and I've loved watching your progress and growth.</p>
            <p>Remember, language learning is a marathon, not a sprint. The foundation you've built with our conversations will stay with you forever!</p>
        </div>

        <p>I hope our time together has inspired you to keep exploring {get_language_name(language)} in your own way. Whether it's through movies, music, books, or conversations with native speakers, every little bit of practice counts.</p>

        <p>Don't forget the vocabulary we've covered together - those words are now part of your {get_language_name(language)} toolkit! Keep using them whenever you can.</p>

        <p>And remember, my friends ChatGPT, Gemini, and Claude are always there to help you with translations, grammar questions, or just to chat in {get_language_name(language)}</p>

        <div style="background-color: #DAB785; padding: 20px; border-radius: 8px; margin: 20px 0;">
            <h2 style="color: #141414; margin-top: 0;">YOU'RE ALWAYS WELCOME BACK:</h2>
            <p>Life gets busy, priorities change, and that's totally okay! If you ever want to pick up where we left off or start fresh with a different language, I'll be here with open arms.</p>
            <p>Just visit our website anytime and sign up again. I'll remember our conversations and we can continue your language journey together!</p>
        </div>

        <p>Keep practicing and never give up on your dreams! Wishing you all the best in your {get_language_name(language)} adventures!</p>

        <div style="margin-top: 30px;">
            <p>With gratitude and warm wishes,<br>
            Bennie<br>
            <em>Your AI Language Learning Friend</em></p>
        </div>

        <div style="margin-top: 30px; font-size: 0.9em; color: #666;">
            <p>P.S. You can always reach out to us at hello@itsbennie.com if you have any questions or just want to say hi!</p>
        </div>
    </body>
    </html>
    """

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

And remember, my friends ChatGPT, Gemini, and Claude are always there to help you with translations, grammar questions, or just to chat in {get_language_name(user_language)}

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
            
            # Mark user as inactive in database
            try:
                # Get auth user first
                SUPABASE_URL = os.getenv("SUPABASE_URL")
                SUPABASE_KEY = os.getenv("SUPABASE_KEY")
                if not SUPABASE_URL or not SUPABASE_KEY:
                    print("Missing SUPABASE_URL or SUPABASE_KEY in environment.")
                    return True  # Still return True as email was sent
                
                supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
                
                # Get auth user
                auth_user = supabase.auth.admin.get_user_by_email(user_email)
                if auth_user:
                    # Update user profile
                    supabase.table("users").update({
                        "is_active": False,
                        "updated_at": "now()"
                    }).eq("auth_user_id", auth_user.id).execute()
                    print(f"✓ User {user_name} marked as inactive")
            except Exception as e:
                print(f"⚠️ Failed to mark user as inactive: {e}")
            
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
