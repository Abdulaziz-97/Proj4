"""
State Management for UDA-Hub Multi-Agent System

This module defines the state structure that flows through the agent workflow.
State carries information between agents during ticket processing.
"""

from typing import TypedDict, Annotated, List, Optional, Dict, Any
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage


class SupportTicketState(TypedDict):
    """
    State that flows through the multi-agent workflow.
    
    This state is shared between all agents and accumulates information
    as the ticket is processed through the system.
    """
    
    # ============= MESSAGES =============
    # Standard LangGraph messages - conversation history
    messages: Annotated[List[BaseMessage], add_messages]
    
    # ============= TICKET INFORMATION =============
    ticket_id: str  # Unique ticket identifier
    user_id: str  # External user ID (e.g., 'a4ab87')
    channel: str  # Communication channel (chat, email, phone)
    
    # ============= CLASSIFICATION RESULTS =============
    # Set by classifier agent
    category: Optional[str]  # technical, billing, account, reservation, general
    urgency: Optional[str]  # low, medium, high, critical
    keywords: Optional[List[str]]  # Extracted keywords from ticket
    recommended_agent: Optional[str]  # Which agent should handle this
    
    # ============= KNOWLEDGE RETRIEVAL =============
    # Set by knowledge agent
    knowledge_retrieved: Optional[bool]  # Was knowledge search performed?
    knowledge_articles: Optional[List[Dict]]  # Retrieved articles
    confidence_score: Optional[float]  # Confidence in knowledge-based answer (0-1)
    
    # ============= ACCOUNT DATA =============
    # Set by account operations agent
    account_lookup_performed: Optional[bool]  # Was account lookup done?
    user_data: Optional[Dict]  # User account information
    subscription_data: Optional[Dict]  # Subscription details
    user_is_blocked: Optional[bool]  # Alert: user account blocked
    
    # ============= AGENT TRACKING =============
    current_step: str  # Current workflow step (e.g., "classification", "knowledge_retrieval")
    agents_called: List[str]  # List of agents that have been invoked
    tools_used: List[str]  # List of tools that have been called
    
    # ============= DECISION TRACKING =============
    requires_escalation: bool  # Should this ticket be escalated?
    escalation_reason: Optional[str]  # Why escalation is needed
    can_auto_resolve: bool  # Can system resolve without human?
    
    # ============= RESOLUTION =============
    status: str  # "processing", "resolved", "escalated", "failed"
    final_response: Optional[str]  # Final message to user
    resolution_summary: Optional[str]  # Summary of how ticket was resolved
    
    # ============= METADATA =============
    timestamp: Optional[str]  # When ticket processing started
    processing_time: Optional[float]  # Time taken to process (seconds)
    error_message: Optional[str]  # Any errors encountered


# Helper function to create initial state
def create_initial_state(
    ticket_id: str,
    user_id: str,
    user_message: str,
    channel: str = "chat"
) -> SupportTicketState:
    """
    Create initial state for a new ticket.
    
    Args:
        ticket_id: Unique ticket identifier
        user_id: External user ID
        user_message: The user's initial message/question
        channel: Communication channel
        
    Returns:
        Initial state dictionary
    """
    from langchain_core.messages import HumanMessage
    from datetime import datetime
    
    return {
        # Messages
        "messages": [HumanMessage(content=user_message)],
        
        # Ticket info
        "ticket_id": ticket_id,
        "user_id": user_id,
        "channel": channel,
        
        # Classification (to be filled by classifier)
        "category": None,
        "urgency": None,
        "keywords": None,
        "recommended_agent": None,
        
        # Knowledge retrieval (to be filled if knowledge agent is called)
        "knowledge_retrieved": False,
        "knowledge_articles": None,
        "confidence_score": None,
        
        # Account data (to be filled if account agent is called)
        "account_lookup_performed": False,
        "user_data": None,
        "subscription_data": None,
        "user_is_blocked": False,
        
        # Tracking
        "current_step": "initialized",
        "agents_called": [],
        "tools_used": [],
        
        # Decisions
        "requires_escalation": False,
        "escalation_reason": None,
        "can_auto_resolve": True,
        
        # Resolution
        "status": "processing",
        "final_response": None,
        "resolution_summary": None,
        
        # Metadata
        "timestamp": datetime.now().isoformat(),
        "processing_time": None,
        "error_message": None
    }


# Helper function to update state
def update_state(
    current_state: SupportTicketState,
    updates: Dict[str, Any]
) -> SupportTicketState:
    """
    Update state with new information from an agent.
    
    Args:
        current_state: Current state
        updates: Dictionary of fields to update
        
    Returns:
        Updated state
    """
    return {**current_state, **updates}


# Helper function to check if escalation is needed
def should_escalate(state: SupportTicketState) -> bool:
    """
    Determine if ticket should be escalated based on state.
    
    Args:
        state: Current ticket state
        
    Returns:
        True if escalation is needed
    """
    # Check explicit escalation flag
    if state.get("requires_escalation", False):
        return True
    
    # Check for blocked user
    if state.get("user_is_blocked", False):
        return True
    
    # Check if knowledge retrieval failed
    if state.get("knowledge_retrieved", False):
        confidence = state.get("confidence_score", 0)
        if confidence < 0.5:
            return True
    
    # Check for critical urgency
    if state.get("urgency") == "critical":
        return True
    
    # Check for specific categories that require escalation
    category = state.get("category", "")
    if category in ["refund", "billing"] and "refund" in state.get("keywords", []):
        return True
    
    return False


# State validation
def validate_state(state: SupportTicketState) -> tuple[bool, Optional[str]]:
    """
    Validate that state has required fields.
    
    Args:
        state: State to validate
        
    Returns:
        (is_valid, error_message)
    """
    required_fields = ["ticket_id", "user_id", "messages", "status"]
    
    for field in required_fields:
        if field not in state or state[field] is None:
            return False, f"Missing required field: {field}"
    
    # Validate status
    valid_statuses = ["processing", "resolved", "escalated", "failed"]
    if state["status"] not in valid_statuses:
        return False, f"Invalid status: {state['status']}"
    
    return True, None

