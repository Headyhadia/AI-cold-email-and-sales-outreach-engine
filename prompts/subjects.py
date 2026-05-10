from langchain_core.prompts import ChatPromptTemplate

SUBJECTS_SYSTEM = """You write cold email subject lines with high open rates. \
Short. Specific. Human. Never salesy. No emojis. No ALL CAPS.

NEVER use these phrases or styles:
- "I hope this email finds you well"
- "touching base"
- "synergies"
- "leverage"
- Exclamation marks
- ALL CAPS words
- Clickbait or overly dramatic phrasing
"""

SUBJECTS_PROMPT = ChatPromptTemplate.from_messages([
    ("system", SUBJECTS_SYSTEM),
    ("human", """Email body: {email_body}
Prospect company: {company_name}

Write exactly 3 subject lines:
1. CURIOSITY: Creates mild intrigue without being clickbait
2. DIRECT: States the value prop plainly in under 7 words
3. QUESTION: Asks something specific to their situation

Format:
CURIOSITY: [subject]
DIRECT: [subject]
QUESTION: [subject]"""),
])