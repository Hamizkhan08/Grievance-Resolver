"""
Forum Controller.
Handles forum discussions and voting on complaints.
Allows citizens to upvote similar incidents to increase priority.
"""
from typing import Dict, Any, Optional, List
from fastapi import HTTPException, UploadFile, File
from src.models.database import db
from src.views.responses import ErrorView
from src.config.settings import settings
import structlog
from datetime import datetime
import uuid
import base64

logger = structlog.get_logger()


class ForumController:
    """Controller for forum and voting operations."""
    
    def get_complaint_forum(self, complaint_id: str) -> Dict[str, Any]:
        """
        Get forum posts and voting data for a complaint.
        
        Args:
            complaint_id: Complaint identifier
        
        Returns:
            Dictionary with forum data
        """
        try:
            # Get complaint
            complaint = db.get_complaint(complaint_id)
            if not complaint:
                return ErrorView.format("Complaint not found", error_code="COMPLAINT_NOT_FOUND")
            
            # Get forum posts (handle missing table gracefully)
            posts = []
            try:
                posts_result = (
                    db.client.table("forum_posts")
                    .select("*")
                    .eq("complaint_id", complaint_id)
                    .order("created_at", desc=True)
                    .execute()
                )
                posts = posts_result.data or []
            except Exception as e:
                error_str = str(e)
                if "forum_posts" in error_str.lower() or "does not exist" in error_str.lower() or "PGRST" in error_str or "relation" in error_str.lower():
                    logger.warning("Forum posts table not found - forum feature may not be set up. Run ADD_FORUM_TABLES.sql", 
                                 complaint_id=complaint_id, error=error_str)
                    # Return empty posts list - forum feature not available
                    posts = []
                else:
                    # Try without ordering
                    try:
                        posts_result = (
                            db.client.table("forum_posts")
                            .select("*")
                            .eq("complaint_id", complaint_id)
                            .execute()
                        )
                        posts = posts_result.data or []
                        # Sort in Python
                        posts.sort(key=lambda x: x.get("created_at", ""), reverse=True)
                    except Exception as e2:
                        logger.warning("Could not fetch forum posts", error=str(e2))
                        posts = []
            
            # Get vote count (handle missing column gracefully)
            upvotes = complaint.get("upvote_count", 0)
            if upvotes is None:
                upvotes = 0
            
            # Get similar complaints (by category and location)
            similar_complaints = self._get_similar_complaints(complaint)
            
            return {
                "success": True,
                "complaint_id": complaint_id,
                "upvote_count": upvotes,
                "posts": posts,
                "post_count": len(posts),
                "similar_complaints": similar_complaints,
                "community_priority_boost": complaint.get("community_priority_boost", 0.0)
            }
        except Exception as e:
            error_str = str(e)
            logger.error("Error fetching forum data", complaint_id=complaint_id, error=error_str)
            
            # Provide more specific error message
            if "forum_posts" in error_str.lower() or "does not exist" in error_str.lower():
                return {
                    "success": False,
                    "error": "Forum feature not available. Please run ADD_FORUM_TABLES.sql migration.",
                    "error_code": "FORUM_NOT_SETUP"
                }
            
            return ErrorView.format(f"Failed to fetch forum data: {error_str}", error_code="FORUM_FETCH_FAILED")
    
    def _upload_image_to_storage(self, image_data: bytes, filename: str, content_type: str) -> Optional[str]:
        """
        Upload an image to Supabase Storage.
        
        Args:
            image_data: Image file bytes
            filename: Original filename
            content_type: MIME type of the image
            
        Returns:
            Public URL of the uploaded image, or None if upload failed
        """
        try:
            # Generate unique filename
            file_extension = filename.split('.')[-1] if '.' in filename else 'jpg'
            unique_filename = f"{uuid.uuid4()}.{file_extension}"
            file_path = f"{unique_filename}"
            
            # Upload to Supabase Storage
            bucket_name = settings.supabase_storage_bucket
            result = db.client.storage.from_(bucket_name).upload(
                file_path,
                image_data,
                file_options={"content-type": content_type, "upsert": False}
            )
            
            # Get public URL
            public_url = db.client.storage.from_(bucket_name).get_public_url(file_path)
            
            logger.info("Image uploaded to storage", 
                        bucket=bucket_name, 
                        file_path=file_path,
                        url=public_url)
            
            return public_url
        except Exception as e:
            logger.error("Failed to upload image to storage", error=str(e), filename=filename)
            return None
    
    def create_forum_post(
        self,
        complaint_id: str,
        author_name: str,
        author_email: str,
        content: str,
        image_urls: Optional[List[str]] = None,
        image_files: Optional[List[bytes]] = None,
        image_filenames: Optional[List[str]] = None,
        image_content_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Create a new forum post for a complaint.
        
        Args:
            complaint_id: Complaint identifier
            author_name: Post author name
            author_email: Post author email
            content: Post content
        
        Returns:
            Created post data
        """
        try:
            # Verify complaint exists
            complaint = db.get_complaint(complaint_id)
            if not complaint:
                return {
                    "success": False,
                    "error": "Complaint not found",
                    "error_code": "COMPLAINT_NOT_FOUND"
                }
            
            # Validate input
            if not content or not content.strip():
                return {
                    "success": False,
                    "error": "Post content cannot be empty",
                    "error_code": "EMPTY_CONTENT"
                }
            
            if not author_email or not author_email.strip():
                return {
                    "success": False,
                    "error": "Author email is required",
                    "error_code": "MISSING_EMAIL"
                }
            
            # Upload images to Supabase Storage if provided
            uploaded_image_urls = []
            if image_files and len(image_files) > 0:
                for i, image_data in enumerate(image_files):
                    filename = image_filenames[i] if image_filenames and i < len(image_filenames) else f"image_{i}.jpg"
                    content_type = image_content_types[i] if image_content_types and i < len(image_content_types) else "image/jpeg"
                    
                    # Handle base64 data URLs (for backward compatibility)
                    if isinstance(image_data, str) and image_data.startswith('data:'):
                        # Extract base64 data
                        try:
                            header, encoded = image_data.split(',', 1)
                            content_type = header.split(';')[0].split(':')[1]
                            image_data = base64.b64decode(encoded)
                        except Exception as e:
                            logger.warning("Failed to decode base64 image", error=str(e))
                            continue
                    
                    public_url = self._upload_image_to_storage(image_data, filename, content_type)
                    if public_url:
                        uploaded_image_urls.append(public_url)
                    else:
                        logger.warning("Failed to upload image", filename=filename)
            
            # Also handle image_urls parameter (for direct URLs or backward compatibility)
            if image_urls:
                uploaded_image_urls.extend(image_urls)
            
            # Create post - handle missing table gracefully
            try:
                post_data = {
                    "complaint_id": complaint_id,
                    "author_name": author_name or "Anonymous",
                    "author_email": author_email,
                    "content": content.strip(),
                    "upvotes": 0,
                    "downvotes": 0,
                    "image_urls": uploaded_image_urls
                }
                
                result = db.client.table("forum_posts").insert(post_data).execute()
                if result.data and len(result.data) > 0:
                    logger.info("Forum post created", 
                               complaint_id=complaint_id, 
                               post_id=result.data[0].get("id"))
                    return {
                        "success": True,
                        "post": result.data[0]
                    }
                else:
                    logger.warning("Forum post insert returned no data", complaint_id=complaint_id)
                    return {
                        "success": False,
                        "error": "Failed to create forum post - no data returned",
                        "error_code": "POST_CREATION_FAILED"
                    }
            except Exception as post_error:
                error_str = str(post_error)
                # Check if forum_posts table doesn't exist
                if "forum_posts" in error_str.lower() and ("does not exist" in error_str.lower() or "PGRST" in error_str or "relation" in error_str.lower()):
                    logger.warning("Forum posts table not found - forum feature may not be set up", 
                                 complaint_id=complaint_id, error=error_str)
                    return {
                        "success": False,
                        "error": "Forum feature not available. Please run ADD_FORUM_TABLES.sql migration in Supabase SQL Editor. See FORUM_SETUP.md for detailed instructions.",
                        "error_code": "FORUM_TABLE_NOT_FOUND",
                        "setup_guide": "See dev/FORUM_SETUP.md for step-by-step instructions"
                    }
                else:
                    raise  # Re-raise if it's a different error
                    
        except Exception as e:
            logger.error("Error creating forum post", complaint_id=complaint_id, error=str(e))
            return {
                "success": False,
                "error": f"Failed to create forum post: {str(e)}",
                "error_code": "POST_CREATION_FAILED"
            }
    
    def vote_on_complaint(
        self,
        complaint_id: str,
        voter_email: str,
        vote_type: str  # "upvote" or "downvote"
    ) -> Dict[str, Any]:
        """
        Vote on a complaint (upvote or downvote).
        Upvotes increase community priority boost.
        
        Args:
            complaint_id: Complaint identifier
            voter_email: Email of the voter
            vote_type: "upvote" or "downvote"
        
        Returns:
            Vote result with updated counts
        """
        try:
            if vote_type not in ["upvote", "downvote"]:
                return ErrorView.format("Invalid vote type", error_code="INVALID_VOTE_TYPE")
            
            # Verify complaint exists
            complaint = db.get_complaint(complaint_id)
            if not complaint:
                return ErrorView.format("Complaint not found", error_code="COMPLAINT_NOT_FOUND")
            
            # Check if votes table exists, handle gracefully if not
            try:
                # Check if user already voted
                existing_vote = (
                    db.client.table("votes")
                    .select("*")
                    .eq("complaint_id", complaint_id)
                    .eq("voter_email", voter_email)
                    .eq("vote_type", vote_type)
                    .execute()
                )
                
                if existing_vote.data and len(existing_vote.data) > 0:
                    # User already voted this way - remove vote (toggle off)
                    vote_id = existing_vote.data[0].get("id")
                    if vote_id:
                        db.client.table("votes").delete().eq("id", vote_id).execute()
                    action = "removed"
                else:
                    # Remove opposite vote if exists
                    opposite_type = "downvote" if vote_type == "upvote" else "upvote"
                    opposite_vote = (
                        db.client.table("votes")
                        .select("*")
                        .eq("complaint_id", complaint_id)
                        .eq("voter_email", voter_email)
                        .eq("vote_type", opposite_type)
                        .execute()
                    )
                    if opposite_vote.data and len(opposite_vote.data) > 0:
                        opposite_vote_id = opposite_vote.data[0].get("id")
                        if opposite_vote_id:
                            db.client.table("votes").delete().eq("id", opposite_vote_id).execute()
                    
                    # Create new vote
                    vote_data = {
                        "complaint_id": complaint_id,
                        "voter_email": voter_email,
                        "vote_type": vote_type
                    }
                    try:
                        db.client.table("votes").insert(vote_data).execute()
                        action = "added"
                    except Exception as insert_error:
                        error_str = str(insert_error)
                        # Handle unique constraint violation (user might have already voted)
                        if "unique" in error_str.lower() or "duplicate" in error_str.lower():
                            logger.warning("Vote already exists, removing it", 
                                         complaint_id=complaint_id, 
                                         voter_email=voter_email,
                                         vote_type=vote_type)
                            # Try to find and remove the existing vote
                            existing = (
                                db.client.table("votes")
                                .select("*")
                                .eq("complaint_id", complaint_id)
                                .eq("voter_email", voter_email)
                                .eq("vote_type", vote_type)
                                .execute()
                            )
                            if existing.data and len(existing.data) > 0:
                                db.client.table("votes").delete().eq("id", existing.data[0].get("id")).execute()
                            action = "removed"
                        else:
                            raise  # Re-raise if it's a different error
                
                # Get updated counts
                updated_complaint = db.get_complaint(complaint_id)
                
                # Check if we should boost urgency based on upvotes
                upvote_count = updated_complaint.get("upvote_count", 0)
                if upvote_count >= 10 and action == "added" and vote_type == "upvote":
                    # Boost urgency if significant community support
                    self._boost_urgency_from_votes(complaint_id, upvote_count)
                
                logger.info("Vote processed", 
                           complaint_id=complaint_id, 
                           vote_type=vote_type, 
                           action=action,
                           upvote_count=upvote_count)
                
                return {
                    "success": True,
                    "action": action,
                    "vote_type": vote_type,
                    "upvote_count": upvote_count,
                    "community_priority_boost": updated_complaint.get("community_priority_boost", 0.0)
                }
            except Exception as vote_error:
                error_str = str(vote_error)
                # Check if votes table doesn't exist
                if "votes" in error_str.lower() and ("does not exist" in error_str.lower() or "PGRST" in error_str or "relation" in error_str.lower()):
                    logger.warning("Votes table not found - forum feature may not be set up", 
                                 complaint_id=complaint_id, error=error_str)
                    return {
                        "success": False,
                        "error": "Voting feature not available. Please run ADD_FORUM_TABLES.sql migration in Supabase SQL Editor. See FORUM_SETUP.md for detailed instructions.",
                        "error_code": "VOTES_TABLE_NOT_FOUND",
                        "setup_guide": "See dev/FORUM_SETUP.md for step-by-step instructions"
                    }
                else:
                    raise  # Re-raise if it's a different error
                    
        except Exception as e:
            logger.error("Error processing vote", complaint_id=complaint_id, error=str(e))
            return {
                "success": False,
                "error": f"Failed to process vote: {str(e)}",
                "error_code": "VOTE_FAILED"
            }
    
    def _boost_urgency_from_votes(self, complaint_id: str, upvote_count: int):
        """
        Boost complaint urgency based on community upvotes.
        
        Args:
            complaint_id: Complaint identifier
            upvote_count: Number of upvotes
        """
        try:
            complaint = db.get_complaint(complaint_id)
            if not complaint:
                return
            
            current_urgency = complaint.get("urgency", "medium")
            urgency_map = {"low": 1, "medium": 2, "high": 3, "urgent": 4}
            current_level = urgency_map.get(current_urgency, 2)
            
            # Boost urgency based on upvote thresholds
            if upvote_count >= 50 and current_level < 4:
                new_urgency = "urgent"
            elif upvote_count >= 20 and current_level < 3:
                new_urgency = "high"
            elif upvote_count >= 10 and current_level < 2:
                new_urgency = "medium"
            else:
                return  # No boost needed
            
            # Update complaint urgency
            db.client.table("complaints").update({
                "urgency": new_urgency,
                "updated_at": datetime.utcnow().isoformat()
            }).eq("id", complaint_id).execute()
            
            logger.warning(f"🚀 Community boost: Complaint {complaint_id} urgency boosted from {current_urgency} to {new_urgency} due to {upvote_count} upvotes")
        except Exception as e:
            logger.error("Error boosting urgency from votes", complaint_id=complaint_id, error=str(e))
    
    def _get_similar_complaints(self, complaint: Dict[str, Any], limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get similar complaints based on category and location.
        
        Args:
            complaint: Complaint dictionary
            limit: Maximum number of similar complaints to return
        
        Returns:
            List of similar complaint dictionaries
        """
        try:
            category = complaint.get("structured_category", "")
            location = complaint.get("location", {})
            city = location.get("city", "") if isinstance(location, dict) else ""
            state = location.get("state", "") if isinstance(location, dict) else ""
            complaint_id = complaint.get("id", "")
            
            # Build query for similar complaints - handle missing upvote_count column
            try:
                # Try with upvote_count first
                query = db.client.table("complaints").select("id,description,urgency,status,upvote_count,created_at,responsible_department,location")
            except Exception:
                # Fallback if upvote_count doesn't exist
                query = db.client.table("complaints").select("id,description,urgency,status,created_at,responsible_department,location")
            
            # Filter by category
            if category:
                query = query.eq("structured_category", category)
            
            # Filter by location (handle both JSON and dict formats)
            if city:
                # Try JSON path query
                try:
                    query = query.eq("location->>city", city)
                except Exception:
                    # Fallback: filter in Python after fetching
                    pass
            elif state:
                try:
                    query = query.eq("location->>state", state)
                except Exception:
                    pass
            
            # Exclude current complaint
            if complaint_id:
                query = query.neq("id", complaint_id)
            
            # Order by recency (upvote_count may not exist)
            try:
                # Try ordering by created_at (most reliable)
                result = query.order("created_at", desc=True).limit(limit).execute()
            except Exception:
                # Fallback: no ordering
                try:
                    result = query.limit(limit).execute()
                    # Sort in Python
                    if result.data:
                        result.data.sort(key=lambda x: x.get("created_at", ""), reverse=True)
                except Exception as e2:
                    logger.warning("Could not execute similar complaints query", error=str(e2))
                    return []
            
            similar = result.data or []
            
            # Filter by location in Python if JSON query didn't work
            if (city or state) and similar:
                filtered = []
                for comp in similar:
                    comp_location = comp.get("location", {})
                    if isinstance(comp_location, dict):
                        comp_city = comp_location.get("city", "")
                        comp_state = comp_location.get("state", "")
                        if (city and comp_city == city) or (state and comp_state == state):
                            filtered.append(comp)
                    elif isinstance(comp_location, str):
                        # Try to parse if it's a JSON string
                        try:
                            import json
                            comp_location = json.loads(comp_location)
                            comp_city = comp_location.get("city", "")
                            comp_state = comp_location.get("state", "")
                            if (city and comp_city == city) or (state and comp_state == state):
                                filtered.append(comp)
                        except Exception:
                            pass
                similar = filtered[:limit]
            
            # Ensure upvote_count exists in all results
            for comp in similar:
                if "upvote_count" not in comp:
                    comp["upvote_count"] = 0
            
            return similar
        except Exception as e:
            logger.error("Error finding similar complaints", error=str(e))
            return []
    
    def get_trending_complaints(self, limit: int = 10) -> Dict[str, Any]:
        """
        Get trending complaints (most upvoted).
        
        Args:
            limit: Maximum number of complaints to return
        
        Returns:
            Dictionary with trending complaints
        """
        try:
            # Try to fetch with forum columns first
            try:
                result = (
                    db.client.table("complaints")
                    .select("id,description,urgency,status,upvote_count,forum_post_count,community_priority_boost,created_at,responsible_department,location")
                    .order("upvote_count", desc=True)
                    .order("community_priority_boost", desc=True)
                    .limit(limit)
                    .execute()
                )
            except Exception as e1:
                error_str = str(e1)
                # If columns don't exist, fetch without them and sort in Python
                if "upvote_count" in error_str.lower() or "does not exist" in error_str.lower() or "PGRST" in error_str:
                    logger.warning("Forum columns not found, fetching without upvote_count", error=error_str)
                    # Fetch without forum-specific columns
                    result = (
                        db.client.table("complaints")
                        .select("id,description,urgency,status,created_at,responsible_department,location")
                        .order("created_at", desc=True)
                        .limit(limit)
                        .execute()
                    )
                    # Add default values for missing columns
                    complaints = result.data or []
                    for complaint in complaints:
                        complaint["upvote_count"] = 0
                        complaint["forum_post_count"] = 0
                        complaint["community_priority_boost"] = 0.0
                    # Sort by created_at (most recent first)
                    complaints.sort(key=lambda x: x.get("created_at", ""), reverse=True)
                    return {
                        "success": True,
                        "complaints": complaints[:limit],
                        "count": len(complaints[:limit])
                    }
                else:
                    raise  # Re-raise if it's a different error
            
            complaints = result.data or []
            
            # Ensure all complaints have required fields
            for complaint in complaints:
                if "upvote_count" not in complaint:
                    complaint["upvote_count"] = 0
                if "forum_post_count" not in complaint:
                    complaint["forum_post_count"] = 0
                if "community_priority_boost" not in complaint:
                    complaint["community_priority_boost"] = 0.0
            
            # If we couldn't order by upvote_count, sort in Python
            if complaints and complaints[0].get("upvote_count", 0) == 0:
                # Sort by created_at if no upvotes
                complaints.sort(key=lambda x: x.get("created_at", ""), reverse=True)
            
            return {
                "success": True,
                "complaints": complaints,
                "count": len(complaints)
            }
        except Exception as e:
            logger.error("Error fetching trending complaints", error=str(e))
            # Return empty list instead of error to allow page to load
            return {
                "success": True,
                "complaints": [],
                "count": 0,
                "message": "Forum feature may not be fully set up. Run ADD_FORUM_TABLES.sql migration."
            }
