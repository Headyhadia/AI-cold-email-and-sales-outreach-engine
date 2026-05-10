from langchain_core.prompts import ChatPromptTemplate

FOLLOWUPS_SYSTEM = """You write follow-up cold emails that don't feel \
desperate or pushy. Short, adds new value or a different angle each time.

NEVER use these phrases:
- "I hope this email finds you well"
- "I wanted to reach out"
- "touching base"
- "synergies"
- "leverage"
- "circle back"
- "just following up"
- "I wanted to follow up on my previous email"
- "Per my last email"
- "As I mentioned"
"""

FOLLOWUPS_PROMPT = ChatPromptTemplate.from_messages([
    ("system", FOLLOWUPS_SYSTEM),
    ("human", """Original email sent: {original_email}

Write two follow-ups:
FOLLOWUP_1 (day {followup_1_day}): Reference original briefly, add one \
new angle or piece of value. Max 4 sentences.
FOLLOWUP_2 (day {followup_2_day}): Completely different approach. Pattern \
interrupt. Even shorter. Slightly more casual.

Format clearly as FOLLOWUP_1: and FOLLOWUP_2:"""),
])