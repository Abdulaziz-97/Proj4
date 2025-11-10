"""
Memory and Ticket History Tools for UDA-Hub
Provides tools for retrieving and storing customer interaction history
"""

import json
import sys
import uuid
from pathlib import Path
from datetime import datetime
from typing import Optional
from langchain_core.tools import tool

# Add parent directories to path for imports
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent
sys.path.insert(0, str(project_root))

from data.models import udahub
from agentic.tools.db_manager import get_db_manager


@tool
def get_user_ticket_history(external_user_id: str, limit: int = 5, account_id: str = "cultpass") -> str:
    """
    Retrieve a user's previous ticket history for context.
    
    This provides long-term memory by showing past interactions, which helps
    personalize responses and identify recurring issues.
    
    Args:
        external_user_id: The user's ID from external system (e.g., 'a4ab87')
        limit: Maximum number of recent tickets to retrieve (default: 5)
        account_id: Account identifier (default: "cultpass")
        
    Returns:
        JSON string with list of previous tickets including:
        - ticket_id, status, main_issue_type
        - creation date
        - message count
        - resolution summary
        
    Examples:
        get_user_ticket_history(external_user_id="a4ab87", limit=3)
    """
    try:
        db_manager = get_db_manager()
        
        with db_manager.get_udahub_session() as session:
            # Find user in UdaHub system
            user = session.query(udahub.User).filter_by(
                account_id=account_id,
                external_user_id=external_user_id
            ).first()
            
            if not user:
                return json.dumps({
                    "found": False,
                    "message": f"No ticket history found for user {external_user_id}",
                    "tickets": []
                })
            
            # Get user's tickets, ordered by most recent
            tickets = session.query(udahub.Ticket).filter_by(
                user_id=user.user_id
            ).order_by(udahub.Ticket.created_at.desc()).limit(limit).all()
            
            ticket_history = []
            for ticket in tickets:
                # Get metadata
                metadata = ticket.ticket_metadata
                
                # Count messages
                message_count = len(ticket.messages)
                
                # Get last message preview
                last_message = ticket.messages[-1].content[:100] if ticket.messages else "No messages"
                
                ticket_history.append({
                    "ticket_id": ticket.ticket_id,
                    "created_at": str(ticket.created_at),
                    "channel": ticket.channel,
                    "status": metadata.status if metadata else "unknown",
                    "main_issue_type": metadata.main_issue_type if metadata else None,
                    "tags": metadata.tags if metadata else None,
                    "message_count": message_count,
                    "last_message_preview": last_message
                })
            
            result = {
                "found": True,
                "user_id": external_user_id,
                "user_name": user.user_name,
                "total_tickets_retrieved": len(ticket_history),
                "tickets": ticket_history,
                "insight": f"User has {len(ticket_history)} previous interaction(s) on record"
            }
            
            return json.dumps(result, indent=2)
            
    except Exception as e:
        return json.dumps({
            "found": False,
            "error": f"Error retrieving ticket history: {str(e)}",
            "tickets": []
        })


@tool
def get_ticket_details(ticket_id: str) -> str:
    """
    Get complete details of a specific ticket including all messages.
    
    Use this to retrieve full conversation history for a ticket.
    
    Args:
        ticket_id: The ticket identifier
        
    Returns:
        JSON string with complete ticket information and message thread
    """
    try:
        db_manager = get_db_manager()
        
        with db_manager.get_udahub_session() as session:
            ticket = session.query(udahub.Ticket).filter_by(ticket_id=ticket_id).first()
            
            if not ticket:
                return json.dumps({
                    "found": False,
                    "error": f"Ticket {ticket_id} not found"
                })
            
            # Get all messages
            messages = []
            for msg in ticket.messages:
                messages.append({
                    "message_id": msg.message_id,
                    "role": msg.role.name if hasattr(msg.role, 'name') else str(msg.role),
                    "content": msg.content,
                    "created_at": str(msg.created_at)
                })
            
            # Get metadata
            metadata = ticket.ticket_metadata
            
            result = {
                "found": True,
                "ticket_id": ticket.ticket_id,
                "user_id": ticket.user.external_user_id,
                "user_name": ticket.user.user_name,
                "channel": ticket.channel,
                "created_at": str(ticket.created_at),
                "status": metadata.status if metadata else "unknown",
                "main_issue_type": metadata.main_issue_type if metadata else None,
                "tags": metadata.tags if metadata else None,
                "messages": messages,
                "message_count": len(messages)
            }
            
            return json.dumps(result, indent=2)
            
    except Exception as e:
        return json.dumps({
            "found": False,
            "error": f"Error retrieving ticket: {str(e)}"
        })


@tool
def update_ticket_status(ticket_id: str, status: str, main_issue_type: Optional[str] = None) -> str:
    """
    Update a ticket's status and classification.
    
    Use this to mark tickets as resolved, escalated, etc.
    
    Args:
        ticket_id: The ticket identifier
        status: New status (e.g., "open", "resolved", "escalated", "closed")
        main_issue_type: Optional issue classification (e.g., "technical", "billing")
        
    Returns:
        JSON string with update confirmation
        
    Examples:
        update_ticket_status(ticket_id="123", status="resolved", main_issue_type="technical")
        update_ticket_status(ticket_id="456", status="escalated")
    """
    try:
        db_manager = get_db_manager()
        
        with db_manager.get_udahub_session() as session:
            ticket = session.query(udahub.Ticket).filter_by(ticket_id=ticket_id).first()
            
            if not ticket:
                return json.dumps({
                    "success": False,
                    "error": f"Ticket {ticket_id} not found"
                })
            
            # Get or create metadata
            metadata = ticket.ticket_metadata
            if not metadata:
                metadata = udahub.TicketMetadata(
                    ticket_id=ticket_id,
                    status=status,
                    main_issue_type=main_issue_type
                )
                session.add(metadata)
            else:
                old_status = metadata.status
                metadata.status = status
                if main_issue_type:
                    metadata.main_issue_type = main_issue_type
                metadata.updated_at = datetime.now()
            
            session.commit()
            
            return json.dumps({
                "success": True,
                "ticket_id": ticket_id,
                "new_status": status,
                "main_issue_type": main_issue_type,
                "updated_at": str(datetime.now())
            }, indent=2)
            
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": f"Error updating ticket: {str(e)}"
        })


@tool
def add_ticket_message(ticket_id: str, role: str, content: str) -> str:
    """
    Add a new message to a ticket (for logging AI responses or agent notes).
    
    Args:
        ticket_id: The ticket identifier
        role: Message role ("ai", "agent", "system")
        content: Message content
        
    Returns:
        JSON string with message creation confirmation
        
    Examples:
        add_ticket_message(ticket_id="123", role="ai", content="I've found a solution...")
    """
    try:
        # Validate role
        valid_roles = ["ai", "agent", "system", "user"]
        if role not in valid_roles:
            return json.dumps({
                "success": False,
                "error": f"Invalid role '{role}'. Must be one of: {valid_roles}"
            })
        
        db_manager = get_db_manager()
        
        with db_manager.get_udahub_session() as session:
            ticket = session.query(udahub.Ticket).filter_by(ticket_id=ticket_id).first()
            
            if not ticket:
                return json.dumps({
                    "success": False,
                    "error": f"Ticket {ticket_id} not found"
                })
            
            # Create new message
            message = udahub.TicketMessage(
                message_id=str(uuid.uuid4()),
                ticket_id=ticket_id,
                role=role,
                content=content
            )
            
            session.add(message)
            session.commit()
            
            return json.dumps({
                "success": True,
                "message_id": message.message_id,
                "ticket_id": ticket_id,
                "role": role,
                "created_at": str(message.created_at)
            }, indent=2)
            
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": f"Error adding message: {str(e)}"
        })


@tool
def create_escalation_ticket(external_user_id: str, issue_summary: str, 
                             reason: str, original_ticket_id: Optional[str] = None,
                             account_id: str = "cultpass") -> str:
    """
    Create an escalation ticket for human review.
    
    Use this when an issue requires human intervention (refunds, blocked accounts,
    complex problems, etc.)
    
    Args:
        external_user_id: User's external ID
        issue_summary: Brief description of the issue
        reason: Escalation reason (e.g., "refund_request", "account_blocked", "no_knowledge_found")
        original_ticket_id: Optional reference to original ticket
        account_id: Account identifier (default: "cultpass")
        
    Returns:
        JSON string with escalation ticket details
        
    Examples:
        create_escalation_ticket(
            external_user_id="a4ab87",
            issue_summary="User requests refund for last month",
            reason="refund_request"
        )
    """
    try:
        db_manager = get_db_manager()
        
        with db_manager.get_udahub_session() as session:
            # Find or create user
            user = session.query(udahub.User).filter_by(
                account_id=account_id,
                external_user_id=external_user_id
            ).first()
            
            if not user:
                return json.dumps({
                    "success": False,
                    "error": f"User {external_user_id} not found in UdaHub system"
                })
            
            # Create escalation ticket
            ticket_id = str(uuid.uuid4())
            ticket = udahub.Ticket(
                ticket_id=ticket_id,
                account_id=account_id,
                user_id=user.user_id,
                channel="escalation"
            )
            
            # Create metadata
            metadata = udahub.TicketMetadata(
                ticket_id=ticket_id,
                status="escalated",
                main_issue_type="escalation",
                tags=f"escalation,{reason}"
            )
            
            # Create initial message
            escalation_content = f"""ESCALATION REQUIRED

Reason: {reason}
Issue Summary: {issue_summary}
Original Ticket: {original_ticket_id if original_ticket_id else 'N/A'}

This ticket requires human review and intervention.
"""
            
            message = udahub.TicketMessage(
                message_id=str(uuid.uuid4()),
                ticket_id=ticket_id,
                role="system",
                content=escalation_content
            )
            
            session.add_all([ticket, metadata, message])
            session.commit()
            
            return json.dumps({
                "success": True,
                "escalation_ticket_id": ticket_id,
                "user_id": external_user_id,
                "user_name": user.user_name,
                "reason": reason,
                "status": "escalated",
                "message": "Escalation ticket created successfully. Human support team will review."
            }, indent=2)
            
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": f"Error creating escalation ticket: {str(e)}"
        })

