"""
Heatmap Controller.
Provides geographic data for real-time grievance heatmap visualization.
"""
from typing import Dict, Any, List, Optional
from src.models.database import db
from src.views.responses import ErrorView
import structlog
from datetime import datetime, timedelta

logger = structlog.get_logger()


class HeatmapController:
    """Controller for heatmap data operations."""
    
    def get_heatmap_data(
        self,
        state: Optional[str] = None,
        city: Optional[str] = None,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get heatmap data including complaint density, categories, and resolution times.
        
        Args:
            state: Filter by state (optional)
            city: Filter by city (optional)
            days: Number of days to look back (default 30)
        
        Returns:
            Dictionary with heatmap data
        """
        try:
            # Calculate date threshold
            threshold_date = datetime.utcnow() - timedelta(days=days)
            
            # Build query
            query = db.client.table("complaints").select("*")
            
            # Apply filters
            if state:
                # Filter by state in JSONB location field
                query = query.eq("location->>state", state)
            if city:
                query = query.eq("location->>city", city)
            
            # Get all complaints in time range
            try:
                result = query.gte("created_at", threshold_date.isoformat()).execute()
                complaints = result.data or []
            except Exception as e:
                logger.error("Error querying complaints for heatmap", error=str(e))
                # Fallback: get all complaints and filter in Python
                result = db.client.table("complaints").select("*").gte("created_at", threshold_date.isoformat()).execute()
                complaints = result.data or []
                if state:
                    complaints = [c for c in complaints if c.get("location", {}).get("state") == state]
                if city:
                    complaints = [c for c in complaints if c.get("location", {}).get("city") == city]
            
            # Process data for heatmap
            heatmap_data = self._process_heatmap_data(complaints)
            
            return {
                "success": True,
                "data": heatmap_data,
                "total_complaints": len(complaints),
                "date_range": {
                    "from": threshold_date.isoformat(),
                    "to": datetime.utcnow().isoformat()
                }
            }
        except Exception as e:
            logger.error("Error fetching heatmap data", error=str(e))
            return ErrorView.format("Failed to fetch heatmap data", error_code="HEATMAP_FETCH_FAILED")
    
    def _process_heatmap_data(self, complaints: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Process complaints into heatmap visualization data.
        
        Args:
            complaints: List of complaint dictionaries
        
        Returns:
            Processed heatmap data structure
        """
        # Group by location (city/district)
        location_groups = {}
        category_counts = {}
        department_stats = {}
        
        for complaint in complaints:
            location = complaint.get("location", {})
            city = location.get("city", "Unknown")
            district = location.get("district", "Unknown")
            state = location.get("state", "Unknown")
            location_key = f"{city}, {district}, {state}"
            
            # Initialize location group
            if location_key not in location_groups:
                location_groups[location_key] = {
                    "location": {
                        "city": city,
                        "district": district,
                        "state": state,
                        "pincode": location.get("pincode", ""),
                        "coordinates": self._get_coordinates(location)
                    },
                    "complaint_count": 0,
                    "categories": {},
                    "departments": {},
                    "avg_resolution_hours": None,
                    "resolved_count": 0,
                    "total_count": 0,
                    "sentiment_avg": 0.0,
                    "emotion_distribution": {}
                }
            
            group = location_groups[location_key]
            group["complaint_count"] += 1
            group["total_count"] += 1
            
            # Category tracking
            category = complaint.get("structured_category", "other")
            if category not in category_counts:
                category_counts[category] = 0
            category_counts[category] += 1
            group["categories"][category] = group["categories"].get(category, 0) + 1
            
            # Department tracking
            dept = complaint.get("responsible_department", "unknown")
            if dept not in department_stats:
                department_stats[dept] = {
                    "count": 0,
                    "total_resolution_hours": 0.0,
                    "resolved_count": 0
                }
            department_stats[dept]["count"] += 1
            
            if dept not in group["departments"]:
                group["departments"][dept] = 0
            group["departments"][dept] += 1
            
            # Resolution time calculation
            status = complaint.get("status", "")
            if status == "resolved":
                group["resolved_count"] += 1
                created_at = complaint.get("created_at")
                updated_at = complaint.get("updated_at")
                if created_at and updated_at:
                    try:
                        created = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                        updated = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
                        hours = (updated - created).total_seconds() / 3600.0
                        department_stats[dept]["total_resolution_hours"] += hours
                        department_stats[dept]["resolved_count"] += 1
                    except:
                        pass
            
            # Sentiment tracking
            sentiment_score = complaint.get("sentiment_score", 0.0)
            if sentiment_score:
                group["sentiment_avg"] = (
                    (group["sentiment_avg"] * (group["total_count"] - 1) + sentiment_score) 
                    / group["total_count"]
                )
            
            emotion = complaint.get("emotion_level", "calm")
            group["emotion_distribution"][emotion] = group["emotion_distribution"].get(emotion, 0) + 1
        
        # Calculate average resolution times
        for location_key, group in location_groups.items():
            if group["resolved_count"] > 0:
                # Calculate from department stats for this location
                total_hours = 0.0
                resolved = 0
                for dept in group["departments"]:
                    if dept in department_stats:
                        total_hours += department_stats[dept]["total_resolution_hours"]
                        resolved += department_stats[dept]["resolved_count"]
                if resolved > 0:
                    group["avg_resolution_hours"] = total_hours / resolved
        
        # Calculate department-wide averages
        department_averages = {}
        for dept, stats in department_stats.items():
            if stats["resolved_count"] > 0:
                department_averages[dept] = {
                    "avg_resolution_hours": stats["total_resolution_hours"] / stats["resolved_count"],
                    "total_complaints": stats["count"],
                    "resolved_count": stats["resolved_count"],
                    "resolution_rate": stats["resolved_count"] / stats["count"] if stats["count"] > 0 else 0
                }
        
        # Top categories
        top_categories = sorted(
            category_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]
        
        return {
            "locations": list(location_groups.values()),
            "top_categories": [{"category": cat, "count": count} for cat, count in top_categories],
            "department_stats": department_averages,
            "summary": {
                "total_locations": len(location_groups),
                "total_complaints": len(complaints),
                "total_categories": len(category_counts),
                "total_departments": len(department_stats)
            }
        }
    
    def _get_coordinates(self, location: Dict[str, Any]) -> Optional[Dict[str, float]]:
        """
        Get approximate coordinates for a location.
        For now, returns None. Can be enhanced with geocoding API.
        
        Args:
            location: Location dictionary
        
        Returns:
            Dictionary with lat/lng or None
        """
        # TODO: Integrate with geocoding API (Google Maps, OpenStreetMap, etc.)
        # For now, return None - frontend can use city/district names for mapping
        return None
