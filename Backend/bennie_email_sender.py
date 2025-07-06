# using SendGrid's Python Library
# https://github.com/sendgrid/sendgrid-python
import os
from dotenv import load_dotenv
import sendgrid
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from openai import OpenAI

load_dotenv()

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


# ==========================================
# Enhanced version with better error handling and formatting
def send_language_learning_email(user_name: str, user_email: str, user_language: str, user_level: int):
    """
    Enhanced version with better error handling
    """
    load_dotenv()
    
    # Check if API keys are loaded
    openai_key = os.getenv("OPENAI_API_KEY")
    sendgrid_key = os.getenv("SENDGRID_API_KEY")
    
    if not openai_key:
        print("Error: OPENAI_API_KEY not found in .env file")
        return
    
    if not sendgrid_key:
        print("Error: SENDGRID_API_KEY not found in .env file")
        return
    
    try:
        # Create OpenAI client
        client = OpenAI(api_key=openai_key)
        
        # Get response from OpenAI
        print("Getting response from OpenAI...")
        completion = client.chat.completions.create(
            model="gpt-4o", 
            messages=[
                {
                    "role": "user",
                    "content": f"""Your name is Bennie. You are a helpful AI friend who is helping {user_name} to learn {user_language} by sending them an email message talking about what you did today. 

Requirements:
- Write in {user_language}
- Cater to a level {str(user_level)} out of 100 speaker where 100 is a native level proficient speaker.
- Keep the message to 3-4 sentences
- End the message in a way that allows the email recipient to carry on the conversation with their own email response. 
- Use 3 words that are likely new to the user
- Keep the message friendly and engaging
- Include a signature as Bennie
- Include definitions of the 3 potentially new words at the bottom after the signature"""
                }
            ],
            max_tokens=500,
            temperature=0.7
        )
        
        # Print usage information
        model_rate = 0.0000025 # $/tolken
        usage = completion.usage
        total_usage = usage.total_tokens
        estimated_cost = total_usage * model_rate
        print(f"📊 OpenAI Usage: {usage.prompt_tokens} prompt tokens, {usage.completion_tokens} completion tokens, {usage.total_tokens} total tokens\nEstimated cost = ${estimated_cost}")


        bennies_response = completion.choices[0].message.content
        print("✓ Got response from OpenAI")
        print(f"Response length: {len(bennies_response)} characters")
        
        # Convert to HTML
        html_content = text_to_html(bennies_response)
        
        # Create email
        message = Mail(
            from_email='Bennie@itsbennie.com',
            to_emails=user_email,
            subject=get_email_subject(user_language=user_language),
            html_content=html_content,
            plain_text_content=bennies_response
        )
        
        # Send email
        print(f"Sending email to {user_name}")
        sg = SendGridAPIClient(sendgrid_key)
        response = sg.send(message)
        
        if response.status_code == 202:
            print(f"✓ Email sent to {user_name} successfully!")
            print(f"Check your inbox for the {user_language} learning email!")
        else:
            print(f"⚠ Unexpected status code: {response.status_code}")
            print(f"Response body: {response.body}")
        
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure both API keys are correctly set in your .env file")


if __name__ == "__main__":
    print("Sending email with language learning content...")
    send_language_learning_email(user_name="Colt", user_email="coltdparker@gmail.com", user_language="chinese", user_level=18)  # user_language is all lowercase


