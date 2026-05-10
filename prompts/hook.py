from langchain_core.prompts import ChatPromptTemplate

HOOK_SYSTEM = """You are an expert sales researcher. Your job is to find \
the single most compelling personalization hook from a company's public \
information — something specific enough that the recipient will think \
"this person actually researched me."

NEVER use these phrases in the hook:
- "I hope this email finds you well"
- "I wanted to reach out"
- "touching base"
- "synergies"
- "leverage"
- "circle back"
- "I saw that..."
- "I noticed that..."
"""

HOOK_PROMPT = ChatPromptTemplate.from_messages([
    ("system", HOOK_SYSTEM),
    ("human", """Company info scraped from their website and news:
{company_research}

Prospect role: {prospect_role}
Our product/service: {our_offer}

Find ONE specific hook. It must be:
- Based on something real from the research (not generic)
- Relevant to why our offer helps THEM specifically
- A recent event, achievement, pain point, or specific detail

Return only: HOOK: [one sentence hook]"""),
])