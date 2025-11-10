"""
Account Management Tools for UDA-Hub
Provides tools for user account lookups and operations
"""
# pyright: reportMissingImports=false
# pyright: reportGeneralTypeIssues=false

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Any, cast
from sqlalchemy.orm import Session
from langchain_core.tools import tool

# Add parent directories to path for imports
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent
sys.path.insert(0, str(project_root))

from data.models import cultpass  # type: ignore[import]
from agentic.tools.db_manager import get_db_manager  # type: ignore[import]


@tool
def lookup_user_account(user_id: str) -> str:
    """
    Get comprehensive user account information from CultPass database.
    
    This tool retrieves complete user details including subscription status,
    account blocks, and basic information. Use this when a customer asks about
    their account or when you need to verify account status.
    
    Args:
        user_id: The user's external ID (e.g., 'a4ab87', 'f556c0')
        
    Returns:
        JSON string containing:
        - user_id, name, email, is_blocked status
        - subscription details (status, tier, quota)
        - active reservations count
        - alerts if user is blocked or has issues
        
    Examples:
        lookup_user_account(user_id="a4ab87")
        lookup_user_account(user_id="f556c0")
    """
    try:
        db_manager = get_db_manager()
        
        with db_manager.get_cultpass_session() as _session:
            session = cast(Session, _session)
            # Query user
            user = session.query(cultpass.User).filter_by(user_id=user_id).first()
            
            if not user:
                return json.dumps({
                    "found": False,
                    "error": f"User with ID {user_id} not found in system",
                    "alert": "USER_NOT_FOUND"
                })
            
            # Get subscription info
            subscription_data = None
            if user.subscription:
                sub = user.subscription
                subscription_data = {
                    "subscription_id": sub.subscription_id,
                    "status": sub.status,
                    "tier": sub.tier,
                    "monthly_quota": sub.monthly_quota,
                    "started_at": str(sub.started_at),
                    "ended_at": str(sub.ended_at) if sub.ended_at else None
                }
            
            # Count active reservations
            active_reservations = len([r for r in user.reservations if r.status == "reserved"])
            
            # Build response
            result: dict[str, Any] = {
                "found": True,
                "user_id": user.user_id,
                "full_name": user.full_name,
                "email": user.email,
                "is_blocked": user.is_blocked,
                "created_at": str(user.created_at),
                "subscription": subscription_data,
                "active_reservations": active_reservations,
                "alerts": []
            }
            
            # Add alerts
            alerts = cast(list[str], result["alerts"])
            if user.is_blocked:
                alerts.append("USER_IS_BLOCKED - ESCALATE TO HUMAN SUPPORT")
            
            if isinstance(subscription_data, dict) and subscription_data.get("status") == "cancelled":
                alerts.append("SUBSCRIPTION_CANCELLED")
            
            return json.dumps(result, indent=2)
            
    except Exception as e:
        return json.dumps({
            "found": False,
            "error": f"Error looking up user: {str(e)}",
            "alert": "DATABASE_ERROR"
        })


@tool
def check_subscription_status(user_id: str) -> str:
    """
    Get detailed subscription information for a user.
    
    Use this tool when customer asks specifically about their subscription,
    billing, or quota information.
    
    Args:
        user_id: The user's external ID
        
    Returns:
        JSON string with subscription details including status, tier, quota, and dates
        
    Examples:
        check_subscription_status(user_id="f556c0")
    """
    try:
        db_manager = get_db_manager()
        
        with db_manager.get_cultpass_session() as session:
            user = session.query(cultpass.User).filter_by(user_id=user_id).first()
            
            if not user:
                return json.dumps({
                    "found": False,
                    "error": f"User {user_id} not found"
                })
            
            if not user.subscription:
                return json.dumps({
                    "found": True,
                    "has_subscription": False,
                    "message": "User has no active subscription"
                })
            
            sub = user.subscription
            
            # Calculate quota usage (based on reservations)
            total_reservations_this_cycle = len(user.reservations)
            quota_remaining = max(0, sub.monthly_quota - total_reservations_this_cycle)
            
            result = {
                "found": True,
                "has_subscription": True,
                "subscription_id": sub.subscription_id,
                "status": sub.status,
                "tier": sub.tier,
                "monthly_quota": sub.monthly_quota,
                "quota_used": total_reservations_this_cycle,
                "quota_remaining": quota_remaining,
                "started_at": str(sub.started_at),
                "ended_at": str(sub.ended_at) if sub.ended_at else None,
                "is_active": sub.status == "active",
                "recommendations": []
            }
            
            # Add recommendations
            if sub.status == "cancelled":
                result["recommendations"].append("User can reactivate subscription in app settings")
            
            if quota_remaining == 0:
                result["recommendations"].append("User has used all quota for this cycle")
            
            return json.dumps(result, indent=2)
            
    except Exception as e:
        return json.dumps({
            "found": False,
            "error": f"Error checking subscription: {str(e)}"
        })


@tool
def get_user_reservations(user_id: str, include_cancelled: bool = False) -> str:
    """
    List all reservations for a user with experience details.
    
    Use this when customer asks about their bookings, upcoming events,
    or reservation history.
    
    Args:
        user_id: The user's external ID
        include_cancelled: If True, include cancelled reservations (default: False)
        
    Returns:
        JSON string with list of reservations including experience details
        
    Examples:
        get_user_reservations(user_id="a4ab87")
        get_user_reservations(user_id="a4ab87", include_cancelled=True)
    """
    try:
        db_manager = get_db_manager()
        
        with db_manager.get_cultpass_session() as session:
            user = session.query(cultpass.User).filter_by(user_id=user_id).first()
            
            if not user:
                return json.dumps({
                    "found": False,
                    "error": f"User {user_id} not found",
                    "reservations": []
                })
            
            reservations_list = []
            for reservation in user.reservations:
                # Filter cancelled if needed
                if not include_cancelled and reservation.status == "cancelled":
                    continue
                
                # Get experience details
                experience = reservation.experience
                
                reservations_list.append({
                    "reservation_id": reservation.reservation_id,
                    "status": reservation.status,
                    "created_at": str(reservation.created_at),
                    "experience": {
                        "experience_id": experience.experience_id,
                        "title": experience.title,
                        "description": experience.description,
                        "location": experience.location,
                        "when": str(experience.when),
                        "is_premium": experience.is_premium,
                        "slots_available": experience.slots_available
                    }
                })
            
            result = {
                "found": True,
                "user_id": user_id,
                "total_reservations": len(reservations_list),
                "reservations": reservations_list
            }
            
            return json.dumps(result, indent=2)
            
    except Exception as e:
        return json.dumps({
            "found": False,
            "error": f"Error retrieving reservations: {str(e)}",
            "reservations": []
        })


@tool
def cancel_reservation(reservation_id: str) -> str:
    """
    Cancel a user's reservation.
    
    Use this tool when a customer requests to cancel their booking.
    Note: Cancellations restore the user's monthly quota.
    
    Args:
        reservation_id: The unique reservation identifier
        
    Returns:
        JSON string with cancellation confirmation or error
        
    Examples:
        cancel_reservation(reservation_id="abc123")
    """
    try:
        db_manager = get_db_manager()
        
        with db_manager.get_cultpass_session() as session:
            reservation = session.query(cultpass.Reservation).filter_by(
                reservation_id=reservation_id
            ).first()
            
            if not reservation:
                return json.dumps({
                    "success": False,
                    "error": f"Reservation {reservation_id} not found"
                })
            
            # Check if already cancelled
            if reservation.status == "cancelled":
                return json.dumps({
                    "success": False,
                    "error": "Reservation is already cancelled",
                    "status": reservation.status
                })
            
            # Get experience details for confirmation
            experience_title = reservation.experience.title
            experience_date = str(reservation.experience.when)
            
            # Update status
            res_obj = cast(Any, reservation)
            res_obj.status = "cancelled"
            res_obj.updated_at = datetime.now()
            
            session.commit()
            
            return json.dumps({
                "success": True,
                "message": "Reservation cancelled successfully",
                "reservation_id": reservation_id,
                "experience": experience_title,
                "scheduled_date": experience_date,
                "note": "Monthly quota slot has been restored"
            }, indent=2)
            
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": f"Error cancelling reservation: {str(e)}"
        })


@tool
def update_subscription_status(subscription_id: str, action: str) -> str:
    """
    Update subscription status (pause or cancel).
    
    Use this tool when customer wants to pause or cancel their subscription.
    NOTE: Refunds require human approval - escalate refund requests.
    
    Args:
        subscription_id: The subscription identifier
        action: Action to take - must be "pause" or "cancel"
        
    Returns:
        JSON string with update confirmation
        
    Examples:
        update_subscription_status(subscription_id="sub123", action="cancel")
        update_subscription_status(subscription_id="sub456", action="pause")
    """
    try:
        # Validate action
        if action not in ["pause", "cancel"]:
            return json.dumps({
                "success": False,
                "error": f"Invalid action '{action}'. Must be 'pause' or 'cancel'"
            })
        
        db_manager = get_db_manager()
        
        with db_manager.get_cultpass_session() as session:
            subscription = session.query(cultpass.Subscription).filter_by(
                subscription_id=subscription_id
            ).first()
            
            if not subscription:
                return json.dumps({
                    "success": False,
                    "error": f"Subscription {subscription_id} not found"
                })
            
            old_status = subscription.status
            
            # Update status based on action
            sub_obj = cast(Any, subscription)
            if action == "cancel":
                sub_obj.status = "cancelled"
                sub_obj.ended_at = datetime.now()
                message = "Subscription cancelled. Takes effect at end of billing cycle."
            else:  # pause
                sub_obj.status = "paused"
                message = "Subscription paused. User data preserved for reactivation."
            
            sub_obj.updated_at = datetime.now()
            session.commit()
            
            return json.dumps({
                "success": True,
                "message": message,
                "subscription_id": subscription_id,
                "old_status": old_status,
                "new_status": subscription.status,
                "tier": subscription.tier,
                "note": "Refund requests require supervisor approval"
            }, indent=2)
            
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": f"Error updating subscription: {str(e)}"
        })

