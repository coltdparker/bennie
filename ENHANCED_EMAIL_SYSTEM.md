# Enhanced Email System Documentation

## Overview

The enhanced email system provides comprehensive user context to OpenAI's GPT-4 model, enabling personalized, engaging, and educationally effective language learning emails. The system includes topic diversity management, user preference integration, and optimized token usage.

## Key Features

### 🎯 **Comprehensive User Context**
- **User Profile**: Name, target language, proficiency level (1-100)
- **Learning Goals**: User's specific objectives for language learning
- **Interests**: Topics that engage the user personally
- **Email History**: Last 20 messages for conversation continuity
- **Topic Diversity**: Smart topic rotation to prevent repetition

### 🧠 **Intelligent Topic Management**
- **50/50 Rule**: 50% chance of new topics vs. revisiting interests
- **7-Message Window**: Avoids repeating exact topics within 7 messages
- **Interest-Based**: All topics relate to user's stated interests
- **Natural Flow**: Topics feel conversational, not forced

### 📚 **Adaptive Language Complexity**
- **Level 1-20**: Basic vocabulary, simple sentences, cognates
- **Level 21-40**: Common phrases, present tense, basic questions
- **Level 41-60**: Past/future tense, compound sentences, cultural references
- **Level 61-80**: Complex grammar, idioms, nuanced expressions
- **Level 81-100**: Native-like fluency, sophisticated vocabulary

### 🎓 College Semester Mapping for Proficiency Levels

To provide more intuitive and pedagogically sound context for the LLM, Bennie now maps user proficiency levels (1-100) to equivalent U.S. college language semesters (1-8). This mapping helps the LLM tailor its output to what a student would be expected to handle at each stage of formal language study.

**Mapping Table:**

| Level Range | Semester | Description |
|-------------|----------|-------------|
| 1-12        | 1        | Absolute beginner. Greetings, basic phrases, simple questions. |
| 13-25       | 2        | Beginner. Simple present tense, basic questions, daily life topics. |
| 26-37       | 3        | Lower intermediate. Past/future tense, more vocabulary, short stories. |
| 38-50       | 4        | Intermediate. Complex sentences, opinions, short essays. |
| 51-62       | 5        | Upper intermediate. Argumentation, abstract topics, intro to literature. |
| 63-75       | 6        | Advanced. Advanced readings, idioms, cultural nuance. |
| 76-87       | 7        | Very advanced. Academic/professional topics, debates, research. |
| 88-100      | 8        | Near-native. Literature, advanced writing, slang, full fluency. |

**Rationale:**
- Most U.S. college language programs span 8 semesters (4 years) to reach near-native proficiency.
- This mapping provides the LLM with a familiar educational framework, making it easier to adjust vocabulary, grammar, and topics to the user's true ability.
- For example, a user at level 10 is treated as a first-semester student, while a user at level 90 is treated as an eighth-semester (senior/near-native) student.

**Prompt Usage:**
- The prompt includes a section like:
  ```
  SEMESTER CONTEXT:
  - The user's proficiency level of {level}/100 is equivalent to a college language learner in semester {semester} out of 8.
  - {semester_description}
  - Tailor your vocabulary, grammar, and topics to what a student would be expected to handle at this semester.
  ```
- This ensures the LLM produces output that is neither too simple nor too advanced for the user, and aligns with real-world language learning progressions.

## System Architecture

### Core Functions

#### `get_user_context(user_email: str) -> Dict`
Fetches comprehensive user information from the database:
- User profile (name, language, level, goals, interests)
- Recent email history (last 20 messages)
- Returns structured context for prompt generation

#### `analyze_topic_diversity(email_history: List[Dict]) -> Tuple[List[str], bool]`
Analyzes conversation history to determine topic strategy:
- Extracts topics from recent Bennie emails
- Implements 50/50 new vs. repeated topic logic
- Returns recent topics and topic strategy decision

#### `create_enhanced_prompt(user_context: Dict, recent_topics: List[str], should_use_new_topic: bool) -> str`
Creates optimized prompts following OpenAI best practices:
- System message defines Bennie's personality
- User message contains structured context
- Clear requirements and constraints
- Topic guidance for natural conversation flow

#### `send_language_learning_email(user_email: str)`
Main function that orchestrates the entire process:
- Fetches user context
- Analyzes topic diversity
- Creates enhanced prompt
- Generates email with OpenAI
- Sends via SendGrid
- Saves to email history

## Token Optimization Strategies

### Current Implementation
The system currently sends full context with each request, which is effective but can be optimized for cost and performance.

### Recommended Optimizations

#### 1. **Context Summarization**
```python
def summarize_user_context(user_context: Dict) -> str:
    """Create a concise summary of user context to reduce tokens."""
    return f"""
User: {user_context['name']} (Level {user_context['proficiency_level']}/100)
Language: {user_context['target_language']}
Interests: {user_context['topics_of_interest'][:100]}...
Recent topics: {', '.join(recent_topics[-3:])}  # Last 3 topics only
"""
```

#### 2. **Session Management with OpenAI**
OpenAI supports conversation sessions that can reduce token usage:

```python
# Initialize conversation session
session = client.beta.threads.create()

# Add context as initial message
client.beta.threads.messages.create(
    thread_id=session.id,
    role="user",
    content=user_context_summary
)

# Generate email using session
response = client.beta.threads.messages.create(
    thread_id=session.id,
    role="user", 
    content="Write today's email"
)
```

#### 3. **Context Caching**
Cache user context to avoid repeated database queries:

```python
from functools import lru_cache
import time

@lru_cache(maxsize=1000)
def get_cached_user_context(user_email: str, cache_timeout: int = 300):
    """Cache user context for 5 minutes to reduce database calls."""
    return get_user_context(user_email)
```

#### 4. **Progressive Context Loading**
Load context progressively based on conversation length:

```python
def get_adaptive_context(user_email: str, conversation_length: int) -> Dict:
    """Load context based on conversation stage."""
    if conversation_length < 5:
        # New user: full context
        return get_full_user_context(user_email)
    elif conversation_length < 20:
        # Established user: summary context
        return get_summary_user_context(user_email)
    else:
        # Long-term user: minimal context
        return get_minimal_user_context(user_email)
```

## OpenAI Best Practices Implementation

### 1. **System Message Design**
```python
system_message = """You are Bennie, a warm and enthusiastic AI language learning friend. 
You write natural, conversational emails in the user's target language, sharing your daily 
experiences while helping them learn. You're encouraging, curious, and genuinely interested 
in their lives."""
```

### 2. **Structured User Messages**
```python
user_message = f"""
USER CONTEXT:
- Name: {user_context['name']}
- Target Language: {user_context['target_language']}
- Proficiency Level: {user_context['proficiency_level']}/100
- Learning Goal: {user_context['learning_goal']}
- Interests: {user_context['topics_of_interest']}

TOPIC GUIDANCE:
- Recent topics: {recent_topics}
- New topic needed: {should_use_new_topic}

REQUIREMENTS:
- Write in {user_context['target_language']}
- Level {user_context['proficiency_level']} complexity
- 3-4 sentences
- Include 2-3 new vocabulary words
- End with engaging question
- Add vocabulary definitions
"""
```

### 3. **Temperature and Token Settings**
```python
completion = client.chat.completions.create(
    model="gpt-4o",
    messages=[system_message, user_message],
    max_tokens=600,  # Increased for more detailed responses
    temperature=0.8,  # Balanced creativity and consistency
    presence_penalty=0.1,  # Encourage topic diversity
    frequency_penalty=0.1   # Reduce repetition
)
```

## Database Schema Enhancements

### Recommended Additions

#### 1. **Topic Tracking Table**
```sql
CREATE TABLE IF NOT EXISTS public.conversation_topics (
    id bigint generated by default as identity not null,
    user_id bigint not null,
    topic text not null,
    topic_category text,
    used_at timestamp with time zone not null default now(),
    constraint conversation_topics_pkey primary key (id),
    constraint conversation_topics_user_id_fkey foreign key (user_id) references users (id)
);
```

#### 2. **User Session Table**
```sql
CREATE TABLE IF NOT EXISTS public.user_sessions (
    id bigint generated by default as identity not null,
    user_id bigint not null,
    openai_session_id text,
    context_summary text,
    created_at timestamp with time zone not null default now(),
    expires_at timestamp with time zone not null,
    constraint user_sessions_pkey primary key (id),
    constraint user_sessions_user_id_fkey foreign key (user_id) references users (id)
);
```

## Testing and Validation

### Test Script Usage
```bash
# Run comprehensive tests
python test_enhanced_email.py

# Test specific components
python -c "
from Backend.bennie_email_sender import get_user_context
context = get_user_context('user@example.com')
print(context)
"
```

### Validation Checklist
- [ ] User context fetched correctly
- [ ] Topic diversity logic working
- [ ] Prompt generation optimized
- [ ] Email content appropriate for user level
- [ ] Vocabulary words included and defined
- [ ] Email saved to history
- [ ] Token usage within acceptable limits

## Performance Monitoring

### Key Metrics
- **Token Usage**: Track prompt and completion tokens
- **Response Time**: Monitor email generation speed
- **User Engagement**: Track reply rates and conversation length
- **Cost Analysis**: Monitor OpenAI API costs per user

### Logging
```python
logger.info(f"📊 OpenAI Usage: {usage.prompt_tokens} prompt, {usage.completion_tokens} completion")
logger.info(f"💰 Estimated cost: ${estimated_cost}")
logger.info(f"⏱️ Response time: {response_time}ms")
```

## Future Enhancements

### 1. **Advanced Topic Analysis**
- NLP-based topic extraction
- Sentiment analysis for tone adjustment
- Cultural context awareness

### 2. **Learning Analytics**
- Progress tracking based on vocabulary usage
- Difficulty adjustment algorithms
- Engagement pattern analysis

### 3. **Multi-Modal Content**
- Image generation for visual context
- Audio pronunciation guides
- Interactive elements

### 4. **Personalization Engine**
- Machine learning for content optimization
- A/B testing for engagement improvement
- Dynamic difficulty adjustment

## Troubleshooting

### Common Issues

#### High Token Usage
- Implement context summarization
- Use session management
- Cache user context

#### Repetitive Topics
- Check topic diversity logic
- Verify interest parsing
- Review conversation history

#### Inappropriate Content Level
- Verify proficiency level in database
- Check level-based requirements
- Test with different user levels

### Debug Commands
```python
# Debug user context
context = get_user_context('user@example.com')
print(json.dumps(context, indent=2))

# Debug topic analysis
topics, new_topic = analyze_topic_diversity(context['email_history'])
print(f"Topics: {topics}, New topic: {new_topic}")

# Debug prompt generation
prompt = create_enhanced_prompt(context, topics, new_topic)
print(f"Prompt length: {len(prompt)}")
```

---

This enhanced system provides a solid foundation for personalized, engaging language learning emails while maintaining cost efficiency and scalability. 