"""
Memory Management for UDA-Hub Multi-Agent System

Handles both short-term (session) and long-term (persistent) memory.
"""

import json
from typing import List, Dict, Optional, Any
from datetime import datetime
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, AIMessage
from langgraph.checkpoint.memory import MemorySaver

import sys
from pathlib import Path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from agentic.tools.memory_tools import get_user_ticket_history


class MemoryManager:
    """
    Manages conversation memory and user history.
    
    Types of memory:
    1. Short-term (Session): Conversation within same ticket (thread_id)
    2. Long-term (Persistent): User's ticket history across sessions
    """
    
    def __init__(self, checkpointer: Optional[MemorySaver] = None):
        """
        Initialize memory manager.
        
        Args:
            checkpointer: LangGraph checkpointer for short-term memory
        """
        self.checkpointer = checkpointer or MemorySaver()
        self.memory_cache = {}  # In-memory cache for performance
    
    # ============= SHORT-TERM MEMORY (Session) =============
    
    def get_session_config(self, ticket_id: str) -> Dict[str, Any]:
        """
        Get LangGraph config for session memory.
        
        This enables conversation continuity within the same ticket.
        Messages are preserved across multiple turns.
        
        Args:
            ticket_id: Ticket ID to use as thread_id
            
        Returns:
            Configuration dict for LangGraph
            
        Example:
            config = memory.get_session_config("ticket-123")
            result = orchestrator.invoke(state, config=config)
        """
        return {
            "configurable": {
                "thread_id": ticket_id,
                # Optional: Add session-specific metadata
                "session_started": datetime.now().isoformat()
            }
        }
    
    # ============= LONG-TERM MEMORY (Persistent) =============
    
    def get_user_history(
        self, 
        user_id: str, 
        limit: int = 5
    ) -> Dict[str, Any]:
        """
        Retrieve user's ticket history (long-term memory).
        
        This provides context about user's past interactions,
        enabling personalized support.
        
        Args:
            user_id: External user ID
            limit: Number of past tickets to retrieve
            
        Returns:
            Dictionary with user's ticket history
            
        Example:
            history = memory.get_user_history("a4ab87", limit=3)
            if history['found']:
                print(f"User has {history['total_tickets_retrieved']} past tickets")
        """
        # Check cache first
        cache_key = f"user_history_{user_id}_{limit}"
        if cache_key in self.memory_cache:
            cached_data, cached_time = self.memory_cache[cache_key]
            # Use cache if less than 5 minutes old
            if (datetime.now() - cached_time).seconds < 300:
                return cached_data
        
        # Retrieve from database using tool
        try:
            result_str = get_user_ticket_history.invoke({
                "external_user_id": user_id,
                "limit": limit
            })
            result = json.loads(result_str)
            
            # Cache the result
            self.memory_cache[cache_key] = (result, datetime.now())
            
            return result
        except Exception as e:
            return {
                "found": False,
                "error": str(e),
                "tickets": []
            }
    
    def enrich_state_with_history(
        self, 
        state: Dict[str, Any], 
        user_id: str
    ) -> Dict[str, Any]:
        """
        Enrich state with user's ticket history for context.
        
        This adds long-term memory to the current state, allowing
        agents to provide personalized responses based on past interactions.
        
        Args:
            state: Current ticket state
            user_id: User ID to look up history for
            
        Returns:
            State enriched with history context
            
        Example:
            state = memory.enrich_state_with_history(state, "a4ab87")
            # Now state['messages'] includes history context
        """
        history = self.get_user_history(user_id, limit=3)
        
        if history.get("found", False) and history.get("tickets"):
            # Create context message summarizing past interactions
            tickets = history["tickets"]
            
            context_parts = [
                f"User History Context for {history.get('user_name', user_id)}:",
                f"- Total previous tickets: {len(tickets)}"
            ]
            
            for i, ticket in enumerate(tickets, 1):
                context_parts.append(
                    f"- Ticket {i}: {ticket.get('main_issue_type', 'Unknown')} "
                    f"({ticket.get('status', 'unknown')} on {ticket.get('created_at', 'N/A')[:10]})"
                )
            
            # Check for recurring issues
            issue_types = [t.get('main_issue_type') for t in tickets if t.get('main_issue_type')]
            if len(issue_types) > 1 and len(set(issue_types)) < len(issue_types):
                context_parts.append("WARNING: RECURRING ISSUE DETECTED")
            
            context_message = SystemMessage(content="\n".join(context_parts))
            
            # Add to beginning of messages (after user message)
            messages = state.get("messages", [])
            if messages:
                state["messages"] = [messages[0], context_message] + messages[1:]
            else:
                state["messages"] = [context_message]
        
        return state
    
    # ============= MEMORY STORAGE =============
    
    def store_interaction(
        self,
        ticket_id: str,
        user_id: str,
        category: str,
        resolution: str,
        status: str
    ) -> bool:
        """
        Store completed interaction for future reference (long-term memory).
        
        This saves the interaction to the database so it can be retrieved
        in future sessions for context.
        
        Args:
            ticket_id: Ticket ID
            user_id: User ID
            category: Issue category
            resolution: How issue was resolved
            status: Final status (resolved/escalated)
            
        Returns:
            True if stored successfully
        """
        from agentic.tools.memory_tools import update_ticket_status, add_ticket_message
        
        try:
            # Update ticket status
            update_ticket_status.invoke({
                "ticket_id": ticket_id,
                "status": status,
                "main_issue_type": category
            })
            
            # Add resolution message
            add_ticket_message.invoke({
                "ticket_id": ticket_id,
                "role": "ai",
                "content": f"Resolution: {resolution}"
            })
            
            # Clear cache for this user
            cache_keys = [k for k in self.memory_cache.keys() if user_id in k]
            for key in cache_keys:
                del self.memory_cache[key]
            
            return True
        except Exception as e:
            print(f"Error storing interaction: {e}")
            return False


# Global memory manager instance
_memory_manager = None

def get_memory_manager() -> MemoryManager:
    """Get or create global memory manager instance"""
    global _memory_manager
    if _memory_manager is None:
        _memory_manager = MemoryManager()
    return _memory_manager


# Helper function for agents to access memory
def get_contextualized_state(
    state: Dict[str, Any],
    include_history: bool = True
) -> Dict[str, Any]:
    """
    Helper function to add memory context to state.
    
    Use this in agent nodes to enrich state with user history.
    
    Args:
        state: Current state
        include_history: Whether to include long-term memory
        
    Returns:
        State with memory context added
        
    Example:
        def knowledge_node(state):
            # Enrich with memory context
            state = get_contextualized_state(state)
            # Now agent can see user's history
            ...
    """
    if not include_history:
        return state
    
    user_id = state.get("user_id")
    if not user_id:
        return state
    
    memory = get_memory_manager()
    return memory.enrich_state_with_history(state, user_id)

