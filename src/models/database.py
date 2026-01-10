"""
Database access layer using Supabase.
Handles all data persistence operations without business logic.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from supabase import create_client, Client
from src.config.settings import settings
from src.models.schemas import (
    Complaint, ComplaintCreate, ComplaintStatus, Escalation,
    EscalationLevel, Location
)
import structlog

logger = structlog.get_logger()


class Database:
    """Database access class for Supabase operations."""
    
    def __init__(self):
        """Initialize Supabase client."""
        # Use service key for backend operations to bypass RLS
        supabase_key = settings.supabase_service_key or settings.supabase_key
        self.client: Client = create_client(
            settings.supabase_url,
            supabase_key
        )
        logger.info("Database client initialized", url=settings.supabase_url, using_service_key=bool(settings.supabase_service_key))
    
    def create_complaint(self, complaint_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new complaint in the database.
        
        Args:
            complaint_data: Dictionary with complaint fields
        
        Returns:
            Created complaint record
        """
        try:
            result = self.client.table("complaints").insert(complaint_data).execute()
            if result.data:
                logger.info("Complaint created", complaint_id=result.data[0].get("id"))
                return result.data[0]
            raise Exception("Failed to create complaint")
        except Exception as e:
            error_str = str(e)
            # Check if error is about missing columns (sentiment fields)
            if "emotion_level" in error_str or "sentiment_score" in error_str or "urgency_boost" in error_str:
                logger.warning("Sentiment columns not found, storing in agent_metadata instead", error=error_str)
                # Remove sentiment columns and store in agent_metadata instead
                filtered_data = complaint_data.copy()
                sentiment_fields = {}
                
                for field in ["sentiment_score", "emotion_level", "urgency_boost"]:
                    if field in filtered_data:
                        sentiment_fields[field] = filtered_data.pop(field)
                
                # Add sentiment fields to agent_metadata if not already there
                if sentiment_fields and "agent_metadata" in filtered_data:
                    if "sentiment" not in filtered_data["agent_metadata"]:
                        filtered_data["agent_metadata"]["sentiment"] = {}
                    filtered_data["agent_metadata"]["sentiment"].update(sentiment_fields)
                
                # Retry without the problematic columns
                result = self.client.table("complaints").insert(filtered_data).execute()
                if result.data:
                    logger.info("Complaint created (sentiment in metadata)", complaint_id=result.data[0].get("id"))
                    return result.data[0]
            
            logger.error("Error creating complaint", error=str(e))
            raise
    
    def get_complaint(self, complaint_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a complaint by ID.
        
        Args:
            complaint_id: Unique complaint identifier
        
        Returns:
            Complaint record or None
        """
        try:
            result = self.client.table("complaints").select("*").eq("id", complaint_id).execute()
            if result.data:
                return result.data[0]
            return None
        except Exception as e:
            logger.error("Error fetching complaint", complaint_id=complaint_id, error=str(e))
            return None
    
    def update_complaint(
        self,
        complaint_id: str,
        updates: Dict[str, Any],
        send_notification: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Update a complaint record.
        
        Args:
            complaint_id: Unique complaint identifier
            updates: Dictionary of fields to update
            send_notification: Whether to send notification for status changes
        
        Returns:
            Updated complaint record or None
        """
        try:
            # Get current complaint to check status change
            current_complaint = self.get_complaint(complaint_id)
            old_status = current_complaint.get("status") if current_complaint else None
            new_status = updates.get("status")
            
            # Set updated_at timestamp
            updates["updated_at"] = datetime.utcnow().isoformat()
            
            # Handle agent_metadata updates (merge with existing)
            if "agent_metadata" in updates and current_complaint:
                existing_metadata = current_complaint.get("agent_metadata", {})
                if not isinstance(existing_metadata, dict):
                    existing_metadata = {}
                if isinstance(updates["agent_metadata"], dict):
                    # Merge metadata
                    existing_metadata.update(updates["agent_metadata"])
                    updates["agent_metadata"] = existing_metadata
                # Add timestamp to admin notes if present
                if "admin_notes" in existing_metadata and isinstance(existing_metadata["admin_notes"], list):
                    for note in existing_metadata["admin_notes"]:
                        if isinstance(note, dict) and "timestamp" not in note:
                            note["timestamp"] = datetime.utcnow().isoformat()
            
            result = self.client.table("complaints").update(updates).eq("id", complaint_id).execute()
            
            if result.data:
                updated_complaint = result.data[0]
                logger.info("Complaint updated", complaint_id=complaint_id, status_change=f"{old_status} -> {new_status}")
                
                # Send notification if status changed and notification is enabled
                if send_notification and new_status and old_status != new_status and current_complaint:
                    from src.services.notification_service import notification_service
                    
                    citizen_email = current_complaint.get("citizen_email")
                    citizen_name = current_complaint.get("citizen_name", "Citizen")
                    department = updated_complaint.get("responsible_department", "Department")
                    
                    if citizen_email:
                        # Send appropriate notification based on status
                        if new_status == ComplaintStatus.IN_PROGRESS.value:
                            sla_deadline = updated_complaint.get("sla_deadline")
                            time_remaining = None
                            if sla_deadline:
                                try:
                                    deadline = datetime.fromisoformat(sla_deadline.replace("Z", "+00:00"))
                                    now = datetime.utcnow()
                                    if deadline.tzinfo:
                                        now = now.replace(tzinfo=deadline.tzinfo)
                                    hours = (deadline - now).total_seconds() / 3600.0
                                    if hours > 0:
                                        time_remaining = f"{int(hours/24)} days, {int(hours%24)} hours"
                                except:
                                    pass
                            
                            notification_service.send_in_progress_notification(
                                complaint_id=complaint_id,
                                citizen_email=citizen_email,
                                citizen_name=citizen_name,
                                department=department,
                                time_remaining=time_remaining
                            )
                        
                        elif new_status == ComplaintStatus.RESOLVED.value:
                            notification_service.send_resolved_notification(
                                complaint_id=complaint_id,
                                citizen_email=citizen_email,
                                citizen_name=citizen_name,
                                department=department
                            )
                        
                        else:
                            # Send generic status update for other status changes (open, escalated, closed)
                            status_messages = {
                                ComplaintStatus.OPEN.value: "Your complaint has been reopened and is being reviewed.",
                                ComplaintStatus.ESCALATED.value: "Your complaint has been escalated to a higher authority for immediate attention.",
                                ComplaintStatus.CLOSED.value: "Your complaint has been closed. If you have any concerns, please contact support."
                            }
                            
                            message = status_messages.get(new_status, f"Your complaint status has been updated to {new_status.replace('_', ' ').title()}.")
                            
                            notification_service.send_status_update_notification(
                                complaint_id=complaint_id,
                                citizen_email=citizen_email,
                                citizen_name=citizen_name,
                                status=new_status,
                                message=message
                            )
                
                return updated_complaint
            return None
        except Exception as e:
            logger.error("Error updating complaint", complaint_id=complaint_id, error=str(e))
            return None
    
    def get_complaints_by_status(
        self,
        status: ComplaintStatus,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get complaints by status.
        
        Args:
            status: Complaint status filter
            limit: Maximum number of results
        
        Returns:
            List of complaint records
        """
        try:
            result = (
                self.client.table("complaints")
                .select("*")
                .eq("status", status.value)
                .order("created_at", desc=True)
                .limit(limit)
                .execute()
            )
            return result.data or []
        except Exception as e:
            logger.error("Error fetching complaints by status", status=status.value, error=str(e))
            return []
    
    def get_complaints_by_department(
        self,
        department: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get complaints by department.
        
        Args:
            department: Department name
            limit: Maximum number of results
        
        Returns:
            List of complaint records
        """
        try:
            result = (
                self.client.table("complaints")
                .select("*")
                .eq("responsible_department", department)
                .order("created_at", desc=True)
                .limit(limit)
                .execute()
            )
            return result.data or []
        except Exception as e:
            logger.error(
                "Error fetching complaints by department",
                department=department,
                error=str(e)
            )
            return []
    
    def get_all_complaints(
        self,
        limit: int = 1000,
        offset: int = 0,
        status: Optional[str] = None,
        department: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all complaints with optional filters.
        
        Args:
            limit: Maximum number of results
            offset: Number of results to skip
            status: Optional status filter
            department: Optional department filter
        
        Returns:
            List of complaint records
        """
        try:
            query = self.client.table("complaints").select("*")
            
            if status:
                query = query.eq("status", status)
            
            if department:
                query = query.eq("responsible_department", department)
            
            result = (
                query
                .order("created_at", desc=True)
                .range(offset, offset + limit - 1)
                .execute()
            )
            return result.data or []
        except Exception as e:
            logger.error("Error fetching all complaints", error=str(e))
            return []
    
    def get_complaints_breaching_sla(self) -> List[Dict[str, Any]]:
        """
        Get complaints that have breached their SLA deadline.
        
        Returns:
            List of complaint records past their SLA
        """
        try:
            now = datetime.utcnow().isoformat()
            result = (
                self.client.table("complaints")
                .select("*")
                .lt("sla_deadline", now)
                .neq("status", ComplaintStatus.RESOLVED.value)
                .neq("status", ComplaintStatus.CLOSED.value)
                .execute()
            )
            return result.data or []
        except Exception as e:
            logger.error("Error fetching SLA-breaching complaints", error=str(e))
            return []
    
    def create_escalation(self, escalation_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create an escalation record.
        
        Args:
            escalation_data: Dictionary with escalation fields
        
        Returns:
            Created escalation record
        """
        try:
            result = self.client.table("escalations").insert(escalation_data).execute()
            if result.data:
                logger.info("Escalation created", escalation_id=result.data[0].get("id"))
                return result.data[0]
            raise Exception("Failed to create escalation")
        except Exception as e:
            logger.error("Error creating escalation", error=str(e))
            raise
    
    def get_escalations_for_complaint(
        self,
        complaint_id: str
    ) -> List[Dict[str, Any]]:
        """
        Get all escalations for a complaint.
        
        Args:
            complaint_id: Unique complaint identifier
        
        Returns:
            List of escalation records
        """
        try:
            result = (
                self.client.table("escalations")
                .select("*")
                .eq("complaint_id", complaint_id)
                .order("created_at", desc=True)
                .execute()
            )
            return result.data or []
        except Exception as e:
            logger.error(
                "Error fetching escalations",
                complaint_id=complaint_id,
                error=str(e)
            )
            return []
    
    def get_complaint_metrics(self) -> Dict[str, Any]:
        """
        Get aggregated complaint metrics for admin dashboard.
        
        Returns:
            Dictionary with metrics
        """
        try:
            # Get total complaints
            total_result = self.client.table("complaints").select("id", count="exact").execute()
            total = total_result.count or 0
            
            # Get by status
            open_result = (
                self.client.table("complaints")
                .select("id", count="exact")
                .eq("status", ComplaintStatus.OPEN.value)
                .execute()
            )
            open_count = open_result.count or 0
            
            in_progress_result = (
                self.client.table("complaints")
                .select("id", count="exact")
                .eq("status", ComplaintStatus.IN_PROGRESS.value)
                .execute()
            )
            in_progress_count = in_progress_result.count or 0
            
            resolved_result = (
                self.client.table("complaints")
                .select("id", count="exact")
                .eq("status", ComplaintStatus.RESOLVED.value)
                .execute()
            )
            resolved_count = resolved_result.count or 0
            
            # Get SLA breaches
            now = datetime.utcnow().isoformat()
            sla_breach_result = (
                self.client.table("complaints")
                .select("id", count="exact")
                .lt("sla_deadline", now)
                .neq("status", ComplaintStatus.RESOLVED.value)
                .neq("status", ComplaintStatus.CLOSED.value)
                .execute()
            )
            sla_breaches = sla_breach_result.count or 0
            
            # Get escalated
            escalated_result = (
                self.client.table("complaints")
                .select("id", count="exact")
                .eq("status", ComplaintStatus.ESCALATED.value)
                .execute()
            )
            escalated_count = escalated_result.count or 0
            
            return {
                "total_complaints": total,
                "open": open_count,
                "in_progress": in_progress_count,
                "resolved": resolved_count,
                "sla_breaches": sla_breaches,
                "escalated": escalated_count,
            }
        except Exception as e:
            logger.error("Error fetching metrics", error=str(e))
            return {
                "total_complaints": 0,
                "open": 0,
                "in_progress": 0,
                "resolved": 0,
                "sla_breaches": 0,
                "escalated": 0,
            }


# Global database instance
db = Database()

