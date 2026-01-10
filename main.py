"""
Main FastAPI application entry point.
Agentic Public Grievance Resolver - India
"""
from fastapi import FastAPI, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import Optional
import structlog
from src.config.settings import settings, validate_settings
from src.controllers.complaint_controller import ComplaintController
from src.controllers.monitoring_controller import MonitoringController
from src.controllers.admin_controller import AdminController
from src.controllers.notification_controller import NotificationController
from src.controllers.followup_controller import FollowUpController
from src.controllers.chatbot_controller import ChatbotController
from src.controllers.heatmap_controller import HeatmapController
from src.controllers.sentiment_controller import SentimentController
from src.controllers.forum_controller import ForumController
from src.models.schemas import ComplaintCreate
from src.views.responses import ErrorView
import asyncio

# Configure structured logging
import logging
log_level_map = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}
log_level = log_level_map.get(settings.log_level.upper(), logging.INFO)

structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(log_level),
)

logger = structlog.get_logger()

# Initialize controllers
complaint_controller = ComplaintController()
monitoring_controller = MonitoringController()
admin_controller = AdminController()
notification_controller = NotificationController()
followup_controller = FollowUpController()
chatbot_controller = ChatbotController()
heatmap_controller = HeatmapController()
sentiment_controller = SentimentController()
forum_controller = ForumController()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    try:
        validate_settings()
        logger.info("Application starting", environment=settings.environment)
    except ValueError as e:
        logger.error("Configuration validation failed", error=str(e))
        raise
    yield
    # Shutdown
    logger.info("Application shutting down")


# Create FastAPI app
app = FastAPI(
    title="Agentic Public Grievance Resolver",
    description="Multi-agent AI system for processing citizen complaints in India",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "Public Grievance Resolver",
        "version": "1.0.0",
        "status": "operational",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "environment": settings.environment,
    }


# Complaint endpoints
@app.post("/api/complaints", status_code=201)
async def create_complaint(complaint: ComplaintCreate, background_tasks: BackgroundTasks):
    """
    Create a new complaint.
    Triggers the agentic workflow to process and route the complaint.
    """
    logger.info("Complaint creation requested", description_length=len(complaint.description))
    result = complaint_controller.create_complaint(complaint, background_tasks)
    return result


@app.get("/api/complaints/{complaint_id}")
async def get_complaint_status(complaint_id: str):
    """
    Get the status of a complaint.
    Returns current lifecycle state, SLA information, and escalation level.
    """
    logger.info("Complaint status requested", complaint_id=complaint_id)
    result = complaint_controller.get_complaint_status(complaint_id)
    return result


# Monitoring endpoints
@app.post("/api/monitoring/run")
async def run_monitoring(background_tasks: BackgroundTasks):
    """
    Manually trigger a monitoring cycle.
    Checks for SLA breaches and triggers escalations.
    """
    logger.info("Monitoring cycle requested")
    result = monitoring_controller.run_monitoring_cycle()
    return result


# Admin endpoints
@app.get("/api/admin/dashboard")
async def get_dashboard():
    """
    Get admin dashboard metrics.
    Returns aggregated complaint statistics.
    """
    logger.info("Dashboard metrics requested")
    result = admin_controller.get_dashboard_metrics()
    return result


@app.get("/api/admin/complaints")
async def get_all_complaints(
    limit: int = Query(100, description="Maximum number of complaints to return"),
    offset: int = Query(0, description="Number of complaints to skip"),
    status: Optional[str] = Query(None, description="Filter by status"),
    department: Optional[str] = Query(None, description="Filter by department")
):
    """
    Get all complaints with optional filters.
    Admin-only endpoint to view all complaints.
    """
    logger.info("All complaints requested", limit=limit, offset=offset, status=status, department=department)
    result = admin_controller.get_all_complaints(
        limit=limit,
        offset=offset,
        status=status,
        department=department
    )
    return result


@app.patch("/api/admin/complaints/{complaint_id}/status")
async def update_complaint_status(
    complaint_id: str,
    new_status: str = Query(..., description="New status value"),
    notes: Optional[str] = Query(None, description="Optional admin notes")
):
    """
    Update complaint status and send notification to citizen.
    Admin-only endpoint to change complaint status.
    """
    logger.info("Complaint status update requested", complaint_id=complaint_id, new_status=new_status)
    result = admin_controller.update_complaint_status(
        complaint_id=complaint_id,
        new_status=new_status,
        notes=notes
    )
    return result


# Notification endpoints
@app.post("/api/notifications/{complaint_id}")
async def send_notification(complaint_id: str):
    """
    Send a status update notification to the citizen.
    """
    logger.info("Notification requested", complaint_id=complaint_id)
    result = notification_controller.send_status_update(complaint_id)
    return result


# Follow-up endpoints
@app.post("/api/followups/run")
async def run_followups(days_without_update: int = 3):
    """
    Run follow-up process for stale in-progress complaints.
    Checks complaints that haven't been updated in specified days.
    """
    logger.info("Follow-up process requested", days=days_without_update)
    result = followup_controller.run_followups(days_without_update)
    return result


@app.post("/api/followups/{complaint_id}")
async def followup_complaint(complaint_id: str):
    """
    Run follow-up for a specific complaint.
    """
    logger.info("Single complaint follow-up requested", complaint_id=complaint_id)
    result = followup_controller.followup_single_complaint(complaint_id)
    return result


# Chatbot endpoints

@app.post("/api/chatbot/query")
async def chatbot_query(
    question: str = Query(..., description="User's question"),
    complaint_id: str = Query(None, description="Optional complaint ID"),
    citizen_email: str = Query(None, description="Optional citizen email"),
    language: str = Query("en", description="Language code: en (English), hi (Hindi), mr (Marathi)")
):
    """
    Handle a chatbot query from a citizen.
    Answers questions about complaints using AI.
    Supports multiple languages: English, Hindi, Marathi.
    """
    logger.info("Chatbot query received", question_length=len(question), complaint_id=complaint_id, language=language)
    result = chatbot_controller.handle_query(question, complaint_id, citizen_email, language)
    return result


# Heatmap endpoints
@app.get("/api/heatmap/data")
async def get_heatmap_data(
    state: str = Query(None, description="Filter by state"),
    city: str = Query(None, description="Filter by city"),
    days: int = Query(30, description="Number of days to look back")
):
    """
    Get heatmap data for geographic visualization.
    Returns complaint density, top categories, and resolution times by location.
    """
    logger.info("Heatmap data requested", state=state, city=city, days=days)
    result = heatmap_controller.get_heatmap_data(state=state, city=city, days=days)
    return result


# Sentiment analysis endpoints
@app.get("/api/sentiment/metrics")
async def get_sentiment_metrics(
    days: int = Query(30, description="Number of days to analyze"),
    department: str = Query(None, description="Filter by department"),
    state: str = Query(None, description="Filter by state")
):
    """
    Get sentiment analysis metrics and citizen satisfaction trends.
    Tracks frustration levels, emotion distribution, and satisfaction over time.
    """
    logger.info("Sentiment metrics requested", days=days, department=department, state=state)
    result = sentiment_controller.get_sentiment_metrics(days=days, department=department, state=state)
    return result


# Forum endpoints
@app.get("/api/forum/complaint/{complaint_id}")
async def get_complaint_forum(complaint_id: str):
    """
    Get forum posts and voting data for a complaint.
    Includes similar incidents and community engagement metrics.
    """
    logger.info("Forum data requested", complaint_id=complaint_id)
    result = forum_controller.get_complaint_forum(complaint_id)
    return result


@app.post("/api/forum/post")
async def create_forum_post(
    complaint_id: str = Query(..., description="Complaint ID"),
    author_name: str = Query(..., description="Author name"),
    author_email: str = Query(..., description="Author email"),
    content: str = Query(..., description="Post content"),
    image_urls: Optional[str] = Query(None, description="Comma-separated image URLs or base64 data URLs")
):
    """
    Create a forum post for a complaint.
    Allows citizens to discuss and share similar experiences with images.
    """
    logger.info("Forum post creation requested", complaint_id=complaint_id)
    
    # Parse image URLs if provided
    image_list = None
    if image_urls:
        image_list = [url.strip() for url in image_urls.split(',') if url.strip()]
    
    result = forum_controller.create_forum_post(
        complaint_id=complaint_id,
        author_name=author_name,
        author_email=author_email,
        content=content,
        image_urls=image_list
    )
    return result


@app.post("/api/forum/vote")
async def vote_on_complaint(
    complaint_id: str = Query(..., description="Complaint ID"),
    voter_email: str = Query(..., description="Voter email"),
    vote_type: str = Query(..., description="Vote type: upvote or downvote")
):
    """
    Vote on a complaint (upvote or downvote).
    Upvotes increase community priority and can boost urgency.
    """
    logger.info("Vote requested", complaint_id=complaint_id, vote_type=vote_type)
    result = forum_controller.vote_on_complaint(complaint_id, voter_email, vote_type)
    return result


@app.get("/api/forum/trending")
async def get_trending_complaints(
    limit: int = Query(10, description="Number of trending complaints to return")
):
    """
    Get trending complaints (most upvoted).
    Shows community-prioritized issues.
    """
    logger.info("Trending complaints requested", limit=limit)
    result = forum_controller.get_trending_complaints(limit=limit)
    return result


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.environment == "development",
        log_level=settings.log_level.lower(),
    )

