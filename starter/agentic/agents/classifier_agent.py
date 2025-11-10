"""
Classifier Agent - Categorizes and prioritizes tickets
"""

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage
from langgraph.prebuilt import create_react_agent


def create_classifier_agent(llm: ChatOpenAI):
    """
    Classifies tickets by category and urgency.
    
    Args:
        llm: Language model to use
        
    Returns:
        Agent that classifies tickets
    """
    
    system_prompt = SystemMessage(content="""
You are a ticket classification specialist for CultPass customer support.

Analyze the ticket and return JSON with this structure:
{
    "category": "technical|billing|account|reservation|general",
    "urgency": "low|medium|high|critical",
    "keywords": ["keyword1", "keyword2"],
    "recommended_agent": "knowledge|account_ops|escalation"
}

Classification Rules:

**Categories:**
- "technical": login, app crashes, QR codes, payment method updates
- "billing": invoices, charges, promo codes, refunds
- "account": profile, blocked accounts, settings, preferences  
- "reservation": bookings, cancellations, event issues
- "general": how-to questions, general inquiries

**Urgency:**
- "critical": account blocked, security issues, event happening now
- "high": payment failures, event today/tomorrow, repeated issues
- "medium": upcoming events, feature questions, minor issues
- "low": general questions, how-to inquiries

**Routing:**
- "knowledge": FAQ, how-to, general information questions
- "account_ops": account lookups, subscription checks, reservations
- "escalation": refunds, blocked accounts, complex issues

**Special Cases:**
- If "blocked" or "suspended" → critical + escalation
- If "refund" → escalation
- If "how to" or "what is" → knowledge
- If "my account", "my subscription", "my bookings" → account_ops

Return ONLY the JSON object, nothing else.
""")
    
    return create_react_agent(
        name="classifier",
        model=llm,
        tools=[],  # No tools - pure classification
        prompt=system_prompt
    )
    