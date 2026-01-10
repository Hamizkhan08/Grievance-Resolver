"""
Sentiment Controller.
Provides sentiment analysis metrics and citizen satisfaction tracking.
"""
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from src.models.database import db
from src.views.responses import ErrorView
import structlog

logger = structlog.get_logger()


class SentimentController:
    """Controller for sentiment analysis and satisfaction metrics."""
    
    def get_sentiment_metrics(
        self,
        days: int = 30,
        department: Optional[str] = None,
        state: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get sentiment analysis metrics and citizen satisfaction trends.
        
        Args:
            days: Number of days to analyze (default 30)
            department: Filter by department (optional)
            state: Filter by state (optional)
        
        Returns:
            Dictionary with sentiment metrics
        """
        try:
            threshold_date = datetime.utcnow() - timedelta(days=days)
            
            # Build query
            query = db.client.table("complaints").select("*")
            query = query.gte("created_at", threshold_date.isoformat())
            
            if department:
                query = query.eq("responsible_department", department)
            if state:
                query = query.eq("location->>state", state)
            
            result = query.execute()
            complaints = result.data or []
            
            # Calculate metrics
            metrics = self._calculate_sentiment_metrics(complaints)
            
            return {
                "success": True,
                "metrics": metrics,
                "total_complaints": len(complaints),
                "date_range": {
                    "from": threshold_date.isoformat(),
                    "to": datetime.utcnow().isoformat()
                }
            }
        except Exception as e:
            logger.error("Error fetching sentiment metrics", error=str(e))
            return ErrorView.format("Failed to fetch sentiment metrics", error_code="SENTIMENT_FETCH_FAILED")
    
    def _calculate_sentiment_metrics(self, complaints: list) -> Dict[str, Any]:
        """Calculate sentiment metrics from complaints."""
        if not complaints:
            return {
                "average_sentiment": 0.0,
                "emotion_distribution": {},
                "frustration_rate": 0.0,
                "satisfaction_trend": [],
                "high_priority_emotions": 0,
                "departments_by_sentiment": {}
            }
        
        total_sentiment = 0.0
        emotion_counts = {}
        frustration_count = 0
        high_priority_emotions = 0
        departments_sentiment = {}
        
        for complaint in complaints:
            sentiment = complaint.get("sentiment_score", 0.0)
            emotion = complaint.get("emotion_level", "calm")
            dept = complaint.get("responsible_department", "unknown")
            
            total_sentiment += sentiment
            emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
            
            if emotion in ["frustrated", "angry", "urgent"]:
                frustration_count += 1
            if emotion in ["angry", "urgent"]:
                high_priority_emotions += 1
            
            if dept not in departments_sentiment:
                departments_sentiment[dept] = {
                    "total_sentiment": 0.0,
                    "count": 0,
                    "frustration_count": 0
                }
            departments_sentiment[dept]["total_sentiment"] += sentiment
            departments_sentiment[dept]["count"] += 1
            if emotion in ["frustrated", "angry", "urgent"]:
                departments_sentiment[dept]["frustration_count"] += 1
        
        # Calculate averages
        avg_sentiment = total_sentiment / len(complaints) if complaints else 0.0
        frustration_rate = frustration_count / len(complaints) if complaints else 0.0
        
        # Department averages
        dept_averages = {}
        for dept, stats in departments_sentiment.items():
            dept_averages[dept] = {
                "average_sentiment": stats["total_sentiment"] / stats["count"] if stats["count"] > 0 else 0.0,
                "frustration_rate": stats["frustration_count"] / stats["count"] if stats["count"] > 0 else 0.0,
                "total_complaints": stats["count"]
            }
        
        # Calculate satisfaction trend (daily averages)
        satisfaction_trend = self._calculate_satisfaction_trend(complaints)
        
        return {
            "average_sentiment": round(avg_sentiment, 3),
            "emotion_distribution": emotion_counts,
            "frustration_rate": round(frustration_rate, 3),
            "satisfaction_trend": satisfaction_trend,
            "high_priority_emotions": high_priority_emotions,
            "departments_by_sentiment": dept_averages
        }
    
    def _calculate_satisfaction_trend(self, complaints: list) -> list:
        """Calculate daily satisfaction trend."""
        # Group by date
        daily_sentiment = {}
        for complaint in complaints:
            created_at = complaint.get("created_at")
            if not created_at:
                continue
            try:
                date = datetime.fromisoformat(created_at.replace("Z", "+00:00")).date()
                if date not in daily_sentiment:
                    daily_sentiment[date] = {"total": 0.0, "count": 0}
                daily_sentiment[date]["total"] += complaint.get("sentiment_score", 0.0)
                daily_sentiment[date]["count"] += 1
            except:
                continue
        
        # Convert to list
        trend = []
        for date in sorted(daily_sentiment.keys()):
            stats = daily_sentiment[date]
            trend.append({
                "date": date.isoformat(),
                "average_sentiment": round(stats["total"] / stats["count"], 3) if stats["count"] > 0 else 0.0,
                "complaint_count": stats["count"]
            })
        
        return trend
