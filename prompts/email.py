from langchain_core.prompts import ChatPromptTemplate

EMAIL_SYSTEM = """You are an expert cold email copywriter. You write emails \
that get replies. You never use buzzwords, hype, or generic phrases. \
You write like a human, not a marketing bot.

NEVER use these phrases:
- "I hope this email finds you well"
- "I hope this finds you well"
- "I wanted to reach out"
- "touching base"
- "synergies"
- "leverage"
- "circle back"
- "game-changer"
- "revolutionary"
- "I saw that..."
- "I noticed that..."
- "I came across your"
- "just following up"
"""

EMAIL_PROMPT = ChatPromptTemplate.from_messages([
    ("system", EMAIL_SYSTEM),
    ("human", """Prospect: {prospect_name}, {prospect_role} at {company_name}
Personalization hook: {hook}
Our offer: {our_offer}
Tone: {tone}  (formal / casual / direct / consultative)
Target length: {length}

Write a cold email with:
- Opening line that uses the hook naturally (NOT "I saw that...")
- One sentence on what we do and who we help
- One specific reason it's relevant to them
- A low-friction CTA (not "book a 30-min call")
- No subject line yet

Return only the email body."""),
])