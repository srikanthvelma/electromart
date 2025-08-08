from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from motor.motor_asyncio import AsyncIOMotorClient
import redis.asyncio as redis
import httpx
import json
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
from pydantic import BaseModel, EmailStr
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from twilio.rest import Client
from twilio.base.exceptions import TwilioException
import asyncio

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="ElectroMart Notification Service",
    description="Notification microservice for ElectroMart e-commerce platform",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB client
mongo_client = AsyncIOMotorClient(os.getenv("MONGODB_URI", "mongodb://mongodb:27017"))
db = mongo_client.electromart_notifications

# Redis client
redis_client = redis.from_url(
    os.getenv("REDIS_URL", "redis://redis:6379"),
    decode_responses=True
)

# HTTP client for calling other services
http_client = httpx.AsyncClient()

# Twilio client for SMS
twilio_client = Client(
    os.getenv("TWILIO_ACCOUNT_SID"),
    os.getenv("TWILIO_AUTH_TOKEN")
)

# Pydantic models
class NotificationRequest(BaseModel):
    user_id: str
    type: str  # email, sms, push
    subject: str
    message: str
    template: Optional[str] = None
    template_data: Optional[Dict[str, Any]] = None
    priority: str = "normal"  # low, normal, high, urgent
    scheduled_at: Optional[datetime] = None

class NotificationResponse(BaseModel):
    id: str
    user_id: str
    type: str
    subject: str
    message: str
    status: str
    sent_at: Optional[datetime] = None
    created_at: datetime

class NotificationPreferences(BaseModel):
    user_id: str
    email_enabled: bool = True
    sms_enabled: bool = False
    push_enabled: bool = True
    marketing_emails: bool = True
    order_updates: bool = True
    promotional_offers: bool = False

@app.on_event("startup")
async def startup_event():
    """Initialize connections on startup"""
    try:
        # Test MongoDB connection
        await mongo_client.admin.command('ping')
        logger.info("Connected to MongoDB")
        
        # Test Redis connection
        await redis_client.ping()
        logger.info("Connected to Redis")
        
        # Create indexes
        await db.notifications.create_index("user_id")
        await db.notifications.create_index("status")
        await db.notifications.create_index("created_at")
        await db.notifications.create_index("scheduled_at")
        
        await db.preferences.create_index("user_id", unique=True)
        
        logger.info("Database indexes created")
        
    except Exception as e:
        logger.error(f"Startup error: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up connections on shutdown"""
    mongo_client.close()
    await redis_client.close()
    await http_client.aclose()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check MongoDB
        await mongo_client.admin.command('ping')
        
        # Check Redis
        await redis_client.ping()
        
        return {
            "status": "healthy",
            "service": "Notification Service",
            "timestamp": datetime.utcnow().isoformat(),
            "mongodb": "connected",
            "redis": "connected"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "service": "Notification Service",
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            }
        )

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "ElectroMart Notification Service",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "send_notification": "/api/notifications/send",
            "get_notifications": "/api/notifications/{user_id}",
            "update_preferences": "/api/preferences/{user_id}",
            "get_preferences": "/api/preferences/{user_id}"
        }
    }

@app.post("/api/notifications/send")
async def send_notification(
    notification: NotificationRequest,
    background_tasks: BackgroundTasks
):
    """Send a notification"""
    try:
        # Check user preferences
        preferences = await get_user_preferences(notification.user_id)
        
        if not preferences:
            # Create default preferences
            preferences = NotificationPreferences(user_id=notification.user_id)
            await save_user_preferences(preferences)
        
        # Check if notification type is enabled
        if notification.type == "email" and not preferences.email_enabled:
            raise HTTPException(status_code=400, detail="Email notifications are disabled")
        elif notification.type == "sms" and not preferences.sms_enabled:
            raise HTTPException(status_code=400, detail="SMS notifications are disabled")
        elif notification.type == "push" and not preferences.push_enabled:
            raise HTTPException(status_code=400, detail="Push notifications are disabled")
        
        # Create notification record
        notification_doc = {
            "user_id": notification.user_id,
            "type": notification.type,
            "subject": notification.subject,
            "message": notification.message,
            "template": notification.template,
            "template_data": notification.template_data,
            "priority": notification.priority,
            "status": "pending",
            "scheduled_at": notification.scheduled_at,
            "created_at": datetime.utcnow(),
            "sent_at": None,
            "retry_count": 0,
            "max_retries": 3
        }
        
        result = await db.notifications.insert_one(notification_doc)
        notification_id = str(result.inserted_id)
        
        # Send notification in background
        if notification.scheduled_at and notification.scheduled_at > datetime.utcnow():
            # Schedule for later
            background_tasks.add_task(schedule_notification, notification_id)
        else:
            # Send immediately
            background_tasks.add_task(send_notification_task, notification_id)
        
        return {
            "message": "Notification queued successfully",
            "notification_id": notification_id,
            "status": "pending"
        }
        
    except Exception as e:
        logger.error(f"Send notification error: {e}")
        raise HTTPException(status_code=500, detail="Failed to send notification")

async def send_notification_task(notification_id: str):
    """Background task to send notification"""
    try:
        # Get notification from database
        notification_doc = await db.notifications.find_one({"_id": notification_id})
        if not notification_doc:
            logger.error(f"Notification {notification_id} not found")
            return
        
        # Get user details
        user_details = await get_user_details(notification_doc["user_id"])
        if not user_details:
            logger.error(f"User {notification_doc['user_id']} not found")
            await update_notification_status(notification_id, "failed", "User not found")
            return
        
        # Send based on type
        success = False
        error_message = ""
        
        if notification_doc["type"] == "email":
            success, error_message = await send_email_notification(
                notification_doc, user_details
            )
        elif notification_doc["type"] == "sms":
            success, error_message = await send_sms_notification(
                notification_doc, user_details
            )
        elif notification_doc["type"] == "push":
            success, error_message = await send_push_notification(
                notification_doc, user_details
            )
        
        # Update notification status
        if success:
            await update_notification_status(notification_id, "sent")
        else:
            # Retry logic
            retry_count = notification_doc.get("retry_count", 0)
            max_retries = notification_doc.get("max_retries", 3)
            
            if retry_count < max_retries:
                await update_notification_status(notification_id, "retrying", error_message)
                # Schedule retry with exponential backoff
                retry_delay = 2 ** retry_count  # 1, 2, 4 seconds
                await asyncio.sleep(retry_delay)
                await send_notification_task(notification_id)
            else:
                await update_notification_status(notification_id, "failed", error_message)
        
    except Exception as e:
        logger.error(f"Send notification task error: {e}")
        await update_notification_status(notification_id, "failed", str(e))

async def send_email_notification(notification_doc: Dict, user_details: Dict) -> tuple[bool, str]:
    """Send email notification"""
    try:
        # Get email template
        template_content = await get_email_template(notification_doc.get("template", "default"))
        
        # Render template
        message_content = render_template(
            template_content,
            notification_doc.get("template_data", {}),
            user_details
        )
        
        # Create email message
        msg = MIMEMultipart()
        msg['From'] = os.getenv("SMTP_FROM_EMAIL")
        msg['To'] = user_details.get("email")
        msg['Subject'] = notification_doc["subject"]
        
        msg.attach(MIMEText(message_content, 'html'))
        
        # Send email
        with smtplib.SMTP(os.getenv("SMTP_HOST"), int(os.getenv("SMTP_PORT", 587))) as server:
            server.starttls()
            server.login(os.getenv("SMTP_USERNAME"), os.getenv("SMTP_PASSWORD"))
            server.send_message(msg)
        
        logger.info(f"Email sent to {user_details.get('email')}")
        return True, ""
        
    except Exception as e:
        logger.error(f"Email notification error: {e}")
        return False, str(e)

async def send_sms_notification(notification_doc: Dict, user_details: Dict) -> tuple[bool, str]:
    """Send SMS notification"""
    try:
        phone_number = user_details.get("phone")
        if not phone_number:
            return False, "No phone number available"
        
        # Send SMS via Twilio
        message = twilio_client.messages.create(
            body=notification_doc["message"],
            from_=os.getenv("TWILIO_PHONE_NUMBER"),
            to=phone_number
        )
        
        logger.info(f"SMS sent to {phone_number}: {message.sid}")
        return True, ""
        
    except TwilioException as e:
        logger.error(f"SMS notification error: {e}")
        return False, str(e)
    except Exception as e:
        logger.error(f"SMS notification error: {e}")
        return False, str(e)

async def send_push_notification(notification_doc: Dict, user_details: Dict) -> tuple[bool, str]:
    """Send push notification"""
    try:
        # This would integrate with Firebase Cloud Messaging or similar
        # For now, we'll just log it
        logger.info(f"Push notification would be sent to user {user_details.get('id')}: {notification_doc['message']}")
        return True, ""
        
    except Exception as e:
        logger.error(f"Push notification error: {e}")
        return False, str(e)

async def get_user_preferences(user_id: str) -> Optional[NotificationPreferences]:
    """Get user notification preferences"""
    try:
        doc = await db.preferences.find_one({"user_id": user_id})
        if doc:
            return NotificationPreferences(**doc)
        return None
    except Exception as e:
        logger.error(f"Get user preferences error: {e}")
        return None

async def save_user_preferences(preferences: NotificationPreferences):
    """Save user notification preferences"""
    try:
        await db.preferences.replace_one(
            {"user_id": preferences.user_id},
            preferences.dict(),
            upsert=True
        )
    except Exception as e:
        logger.error(f"Save user preferences error: {e}")

async def get_user_details(user_id: str) -> Optional[Dict]:
    """Get user details from User Service"""
    try:
        user_service_url = os.getenv("USER_SERVICE_URL", "http://user-service:8002")
        
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{user_service_url}/api/users/{user_id}")
            if response.status_code == 200:
                return response.json().get("user")
            return None
    except Exception as e:
        logger.error(f"Get user details error: {e}")
        return None

async def get_email_template(template_name: str) -> str:
    """Get email template content"""
    # In a real application, templates would be stored in a database or file system
    templates = {
        "default": """
        <html>
        <body>
            <h2>{{subject}}</h2>
            <p>{{message}}</p>
            <p>Best regards,<br>ElectroMart Team</p>
        </body>
        </html>
        """,
        "order_confirmation": """
        <html>
        <body>
            <h2>Order Confirmation</h2>
            <p>Dear {{user.firstName}},</p>
            <p>Your order #{{orderNumber}} has been confirmed.</p>
            <p>Total: ${{total}}</p>
            <p>Thank you for shopping with ElectroMart!</p>
        </body>
        </html>
        """,
        "password_reset": """
        <html>
        <body>
            <h2>Password Reset</h2>
            <p>Dear {{user.firstName}},</p>
            <p>Click the link below to reset your password:</p>
            <a href="{{resetLink}}">Reset Password</a>
            <p>This link will expire in 1 hour.</p>
        </body>
        </html>
        """
    }
    
    return templates.get(template_name, templates["default"])

def render_template(template_content: str, data: Dict, user_details: Dict) -> str:
    """Render template with data"""
    try:
        # Simple template rendering - in production, use a proper template engine
        rendered = template_content
        
        # Replace user data
        for key, value in user_details.items():
            rendered = rendered.replace(f"{{{{user.{key}}}}}", str(value))
        
        # Replace other data
        for key, value in data.items():
            rendered = rendered.replace(f"{{{{{key}}}}}", str(value))
        
        return rendered
    except Exception as e:
        logger.error(f"Template rendering error: {e}")
        return template_content

async def update_notification_status(notification_id: str, status: str, error_message: str = ""):
    """Update notification status in database"""
    try:
        update_data = {
            "status": status,
            "updated_at": datetime.utcnow()
        }
        
        if status == "sent":
            update_data["sent_at"] = datetime.utcnow()
        elif status == "retrying":
            update_data["retry_count"] = {"$inc": 1}
        elif status == "failed":
            update_data["error_message"] = error_message
        
        await db.notifications.update_one(
            {"_id": notification_id},
            {"$set": update_data}
        )
    except Exception as e:
        logger.error(f"Update notification status error: {e}")

async def schedule_notification(notification_id: str):
    """Schedule notification for later delivery"""
    try:
        notification_doc = await db.notifications.find_one({"_id": notification_id})
        if not notification_doc:
            return
        
        scheduled_at = notification_doc.get("scheduled_at")
        if not scheduled_at:
            return
        
        # Calculate delay
        delay = (scheduled_at - datetime.utcnow()).total_seconds()
        if delay > 0:
            await asyncio.sleep(delay)
            await send_notification_task(notification_id)
        
    except Exception as e:
        logger.error(f"Schedule notification error: {e}")

@app.get("/api/notifications/{user_id}")
async def get_user_notifications(
    user_id: str,
    page: int = 1,
    limit: int = 20,
    status: Optional[str] = None
):
    """Get notifications for a user"""
    try:
        # Build query
        query = {"user_id": user_id}
        if status:
            query["status"] = status
        
        # Get notifications
        skip = (page - 1) * limit
        cursor = db.notifications.find(query).sort("created_at", -1).skip(skip).limit(limit)
        
        notifications = []
        async for doc in cursor:
            doc["id"] = str(doc["_id"])
            del doc["_id"]
            notifications.append(doc)
        
        # Get total count
        total = await db.notifications.count_documents(query)
        
        return {
            "notifications": notifications,
            "total": total,
            "page": page,
            "limit": limit,
            "pages": (total + limit - 1) // limit
        }
        
    except Exception as e:
        logger.error(f"Get user notifications error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get notifications")

@app.put("/api/preferences/{user_id}")
async def update_user_preferences(user_id: str, preferences: NotificationPreferences):
    """Update user notification preferences"""
    try:
        preferences.user_id = user_id
        await save_user_preferences(preferences)
        
        return {
            "message": "Preferences updated successfully",
            "preferences": preferences.dict()
        }
        
    except Exception as e:
        logger.error(f"Update preferences error: {e}")
        raise HTTPException(status_code=500, detail="Failed to update preferences")

@app.get("/api/preferences/{user_id}")
async def get_user_preferences_endpoint(user_id: str):
    """Get user notification preferences"""
    try:
        preferences = await get_user_preferences(user_id)
        
        if not preferences:
            # Return default preferences
            preferences = NotificationPreferences(user_id=user_id)
        
        return preferences.dict()
        
    except Exception as e:
        logger.error(f"Get preferences error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get preferences")

@app.post("/api/notifications/bulk")
async def send_bulk_notifications(
    notifications: List[NotificationRequest],
    background_tasks: BackgroundTasks
):
    """Send multiple notifications"""
    try:
        results = []
        
        for notification in notifications:
            try:
                result = await send_notification(notification, background_tasks)
                results.append({
                    "user_id": notification.user_id,
                    "status": "queued",
                    "notification_id": result["notification_id"]
                })
            except Exception as e:
                results.append({
                    "user_id": notification.user_id,
                    "status": "failed",
                    "error": str(e)
                })
        
        return {
            "message": "Bulk notifications processed",
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Bulk notifications error: {e}")
        raise HTTPException(status_code=500, detail="Failed to send bulk notifications")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8006)
