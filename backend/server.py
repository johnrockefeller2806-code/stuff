from fastapi import FastAPI, APIRouter, HTTPException, Depends, Request, UploadFile, File, Response, Cookie
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional, Dict, Any, Literal
import uuid
from datetime import datetime, timezone, timedelta
import jwt
import bcrypt
from emergentintegrations.payments.stripe.checkout import (
    StripeCheckout, CheckoutSessionResponse, CheckoutStatusResponse, CheckoutSessionRequest
)
import base64
from pywebpush import webpush, WebPushException
import json
import httpx

# Import chat module
from chat import chat_router, init_chat_module, setup_ttl_index

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# JWT Config
JWT_SECRET = os.environ.get('JWT_SECRET_KEY', 'default-secret-key')
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

# Stripe Config
STRIPE_API_KEY = os.environ.get('STRIPE_API_KEY', 'sk_test_emergent')

# Create the main app
app = FastAPI(title="Dublin Study API")
api_router = APIRouter(prefix="/api")
security = HTTPBearer(auto_error=False)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============== MODELS ==============

# User roles: student, school, admin
UserRole = Literal["student", "school", "admin"]

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: UserRole = "student"

class SchoolRegister(BaseModel):
    name: str
    email: EmailStr
    password: str
    school_name: str
    description: str
    description_en: str
    address: str
    phone: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    name: str
    email: str
    role: str = "student"
    created_at: str
    school_id: Optional[str] = None
    avatar: Optional[str] = None  # Profile photo URL
    plan: str = "free"  # free or plus
    plan_purchased_at: Optional[str] = None

class UserProfileUpdate(BaseModel):
    name: Optional[str] = None
    avatar: Optional[str] = None

# Plano PLUS para estudantes
STUDENT_PLUS_PLAN = {
    "name": "PLUS",
    "price": 49.90,
    "currency": "EUR",
    "type": "one_time",  # pagamento único
    "description": "Acesso completo à plataforma STUFF Intercâmbio"
}

class PlusPlanCheckoutRequest(BaseModel):
    origin_url: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

class School(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    description_en: str
    address: str
    city: str = "Dublin"
    country: str = "Ireland"
    phone: str = ""
    email: str = ""
    website: str = ""
    image_url: str = ""
    rating: float = 4.5
    reviews_count: int = 0
    accreditation: List[str] = []
    facilities: List[str] = []
    status: str = "pending"  # pending, approved, rejected
    owner_id: Optional[str] = None  # User ID of school owner
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    # Stripe Connect fields
    stripe_account_id: Optional[str] = None  # Connected Stripe account
    stripe_onboarding_complete: bool = False
    subscription_plan: str = "none"  # none, starter, professional, premium
    subscription_status: str = "inactive"  # inactive, active, cancelled
    subscription_id: Optional[str] = None

# Subscription Plans Configuration
SUBSCRIPTION_PLANS = {
    "starter": {
        "name": "Starter",
        "price": 49.00,
        "commission_rate": 0.08,  # 8%
        "description": "Ideal para escolas pequenas"
    },
    "professional": {
        "name": "Professional", 
        "price": 99.00,
        "commission_rate": 0.05,  # 5%
        "description": "Para escolas em crescimento"
    },
    "premium": {
        "name": "Premium",
        "price": 199.00,
        "commission_rate": 0.03,  # 3%
        "description": "Para grandes instituições"
    }
}

class SubscriptionRequest(BaseModel):
    plan: str  # starter, professional, premium
    origin_url: str

class StripeOnboardingRequest(BaseModel):
    origin_url: str

class SchoolUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    description_en: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    image_url: Optional[str] = None
    accreditation: Optional[List[str]] = None
    facilities: Optional[List[str]] = None

class Course(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    school_id: str
    name: str
    name_en: str
    description: str
    description_en: str
    duration_weeks: int
    hours_per_week: int
    level: str
    price: float
    currency: str = "EUR"
    requirements: List[str] = []
    includes: List[str] = []
    start_dates: List[str] = []
    available_spots: int = 20
    status: str = "active"  # active, inactive
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class CourseCreate(BaseModel):
    name: str
    name_en: str
    description: str
    description_en: str
    duration_weeks: int
    hours_per_week: int
    level: str
    price: float
    requirements: List[str] = []
    includes: List[str] = []
    start_dates: List[str] = []
    available_spots: int = 20

class CourseUpdate(BaseModel):
    name: Optional[str] = None
    name_en: Optional[str] = None
    description: Optional[str] = None
    description_en: Optional[str] = None
    duration_weeks: Optional[int] = None
    hours_per_week: Optional[int] = None
    level: Optional[str] = None
    price: Optional[float] = None
    requirements: Optional[List[str]] = None
    includes: Optional[List[str]] = None
    start_dates: Optional[List[str]] = None
    available_spots: Optional[int] = None
    status: Optional[str] = None

class Enrollment(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    user_email: str
    user_name: str
    school_id: str
    school_name: str
    course_id: str
    course_name: str
    start_date: str
    price: float
    currency: str = "EUR"
    status: str = "pending"
    payment_session_id: Optional[str] = None
    letter_sent: bool = False
    letter_sent_date: Optional[str] = None
    letter_url: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class PaymentTransaction(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    user_id: Optional[str] = None
    user_email: Optional[str] = None
    enrollment_id: str
    amount: float
    currency: str
    status: str = "initiated"
    payment_status: str = "pending"
    metadata: Dict[str, str] = {}
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class CreateCheckoutRequest(BaseModel):
    enrollment_id: str
    origin_url: str

class ContactFormRequest(BaseModel):
    name: str
    email: EmailStr
    subject: str
    message: str

class BusRoute(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    route_number: str
    name: str
    name_en: str
    from_location: str
    to_location: str
    frequency_minutes: int
    first_bus: str
    last_bus: str
    fare: float
    zones: List[str] = []
    popular_stops: List[str] = []

class GovernmentAgency(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    name_en: str
    description: str
    description_en: str
    category: str
    address: str
    phone: str
    email: str
    website: str
    opening_hours: str
    services: List[str] = []

class AdminStats(BaseModel):
    total_users: int
    total_schools: int
    pending_schools: int
    approved_schools: int
    total_courses: int
    total_enrollments: int
    paid_enrollments: int
    total_revenue: float
    plus_subscribers: int = 0
    plus_revenue: float = 0.0

# ============== AUTH HELPERS ==============

# Emergent Auth URL for Google OAuth
EMERGENT_AUTH_URL = "https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data"
SESSION_EXPIRY_DAYS = 7

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_token(user_id: str, email: str, role: str = "student") -> str:
    payload = {
        "sub": user_id,
        "email": email,
        "role": role,
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

async def get_session_from_cookie_or_header(
    request: Request,
    session_token: Optional[str] = Cookie(default=None),
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Optional[str]:
    """Get session token from cookie first, then Authorization header as fallback"""
    if session_token:
        return session_token
    if credentials:
        return credentials.credentials
    return None

async def get_current_user(
    request: Request,
    session_token: Optional[str] = Cookie(default=None),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get current user from session token (cookie or header)"""
    token = session_token or (credentials.credentials if credentials else None)
    
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Check user_sessions collection for Google OAuth sessions
    session = await db.user_sessions.find_one({"session_token": token}, {"_id": 0})
    if session:
        # Validate expiry
        expires_at = session.get("expires_at")
        if isinstance(expires_at, str):
            expires_at = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at < datetime.now(timezone.utc):
            raise HTTPException(status_code=401, detail="Session expired")
        
        # Get user by user_id
        user = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    
    # Fallback to legacy JWT token validation
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user = await db.users.find_one({"id": payload["sub"]}, {"_id": 0, "password": 0})
        if not user:
            # Try user_id field
            user = await db.users.find_one({"user_id": payload["sub"]}, {"_id": 0})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def get_admin_user(
    request: Request,
    session_token: Optional[str] = Cookie(default=None),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    user = await get_current_user(request, session_token, credentials)
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user

async def get_school_user(
    request: Request,
    session_token: Optional[str] = Cookie(default=None),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    user = await get_current_user(request, session_token, credentials)
    if user.get("role") != "school":
        raise HTTPException(status_code=403, detail="School access required")
    return user

async def get_optional_user(
    request: Request,
    session_token: Optional[str] = Cookie(default=None),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    try:
        return await get_current_user(request, session_token, credentials)
    except:
        return None

# ============== AUTH ROUTES ==============

# Google OAuth Session Request Model
class GoogleSessionRequest(BaseModel):
    session_id: str

# Google OAuth Session Response
class GoogleAuthResponse(BaseModel):
    user: UserResponse
    message: str = "Login successful"

@api_router.post("/auth/google/session")
async def process_google_session(data: GoogleSessionRequest, response: Response):
    """
    Process Google OAuth session_id from Emergent Auth.
    Exchange session_id for user data and create persistent session.
    REMINDER: DO NOT HARDCODE THE URL, OR ADD ANY FALLBACKS OR REDIRECT URLS, THIS BREAKS THE AUTH
    """
    try:
        # Call Emergent Auth to get session data
        async with httpx.AsyncClient() as client:
            auth_response = await client.get(
                EMERGENT_AUTH_URL,
                headers={"X-Session-ID": data.session_id},
                timeout=30.0
            )
            
            if auth_response.status_code != 200:
                logger.error(f"Emergent Auth error: {auth_response.status_code} - {auth_response.text}")
                raise HTTPException(status_code=401, detail="Invalid session")
            
            session_data = auth_response.json()
        
        email = session_data.get("email")
        name = session_data.get("name", "")
        picture = session_data.get("picture", "")
        session_token = session_data.get("session_token")
        
        if not email or not session_token:
            raise HTTPException(status_code=401, detail="Invalid session data")
        
        # Check if user exists by email
        existing_user = await db.users.find_one({"email": email}, {"_id": 0})
        
        if existing_user:
            # Update existing user data if needed
            user_id = existing_user.get("user_id") or existing_user.get("id")
            await db.users.update_one(
                {"email": email},
                {"$set": {
                    "name": name or existing_user.get("name"),
                    "avatar": picture or existing_user.get("avatar"),
                    "user_id": user_id,  # Ensure user_id field exists
                    "last_login": datetime.now(timezone.utc).isoformat()
                }}
            )
            user = await db.users.find_one({"email": email}, {"_id": 0})
        else:
            # Create new user
            user_id = f"user_{uuid.uuid4().hex[:12]}"
            user = {
                "user_id": user_id,
                "id": user_id,  # For compatibility with legacy code
                "name": name,
                "email": email,
                "avatar": picture,
                "role": "student",
                "plan": "free",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "last_login": datetime.now(timezone.utc).isoformat()
            }
            await db.users.insert_one(user)
            user = await db.users.find_one({"email": email}, {"_id": 0})
        
        # Create session record
        expires_at = datetime.now(timezone.utc) + timedelta(days=SESSION_EXPIRY_DAYS)
        session_record = {
            "user_id": user.get("user_id") or user.get("id"),
            "session_token": session_token,
            "expires_at": expires_at,
            "created_at": datetime.now(timezone.utc)
        }
        
        # Delete old sessions for this user and insert new one
        await db.user_sessions.delete_many({"user_id": session_record["user_id"]})
        await db.user_sessions.insert_one(session_record)
        
        # Set httpOnly cookie
        response.set_cookie(
            key="session_token",
            value=session_token,
            httponly=True,
            secure=True,
            samesite="none",
            path="/",
            max_age=SESSION_EXPIRY_DAYS * 24 * 60 * 60
        )
        
        logger.info(f"Google OAuth login successful for {email}")
        
        return {
            "user": UserResponse(
                id=user.get("user_id") or user.get("id"),
                name=user.get("name", ""),
                email=user.get("email"),
                role=user.get("role", "student"),
                plan=user.get("plan", "free"),
                avatar=user.get("avatar"),
                created_at=user.get("created_at", datetime.now(timezone.utc).isoformat())
            ),
            "message": "Login successful"
        }
        
    except httpx.RequestError as e:
        logger.error(f"HTTP error during Google auth: {e}")
        raise HTTPException(status_code=500, detail="Authentication service unavailable")
    except Exception as e:
        logger.error(f"Google auth error: {e}")
        raise HTTPException(status_code=401, detail="Authentication failed")

@api_router.get("/auth/me")
async def get_me(
    request: Request,
    session_token: Optional[str] = Cookie(default=None),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get current authenticated user"""
    user = await get_current_user(request, session_token, credentials)
    return UserResponse(
        id=user.get("user_id") or user.get("id"),
        name=user.get("name", ""),
        email=user.get("email"),
        role=user.get("role", "student"),
        school_id=user.get("school_id"),
        plan=user.get("plan", "free"),
        plan_purchased_at=user.get("plan_purchased_at"),
        created_at=user.get("created_at", ""),
        avatar=user.get("avatar")
    )

@api_router.post("/auth/logout")
async def logout(
    response: Response,
    request: Request,
    session_token: Optional[str] = Cookie(default=None),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Logout user by deleting session and clearing cookie"""
    token = session_token or (credentials.credentials if credentials else None)
    
    if token:
        # Delete session from database
        await db.user_sessions.delete_one({"session_token": token})
    
    # Clear cookie
    response.delete_cookie(
        key="session_token",
        path="/",
        secure=True,
        samesite="none"
    )
    
    return {"message": "Logged out successfully"}

# Legacy routes kept for school registration (they still need password)
@api_router.post("/auth/register-school", response_model=TokenResponse)
async def register_school(data: SchoolRegister):
    """Register a new school account"""
    existing = await db.users.find_one({"email": data.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email já cadastrado")
    
    user_id = f"user_{uuid.uuid4().hex[:12]}"
    school_id = str(uuid.uuid4())
    
    # Create school record
    school = School(
        id=school_id,
        name=data.school_name,
        description=data.description,
        description_en=data.description_en,
        address=data.address,
        phone=data.phone,
        email=data.email,
        status="pending",
        owner_id=user_id
    )
    await db.schools.insert_one(school.model_dump())
    
    # Create user record
    user = {
        "id": user_id,
        "user_id": user_id,
        "name": data.name,
        "email": data.email,
        "password": hash_password(data.password),
        "role": "school",
        "school_id": school_id,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.users.insert_one(user)
    
    token = create_token(user_id, data.email, "school")
    return TokenResponse(
        access_token=token,
        user=UserResponse(
            id=user_id,
            name=data.name,
            email=data.email,
            role="school",
            school_id=school_id,
            created_at=user["created_at"]
        )
    )

@api_router.put("/auth/profile")
async def update_profile(
    data: UserProfileUpdate,
    request: Request,
    session_token: Optional[str] = Cookie(default=None),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Update user profile (name and avatar)"""
    user = await get_current_user(request, session_token, credentials)
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    
    if not update_data:
        raise HTTPException(status_code=400, detail="No data to update")
    
    user_id = user.get("user_id") or user.get("id")
    await db.users.update_one(
        {"$or": [{"user_id": user_id}, {"id": user_id}]},
        {"$set": update_data}
    )
    
    updated_user = await db.users.find_one(
        {"$or": [{"user_id": user_id}, {"id": user_id}]}, 
        {"_id": 0, "password": 0}
    )
    return UserResponse(
        id=updated_user.get("user_id") or updated_user.get("id"),
        name=updated_user.get("name", ""),
        email=updated_user.get("email"),
        role=updated_user.get("role", "student"),
        school_id=updated_user.get("school_id"),
        plan=updated_user.get("plan", "free"),
        plan_purchased_at=updated_user.get("plan_purchased_at"),
        created_at=updated_user.get("created_at", ""),
        avatar=updated_user.get("avatar")
    )

@api_router.post("/auth/upload-avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    request: Request = None,
    session_token: Optional[str] = Cookie(default=None),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Upload profile avatar image"""
    user = await get_current_user(request, session_token, credentials)
    
    # Validate file type - accept all image types
    if not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="Por favor, envie uma imagem.")
    
    # Validate file size (max 5MB for mobile photos)
    contents = await file.read()
    if len(contents) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Arquivo muito grande. Máximo 5MB.")
    
    # Convert to base64
    base64_image = base64.b64encode(contents).decode('utf-8')
    avatar_data = f"data:{file.content_type};base64,{base64_image}"
    
    # Update user avatar
    user_id = user.get("user_id") or user.get("id")
    await db.users.update_one(
        {"$or": [{"user_id": user_id}, {"id": user_id}]},
        {"$set": {"avatar": avatar_data}}
    )
    
    logger.info(f"Avatar uploaded for user {user_id}")
    
    return {"message": "Avatar atualizado com sucesso", "avatar": avatar_data}

# ============== PLANO PLUS ROUTES ==============

@api_router.get("/plus/info")
async def get_plus_plan_info():
    """Get PLUS plan information (public)"""
    return {
        "plan": STUDENT_PLUS_PLAN,
        "features": [
            "Acesso completo ao catálogo de escolas",
            "Realizar matrículas em cursos",
            "Chat da comunidade STUFF",
            "Guias completos (PPS, GNIB, Passaporte, Carteira)",
            "Suporte prioritário",
            "Acesso vitalício"
        ]
    }

@api_router.post("/plus/checkout")
async def create_plus_checkout(
    data: PlusPlanCheckoutRequest,
    request: Request,
    user: dict = Depends(get_current_user)
):
    """Create checkout session for PLUS plan"""
    # Check if user already has PLUS
    if user.get("plan") == "plus":
        raise HTTPException(status_code=400, detail="Você já possui o Plano PLUS!")
    
    # Only students can buy PLUS plan
    if user.get("role") != "student":
        raise HTTPException(status_code=400, detail="Apenas estudantes podem adquirir o Plano PLUS")
    
    host_url = str(request.base_url).rstrip('/')
    webhook_url = f"{host_url}/api/webhook/stripe"
    
    stripe_checkout = StripeCheckout(api_key=STRIPE_API_KEY, webhook_url=webhook_url)
    
    success_url = f"{data.origin_url}/plus/success?session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url = f"{data.origin_url}/schools"
    
    checkout_request = CheckoutSessionRequest(
        amount=STUDENT_PLUS_PLAN["price"],
        currency="eur",
        success_url=success_url,
        cancel_url=cancel_url,
        metadata={
            "type": "plus_plan",
            "user_id": user["id"],
            "user_email": user["email"],
            "plan_name": "PLUS"
        }
    )
    
    session: CheckoutSessionResponse = await stripe_checkout.create_checkout_session(checkout_request)
    
    # Create transaction record
    transaction = {
        "id": str(uuid.uuid4()),
        "session_id": session.session_id,
        "type": "plus_plan",
        "user_id": user["id"],
        "user_email": user["email"],
        "amount": STUDENT_PLUS_PLAN["price"],
        "currency": "EUR",
        "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.payment_transactions.insert_one(transaction)
    
    logger.info(f"PLUS checkout created for user {user['id']}")
    
    return {"checkout_url": session.url, "session_id": session.session_id}

@api_router.get("/plus/status/{session_id}")
async def check_plus_payment_status(session_id: str, request: Request, user: dict = Depends(get_current_user)):
    """Check PLUS plan payment status and activate if paid"""
    host_url = str(request.base_url).rstrip('/')
    webhook_url = f"{host_url}/api/webhook/stripe"
    
    stripe_checkout = StripeCheckout(api_key=STRIPE_API_KEY, webhook_url=webhook_url)
    
    try:
        status = await stripe_checkout.get_checkout_status(session_id)
        
        # If paid, activate PLUS plan
        if status.payment_status == "paid":
            # Check if not already activated
            transaction = await db.payment_transactions.find_one({"session_id": session_id}, {"_id": 0})
            if transaction and transaction.get("status") != "completed":
                # Update transaction
                await db.payment_transactions.update_one(
                    {"session_id": session_id},
                    {"$set": {"status": "completed", "paid_at": datetime.now(timezone.utc).isoformat()}}
                )
                
                # Activate PLUS plan for user
                await db.users.update_one(
                    {"id": user["id"]},
                    {"$set": {
                        "plan": "plus",
                        "plan_purchased_at": datetime.now(timezone.utc).isoformat(),
                        "plan_session_id": session_id
                    }}
                )
                
                logger.info(f"🎉 PLUS plan activated for user {user['id']} ({user['email']})")
                logger.info("📧 EMAIL: Bem-vindo ao Plano PLUS!")
                logger.info(f"   To: {user['email']}")
        
        return {
            "status": status.status,
            "payment_status": status.payment_status,
            "amount": status.amount_total / 100 if status.amount_total else STUDENT_PLUS_PLAN["price"],
            "currency": status.currency or "eur",
            "plan_activated": status.payment_status == "paid"
        }
    except Exception as e:
        logger.error(f"Error checking PLUS payment status: {e}")
        raise HTTPException(status_code=500, detail="Erro ao verificar status do pagamento")

@api_router.get("/plus/subscribers/count")
async def get_plus_subscribers_count():
    """Get count of PLUS subscribers (public - for social proof)"""
    count = await db.users.count_documents({"plan": "plus"})
    return {"count": count}

# Helper to check if user has PLUS plan
async def require_plus_plan(user: dict = Depends(get_current_user)):
    """Dependency that requires user to have PLUS plan"""
    # Admin and school users have full access
    if user.get("role") in ["admin", "school"]:
        return user
    # Students need PLUS plan for schools access
    if user.get("plan") != "plus":
        raise HTTPException(
            status_code=403, 
            detail="Acesso exclusivo para assinantes do Plano PLUS. Assine agora por €49,90!"
        )
    return user

# ============== ADMIN ROUTES ==============

@api_router.get("/admin/stats", response_model=AdminStats)
async def get_admin_stats(admin: dict = Depends(get_admin_user)):
    """Get dashboard statistics for admin"""
    total_users = await db.users.count_documents({"role": "student"})
    total_schools = await db.schools.count_documents({})
    pending_schools = await db.schools.count_documents({"status": "pending"})
    approved_schools = await db.schools.count_documents({"status": "approved"})
    total_courses = await db.courses.count_documents({})
    total_enrollments = await db.enrollments.count_documents({})
    paid_enrollments = await db.enrollments.count_documents({"status": "paid"})
    
    # Calculate total revenue
    pipeline = [
        {"$match": {"status": "paid"}},
        {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
    ]
    revenue_result = await db.payment_transactions.aggregate(pipeline).to_list(1)
    total_revenue = revenue_result[0]["total"] if revenue_result else 0
    
    # PLUS subscribers stats
    plus_subscribers = await db.users.count_documents({"plan": "plus"})
    plus_revenue = plus_subscribers * STUDENT_PLUS_PLAN["price"]
    
    return AdminStats(
        total_users=total_users,
        total_schools=total_schools,
        pending_schools=pending_schools,
        approved_schools=approved_schools,
        total_courses=total_courses,
        total_enrollments=total_enrollments,
        paid_enrollments=paid_enrollments,
        total_revenue=total_revenue,
        plus_subscribers=plus_subscribers,
        plus_revenue=plus_revenue
    )

@api_router.get("/admin/schools")
async def admin_get_schools(admin: dict = Depends(get_admin_user), status: Optional[str] = None):
    """Get all schools for admin"""
    query = {}
    if status:
        query["status"] = status
    schools = await db.schools.find(query, {"_id": 0}).to_list(100)
    return schools

@api_router.put("/admin/schools/{school_id}/approve")
async def admin_approve_school(school_id: str, admin: dict = Depends(get_admin_user)):
    """Approve a school"""
    result = await db.schools.update_one(
        {"id": school_id},
        {"$set": {"status": "approved"}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="School not found")
    return {"message": "School approved", "school_id": school_id}

@api_router.put("/admin/schools/{school_id}/reject")
async def admin_reject_school(school_id: str, admin: dict = Depends(get_admin_user)):
    """Reject a school"""
    result = await db.schools.update_one(
        {"id": school_id},
        {"$set": {"status": "rejected"}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="School not found")
    return {"message": "School rejected", "school_id": school_id}

@api_router.get("/admin/users")
async def admin_get_users(admin: dict = Depends(get_admin_user), role: Optional[str] = None):
    """Get all users for admin"""
    query = {}
    if role:
        query["role"] = role
    users = await db.users.find(query, {"_id": 0, "password": 0}).to_list(500)
    return users

@api_router.get("/admin/enrollments")
async def admin_get_enrollments(admin: dict = Depends(get_admin_user), status: Optional[str] = None):
    """Get all enrollments for admin"""
    query = {}
    if status:
        query["status"] = status
    enrollments = await db.enrollments.find(query, {"_id": 0}).to_list(500)
    return enrollments

@api_router.get("/admin/payments")
async def admin_get_payments(admin: dict = Depends(get_admin_user), status: Optional[str] = None):
    """Get all payments for admin"""
    query = {}
    if status:
        query["status"] = status
    payments = await db.payment_transactions.find(query, {"_id": 0}).to_list(500)
    return payments

# ============== SCHOOL DASHBOARD ROUTES ==============

@api_router.get("/school/dashboard")
async def school_dashboard(user: dict = Depends(get_school_user)):
    """Get school dashboard data"""
    school_id = user.get("school_id")
    if not school_id:
        raise HTTPException(status_code=400, detail="No school associated with this account")
    
    school = await db.schools.find_one({"id": school_id}, {"_id": 0})
    if not school:
        raise HTTPException(status_code=404, detail="School not found")
    
    # Get stats
    total_courses = await db.courses.count_documents({"school_id": school_id})
    total_enrollments = await db.enrollments.count_documents({"school_id": school_id})
    paid_enrollments = await db.enrollments.count_documents({"school_id": school_id, "status": "paid"})
    pending_letters = await db.enrollments.count_documents({
        "school_id": school_id, 
        "status": "paid",
        "letter_sent": False
    })
    
    # Calculate revenue
    pipeline = [
        {"$match": {"school_id": school_id, "status": "paid"}},
        {"$group": {"_id": None, "total": {"$sum": "$price"}}}
    ]
    revenue_result = await db.enrollments.aggregate(pipeline).to_list(1)
    total_revenue = revenue_result[0]["total"] if revenue_result else 0
    
    return {
        "school": school,
        "stats": {
            "total_courses": total_courses,
            "total_enrollments": total_enrollments,
            "paid_enrollments": paid_enrollments,
            "pending_letters": pending_letters,
            "total_revenue": total_revenue
        }
    }

@api_router.get("/school/profile")
async def get_school_profile(user: dict = Depends(get_school_user)):
    """Get school profile"""
    school_id = user.get("school_id")
    school = await db.schools.find_one({"id": school_id}, {"_id": 0})
    if not school:
        raise HTTPException(status_code=404, detail="School not found")
    return school

@api_router.put("/school/profile")
async def update_school_profile(data: SchoolUpdate, user: dict = Depends(get_school_user)):
    """Update school profile"""
    school_id = user.get("school_id")
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    
    if not update_data:
        raise HTTPException(status_code=400, detail="No data to update")
    
    result = await db.schools.update_one(
        {"id": school_id},
        {"$set": update_data}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="School not found")
    
    school = await db.schools.find_one({"id": school_id}, {"_id": 0})
    return school

@api_router.get("/school/courses")
async def get_school_courses(user: dict = Depends(get_school_user)):
    """Get courses for the school"""
    school_id = user.get("school_id")
    courses = await db.courses.find({"school_id": school_id}, {"_id": 0}).to_list(100)
    return courses

@api_router.post("/school/courses")
async def create_school_course(data: CourseCreate, user: dict = Depends(get_school_user)):
    """Create a new course for the school"""
    school_id = user.get("school_id")
    
    # Check if school is approved
    school = await db.schools.find_one({"id": school_id}, {"_id": 0})
    if not school or school.get("status") != "approved":
        raise HTTPException(status_code=403, detail="School must be approved to create courses")
    
    course = Course(
        school_id=school_id,
        **data.model_dump()
    )
    await db.courses.insert_one(course.model_dump())
    return course

@api_router.put("/school/courses/{course_id}")
async def update_school_course(course_id: str, data: CourseUpdate, user: dict = Depends(get_school_user)):
    """Update a course"""
    school_id = user.get("school_id")
    
    # Verify course belongs to school
    course = await db.courses.find_one({"id": course_id, "school_id": school_id})
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No data to update")
    
    await db.courses.update_one({"id": course_id}, {"$set": update_data})
    course = await db.courses.find_one({"id": course_id}, {"_id": 0})
    return course

@api_router.delete("/school/courses/{course_id}")
async def delete_school_course(course_id: str, user: dict = Depends(get_school_user)):
    """Delete a course (soft delete - set status to inactive)"""
    school_id = user.get("school_id")
    
    result = await db.courses.update_one(
        {"id": course_id, "school_id": school_id},
        {"$set": {"status": "inactive"}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Course not found")
    return {"message": "Course deleted"}

@api_router.get("/school/enrollments")
async def get_school_enrollments(user: dict = Depends(get_school_user), status: Optional[str] = None):
    """Get enrollments for the school"""
    school_id = user.get("school_id")
    query = {"school_id": school_id}
    if status:
        query["status"] = status
    enrollments = await db.enrollments.find(query, {"_id": 0}).to_list(500)
    return enrollments

@api_router.put("/school/enrollments/{enrollment_id}/send-letter")
async def send_enrollment_letter(enrollment_id: str, letter_url: str, user: dict = Depends(get_school_user)):
    """Mark letter as sent for an enrollment"""
    school_id = user.get("school_id")
    
    result = await db.enrollments.update_one(
        {"id": enrollment_id, "school_id": school_id, "status": "paid"},
        {"$set": {
            "letter_sent": True,
            "letter_sent_date": datetime.now(timezone.utc).isoformat(),
            "letter_url": letter_url
        }}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Enrollment not found or not paid")
    
    # Log email notification
    enrollment = await db.enrollments.find_one({"id": enrollment_id}, {"_id": 0})
    logger.info(f"📧 EMAIL: Letter sent for enrollment {enrollment_id}")
    logger.info(f"   To: {enrollment.get('user_email')}")
    logger.info(f"   Letter URL: {letter_url}")
    
    return {"message": "Letter sent", "enrollment_id": enrollment_id}

# ============== STRIPE CONNECT FOR SCHOOLS ==============

@api_router.get("/school/subscription/plans")
async def get_subscription_plans():
    """Get available subscription plans"""
    return {
        "plans": [
            {
                "id": plan_id,
                "name": plan["name"],
                "price": plan["price"],
                "commission_rate": plan["commission_rate"] * 100,  # Return as percentage
                "description": plan["description"]
            }
            for plan_id, plan in SUBSCRIPTION_PLANS.items()
        ]
    }

@api_router.post("/school/subscription/subscribe")
async def subscribe_to_plan(data: SubscriptionRequest, request: Request, user: dict = Depends(get_school_user)):
    """Subscribe school to a plan"""
    if data.plan not in SUBSCRIPTION_PLANS:
        raise HTTPException(status_code=400, detail="Plano inválido")
    
    school_id = user.get("school_id")
    school = await db.schools.find_one({"id": school_id}, {"_id": 0})
    if not school:
        raise HTTPException(status_code=404, detail="Escola não encontrada")
    
    plan = SUBSCRIPTION_PLANS[data.plan]
    
    # Create Stripe checkout for subscription
    host_url = data.origin_url
    success_url = f"{host_url}/school/subscription/success?session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url = f"{host_url}/school/subscription"
    
    stripe_checkout = StripeCheckout(api_key=STRIPE_API_KEY, webhook_url=f"{str(request.base_url)}api/webhook/stripe")
    
    checkout_request = CheckoutSessionRequest(
        amount=plan["price"],
        currency="eur",
        success_url=success_url,
        cancel_url=cancel_url,
        metadata={
            "type": "subscription",
            "school_id": school_id,
            "plan": data.plan,
            "plan_name": plan["name"]
        }
    )
    
    session = await stripe_checkout.create_checkout_session(checkout_request)
    
    # Create payment transaction record
    transaction = {
        "id": str(uuid.uuid4()),
        "session_id": session.session_id,
        "type": "subscription",
        "school_id": school_id,
        "plan": data.plan,
        "amount": plan["price"],
        "currency": "EUR",
        "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.payment_transactions.insert_one(transaction)
    
    return {"checkout_url": session.url, "session_id": session.session_id}

@api_router.get("/school/subscription/status/{session_id}")
async def check_subscription_status(session_id: str, request: Request, user: dict = Depends(get_school_user)):
    """Check subscription payment status"""
    school_id = user.get("school_id")
    
    stripe_checkout = StripeCheckout(api_key=STRIPE_API_KEY, webhook_url=f"{str(request.base_url)}api/webhook/stripe")
    
    try:
        status = await stripe_checkout.get_checkout_status(session_id)
        
        # Update transaction and school if paid
        if status.payment_status == "paid":
            # Get transaction to find plan
            transaction = await db.payment_transactions.find_one({"session_id": session_id}, {"_id": 0})
            if transaction and transaction.get("status") != "completed":
                plan = transaction.get("plan", "starter")
                
                # Update transaction
                await db.payment_transactions.update_one(
                    {"session_id": session_id},
                    {"$set": {"status": "completed", "paid_at": datetime.now(timezone.utc).isoformat()}}
                )
                
                # Update school subscription
                await db.schools.update_one(
                    {"id": school_id},
                    {"$set": {
                        "subscription_plan": plan,
                        "subscription_status": "active",
                        "subscription_id": session_id,
                        "subscription_started_at": datetime.now(timezone.utc).isoformat()
                    }}
                )
                
                logger.info(f"School {school_id} subscribed to {plan} plan")
        
        return {
            "status": status.status,
            "payment_status": status.payment_status,
            "amount": status.amount_total / 100,  # Convert from cents
            "currency": status.currency
        }
    except Exception as e:
        logger.error(f"Error checking subscription status: {e}")
        raise HTTPException(status_code=500, detail="Erro ao verificar status do pagamento")

@api_router.get("/school/subscription")
async def get_school_subscription(user: dict = Depends(get_school_user)):
    """Get school subscription details"""
    school_id = user.get("school_id")
    school = await db.schools.find_one({"id": school_id}, {"_id": 0})
    
    if not school:
        raise HTTPException(status_code=404, detail="Escola não encontrada")
    
    plan_id = school.get("subscription_plan", "none")
    plan_details = SUBSCRIPTION_PLANS.get(plan_id, None)
    
    return {
        "plan": plan_id,
        "plan_details": {
            "name": plan_details["name"] if plan_details else "Sem plano",
            "price": plan_details["price"] if plan_details else 0,
            "commission_rate": plan_details["commission_rate"] * 100 if plan_details else 0
        } if plan_details else None,
        "status": school.get("subscription_status", "inactive"),
        "stripe_connected": school.get("stripe_onboarding_complete", False),
        "stripe_account_id": school.get("stripe_account_id")
    }

@api_router.get("/school/earnings")
async def get_school_earnings(user: dict = Depends(get_school_user)):
    """Get school earnings breakdown"""
    school_id = user.get("school_id")
    school = await db.schools.find_one({"id": school_id}, {"_id": 0})
    
    if not school:
        raise HTTPException(status_code=404, detail="Escola não encontrada")
    
    # Get commission rate based on plan
    plan_id = school.get("subscription_plan", "starter")
    commission_rate = SUBSCRIPTION_PLANS.get(plan_id, SUBSCRIPTION_PLANS["starter"])["commission_rate"]
    
    # Get all paid enrollments
    enrollments = await db.enrollments.find(
        {"school_id": school_id, "status": "paid"},
        {"_id": 0}
    ).to_list(1000)
    
    total_gross = sum(e.get("price", 0) for e in enrollments)
    total_commission = total_gross * commission_rate
    total_net = total_gross - total_commission
    
    # Monthly breakdown
    monthly_earnings = {}
    for enrollment in enrollments:
        paid_at = enrollment.get("paid_at", enrollment.get("created_at", ""))
        if paid_at:
            month_key = paid_at[:7]  # YYYY-MM
            if month_key not in monthly_earnings:
                monthly_earnings[month_key] = {"gross": 0, "commission": 0, "net": 0}
            monthly_earnings[month_key]["gross"] += enrollment.get("price", 0)
            monthly_earnings[month_key]["commission"] += enrollment.get("price", 0) * commission_rate
            monthly_earnings[month_key]["net"] += enrollment.get("price", 0) * (1 - commission_rate)
    
    return {
        "summary": {
            "total_gross": round(total_gross, 2),
            "total_commission": round(total_commission, 2),
            "commission_rate": commission_rate * 100,
            "total_net": round(total_net, 2),
            "total_enrollments": len(enrollments)
        },
        "plan": {
            "name": SUBSCRIPTION_PLANS.get(plan_id, {}).get("name", "Starter"),
            "commission_rate": commission_rate * 100
        },
        "monthly": monthly_earnings
    }

# ============== PUBLIC SCHOOLS ROUTES ==============

@api_router.get("/schools", response_model=List[School])
async def get_schools():
    # Only return approved schools for public listing
    schools = await db.schools.find({"status": "approved"}, {"_id": 0}).to_list(100)
    return schools

@api_router.get("/schools/{school_id}", response_model=School)
async def get_school(school_id: str):
    school = await db.schools.find_one({"id": school_id, "status": "approved"}, {"_id": 0})
    if not school:
        raise HTTPException(status_code=404, detail="Escola não encontrada")
    return school

@api_router.get("/schools/{school_id}/courses", response_model=List[Course])
async def get_school_courses_public(school_id: str):
    courses = await db.courses.find(
        {"school_id": school_id, "status": "active"}, 
        {"_id": 0}
    ).to_list(100)
    return courses

# ============== COURSES ROUTES ==============

@api_router.get("/courses", response_model=List[Course])
async def get_courses():
    courses = await db.courses.find({"status": "active"}, {"_id": 0}).to_list(100)
    return courses

@api_router.get("/courses/{course_id}", response_model=Course)
async def get_course(course_id: str):
    course = await db.courses.find_one({"id": course_id, "status": "active"}, {"_id": 0})
    if not course:
        raise HTTPException(status_code=404, detail="Curso não encontrado")
    return course

# ============== ENROLLMENT ROUTES ==============

@api_router.post("/enrollments", response_model=Enrollment)
async def create_enrollment(
    course_id: str,
    start_date: str,
    user: dict = Depends(get_current_user)
):
    course = await db.courses.find_one({"id": course_id, "status": "active"}, {"_id": 0})
    if not course:
        raise HTTPException(status_code=404, detail="Curso não encontrado")
    
    school = await db.schools.find_one({"id": course["school_id"], "status": "approved"}, {"_id": 0})
    if not school:
        raise HTTPException(status_code=404, detail="Escola não encontrada")
    
    enrollment = Enrollment(
        user_id=user["id"],
        user_email=user["email"],
        user_name=user["name"],
        school_id=school["id"],
        school_name=school["name"],
        course_id=course["id"],
        course_name=course["name"],
        start_date=start_date,
        price=course["price"],
        currency=course["currency"]
    )
    
    await db.enrollments.insert_one(enrollment.model_dump())
    return enrollment

@api_router.get("/enrollments", response_model=List[Enrollment])
async def get_user_enrollments(user: dict = Depends(get_current_user)):
    enrollments = await db.enrollments.find(
        {"user_id": user["id"]}, {"_id": 0}
    ).to_list(100)
    return enrollments

@api_router.get("/enrollments/{enrollment_id}", response_model=Enrollment)
async def get_enrollment(enrollment_id: str, user: dict = Depends(get_current_user)):
    enrollment = await db.enrollments.find_one(
        {"id": enrollment_id, "user_id": user["id"]}, {"_id": 0}
    )
    if not enrollment:
        raise HTTPException(status_code=404, detail="Matrícula não encontrada")
    return enrollment

# ============== PAYMENT ROUTES ==============

@api_router.post("/payments/checkout")
async def create_checkout(
    request: CreateCheckoutRequest,
    http_request: Request,
    user: dict = Depends(get_current_user)
):
    enrollment = await db.enrollments.find_one(
        {"id": request.enrollment_id, "user_id": user["id"]}, {"_id": 0}
    )
    if not enrollment:
        raise HTTPException(status_code=404, detail="Matrícula não encontrada")
    
    if enrollment.get("status") == "paid":
        raise HTTPException(status_code=400, detail="Esta matrícula já foi paga")
    
    host_url = str(http_request.base_url).rstrip('/')
    webhook_url = f"{host_url}/api/webhook/stripe"
    
    stripe_checkout = StripeCheckout(api_key=STRIPE_API_KEY, webhook_url=webhook_url)
    
    success_url = f"{request.origin_url}/payment/success?session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url = f"{request.origin_url}/dashboard"
    
    checkout_request = CheckoutSessionRequest(
        amount=float(enrollment["price"]),
        currency="eur",
        success_url=success_url,
        cancel_url=cancel_url,
        metadata={
            "enrollment_id": enrollment["id"],
            "user_id": user["id"],
            "user_email": user["email"],
            "school_name": enrollment["school_name"],
            "course_name": enrollment["course_name"]
        }
    )
    
    session: CheckoutSessionResponse = await stripe_checkout.create_checkout_session(checkout_request)
    
    transaction = PaymentTransaction(
        session_id=session.session_id,
        user_id=user["id"],
        user_email=user["email"],
        enrollment_id=enrollment["id"],
        amount=float(enrollment["price"]),
        currency="eur",
        status="initiated",
        payment_status="pending",
        metadata={
            "school_name": enrollment["school_name"],
            "course_name": enrollment["course_name"]
        }
    )
    await db.payment_transactions.insert_one(transaction.model_dump())
    
    await db.enrollments.update_one(
        {"id": enrollment["id"]},
        {"$set": {"payment_session_id": session.session_id}}
    )
    
    return {"url": session.url, "session_id": session.session_id}

@api_router.get("/payments/status/{session_id}")
async def get_payment_status(session_id: str, http_request: Request):
    host_url = str(http_request.base_url).rstrip('/')
    webhook_url = f"{host_url}/api/webhook/stripe"
    
    stripe_checkout = StripeCheckout(api_key=STRIPE_API_KEY, webhook_url=webhook_url)
    
    try:
        status: CheckoutStatusResponse = await stripe_checkout.get_checkout_status(session_id)
        
        transaction = await db.payment_transactions.find_one(
            {"session_id": session_id}, {"_id": 0}
        )
        
        if transaction and transaction.get("status") != "paid" and status.payment_status == "paid":
            await db.payment_transactions.update_one(
                {"session_id": session_id},
                {"$set": {
                    "status": "paid",
                    "payment_status": "paid",
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }}
            )
            
            enrollment_id = transaction.get("enrollment_id")
            if enrollment_id:
                await db.enrollments.update_one(
                    {"id": enrollment_id},
                    {"$set": {"status": "paid", "paid_at": datetime.now(timezone.utc).isoformat()}}
                )
                
                # Generate Digital Passport automatically
                passport = await generate_digital_passport(enrollment_id)
                if passport:
                    logger.info(f"🎫 Digital Passport auto-generated: {passport.get('enrollment_number')}")
                
                logger.info(f"📧 EMAIL NOTIFICATION: Payment confirmed for enrollment {enrollment_id}")
                logger.info(f"   To: {transaction.get('user_email')}")
                logger.info("   Subject: Pagamento Confirmado - Dublin Study")
        
        return {
            "status": status.status,
            "payment_status": status.payment_status,
            "amount_total": status.amount_total,
            "currency": status.currency
        }
    except Exception as e:
        logger.error(f"Error checking payment status: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@api_router.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    body = await request.body()
    signature = request.headers.get("Stripe-Signature")
    
    host_url = str(request.base_url).rstrip('/')
    webhook_url = f"{host_url}/api/webhook/stripe"
    
    stripe_checkout = StripeCheckout(api_key=STRIPE_API_KEY, webhook_url=webhook_url)
    
    try:
        webhook_response = await stripe_checkout.handle_webhook(body, signature)
        
        if webhook_response.payment_status == "paid":
            session_id = webhook_response.session_id
            
            transaction = await db.payment_transactions.find_one(
                {"session_id": session_id}, {"_id": 0}
            )
            
            if transaction and transaction.get("status") != "paid":
                await db.payment_transactions.update_one(
                    {"session_id": session_id},
                    {"$set": {
                        "status": "paid",
                        "payment_status": "paid",
                        "updated_at": datetime.now(timezone.utc).isoformat()
                    }}
                )
                
                enrollment_id = webhook_response.metadata.get("enrollment_id")
                if enrollment_id:
                    await db.enrollments.update_one(
                        {"id": enrollment_id},
                        {"$set": {"status": "paid"}}
                    )
        
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return {"status": "error", "message": str(e)}

# ============== TRANSPORT ROUTES ==============

@api_router.get("/transport/routes", response_model=List[BusRoute])
async def get_bus_routes():
    routes = await db.bus_routes.find({}, {"_id": 0}).to_list(100)
    return routes

# ============== GOVERNMENT SERVICES ROUTES ==============

@api_router.get("/services/agencies", response_model=List[GovernmentAgency])
async def get_agencies():
    agencies = await db.agencies.find({}, {"_id": 0}).to_list(100)
    return agencies

@api_router.get("/services/agencies/{category}")
async def get_agencies_by_category(category: str):
    agencies = await db.agencies.find({"category": category}, {"_id": 0}).to_list(100)
    return agencies

# ============== CONTACT FORM ==============

@api_router.post("/contact")
async def submit_contact_form(data: ContactFormRequest):
    """Submit contact form - currently logs to console (mock)"""
    logger.info("📧 CONTACT FORM RECEIVED:")
    logger.info(f"   From: {data.name} <{data.email}>")
    logger.info(f"   Subject: {data.subject}")
    logger.info(f"   Message: {data.message}")
    
    # Store in database for future reference
    contact_entry = {
        "id": str(uuid.uuid4()),
        "name": data.name,
        "email": data.email,
        "subject": data.subject,
        "message": data.message,
        "status": "new",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.contact_messages.insert_one(contact_entry)
    
    return {"message": "Mensagem enviada com sucesso!", "id": contact_entry["id"]}

# ============== GUIDES (Static Content) ==============

@api_router.get("/guides/pps")
async def get_pps_guide():
    return {
        "title": "Guia PPS Number",
        "title_en": "PPS Number Guide",
        "description": "O PPS (Personal Public Service) Number é essencial para trabalhar na Irlanda",
        "steps": [
            {
                "step": 1,
                "title": "Agende online",
                "title_en": "Book online",
                "description": "Acesse mywelfare.ie e agende seu atendimento",
                "link": "https://www.mywelfare.ie"
            },
            {
                "step": 2,
                "title": "Prepare os documentos",
                "title_en": "Prepare documents",
                "description": "Passaporte, comprovante de endereço, carta da escola",
                "documents": ["Passaporte válido", "Comprovante de endereço (utility bill)", "Carta da escola", "Formulário REG1"]
            },
            {
                "step": 3,
                "title": "Compareça ao atendimento",
                "title_en": "Attend appointment",
                "description": "Vá ao escritório do DSP no dia e hora marcados"
            },
            {
                "step": 4,
                "title": "Receba seu PPS",
                "title_en": "Receive your PPS",
                "description": "O número será enviado por correio em até 5 dias úteis"
            }
        ],
        "tips": [
            "Chegue 15 minutos antes do horário marcado",
            "Leve documentos originais e cópias",
            "O PPS é gratuito"
        ],
        "useful_links": [
            {"name": "MyWelfare.ie", "url": "https://www.mywelfare.ie"},
            {"name": "Citizens Information", "url": "https://www.citizensinformation.ie/en/social-welfare/irish-social-welfare-system/personal-public-service-number/"}
        ]
    }

@api_router.get("/guides/gnib")
async def get_gnib_guide():
    return {
        "title": "Guia GNIB/IRP",
        "title_en": "GNIB/IRP Guide",
        "description": "O IRP (Irish Residence Permit) é obrigatório para estudantes não-europeus",
        "steps": [
            {
                "step": 1,
                "title": "Agende online",
                "title_en": "Book online",
                "description": "Acesse o site do INIS para agendar",
                "link": "https://burghquayregistrationoffice.inis.gov.ie/"
            },
            {
                "step": 2,
                "title": "Prepare os documentos",
                "title_en": "Prepare documents",
                "description": "Documentos necessários para o registro",
                "documents": [
                    "Passaporte válido",
                    "Carta da escola",
                    "Comprovante de endereço",
                    "Comprovante financeiro (€4.200)",
                    "Seguro de saúde privado",
                    "Taxa de €300"
                ]
            },
            {
                "step": 3,
                "title": "Compareça ao Burgh Quay",
                "title_en": "Attend Burgh Quay",
                "description": "Vá ao Immigration Office com todos os documentos"
            },
            {
                "step": 4,
                "title": "Receba seu IRP Card",
                "title_en": "Receive IRP Card",
                "description": "O cartão será entregue no local ou enviado por correio"
            }
        ],
        "costs": {
            "registration_fee": 300,
            "currency": "EUR",
            "bank_statement_minimum": 4200
        },
        "tips": [
            "Agende com antecedência - as vagas acabam rápido!",
            "A taxa só pode ser paga com cartão de débito/crédito",
            "O IRP tem validade de 1 ano para estudantes"
        ],
        "useful_links": [
            {"name": "INIS Booking", "url": "https://burghquayregistrationoffice.inis.gov.ie/"},
            {"name": "Immigration Service", "url": "https://www.irishimmigration.ie/"}
        ]
    }

@api_router.get("/guides/passport")
async def get_passport_guide():
    return {
        "title": "Guia de Passaporte Brasileiro",
        "title_en": "Brazilian Passport Guide",
        "description": "Como tirar ou renovar seu passaporte brasileiro",
        "steps": [
            {
                "step": 1,
                "title": "Acesse o Portal da PF",
                "title_en": "Access Federal Police Portal",
                "description": "Entre no site da Polícia Federal e preencha o formulário",
                "link": "https://www.gov.br/pf/pt-br/assuntos/passaporte"
            },
            {
                "step": 2,
                "title": "Pague a taxa (GRU)",
                "title_en": "Pay the fee (GRU)",
                "description": "Emita e pague a Guia de Recolhimento da União",
                "cost": 257.25,
                "currency": "BRL"
            },
            {
                "step": 3,
                "title": "Agende o atendimento",
                "title_en": "Schedule appointment",
                "description": "Escolha um posto da PF e agende seu horário"
            },
            {
                "step": 4,
                "title": "Compareça ao atendimento",
                "title_en": "Attend appointment",
                "description": "Vá ao posto com os documentos originais",
                "documents": [
                    "RG ou CNH",
                    "CPF",
                    "Título de Eleitor (se aplicável)",
                    "Certificado de Reservista (homens)",
                    "Comprovante de pagamento da GRU"
                ]
            },
            {
                "step": 5,
                "title": "Retire seu passaporte",
                "title_en": "Pick up passport",
                "description": "Aguarde a emissão e retire no mesmo posto (6 a 10 dias úteis)"
            }
        ],
        "costs": {
            "regular": 257.25,
            "emergency": 334.42,
            "currency": "BRL"
        },
        "validity": {
            "adults": "10 anos",
            "minors": "5 anos (menores de 18 anos)"
        },
        "tips": [
            "Verifique se seu RG está atualizado (menos de 10 anos)",
            "Certidão de nascimento pode ser necessária",
            "Menores precisam de autorização dos pais"
        ],
        "useful_links": [
            {"name": "Portal da PF", "url": "https://www.gov.br/pf/pt-br/assuntos/passaporte"},
            {"name": "Emitir GRU", "url": "https://servicos.dpf.gov.br/gru/gru.html"}
        ]
    }

@api_router.get("/guides/driving-license")
async def get_driving_license_guide():
    return {
        "title": "Carteira de Motorista na Irlanda",
        "title_en": "Driver's License in Ireland",
        "description": "Guia completo para tirar ou trocar sua carteira de motorista na Irlanda",
        "intro": {
            "pt": "Se você pretende dirigir na Irlanda, precisa entender as regras sobre carteira de motorista. Brasileiros podem usar a CNH por até 12 meses, mas após esse período precisam obter a carteira irlandesa.",
            "en": "If you plan to drive in Ireland, you need to understand the rules about driver's licenses. Brazilians can use their license for up to 12 months, but after that they need to obtain an Irish license."
        },
        "options": [
            {
                "title": "Usar CNH Brasileira",
                "title_en": "Use Brazilian License",
                "description": "Válida por até 12 meses após chegada na Irlanda",
                "description_en": "Valid for up to 12 months after arriving in Ireland",
                "requirements": ["CNH válida", "Tradução juramentada (recomendado)", "Permissão Internacional (IDP)"]
            },
            {
                "title": "Trocar CNH por Carteira Irlandesa",
                "title_en": "Exchange Brazilian License",
                "description": "Brasil não tem acordo de troca direta com a Irlanda. Você precisará fazer o processo completo.",
                "description_en": "Brazil does not have a direct exchange agreement with Ireland. You will need to complete the full process.",
                "note": "Não é possível trocar diretamente"
            },
            {
                "title": "Tirar Carteira Irlandesa (Processo Completo)",
                "title_en": "Get Irish License (Full Process)",
                "description": "Processo obrigatório para quem quer dirigir legalmente após 12 meses",
                "description_en": "Mandatory process for those who want to drive legally after 12 months"
            }
        ],
        "steps": [
            {
                "step": 1,
                "title": "Solicite a Learner Permit",
                "title_en": "Apply for Learner Permit",
                "description": "A Learner Permit é a carteira provisória. Você precisa passar no teste teórico primeiro.",
                "description_en": "The Learner Permit is the provisional license. You need to pass the theory test first.",
                "sub_steps": [
                    "Agende o Theory Test no site theorytest.ie",
                    "Estude o livro 'Rules of the Road'",
                    "Passe no teste teórico (40 questões, precisa acertar 35)",
                    "Solicite a Learner Permit no NDLS"
                ],
                "link": "https://www.theorytest.ie"
            },
            {
                "step": 2,
                "title": "Faça Aulas de Condução (EDT)",
                "title_en": "Take Driving Lessons (EDT)",
                "description": "São obrigatórias 12 aulas de condução com instrutor aprovado (ADI).",
                "description_en": "12 driving lessons with an approved instructor (ADI) are mandatory.",
                "details": {
                    "lessons": 12,
                    "duration": "Cada aula tem 1 hora",
                    "cost_range": "€30-50 por aula",
                    "total_estimate": "€360-600 total"
                }
            },
            {
                "step": 3,
                "title": "Pratique com Acompanhante",
                "title_en": "Practice with Sponsor",
                "description": "Com a Learner Permit, você pode praticar acompanhado de alguém com carteira há mais de 2 anos.",
                "description_en": "With the Learner Permit, you can practice accompanied by someone with a license for more than 2 years.",
                "rules": [
                    "Sempre use placa 'L' (Learner)",
                    "Não pode dirigir em autoestradas",
                    "Acompanhante deve ter carteira há 2+ anos"
                ]
            },
            {
                "step": 4,
                "title": "Agende o Teste Prático",
                "title_en": "Book Practical Test",
                "description": "Após completar as 12 aulas EDT, você pode agendar o teste prático de direção.",
                "description_en": "After completing the 12 EDT lessons, you can book the practical driving test.",
                "link": "https://www.rsa.ie/services/learner-drivers/the-driving-test",
                "cost": 85,
                "currency": "EUR"
            },
            {
                "step": 5,
                "title": "Solicite a Full Driving Licence",
                "title_en": "Apply for Full Driving Licence",
                "description": "Após passar no teste prático, solicite sua carteira definitiva no NDLS.",
                "description_en": "After passing the practical test, apply for your full license at NDLS.",
                "link": "https://www.ndls.ie",
                "documents": [
                    "Learner Permit",
                    "Certificado de aprovação no teste",
                    "Comprovante de residência",
                    "GNIB/IRP Card",
                    "PPS Number",
                    "Foto tipo passaporte"
                ],
                "cost": 55,
                "currency": "EUR"
            }
        ],
        "costs": {
            "theory_test": 45,
            "learner_permit": 35,
            "edt_lessons": "360-600 (12 aulas)",
            "practical_test": 85,
            "full_license": 55,
            "total_estimate": "580-820",
            "currency": "EUR"
        },
        "timeline": {
            "minimum": "6 meses",
            "typical": "6-12 meses",
            "note": "Você precisa ter a Learner Permit por pelo menos 6 meses antes de fazer o teste prático"
        },
        "tips": [
            "Comece o processo cedo - leva no mínimo 6 meses",
            "O Theory Test está disponível em vários idiomas, incluindo português",
            "Guarde todos os recibos das aulas EDT - são obrigatórios",
            "O teste prático tem lista de espera - agende com antecedência",
            "Considere fazer mais que 12 aulas se não tiver experiência",
            "Pratique bastante em diferentes condições (chuva, noite)"
        ],
        "useful_links": [
            {"name": "NDLS - National Driver Licence Service", "url": "https://www.ndls.ie"},
            {"name": "Theory Test Ireland", "url": "https://www.theorytest.ie"},
            {"name": "RSA - Road Safety Authority", "url": "https://www.rsa.ie"},
            {"name": "Rules of the Road (PDF)", "url": "https://www.rsa.ie/road-safety/education/rules-of-the-road"},
            {"name": "Encontrar Instrutor (ADI)", "url": "https://www.rsa.ie/services/learner-drivers/finding-an-instructor"}
        ],
        "important_notes": [
            {
                "title": "Acordo Brasil-Irlanda",
                "content": "Infelizmente, o Brasil não tem acordo de troca de carteira com a Irlanda. Isso significa que você precisará fazer todo o processo do zero, mesmo tendo CNH válida."
            },
            {
                "title": "Validade da CNH",
                "content": "Sua CNH brasileira é válida por 12 meses após sua chegada. Após esse período, dirigir com CNH brasileira é considerado dirigir sem habilitação."
            },
            {
                "title": "Seguro",
                "content": "O seguro de carro na Irlanda é caro, especialmente para novos motoristas. Com Learner Permit, você precisará de seguro específico."
            }
        ]
    }

# ============== SEED DATA ==============

@api_router.post("/seed")
async def seed_database():
    """Seed database with initial data"""
    
    # Clear existing data (except users)
    await db.schools.delete_many({})
    await db.courses.delete_many({})
    await db.bus_routes.delete_many({})
    await db.agencies.delete_many({})
    
    # Create admin user if not exists
    admin_exists = await db.users.find_one({"email": "admin@dublinstudy.com"})
    if not admin_exists:
        admin_id = str(uuid.uuid4())
        await db.users.insert_one({
            "id": admin_id,
            "name": "Admin",
            "email": "admin@dublinstudy.com",
            "password": hash_password("admin123"),
            "role": "admin",
            "created_at": datetime.now(timezone.utc).isoformat()
        })
    
    # Seed Schools - 25 Real Dublin Language Schools
    schools = [
        School(
            id="school-1",
            name="Atlas Language School",
            description="Escola premiada em Portobello, Dublin. Oferece cursos de inglês de alta qualidade com professores experientes e ambiente internacional.",
            description_en="Award-winning school in Portobello, Dublin. Offers high-quality English courses with experienced teachers and international environment.",
            address="Portobello House, 34A South Richmond St, Dublin 2",
            phone="+353 1 478 2845",
            email="enquiries@atlaslanguageschool.com",
            website="https://atlaslanguageschool.com",
            image_url="https://images.unsplash.com/photo-1580582932707-520aed937b7b?w=800&q=80",
            rating=4.8,
            reviews_count=342,
            accreditation=["ACELS", "QQI", "MEI"],
            facilities=["Wi-Fi", "Biblioteca", "Sala de estudos", "Cafeteria", "Terraço"],
            status="approved"
        ),
        School(
            id="school-2",
            name="ISI Dublin – International School of English",
            description="Escola internacional de inglês localizada no centro de Dublin, oferecendo programas para todos os níveis.",
            description_en="International English school located in Dublin city center, offering programs for all levels.",
            address="4 Meetinghouse Lane, Dublin 2",
            phone="+353 1 679 2777",
            email="info@isi-ireland.ie",
            website="https://www.studyinireland.ie",
            image_url="https://images.unsplash.com/photo-1562774053-701939374585?w=800&q=80",
            rating=4.7,
            reviews_count=286,
            accreditation=["ACELS", "QQI"],
            facilities=["Wi-Fi", "Computadores", "Área social", "Aulas online"],
            status="approved"
        ),
        School(
            id="school-3",
            name="Irish College of English",
            description="Escola familiar em Malahide, conhecida pela qualidade do ensino e ambiente acolhedor para estudantes internacionais.",
            description_en="Family-run school in Malahide, known for teaching quality and welcoming environment for international students.",
            address="6 Church Rd, Malahide, Co. Dublin K36 KF21",
            phone="+353 1 845 3744",
            email="info@iceireland.com",
            website="https://www.iceireland.com",
            image_url="https://images.unsplash.com/photo-1497366216548-37526070297c?w=800&q=80",
            rating=4.9,
            reviews_count=198,
            accreditation=["ACELS", "QQI", "MEI"],
            facilities=["Wi-Fi", "Jardim", "Sala de estudos", "Atividades sociais"],
            status="approved"
        ),
        School(
            id="school-4",
            name="Centre of English Studies (CES)",
            description="Uma das escolas mais tradicionais de Dublin, oferecendo cursos de inglês desde 1979 com excelência acadêmica.",
            description_en="One of Dublin's most traditional schools, offering English courses since 1979 with academic excellence.",
            address="31 Dame Street, Dublin 2",
            phone="+353 1 671 4233",
            email="info@ces-schools.com",
            website="https://www.ces-schools.com",
            image_url="https://images.unsplash.com/photo-1541339907198-e08756dedf3f?w=800&q=80",
            rating=4.8,
            reviews_count=456,
            accreditation=["ACELS", "QQI", "EAQUALS"],
            facilities=["Wi-Fi", "Biblioteca", "Laboratório", "Cafeteria"],
            status="approved"
        ),
        School(
            id="school-5",
            name="EC English Dublin",
            description="Parte da rede internacional EC, oferece metodologia moderna e instalações de primeira linha em Rathmines.",
            description_en="Part of the international EC network, offers modern methodology and first-class facilities in Rathmines.",
            address="La Touche House, Rathmines, Dublin 6",
            phone="+353 1 905 1900",
            email="dublin@ecenglish.com",
            website="https://www.ecenglish.com",
            image_url="https://images.unsplash.com/photo-1523050854058-8df90110c9f1?w=800&q=80",
            rating=4.7,
            reviews_count=312,
            accreditation=["ACELS", "QQI", "British Council"],
            facilities=["Wi-Fi", "Lounge", "Computadores", "Biblioteca digital"],
            status="approved"
        ),
        School(
            id="school-6",
            name="Kaplan International Languages Dublin",
            description="Escola global com décadas de experiência, localizada no histórico Temple Bar com programas certificados.",
            description_en="Global school with decades of experience, located in historic Temple Bar with certified programs.",
            address="The Presbytery Building, Exchange St Lower, Temple Bar, Dublin",
            phone="+353 1 672 7122",
            email="dublin@kaplan.com",
            website="https://www.kaplaninternational.com",
            image_url="https://images.unsplash.com/photo-1606761568499-6d2451b23c66?w=800&q=80",
            rating=4.6,
            reviews_count=389,
            accreditation=["ACELS", "QQI", "ACCET"],
            facilities=["Wi-Fi", "Sala multimídia", "Área de convivência", "Jardim"],
            status="approved"
        ),
        School(
            id="school-7",
            name="Apollo Language Centre",
            description="Escola boutique com turmas pequenas e atenção personalizada para cada estudante.",
            description_en="Boutique school with small classes and personalized attention for each student.",
            address="5 Lad Lane, Dublin 2",
            phone="+353 1 906 0860",
            email="info@apollolanguagecentre.com",
            website="https://apollolanguagecentre.com",
            image_url="https://images.unsplash.com/photo-1517486808906-6ca8b3f04846?w=800&q=80",
            rating=4.8,
            reviews_count=167,
            accreditation=["ACELS", "QQI"],
            facilities=["Wi-Fi", "Cozinha", "Sala de estar", "Biblioteca"],
            status="approved"
        ),
        School(
            id="school-8",
            name="Babel Academy of English",
            description="Escola moderna em Eden Quay com vista para o Rio Liffey e programas flexíveis.",
            description_en="Modern school in Eden Quay with River Liffey views and flexible programs.",
            address="4–6 Eden Quay, Dublin 1",
            phone="+353 1 547 7665",
            email="info@babelacademy.ie",
            website="https://babelacademy.ie",
            image_url="https://images.unsplash.com/photo-1509062522246-3755977927d7?w=800&q=80",
            rating=4.5,
            reviews_count=234,
            accreditation=["ACELS", "QQI"],
            facilities=["Wi-Fi", "Terraço", "Computadores", "Área social"],
            status="approved"
        ),
        School(
            id="school-9",
            name="SEDA College",
            description="Uma das maiores escolas de Dublin, popular entre estudantes brasileiros com excelente estrutura.",
            description_en="One of Dublin's largest schools, popular among Brazilian students with excellent facilities.",
            address="64 Dame St, Dublin 2",
            phone="+353 1 446 3377",
            email="info@sedacollege.ie",
            website="https://sedacollege.ie",
            image_url="https://images.unsplash.com/photo-1524178232363-1fb2b075b655?w=800&q=80",
            rating=4.6,
            reviews_count=567,
            accreditation=["ACELS", "QQI", "MEI"],
            facilities=["Wi-Fi", "Biblioteca", "Cafeteria", "Sala de jogos", "Eventos"],
            status="approved"
        ),
        School(
            id="school-10",
            name="ULearn English School",
            description="Escola dinâmica em Capel Street com metodologia interativa e ambiente multicultural.",
            description_en="Dynamic school in Capel Street with interactive methodology and multicultural environment.",
            address="144 Capel St, Dublin 1",
            phone="+353 1 873 3838",
            email="info@ulearn.ie",
            website="https://ulearn.ie",
            image_url="https://images.unsplash.com/photo-1577896851231-70ef18881754?w=800&q=80",
            rating=4.5,
            reviews_count=278,
            accreditation=["ACELS", "QQI"],
            facilities=["Wi-Fi", "Computadores", "Cozinha", "Área social"],
            status="approved"
        ),
        School(
            id="school-11",
            name="Everest Language School",
            description="Localização privilegiada em Westmoreland Street, no coração de Dublin com fácil acesso.",
            description_en="Prime location on Westmoreland Street, in the heart of Dublin with easy access.",
            address="15 Westmoreland St, Dublin 2",
            phone="+353 1 679 4800",
            email="info@everestlanguageschool.com",
            website="https://everestlanguageschool.com",
            image_url="https://images.unsplash.com/photo-1571260899304-425eee4c7efc?w=800&q=80",
            rating=4.4,
            reviews_count=189,
            accreditation=["ACELS", "QQI"],
            facilities=["Wi-Fi", "Biblioteca", "Sala de estudos"],
            status="approved"
        ),
        School(
            id="school-12",
            name="Erin School of English",
            description="Escola tradicional na histórica North Great George's Street com ambiente familiar.",
            description_en="Traditional school on historic North Great George's Street with family atmosphere.",
            address="North Great George's Street, Dublin 1",
            phone="+353 1 874 6975",
            email="info@erinschoolofenglish.ie",
            website="https://erinschoolofenglish.ie",
            image_url="https://images.unsplash.com/photo-1546410531-bb4caa6b424d?w=800&q=80",
            rating=4.6,
            reviews_count=156,
            accreditation=["ACELS", "QQI"],
            facilities=["Wi-Fi", "Sala de estar", "Jardim", "Biblioteca"],
            status="approved"
        ),
        School(
            id="school-13",
            name="Horner School of English",
            description="Escola boutique em Fitzwilliam Street, área nobre de Dublin com turmas reduzidas.",
            description_en="Boutique school on Fitzwilliam Street, Dublin's upscale area with small classes.",
            address="40 Fitzwilliam Street Upper, Dublin 2",
            phone="+353 1 662 2911",
            email="info@hornerschool.com",
            website="https://www.hornerschool.com",
            image_url="https://images.unsplash.com/photo-1580894732444-8ecded7900cd?w=800&q=80",
            rating=4.9,
            reviews_count=134,
            accreditation=["ACELS", "QQI", "EAQUALS"],
            facilities=["Wi-Fi", "Jardim georgiano", "Biblioteca", "Sala de estudos"],
            status="approved"
        ),
        School(
            id="school-14",
            name="ELI Schools Dublin",
            description="Escola moderna em Dame Street com tecnologia de ponta e métodos inovadores.",
            description_en="Modern school on Dame Street with cutting-edge technology and innovative methods.",
            address="19–22 Dame Street, Dublin 2",
            phone="+353 1 559 8717",
            email="hello@elischools.com",
            website="https://elischools.com",
            image_url="https://images.unsplash.com/photo-1522202176988-66273c2fd55f?w=800&q=80",
            rating=4.5,
            reviews_count=201,
            accreditation=["ACELS", "QQI"],
            facilities=["Wi-Fi", "Tablets", "Lounge", "Cafeteria"],
            status="approved"
        ),
        School(
            id="school-15",
            name="IBAT College Dublin",
            description="Escola em Temple Bar oferecendo inglês e cursos profissionalizantes com certificação.",
            description_en="School in Temple Bar offering English and professional courses with certification.",
            address="Temple Bar, Dublin 2",
            phone="+353 1 807 5055",
            email="info@ibat.ie",
            website="https://www.ibat.ie",
            image_url="https://images.unsplash.com/photo-1562774053-701939374585?w=800&q=80",
            rating=4.4,
            reviews_count=298,
            accreditation=["ACELS", "QQI", "FETAC"],
            facilities=["Wi-Fi", "Laboratório", "Biblioteca", "Área de TI"],
            status="approved"
        ),
        School(
            id="school-16",
            name="Englishour",
            description="Escola descontraída em Wellington Quay com foco em conversação e fluência.",
            description_en="Relaxed school on Wellington Quay focused on conversation and fluency.",
            address="16–19 Wellington Quay, Dublin 2",
            phone="+353 1 670 9033",
            email="info@englishour.com",
            website="https://englishour.com",
            image_url="https://images.unsplash.com/photo-1517486808906-6ca8b3f04846?w=800&q=80",
            rating=4.5,
            reviews_count=167,
            accreditation=["ACELS", "QQI"],
            facilities=["Wi-Fi", "Área social", "Cozinha", "Eventos semanais"],
            status="approved"
        ),
        School(
            id="school-17",
            name="Castleforbes College",
            description="Escola em Dublin 1 com programas flexíveis e preços acessíveis para estudantes.",
            description_en="School in Dublin 1 with flexible programs and affordable prices for students.",
            address="Castleforbes Rd, Dublin 1",
            phone="+353 1 254 9710",
            email="info@castleforbescollege.com",
            website="https://castleforbescollege.com",
            image_url="https://images.unsplash.com/photo-1509062522246-3755977927d7?w=800&q=80",
            rating=4.3,
            reviews_count=234,
            accreditation=["ACELS", "QQI"],
            facilities=["Wi-Fi", "Computadores", "Sala de estudos"],
            status="approved"
        ),
        School(
            id="school-18",
            name="Twin English Centres Dublin",
            description="Parte da rede Twin UK, oferece programas de qualidade com metodologia britânica.",
            description_en="Part of Twin UK network, offers quality programs with British methodology.",
            address="4 North Great George's St, Dublin 1",
            phone="+353 1 874 6123",
            email="dublin@twinuk.com",
            website="https://www.twinuk.com",
            image_url="https://images.unsplash.com/photo-1571260899304-425eee4c7efc?w=800&q=80",
            rating=4.6,
            reviews_count=189,
            accreditation=["ACELS", "QQI", "British Council"],
            facilities=["Wi-Fi", "Biblioteca", "Área de convivência"],
            status="approved"
        ),
        School(
            id="school-19",
            name="ATC Language Schools",
            description="Rede irlandesa de escolas com programas para adultos e jovens durante todo o ano.",
            description_en="Irish school network with programs for adults and young learners year-round.",
            address="Dublin city centre",
            phone="+353 1 254 5150",
            email="info@atcireland.ie",
            website="https://www.atcireland.ie",
            image_url="https://images.unsplash.com/photo-1523050854058-8df90110c9f1?w=800&q=80",
            rating=4.7,
            reviews_count=312,
            accreditation=["ACELS", "QQI", "MEI"],
            facilities=["Wi-Fi", "Campus", "Atividades", "Acomodação"],
            status="approved"
        ),
        School(
            id="school-20",
            name="DCU International Academy",
            description="Escola de inglês da Dublin City University com acesso às instalações universitárias.",
            description_en="Dublin City University's English school with access to university facilities.",
            address="Dublin City University, Glasnevin, Dublin 9",
            phone="+353 1 700 5481",
            email="english.courses@dcu.ie",
            website="https://www.english.dcu.ie",
            image_url="https://images.unsplash.com/photo-1562774053-701939374585?w=800&q=80",
            rating=4.8,
            reviews_count=267,
            accreditation=["University", "QQI", "MEI"],
            facilities=["Campus universitário", "Biblioteca", "Ginásio", "Restaurantes"],
            status="approved"
        ),
        School(
            id="school-21",
            name="Griffith Institute of Language",
            description="Instituto de idiomas do Griffith College com programas acadêmicos e preparatórios.",
            description_en="Griffith College language institute with academic and preparatory programs.",
            address="Griffith College, South Circular Rd, Dublin 8",
            phone="+353 1 415 0453",
            email="gil@gcd.ie",
            website="https://gcd.ie",
            image_url="https://images.unsplash.com/photo-1524178232363-1fb2b075b655?w=800&q=80",
            rating=4.6,
            reviews_count=178,
            accreditation=["QQI", "HETAC"],
            facilities=["Campus", "Biblioteca", "Cafeteria", "Centro esportivo"],
            status="approved"
        ),
        School(
            id="school-22",
            name="International House Dublin",
            description="Parte da rede mundial International House, padrão de qualidade internacional.",
            description_en="Part of the worldwide International House network, international quality standard.",
            address="Fitzwilliam Square, Dublin",
            phone="+353 1 676 7900",
            email="info@ihdublin.com",
            website="https://ihdublin.com",
            image_url="https://images.unsplash.com/photo-1577896851231-70ef18881754?w=800&q=80",
            rating=4.7,
            reviews_count=234,
            accreditation=["ACELS", "QQI", "IH World"],
            facilities=["Wi-Fi", "Jardim", "Biblioteca", "Sala de professores"],
            status="approved"
        ),
        School(
            id="school-23",
            name="English Path Dublin",
            description="Escola moderna com programas em Dun Laoghaire e parceria com UCD.",
            description_en="Modern school with programs in Dun Laoghaire and partnership with UCD.",
            address="Dun Laoghaire / UCD campus programmes",
            phone="+353 1 901 3737",
            email="info@englishpath.com",
            website="https://englishpath.com",
            image_url="https://images.unsplash.com/photo-1546410531-bb4caa6b424d?w=800&q=80",
            rating=4.5,
            reviews_count=145,
            accreditation=["ACELS", "QQI"],
            facilities=["Wi-Fi", "Campus UCD", "Praia próxima", "Transporte"],
            status="approved"
        ),
        School(
            id="school-24",
            name="Home Language International Dublin",
            description="Programa exclusivo de imersão total na casa de professores nativos.",
            description_en="Exclusive total immersion program staying in native teachers' homes.",
            address="Programas em casas de professores em Dublin",
            phone="+44 1273 830960",
            email="info@hli.co.uk",
            website="https://www.hli.co.uk",
            image_url="https://images.unsplash.com/photo-1580894732444-8ecded7900cd?w=800&q=80",
            rating=4.9,
            reviews_count=89,
            accreditation=["British Council", "QQI"],
            facilities=["Imersão total", "Aulas particulares", "Acomodação inclusa"],
            status="approved"
        ),
        School(
            id="school-25",
            name="Travelling Languages Dublin",
            description="Escola com foco em programas personalizados e experiências culturais.",
            description_en="School focused on personalized programs and cultural experiences.",
            address="Dublin city centre",
            phone="+353 1 443 3920",
            email="info@travellinglanguages.com",
            website="https://travellinglanguages.com",
            image_url="https://images.unsplash.com/photo-1522202176988-66273c2fd55f?w=800&q=80",
            rating=4.6,
            reviews_count=112,
            accreditation=["ACELS", "QQI"],
            facilities=["Wi-Fi", "Atividades culturais", "Tours", "Eventos"],
            status="approved"
        )
    ]
    
    for school in schools:
        await db.schools.insert_one(school.model_dump())
    
    # Seed Courses
    courses = [
        Course(
            id="course-1",
            school_id="school-1",
            name="Inglês Geral - 25 semanas",
            name_en="General English - 25 weeks",
            description="Curso completo de inglês para todos os níveis, com foco em conversação, gramática e vocabulário.",
            description_en="Complete English course for all levels, focusing on conversation, grammar and vocabulary.",
            duration_weeks=25,
            hours_per_week=15,
            level="all_levels",
            price=2950.00,
            requirements=["Passaporte válido", "Seguro saúde"],
            includes=["Material didático", "Certificado", "Acesso à biblioteca"],
            start_dates=["2025-01-13", "2025-02-10", "2025-03-10", "2025-04-07"],
            available_spots=15
        ),
        Course(
            id="course-2",
            school_id="school-1",
            name="Preparatório IELTS - 12 semanas",
            name_en="IELTS Preparation - 12 weeks",
            description="Curso focado na preparação para o exame IELTS com simulados e técnicas de prova.",
            description_en="Course focused on IELTS exam preparation with mock tests and exam techniques.",
            duration_weeks=12,
            hours_per_week=20,
            level="intermediate",
            price=1980.00,
            requirements=["Nível intermediário de inglês", "Passaporte válido"],
            includes=["Material IELTS", "Simulados", "Certificado"],
            start_dates=["2025-01-20", "2025-03-17", "2025-05-12"],
            available_spots=12
        ),
        Course(
            id="course-3",
            school_id="school-2",
            name="Inglês Intensivo - 25 semanas",
            name_en="Intensive English - 25 weeks",
            description="Programa intensivo com aulas pela manhã e workshops à tarde. Ideal para quem quer progredir rapidamente.",
            description_en="Intensive program with morning classes and afternoon workshops. Ideal for rapid progress.",
            duration_weeks=25,
            hours_per_week=26,
            level="all_levels",
            price=4200.00,
            requirements=["Passaporte válido", "Seguro saúde", "Visto de estudante"],
            includes=["Material didático premium", "Atividades sociais", "Certificado ACELS"],
            start_dates=["2025-01-06", "2025-02-03", "2025-03-03"],
            available_spots=10
        ),
        Course(
            id="course-4",
            school_id="school-2",
            name="Business English - 8 semanas",
            name_en="Business English - 8 weeks",
            description="Inglês para negócios com foco em apresentações, negociações e comunicação corporativa.",
            description_en="Business English focusing on presentations, negotiations and corporate communication.",
            duration_weeks=8,
            hours_per_week=20,
            level="advanced",
            price=1650.00,
            requirements=["Nível avançado de inglês"],
            includes=["Material especializado", "Networking events", "Certificado"],
            start_dates=["2025-02-17", "2025-04-14", "2025-06-09"],
            available_spots=8
        ),
        Course(
            id="course-5",
            school_id="school-3",
            name="Inglês + Trabalho - 25 semanas",
            name_en="English + Work - 25 weeks",
            description="Combine aulas de inglês com a possibilidade de trabalhar meio período na Irlanda.",
            description_en="Combine English classes with the possibility of part-time work in Ireland.",
            duration_weeks=25,
            hours_per_week=15,
            level="all_levels",
            price=2750.00,
            requirements=["Passaporte válido", "Seguro saúde", "Comprovante financeiro"],
            includes=["Orientação para trabalho", "CV workshop", "Material didático"],
            start_dates=["2025-01-13", "2025-02-10", "2025-03-10"],
            available_spots=20
        ),
        Course(
            id="course-6",
            school_id="school-4",
            name="Inglês Geral Manhã - 25 semanas",
            name_en="General English Morning - 25 weeks",
            description="Aulas no período da manhã, perfeito para quem quer trabalhar à tarde.",
            description_en="Morning classes, perfect for those who want to work in the afternoon.",
            duration_weeks=25,
            hours_per_week=15,
            level="all_levels",
            price=2500.00,
            requirements=["Passaporte válido"],
            includes=["Material didático", "Wi-Fi", "Certificado"],
            start_dates=["2025-01-20", "2025-02-17", "2025-03-17"],
            available_spots=18
        )
    ]
    
    for course in courses:
        await db.courses.insert_one(course.model_dump())
    
    # Seed Bus Routes
    bus_routes = [
        BusRoute(
            id="route-1",
            route_number="16",
            name="Dublin Airport - Centro",
            name_en="Dublin Airport - City Centre",
            from_location="Dublin Airport",
            to_location="O'Connell Street",
            frequency_minutes=15,
            first_bus="05:00",
            last_bus="00:30",
            fare=3.80,
            zones=["Airport", "City Centre"],
            popular_stops=["Airport Terminal 1", "Drumcondra", "Parnell Square", "O'Connell Street"]
        ),
        BusRoute(
            id="route-2",
            route_number="46A",
            name="Phoenix Park - Dun Laoghaire",
            name_en="Phoenix Park - Dun Laoghaire",
            from_location="Phoenix Park",
            to_location="Dun Laoghaire",
            frequency_minutes=10,
            first_bus="06:00",
            last_bus="23:30",
            fare=2.60,
            zones=["West Dublin", "South Dublin"],
            popular_stops=["Phoenix Park", "Heuston Station", "Dame Street", "Donnybrook", "Dun Laoghaire"]
        ),
        BusRoute(
            id="route-3",
            route_number="LUAS Green",
            name="Broombridge - Bride's Glen",
            name_en="Broombridge - Bride's Glen",
            from_location="Broombridge",
            to_location="Bride's Glen",
            frequency_minutes=5,
            first_bus="05:30",
            last_bus="00:30",
            fare=2.50,
            zones=["North Dublin", "City Centre", "South Dublin"],
            popular_stops=["Parnell", "O'Connell GPO", "Stephen's Green", "Ranelagh", "Dundrum"]
        ),
        BusRoute(
            id="route-4",
            route_number="DART",
            name="Howth - Greystones",
            name_en="Howth - Greystones",
            from_location="Howth",
            to_location="Greystones",
            frequency_minutes=10,
            first_bus="06:00",
            last_bus="23:45",
            fare=3.50,
            zones=["North Coast", "City", "South Coast"],
            popular_stops=["Howth", "Connolly", "Pearse", "Dun Laoghaire", "Bray", "Greystones"]
        ),
        BusRoute(
            id="route-5",
            route_number="747",
            name="Airport Express - Heuston",
            name_en="Airport Express - Heuston",
            from_location="Dublin Airport",
            to_location="Heuston Station",
            frequency_minutes=20,
            first_bus="05:45",
            last_bus="00:00",
            fare=8.00,
            zones=["Airport", "City Centre"],
            popular_stops=["Airport", "O'Connell Street", "Aston Quay", "Heuston Station"]
        )
    ]
    
    for route in bus_routes:
        await db.bus_routes.insert_one(route.model_dump())
    
    # Seed Government Agencies
    agencies = [
        GovernmentAgency(
            id="agency-1",
            name="INIS - Serviço de Imigração",
            name_en="INIS - Immigration Service",
            description="Responsável por vistos, permissões de residência e registro de imigrantes",
            description_en="Responsible for visas, residence permits and immigrant registration",
            category="immigration",
            address="Burgh Quay, Dublin 2",
            phone="+353 1 616 7700",
            email="immigrationsupport@justice.ie",
            website="https://www.irishimmigration.ie",
            opening_hours="Mon-Fri: 08:00 - 16:00",
            services=["IRP/GNIB Registration", "Visa Applications", "Stamp Changes"]
        ),
        GovernmentAgency(
            id="agency-2",
            name="DSP - Departamento de Proteção Social",
            name_en="DSP - Department of Social Protection",
            description="Emissão do PPS Number e serviços de proteção social",
            description_en="PPS Number issuance and social protection services",
            category="public_services",
            address="Various locations in Dublin",
            phone="+353 1 704 3000",
            email="info@welfare.ie",
            website="https://www.gov.ie/dsp",
            opening_hours="Mon-Fri: 09:00 - 17:00",
            services=["PPS Number", "Social Welfare", "JobPath"]
        ),
        GovernmentAgency(
            id="agency-3",
            name="Revenue - Receita Federal Irlandesa",
            name_en="Revenue - Irish Tax Authority",
            description="Questões fiscais, registro de emprego e impostos",
            description_en="Tax matters, employment registration and taxes",
            category="public_services",
            address="Castle House, South Great George's Street, Dublin 2",
            phone="+353 1 738 3660",
            email="taxpayerinfo@revenue.ie",
            website="https://www.revenue.ie",
            opening_hours="Mon-Fri: 09:30 - 16:30",
            services=["Tax Registration", "Tax Returns", "Emergency Tax Refunds"]
        ),
        GovernmentAgency(
            id="agency-4",
            name="HSE - Serviço de Saúde",
            name_en="HSE - Health Service Executive",
            description="Serviços de saúde pública, registro médico e medical cards",
            description_en="Public health services, medical registration and medical cards",
            category="public_services",
            address="Various Health Centres",
            phone="+353 1 240 8000",
            email="info@hse.ie",
            website="https://www.hse.ie",
            opening_hours="Mon-Fri: 09:00 - 17:00",
            services=["Medical Card", "GP Services", "Emergency Services"]
        ),
        GovernmentAgency(
            id="agency-5",
            name="Citizens Information",
            name_en="Citizens Information",
            description="Informações gratuitas sobre direitos e serviços na Irlanda",
            description_en="Free information about rights and services in Ireland",
            category="public_services",
            address="Various locations",
            phone="0818 07 4000",
            email="via website",
            website="https://www.citizensinformation.ie",
            opening_hours="Mon-Fri: 09:00 - 17:00",
            services=["Rights Information", "Social Services Info", "Employment Rights"]
        )
    ]
    
    for agency in agencies:
        await db.agencies.insert_one(agency.model_dump())
    
    return {
        "message": "Database seeded successfully",
        "admin_email": "admin@dublinstudy.com",
        "admin_password": "admin123",
        "schools": len(schools),
        "courses": len(courses),
        "bus_routes": len(bus_routes),
        "agencies": len(agencies)
    }

# ============== ROOT ==============

@api_router.get("/")
async def root():
    return {"message": "Dublin Study API", "version": "2.0.0"}

# ============== DIGITAL PASSPORT ROUTES ==============

class DigitalPassport(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    enrollment_id: str
    user_id: str
    user_name: str
    user_email: str
    user_nationality: str = "Brasil"
    user_avatar: Optional[str] = None
    school_id: str
    school_name: str
    school_address: str
    school_phone: str
    school_email: str
    school_website: str = ""
    course_id: str
    course_name: str
    course_start_date: str
    course_end_date: str
    course_duration_weeks: int
    course_schedule: str = "Segunda a Sexta, 9:00 - 13:00"
    enrollment_number: str  # Número de matrícula único
    status: str = "active"  # active, inactive, expired
    issued_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    valid_until: str = ""
    qr_code_token: str = Field(default_factory=lambda: str(uuid.uuid4()))

class PassportUpdateNationality(BaseModel):
    nationality: str

@api_router.get("/passport/my")
async def get_my_passport(user: dict = Depends(get_current_user)):
    """Get current user's digital passport"""
    passport = await db.digital_passports.find_one(
        {"user_id": user["id"], "status": "active"},
        {"_id": 0}
    )
    if not passport:
        raise HTTPException(status_code=404, detail="Passaporte digital não encontrado. Complete o pagamento do curso para gerar seu passaporte.")
    return passport

@api_router.get("/passport/all")
async def get_all_my_passports(user: dict = Depends(get_current_user)):
    """Get all passports for current user"""
    passports = await db.digital_passports.find(
        {"user_id": user["id"]},
        {"_id": 0}
    ).to_list(100)
    return passports

@api_router.get("/passport/verify/{token}")
async def verify_passport(token: str):
    """Public endpoint to verify passport via QR code"""
    passport = await db.digital_passports.find_one(
        {"qr_code_token": token},
        {"_id": 0}
    )
    if not passport:
        raise HTTPException(status_code=404, detail="Passaporte não encontrado")
    
    # Return limited public info for verification
    return {
        "valid": True,
        "status": passport.get("status"),
        "student_name": passport.get("user_name"),
        "student_nationality": passport.get("user_nationality"),
        "enrollment_number": passport.get("enrollment_number"),
        "school_name": passport.get("school_name"),
        "course_name": passport.get("course_name"),
        "course_start_date": passport.get("course_start_date"),
        "course_end_date": passport.get("course_end_date"),
        "issued_at": passport.get("issued_at"),
        "valid_until": passport.get("valid_until")
    }

@api_router.get("/passport/view/{token}")
async def view_passport(token: str):
    """Public endpoint to view full passport (for QR scan)"""
    passport = await db.digital_passports.find_one(
        {"qr_code_token": token},
        {"_id": 0}
    )
    if not passport:
        raise HTTPException(status_code=404, detail="Passaporte não encontrado")
    
    # Return full passport data for display
    return {
        "id": passport.get("id"),
        "status": passport.get("status"),
        "user_name": passport.get("user_name"),
        "user_email": passport.get("user_email"),
        "user_nationality": passport.get("user_nationality"),
        "user_avatar": passport.get("user_avatar"),
        "enrollment_number": passport.get("enrollment_number"),
        "school_name": passport.get("school_name"),
        "school_address": passport.get("school_address"),
        "school_phone": passport.get("school_phone"),
        "school_email": passport.get("school_email"),
        "course_name": passport.get("course_name"),
        "course_start_date": passport.get("course_start_date"),
        "course_end_date": passport.get("course_end_date"),
        "course_duration_weeks": passport.get("course_duration_weeks"),
        "course_schedule": passport.get("course_schedule"),
        "issued_at": passport.get("issued_at"),
        "valid_until": passport.get("valid_until")
    }

class SimulatePaymentRequest(BaseModel):
    email: str
    name: str
    course_id: str = "course-1"
    start_date: str = "2026-04-01"

@api_router.post("/passport/simulate-payment")
async def simulate_payment_flow(request: SimulatePaymentRequest):
    """Simulate complete payment flow to test passport generation and email"""
    
    # 1. Create or get user
    existing_user = await db.users.find_one({"email": request.email})
    if existing_user:
        user_id = existing_user["id"]
        user = existing_user
    else:
        user_id = str(uuid.uuid4())
        user = {
            "id": user_id,
            "email": request.email,
            "name": request.name,
            "password": "simulated",
            "role": "student",
            "nationality": "Brasil",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.users.insert_one(user)
    
    # 2. Get course and school
    course = await db.courses.find_one({"id": request.course_id}, {"_id": 0})
    if not course:
        raise HTTPException(status_code=404, detail="Curso não encontrado")
    
    school = await db.schools.find_one({"id": course["school_id"]}, {"_id": 0})
    if not school:
        raise HTTPException(status_code=404, detail="Escola não encontrada")
    
    # 3. Create enrollment
    enrollment_id = str(uuid.uuid4())
    enrollment = {
        "id": enrollment_id,
        "user_id": user_id,
        "user_email": request.email,
        "user_name": request.name,
        "school_id": school["id"],
        "school_name": school["name"],
        "course_id": course["id"],
        "course_name": course["name"],
        "start_date": request.start_date,
        "status": "paid",  # Simulating paid status
        "paid_at": datetime.now(timezone.utc).isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.enrollments.insert_one(enrollment)
    
    logger.info(f"💳 [SIMULATE] Payment confirmed for {request.email}")
    
    # 4. Generate Digital Passport
    passport = await generate_digital_passport(enrollment_id)
    
    if not passport:
        raise HTTPException(status_code=500, detail="Erro ao gerar passaporte")
    
    # 5. Get email log
    email_log = await db.email_logs.find_one(
        {"enrollment_number": passport["enrollment_number"]},
        {"_id": 0}
    )
    
    return {
        "success": True,
        "message": "Pagamento simulado com sucesso!",
        "enrollment": {
            "id": enrollment_id,
            "status": "paid"
        },
        "passport": {
            "enrollment_number": passport["enrollment_number"],
            "view_url": f"https://student-passport-hub.preview.emergentagent.com/passport/view/{passport['qr_code_token']}"
        },
        "email_sent_to": request.email,
        "email_log": email_log
    }

@api_router.put("/passport/nationality")
async def update_passport_nationality(data: PassportUpdateNationality, user: dict = Depends(get_current_user)):
    """Update nationality on passport"""
    result = await db.digital_passports.update_many(
        {"user_id": user["id"]},
        {"$set": {"user_nationality": data.nationality}}
    )
    return {"message": "Nacionalidade atualizada", "updated": result.modified_count}

@api_router.get("/passport/documents/{enrollment_id}")
async def get_passport_documents(enrollment_id: str, user: dict = Depends(get_current_user)):
    """Get documents associated with enrollment"""
    enrollment = await db.enrollments.find_one(
        {"id": enrollment_id, "user_id": user["id"]},
        {"_id": 0}
    )
    if not enrollment:
        raise HTTPException(status_code=404, detail="Matrícula não encontrada")
    
    documents = [
        {
            "id": "enrollment_proof",
            "name": "Comprovante de Matrícula",
            "name_en": "Enrollment Proof",
            "type": "auto_generated",
            "available": enrollment.get("status") == "paid"
        },
        {
            "id": "school_letter",
            "name": "Carta da Escola",
            "name_en": "School Letter",
            "type": "school_upload",
            "available": enrollment.get("letter_sent", False),
            "url": enrollment.get("letter_url")
        },
        {
            "id": "course_info",
            "name": "Informações do Curso",
            "name_en": "Course Information",
            "type": "auto_generated",
            "available": True
        },
        {
            "id": "digital_passport",
            "name": "Passaporte Digital",
            "name_en": "Digital Passport",
            "type": "auto_generated",
            "available": enrollment.get("status") == "paid"
        }
    ]
    return documents

async def generate_digital_passport(enrollment_id: str):
    """Generate digital passport after payment confirmation"""
    enrollment = await db.enrollments.find_one({"id": enrollment_id}, {"_id": 0})
    if not enrollment:
        return None
    
    # Check if passport already exists
    existing = await db.digital_passports.find_one({"enrollment_id": enrollment_id})
    if existing:
        return existing
    
    # Get user data
    user = await db.users.find_one({"id": enrollment["user_id"]}, {"_id": 0, "password": 0})
    
    # Get school data
    school = await db.schools.find_one({"id": enrollment["school_id"]}, {"_id": 0})
    
    # Get course data
    course = await db.courses.find_one({"id": enrollment["course_id"]}, {"_id": 0})
    
    if not user or not school or not course:
        return None
    
    # Calculate end date based on duration
    from datetime import datetime
    start_date = datetime.fromisoformat(enrollment["start_date"].replace("Z", "+00:00"))
    end_date = start_date + timedelta(weeks=course.get("duration_weeks", 12))
    valid_until = end_date + timedelta(days=30)  # Valid 30 days after course ends
    
    # Generate unique enrollment number
    count = await db.digital_passports.count_documents({})
    enrollment_number = f"STUFF-{datetime.now().year}-{str(count + 1).zfill(5)}"
    
    passport = DigitalPassport(
        enrollment_id=enrollment_id,
        user_id=user["id"],
        user_name=user["name"],
        user_email=user["email"],
        user_avatar=user.get("avatar"),
        school_id=school["id"],
        school_name=school["name"],
        school_address=school.get("address", "Dublin, Ireland"),
        school_phone=school.get("phone", ""),
        school_email=school.get("email", ""),
        school_website=school.get("website", ""),
        course_id=course["id"],
        course_name=course["name"],
        course_start_date=enrollment["start_date"],
        course_end_date=end_date.isoformat(),
        course_duration_weeks=course.get("duration_weeks", 12),
        course_schedule=f"{course.get('hours_per_week', 20)}h/semana",
        enrollment_number=enrollment_number,
        valid_until=valid_until.isoformat()
    )
    
    await db.digital_passports.insert_one(passport.model_dump())
    
    logger.info(f"🎫 Digital Passport generated for {user['name']} - {enrollment_number}")
    
    # Send email notification with passport link
    await send_passport_email(user, passport.model_dump(), school, course)
    
    return passport.model_dump()

async def send_passport_email(user: dict, passport: dict, school: dict, course: dict):
    """Send email with digital passport link (MOCK - logs to console)"""
    passport_url = f"https://student-passport-hub.preview.emergentagent.com/passport/view/{passport['qr_code_token']}"
    
    email_html = f"""
    ╔══════════════════════════════════════════════════════════════════════╗
    ║                    📧 EMAIL NOTIFICATION (MOCK)                       ║
    ╠══════════════════════════════════════════════════════════════════════╣
    ║ To: {user['email']:<58} ║
    ║ Subject: Seu Passaporte Digital STUFF está pronto! 🎫                ║
    ╠══════════════════════════════════════════════════════════════════════╣
    ║                                                                      ║
    ║  Olá {user['name'][:50]:<50} ║
    ║                                                                      ║
    ║  Parabéns! Seu pagamento foi confirmado e seu Passaporte Digital     ║
    ║  de Intercambista está pronto!                                       ║
    ║                                                                      ║
    ║  ═══════════════════════════════════════════════════════════════     ║
    ║  📋 DETALHES DA MATRÍCULA:                                           ║
    ║  ═══════════════════════════════════════════════════════════════     ║
    ║  • Número: {passport['enrollment_number']:<48} ║
    ║  • Escola: {school['name'][:48]:<48} ║
    ║  • Curso: {course['name'][:49]:<49} ║
    ║  • Início: {passport['course_start_date'][:10]:<48} ║
    ║  • Duração: {passport['course_duration_weeks']} semanas{' ':<39} ║
    ║                                                                      ║
    ║  ═══════════════════════════════════════════════════════════════     ║
    ║  🎫 SEU PASSAPORTE DIGITAL:                                          ║
    ║  ═══════════════════════════════════════════════════════════════     ║
    ║                                                                      ║
    ║  Clique no link abaixo para visualizar seu passaporte:               ║
    ║                                                                      ║
    ║  🔗 {passport_url:<58} ║
    ║                                                                      ║
    ║  Este passaporte contém um QR Code que pode ser escaneado para       ║
    ║  verificar sua matrícula a qualquer momento.                         ║
    ║                                                                      ║
    ║  ═══════════════════════════════════════════════════════════════     ║
    ║                                                                      ║
    ║  A carta da escola será enviada separadamente em até 5 dias úteis.   ║
    ║                                                                      ║
    ║  Boa sorte no seu intercâmbio! 🍀                                    ║
    ║  Equipe STUFF Intercâmbio                                            ║
    ║                                                                      ║
    ╚══════════════════════════════════════════════════════════════════════╝
    """
    
    logger.info(email_html)
    logger.info(f"")
    logger.info(f"📧 [MOCK EMAIL] Would send to: {user['email']}")
    logger.info(f"📧 [MOCK EMAIL] Passport URL: {passport_url}")
    logger.info(f"")
    
    # Store email log in database for testing
    email_log = {
        "id": str(uuid.uuid4()),
        "type": "passport_notification",
        "to": user["email"],
        "subject": "Seu Passaporte Digital STUFF está pronto!",
        "passport_url": passport_url,
        "enrollment_number": passport["enrollment_number"],
        "sent_at": datetime.now(timezone.utc).isoformat(),
        "status": "mock_sent"
    }
    await db.email_logs.insert_one(email_log)
    
    # Send push notification for passport ready
    await send_push_notification_for_event(user["id"], "passport_ready", {"passport_url": passport_url})
    
    return email_log

# ============== CONTRACT & SIGNATURE SYSTEM ==============

class ContractData(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    enrollment_id: str
    user_id: str
    user_name: str
    user_email: str
    school_id: str
    school_name: str
    course_id: str
    course_name: str
    course_price: float
    platform_fee: float  # 20%
    school_amount: float  # 80%
    start_date: str
    duration_weeks: int
    contract_text: str
    status: str = "pending"  # pending, signed, expired
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    signed_at: Optional[str] = None
    signature_data: Optional[str] = None  # Base64 signature image or "checkbox"
    signer_ip: Optional[str] = None
    signer_user_agent: Optional[str] = None

class SignContractRequest(BaseModel):
    signature_type: str = "checkbox"  # checkbox, drawn
    signature_data: Optional[str] = None  # Base64 if drawn
    agreed_terms: bool = True

@api_router.get("/contract/{enrollment_id}")
async def get_contract(enrollment_id: str, user: dict = Depends(get_current_user)):
    """Get contract for enrollment"""
    contract = await db.contracts.find_one(
        {"enrollment_id": enrollment_id, "user_id": user["id"]},
        {"_id": 0}
    )
    if not contract:
        # Generate contract if doesn't exist
        enrollment = await db.enrollments.find_one({"id": enrollment_id}, {"_id": 0})
        if not enrollment:
            raise HTTPException(status_code=404, detail="Matrícula não encontrada")
        
        if enrollment["user_id"] != user["id"]:
            raise HTTPException(status_code=403, detail="Acesso negado")
        
        school = await db.schools.find_one({"id": enrollment["school_id"]}, {"_id": 0})
        course = await db.courses.find_one({"id": enrollment["course_id"]}, {"_id": 0})
        
        if not school or not course:
            raise HTTPException(status_code=404, detail="Dados não encontrados")
        
        # Calculate split
        total_price = course.get("price", 0)
        platform_fee = total_price * 0.20  # 20% STUFF
        school_amount = total_price * 0.80  # 80% School
        
        # Generate contract text
        contract_text = generate_contract_text(
            user_name=user["name"],
            school_name=school["name"],
            course_name=course["name"],
            start_date=enrollment["start_date"],
            duration_weeks=course.get("duration_weeks", 25),
            total_price=total_price,
            platform_fee=platform_fee,
            school_amount=school_amount
        )
        
        contract = ContractData(
            enrollment_id=enrollment_id,
            user_id=user["id"],
            user_name=user["name"],
            user_email=user["email"],
            school_id=school["id"],
            school_name=school["name"],
            course_id=course["id"],
            course_name=course["name"],
            course_price=total_price,
            platform_fee=platform_fee,
            school_amount=school_amount,
            start_date=enrollment["start_date"],
            duration_weeks=course.get("duration_weeks", 25),
            contract_text=contract_text
        )
        
        await db.contracts.insert_one(contract.model_dump())
        contract = contract.model_dump()
    
    return contract

def generate_contract_text(user_name: str, school_name: str, course_name: str, 
                          start_date: str, duration_weeks: int, total_price: float,
                          platform_fee: float, school_amount: float) -> str:
    """Generate contract text"""
    return f"""
CONTRATO DE PRESTAÇÃO DE SERVIÇOS EDUCACIONAIS

CONTRATANTE (ALUNO):
Nome: {user_name}

CONTRATADA (ESCOLA):
{school_name}
Dublin, Ireland

INTERMEDIÁRIO:
STUFF Intercâmbio - Plataforma de Intercâmbio Educacional

1. OBJETO DO CONTRATO
O presente contrato tem por objeto a prestação de serviços educacionais consistentes no curso de idiomas "{course_name}", com duração de {duration_weeks} semanas, com início previsto para {start_date[:10]}.

2. VALOR E FORMA DE PAGAMENTO
2.1. O valor total do curso é de €{total_price:,.2f} (euros).
2.2. A distribuição do pagamento será:
    - Taxa de serviço STUFF Intercâmbio: €{platform_fee:,.2f} (20%)
    - Valor repassado à escola: €{school_amount:,.2f} (80%)

3. OBRIGAÇÕES DA ESCOLA
3.1. Fornecer as aulas conforme grade horária estabelecida;
3.2. Emitir carta de matrícula para fins de visto;
3.3. Disponibilizar material didático necessário;
3.4. Emitir certificado de conclusão ao término do curso.

4. OBRIGAÇÕES DO ALUNO
4.1. Comparecer às aulas regularmente;
4.2. Cumprir as normas internas da escola;
4.3. Manter documentação de imigração em dia;
4.4. Respeitar as leis irlandesas durante a estadia.

5. CANCELAMENTO E REEMBOLSO
5.1. Cancelamento até 30 dias antes do início: reembolso de 80% do valor;
5.2. Cancelamento entre 15-30 dias: reembolso de 50%;
5.3. Cancelamento com menos de 15 dias: sem reembolso;
5.4. A taxa de serviço STUFF não é reembolsável.

6. DOCUMENTAÇÃO
6.1. Após assinatura deste contrato, o aluno receberá:
    - Passaporte Digital do Estudante Internacional
    - Carta oficial da escola para visto
    - Comprovante de matrícula

7. FORO
Fica eleito o foro de Dublin, Irlanda, para dirimir quaisquer dúvidas oriundas do presente contrato.

Data de geração: {datetime.now().strftime('%d/%m/%Y às %H:%M')}
"""

@api_router.post("/contract/{enrollment_id}/sign")
async def sign_contract(
    enrollment_id: str, 
    request: SignContractRequest,
    req: Request,
    user: dict = Depends(get_current_user)
):
    """Sign contract digitally"""
    contract = await db.contracts.find_one(
        {"enrollment_id": enrollment_id, "user_id": user["id"]},
        {"_id": 0}
    )
    
    if not contract:
        raise HTTPException(status_code=404, detail="Contrato não encontrado")
    
    if contract["status"] == "signed":
        raise HTTPException(status_code=400, detail="Contrato já foi assinado")
    
    if not request.agreed_terms:
        raise HTTPException(status_code=400, detail="Você precisa aceitar os termos")
    
    # Get client info for legal record
    client_ip = req.client.host if req.client else "unknown"
    user_agent = req.headers.get("user-agent", "unknown")
    
    # Update contract
    signed_at = datetime.now(timezone.utc).isoformat()
    await db.contracts.update_one(
        {"id": contract["id"]},
        {"$set": {
            "status": "signed",
            "signed_at": signed_at,
            "signature_type": request.signature_type,
            "signature_data": request.signature_data,
            "signer_ip": client_ip,
            "signer_user_agent": user_agent
        }}
    )
    
    # Update enrollment status
    await db.enrollments.update_one(
        {"id": enrollment_id},
        {"$set": {"contract_signed": True, "contract_signed_at": signed_at}}
    )
    
    logger.info(f"✍️ Contract signed by {user['name']} for enrollment {enrollment_id}")
    logger.info(f"   IP: {client_ip}")
    logger.info(f"   Time: {signed_at}")
    
    # Send signature confirmation email
    await send_contract_signed_email(user, contract, signed_at)
    
    # Send push notification
    await send_push_notification_for_event(user["id"], "contract_signed")
    
    # Generate passport if payment was made
    enrollment = await db.enrollments.find_one({"id": enrollment_id}, {"_id": 0})
    if enrollment and enrollment.get("status") == "paid":
        passport = await generate_digital_passport(enrollment_id)
        if passport:
            logger.info(f"🎫 Passport generated after contract signature")
    
    return {
        "success": True,
        "message": "Contrato assinado com sucesso!",
        "signed_at": signed_at,
        "next_step": "passport" if enrollment.get("status") == "paid" else "payment"
    }

async def send_contract_signed_email(user: dict, contract: dict, signed_at: str):
    """Send contract signed confirmation email (MOCK)"""
    
    email_content = f"""
    ╔══════════════════════════════════════════════════════════════════════╗
    ║                    📧 EMAIL NOTIFICATION (MOCK)                       ║
    ╠══════════════════════════════════════════════════════════════════════╣
    ║ To: {user['email']:<58} ║
    ║ Subject: Contrato Assinado - STUFF Intercâmbio ✍️                    ║
    ╠══════════════════════════════════════════════════════════════════════╣
    ║                                                                      ║
    ║  Olá {user['name'][:50]:<50} ║
    ║                                                                      ║
    ║  Seu contrato foi assinado com sucesso!                              ║
    ║                                                                      ║
    ║  ═══════════════════════════════════════════════════════════════     ║
    ║  📋 DETALHES DO CONTRATO:                                            ║
    ║  ═══════════════════════════════════════════════════════════════     ║
    ║  • Escola: {contract['school_name'][:48]:<48} ║
    ║  • Curso: {contract['course_name'][:49]:<49} ║
    ║  • Valor Total: €{contract['course_price']:,.2f}{' ':<39} ║
    ║  • Taxa STUFF (20%): €{contract['platform_fee']:,.2f}{' ':<34} ║
    ║  • Valor Escola (80%): €{contract['school_amount']:,.2f}{' ':<32} ║
    ║  • Assinado em: {signed_at[:19]:<43} ║
    ║                                                                      ║
    ║  ═══════════════════════════════════════════════════════════════     ║
    ║  📌 PRÓXIMOS PASSOS:                                                 ║
    ║  ═══════════════════════════════════════════════════════════════     ║
    ║                                                                      ║
    ║  1. Realize o pagamento do curso                                     ║
    ║  2. Após confirmação, você receberá:                                 ║
    ║     • Passaporte Digital do Estudante                                ║
    ║     • Carta oficial da escola                                        ║
    ║                                                                      ║
    ║  Boa sorte no seu intercâmbio! 🍀                                    ║
    ║  Equipe STUFF Intercâmbio                                            ║
    ║                                                                      ║
    ╚══════════════════════════════════════════════════════════════════════╝
    """
    
    logger.info(email_content)
    logger.info(f"📧 [MOCK EMAIL] Contract signed notification sent to: {user['email']}")
    
    # Log email
    await db.email_logs.insert_one({
        "id": str(uuid.uuid4()),
        "type": "contract_signed",
        "to": user["email"],
        "subject": "Contrato Assinado - STUFF Intercâmbio",
        "contract_id": contract["id"],
        "sent_at": datetime.now(timezone.utc).isoformat(),
        "status": "mock_sent"
    })

# ============== ENROLLMENT FLOW WITH CONTRACT ==============

@api_router.post("/enrollment/full-flow")
async def create_full_enrollment_flow(
    course_id: str,
    start_date: str,
    user: dict = Depends(get_current_user)
):
    """Create enrollment and generate contract - Full flow"""
    
    # Get course and school
    course = await db.courses.find_one({"id": course_id}, {"_id": 0})
    if not course:
        raise HTTPException(status_code=404, detail="Curso não encontrado")
    
    school = await db.schools.find_one({"id": course["school_id"]}, {"_id": 0})
    if not school:
        raise HTTPException(status_code=404, detail="Escola não encontrada")
    
    # Create enrollment
    enrollment_id = str(uuid.uuid4())
    enrollment = {
        "id": enrollment_id,
        "user_id": user["id"],
        "user_email": user["email"],
        "user_name": user["name"],
        "school_id": school["id"],
        "school_name": school["name"],
        "course_id": course["id"],
        "course_name": course["name"],
        "start_date": start_date,
        "status": "pending",
        "contract_signed": False,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.enrollments.insert_one(enrollment)
    
    # Calculate split
    total_price = course.get("price", 0)
    platform_fee = total_price * 0.20
    school_amount = total_price * 0.80
    
    # Generate contract
    contract_text = generate_contract_text(
        user_name=user["name"],
        school_name=school["name"],
        course_name=course["name"],
        start_date=start_date,
        duration_weeks=course.get("duration_weeks", 25),
        total_price=total_price,
        platform_fee=platform_fee,
        school_amount=school_amount
    )
    
    contract = ContractData(
        enrollment_id=enrollment_id,
        user_id=user["id"],
        user_name=user["name"],
        user_email=user["email"],
        school_id=school["id"],
        school_name=school["name"],
        course_id=course["id"],
        course_name=course["name"],
        course_price=total_price,
        platform_fee=platform_fee,
        school_amount=school_amount,
        start_date=start_date,
        duration_weeks=course.get("duration_weeks", 25),
        contract_text=contract_text
    )
    await db.contracts.insert_one(contract.model_dump())
    
    logger.info(f"📝 New enrollment created: {enrollment_id}")
    logger.info(f"   Student: {user['name']}")
    logger.info(f"   School: {school['name']}")
    logger.info(f"   Course: {course['name']}")
    logger.info(f"   Total: €{total_price:,.2f} (STUFF: €{platform_fee:,.2f} / School: €{school_amount:,.2f})")
    
    return {
        "enrollment": {k: v for k, v in enrollment.items() if k != "_id"},
        "contract": contract.model_dump(),
        "payment_split": {
            "total": total_price,
            "platform_fee": platform_fee,
            "platform_percentage": 20,
            "school_amount": school_amount,
            "school_percentage": 80
        },
        "next_step": "sign_contract"
    }

@api_router.post("/enrollment/{enrollment_id}/simulate-full-flow")
async def simulate_complete_flow(enrollment_id: str, request: Request):
    """Simulate the complete flow: Sign → Pay → Passport → Letter"""
    
    enrollment = await db.enrollments.find_one({"id": enrollment_id}, {"_id": 0})
    if not enrollment:
        raise HTTPException(status_code=404, detail="Matrícula não encontrada")
    
    user = await db.users.find_one({"id": enrollment["user_id"]}, {"_id": 0, "password": 0})
    contract = await db.contracts.find_one({"enrollment_id": enrollment_id}, {"_id": 0})
    
    results = {
        "steps": [],
        "enrollment_id": enrollment_id,
        "user_email": enrollment.get("user_email")
    }
    
    # Step 1: Sign Contract (if not signed)
    if contract and contract.get("status") != "signed":
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        signed_at = datetime.now(timezone.utc).isoformat()
        
        await db.contracts.update_one(
            {"id": contract["id"]},
            {"$set": {
                "status": "signed",
                "signed_at": signed_at,
                "signature_type": "simulated",
                "signer_ip": client_ip,
                "signer_user_agent": user_agent
            }}
        )
        await db.enrollments.update_one(
            {"id": enrollment_id},
            {"$set": {"contract_signed": True, "contract_signed_at": signed_at}}
        )
        
        await send_contract_signed_email(user, contract, signed_at)
        results["steps"].append({"step": 1, "action": "contract_signed", "status": "✅"})
    else:
        results["steps"].append({"step": 1, "action": "contract_signed", "status": "⏭️ já assinado"})
    
    # Step 2: Process Payment (mock)
    if enrollment.get("status") != "paid":
        paid_at = datetime.now(timezone.utc).isoformat()
        await db.enrollments.update_one(
            {"id": enrollment_id},
            {"$set": {"status": "paid", "paid_at": paid_at}}
        )
        
        # Send payment confirmation
        await send_payment_confirmation_email(user, enrollment, contract)
        results["steps"].append({"step": 2, "action": "payment_processed", "status": "✅"})
    else:
        results["steps"].append({"step": 2, "action": "payment_processed", "status": "⏭️ já pago"})
    
    # Step 3: Generate Passport
    existing_passport = await db.digital_passports.find_one({"enrollment_id": enrollment_id})
    if not existing_passport:
        passport = await generate_digital_passport(enrollment_id)
        if passport:
            results["steps"].append({
                "step": 3, 
                "action": "passport_generated", 
                "status": "✅",
                "passport_url": f"https://student-passport-hub.preview.emergentagent.com/passport/view/{passport['qr_code_token']}"
            })
            results["passport_url"] = f"https://student-passport-hub.preview.emergentagent.com/passport/view/{passport['qr_code_token']}"
    else:
        results["steps"].append({
            "step": 3, 
            "action": "passport_generated", 
            "status": "⏭️ já existe",
            "passport_url": f"https://student-passport-hub.preview.emergentagent.com/passport/view/{existing_passport['qr_code_token']}"
        })
        results["passport_url"] = f"https://student-passport-hub.preview.emergentagent.com/passport/view/{existing_passport['qr_code_token']}"
    
    # Step 4: School Letter notification
    await send_school_letter_notification(user, enrollment)
    results["steps"].append({"step": 4, "action": "school_letter_notification", "status": "✅"})
    
    return results

async def send_payment_confirmation_email(user: dict, enrollment: dict, contract: dict):
    """Send payment confirmation email (MOCK)"""
    
    email_content = f"""
    ╔══════════════════════════════════════════════════════════════════════╗
    ║                    📧 EMAIL NOTIFICATION (MOCK)                       ║
    ╠══════════════════════════════════════════════════════════════════════╣
    ║ To: {user['email']:<58} ║
    ║ Subject: Pagamento Confirmado! 💳 STUFF Intercâmbio                  ║
    ╠══════════════════════════════════════════════════════════════════════╣
    ║                                                                      ║
    ║  Olá {user['name'][:50]:<50} ║
    ║                                                                      ║
    ║  🎉 Seu pagamento foi confirmado com sucesso!                        ║
    ║                                                                      ║
    ║  ═══════════════════════════════════════════════════════════════     ║
    ║  💳 DETALHES DO PAGAMENTO:                                           ║
    ║  ═══════════════════════════════════════════════════════════════     ║
    ║  • Valor Total: €{contract['course_price']:,.2f}{' ':<40} ║
    ║  • Taxa STUFF (20%): €{contract['platform_fee']:,.2f}{' ':<34} ║
    ║  • Valor para Escola (80%): €{contract['school_amount']:,.2f}{' ':<26} ║
    ║                                                                      ║
    ║  ═══════════════════════════════════════════════════════════════     ║
    ║  📋 SUA MATRÍCULA:                                                   ║
    ║  ═══════════════════════════════════════════════════════════════     ║
    ║  • Escola: {enrollment['school_name'][:48]:<48} ║
    ║  • Curso: {enrollment['course_name'][:49]:<49} ║
    ║  • Início: {enrollment['start_date'][:10]:<48} ║
    ║                                                                      ║
    ║  ═══════════════════════════════════════════════════════════════     ║
    ║  🎫 PRÓXIMOS PASSOS:                                                 ║
    ║  ═══════════════════════════════════════════════════════════════     ║
    ║                                                                      ║
    ║  ✅ Seu Passaporte Digital está sendo gerado                         ║
    ║  ✅ A carta da escola será enviada em até 5 dias úteis               ║
    ║                                                                      ║
    ║  Você receberá os documentos em um próximo email.                    ║
    ║                                                                      ║
    ║  Boa sorte no seu intercâmbio! 🍀                                    ║
    ║  Equipe STUFF Intercâmbio                                            ║
    ║                                                                      ║
    ╚══════════════════════════════════════════════════════════════════════╝
    """
    
    logger.info(email_content)
    logger.info(f"📧 [MOCK EMAIL] Payment confirmation sent to: {user['email']}")
    
    await db.email_logs.insert_one({
        "id": str(uuid.uuid4()),
        "type": "payment_confirmation",
        "to": user["email"],
        "subject": "Pagamento Confirmado! - STUFF Intercâmbio",
        "enrollment_id": enrollment["id"],
        "sent_at": datetime.now(timezone.utc).isoformat(),
        "status": "mock_sent"
    })

async def send_school_letter_notification(user: dict, enrollment: dict):
    """Send school letter notification (MOCK)"""
    
    email_content = f"""
    ╔══════════════════════════════════════════════════════════════════════╗
    ║                    📧 EMAIL NOTIFICATION (MOCK)                       ║
    ╠══════════════════════════════════════════════════════════════════════╣
    ║ To: {user['email']:<58} ║
    ║ Subject: Carta da Escola em Processamento 📄                         ║
    ╠══════════════════════════════════════════════════════════════════════╣
    ║                                                                      ║
    ║  Olá {user['name'][:50]:<50} ║
    ║                                                                      ║
    ║  A carta oficial da escola {enrollment['school_name'][:30]:<30} ║
    ║  está sendo processada e será enviada em até 5 dias úteis.           ║
    ║                                                                      ║
    ║  📄 A carta incluirá:                                                ║
    ║  • Confirmação de matrícula                                          ║
    ║  • Detalhes do curso                                                 ║
    ║  • Informações para solicitação de visto                             ║
    ║                                                                      ║
    ║  Enquanto isso, seu Passaporte Digital já está disponível!           ║
    ║                                                                      ║
    ║  Equipe STUFF Intercâmbio                                            ║
    ║                                                                      ║
    ╚══════════════════════════════════════════════════════════════════════╝
    """
    
    logger.info(email_content)
    logger.info(f"📧 [MOCK EMAIL] School letter notification sent to: {user['email']}")

# ============== PUSH NOTIFICATIONS ==============

VAPID_PUBLIC_KEY = os.environ.get('VAPID_PUBLIC_KEY', '')
VAPID_PRIVATE_KEY = os.environ.get('VAPID_PRIVATE_KEY', '')
VAPID_MAILTO = os.environ.get('VAPID_MAILTO', 'mailto:support@stuffintercambio.com')

class PushSubscription(BaseModel):
    endpoint: str
    keys: Dict[str, str]

class PushNotificationRequest(BaseModel):
    title: str
    body: str
    icon: str = "/logo192.png"
    url: str = "/"
    tag: str = "stuff-notification"

@api_router.get("/push/vapid-key")
async def get_vapid_public_key():
    """Get VAPID public key for push subscription"""
    return {"publicKey": VAPID_PUBLIC_KEY}

@api_router.post("/push/subscribe")
async def subscribe_push(subscription: PushSubscription, user: dict = Depends(get_current_user)):
    """Subscribe user to push notifications"""
    # Store subscription in database
    sub_data = {
        "id": str(uuid.uuid4()),
        "user_id": user["id"],
        "user_email": user["email"],
        "endpoint": subscription.endpoint,
        "keys": subscription.keys,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "active": True
    }
    
    # Update or insert subscription (one per endpoint)
    await db.push_subscriptions.update_one(
        {"endpoint": subscription.endpoint},
        {"$set": sub_data},
        upsert=True
    )
    
    logger.info(f"🔔 Push subscription registered for {user['email']}")
    
    # Send welcome notification
    await send_push_to_user(user["id"], {
        "title": "Notificações Ativadas! 🔔",
        "body": "Você receberá atualizações sobre sua matrícula.",
        "icon": "/logo192.png",
        "url": "/dashboard"
    })
    
    return {"success": True, "message": "Subscribed to push notifications"}

@api_router.delete("/push/unsubscribe")
async def unsubscribe_push(user: dict = Depends(get_current_user)):
    """Unsubscribe user from push notifications"""
    result = await db.push_subscriptions.update_many(
        {"user_id": user["id"]},
        {"$set": {"active": False}}
    )
    logger.info(f"🔕 Push unsubscribed for {user['email']}")
    return {"success": True, "unsubscribed": result.modified_count}

@api_router.get("/push/status")
async def get_push_status(user: dict = Depends(get_current_user)):
    """Get push notification status for user"""
    subscription = await db.push_subscriptions.find_one(
        {"user_id": user["id"], "active": True},
        {"_id": 0, "endpoint": 1, "created_at": 1}
    )
    return {
        "subscribed": subscription is not None,
        "subscription": subscription
    }

async def send_push_to_user(user_id: str, notification: dict):
    """Send push notification to a specific user"""
    subscriptions = await db.push_subscriptions.find(
        {"user_id": user_id, "active": True}
    ).to_list(10)
    
    if not subscriptions:
        logger.info(f"🔕 No active push subscriptions for user {user_id}")
        return False
    
    payload = json.dumps({
        "title": notification.get("title", "STUFF Intercâmbio"),
        "body": notification.get("body", ""),
        "icon": notification.get("icon", "/logo192.png"),
        "badge": "/logo192.png",
        "tag": notification.get("tag", "stuff-notification"),
        "data": {
            "url": notification.get("url", "/"),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    })
    
    success_count = 0
    for sub in subscriptions:
        try:
            webpush(
                subscription_info={
                    "endpoint": sub["endpoint"],
                    "keys": sub["keys"]
                },
                data=payload,
                vapid_private_key=VAPID_PRIVATE_KEY,
                vapid_claims={"sub": VAPID_MAILTO}
            )
            success_count += 1
            logger.info(f"🔔 Push sent to {sub.get('user_email', user_id)}")
        except WebPushException as e:
            logger.error(f"Push failed: {e}")
            # Mark subscription as inactive if expired
            if e.response and e.response.status_code in [404, 410]:
                await db.push_subscriptions.update_one(
                    {"id": sub["id"]},
                    {"$set": {"active": False}}
                )
    
    return success_count > 0

async def send_push_notification_for_event(user_id: str, event_type: str, data: dict = None):
    """Send push notification based on event type"""
    notifications = {
        "contract_signed": {
            "title": "Contrato Assinado! ✍️",
            "body": "Seu contrato foi assinado com sucesso. Próximo passo: pagamento.",
            "url": "/dashboard"
        },
        "payment_confirmed": {
            "title": "Pagamento Confirmado! 💳",
            "body": "Seu pagamento foi processado. Seu passaporte está sendo gerado!",
            "url": "/dashboard"
        },
        "passport_ready": {
            "title": "Passaporte Digital Pronto! 🎫",
            "body": "Seu Passaporte Digital de Estudante está disponível.",
            "url": data.get("passport_url", "/passport") if data else "/passport"
        },
        "letter_processing": {
            "title": "Carta em Processamento 📄",
            "body": "A carta da escola está sendo preparada. Prazo: 5 dias úteis.",
            "url": "/dashboard"
        },
        "letter_ready": {
            "title": "Carta da Escola Pronta! 📄",
            "body": "A carta oficial da escola está disponível para download.",
            "url": "/dashboard"
        }
    }
    
    notification = notifications.get(event_type)
    if notification:
        await send_push_to_user(user_id, notification)

# ============== DESTINOAI AGENT ==============

from emergentintegrations.llm.chat import LlmChat, UserMessage

DESTINOAI_SYSTEM_PROMPT = """Você é o DestinoAI, um especialista em intercâmbio internacional.

Seu objetivo é ajudar estudantes brasileiros a planejar todo o intercâmbio de forma personalizada.

## Suas capacidades:
1. **Descobrir o perfil do estudante** - Faça perguntas sobre idade, objetivo, orçamento, tempo disponível e nível de inglês
2. **Recomendar destinos** - Com base no perfil, sugira os melhores países
3. **Sugerir escolas** - Recomende escolas que se encaixem no perfil e orçamento
4. **Calcular custos** - Apresente uma estimativa detalhada de custos
5. **Gerar checklist** - Liste todos os documentos necessários
6. **Criar plano completo** - Monte um plano de intercâmbio personalizado

## Regras importantes:
- Seja amigável, profissional e empático
- Faça uma pergunta por vez para não sobrecarregar o estudante
- Use emojis moderadamente para tornar a conversa mais acolhedora
- Sempre apresente valores em EUR (€) para Europa e na moeda local para outros destinos
- Quando tiver informações suficientes, ofereça-se para criar um plano completo

## Fluxo ideal da conversa:
1. Cumprimente e pergunte o nome do estudante
2. Descubra o objetivo (estudar inglês, faculdade, trabalhar e estudar)
3. Pergunte sobre países de interesse
4. Entenda o orçamento disponível
5. Pergunte sobre a duração desejada
6. Avalie o nível de inglês atual
7. Faça recomendações personalizadas
8. Calcule custos e apresente opções
9. Gere checklist de documentos
10. Ofereça criar um plano completo

## Dados disponíveis:
Você tem acesso a informações sobre países como Irlanda, Malta, Canadá, Austrália, Reino Unido e suas respectivas escolas de idiomas.

Comece sempre se apresentando de forma calorosa e perguntando como pode ajudar!"""

EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY', 'sk-emergent-aAaD492D5E7E2D1261')

class DestinoAIAgent:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.api_key = EMERGENT_LLM_KEY
        self._chat = None
    
    def _get_chat(self):
        if self._chat is None:
            self._chat = LlmChat(
                api_key=self.api_key,
                session_id=self.session_id,
                system_message=DESTINOAI_SYSTEM_PROMPT
            ).with_model("openai", "gpt-4o")
        return self._chat
    
    async def process_message(self, user_input: str, conversation_history: list) -> str:
        """Process user message and generate response"""
        try:
            data_context = await self._get_relevant_data(user_input)
            enriched_message = user_input
            if data_context:
                enriched_message = f"{user_input}\n\n[Dados disponíveis para sua resposta]:\n{data_context}"
            message = UserMessage(text=enriched_message)
            chat = self._get_chat()
            response = await chat.send_message(message)
            return response
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error processing message: {error_msg}")
            
            # Check if it's a budget error and return a helpful message
            if "Budget has been exceeded" in error_msg or "budget" in error_msg.lower():
                return self._get_fallback_response(user_input)
            
            return "Desculpe, tive um problema ao processar sua mensagem. Pode tentar novamente?"
    
    def _get_fallback_response(self, user_input: str) -> str:
        """Provide a helpful fallback response when LLM is unavailable"""
        user_lower = user_input.lower()
        
        if any(kw in user_lower for kw in ["olá", "oi", "hello", "hi"]):
            return """Olá! 👋 Eu sou o DestinoAI, seu consultor especialista em intercâmbio!

Infelizmente, estou com um problema temporário na minha conexão com a IA. Mas posso te ajudar com informações básicas!

📍 **Destinos populares:**
- 🇮🇪 Irlanda - Trabalho permitido (20h/semana), custo médio €7.500
- 🇲🇹 Malta - Custo menor (€5.500), clima mediterrâneo
- 🇨🇦 Canadá - Possibilidade de imigração, custo ~CAD 12.000
- 🇦🇺 Austrália - Trabalho 48h/quinzena, custo ~AUD 15.000

Me conte: qual país te interessa mais?

⚠️ *Nota: Para respostas mais personalizadas, peça ao administrador para adicionar saldo na Universal Key (Profile > Universal Key > Add Balance)*"""
        
        if any(kw in user_lower for kw in ["irlanda", "ireland", "dublin"]):
            return """🇮🇪 **Irlanda - Excelente escolha!**

**Por que a Irlanda?**
✅ Permissão de trabalho: 20h/semana durante aulas
✅ Inglês nativo
✅ Porta de entrada para a Europa
✅ Cultura acolhedora

**Escolas em Dublin:**
- Kaplan Dublin: €280/semana
- EC Dublin: €260/semana  
- Atlas Language School: €200/semana
- ISI Dublin: €180/semana

**Custo estimado (25 semanas):**
- Curso: ~€4.000
- Acomodação: ~€5.000
- Seguro: ~€400
- Passagem: ~€700
- **Total: ~€10.100**

Quer que eu detalhe mais sobre alguma escola específica?"""
        
        if any(kw in user_lower for kw in ["custo", "preço", "valor", "quanto"]):
            return """💰 **Custos de Intercâmbio (estimativa 25 semanas)**

🇮🇪 **Irlanda:**
- Curso: €3.750-€7.000
- Acomodação: €5.000-€6.500
- Seguro: €400
- Passagem: €700
- **Total: €9.850-€14.600**

🇲🇹 **Malta:**
- Curso: €4.000-€5.000
- Acomodação: €3.500-€4.500
- **Total: €8.000-€10.000**

🇨🇦 **Canadá:**
- Curso: CAD 8.000-€10.000
- Acomodação: CAD 6.000-€8.000
- **Total: CAD 15.000-€20.000**

Qual destino gostaria de explorar?"""
        
        return """Obrigado pela sua mensagem! 😊

Estou com um pequeno problema técnico no momento, mas posso te ajudar com:

📍 **Informações sobre destinos** - Irlanda, Malta, Canadá, Austrália
📚 **Escolas de inglês** - Preços e características
💰 **Estimativa de custos** - Curso, acomodação, seguro
📋 **Checklist de documentos** - O que você precisa

Digite uma dessas opções ou me conte seu objetivo de intercâmbio!

*Para ativar a IA completa, adicione saldo na Universal Key em Profile > Universal Key > Add Balance*"""
    
    async def _get_relevant_data(self, user_input: str) -> str:
        """Get relevant data based on user input"""
        data_parts = []
        user_lower = user_input.lower()
        
        country_keywords = ["irlanda", "ireland", "malta", "canada", "canadá", "australia", "austrália", "uk", "reino unido", "país", "destino"]
        if any(kw in user_lower for kw in country_keywords):
            countries = await db.destinoai_countries.find({}, {"_id": 0}).to_list(10)
            if countries:
                data_parts.append("Países disponíveis:")
                for c in countries[:5]:
                    work_info = f"Trabalho: {c.get('work_hours', 0)}h/semana" if c.get('work_permitted') else "Sem permissão de trabalho"
                    data_parts.append(f"- {c.get('name')}: Custo médio €{c.get('average_cost', 0)}, {work_info}")
        
        school_keywords = ["escola", "school", "curso", "estudar", "aula"]
        if any(kw in user_lower for kw in school_keywords):
            country_filter = None
            if "irlanda" in user_lower or "dublin" in user_lower:
                country_filter = "Irlanda"
            elif "malta" in user_lower:
                country_filter = "Malta"
            
            query = {"country": {"$regex": country_filter, "$options": "i"}} if country_filter else {}
            schools = await db.destinoai_schools.find(query, {"_id": 0}).to_list(10)
            if schools:
                data_parts.append("\nEscolas disponíveis:")
                for s in schools[:5]:
                    data_parts.append(f"- {s.get('name')} ({s.get('city')}): €{s.get('price_per_week', 0)}/semana")
        
        cost_keywords = ["custo", "preço", "valor", "quanto", "orçamento", "budget"]
        if any(kw in user_lower for kw in cost_keywords):
            data_parts.append(f"\nExemplo de custos (25 semanas, Irlanda):")
            data_parts.append(f"- Curso: €3.750 (€150/semana)")
            data_parts.append(f"- Acomodação: €5.000 (€200/semana)")
            data_parts.append(f"- Seguro: €400")
            data_parts.append(f"- Passagem: €700")
            data_parts.append(f"- Total estimado: €9.850")
        
        doc_keywords = ["documento", "checklist", "visto", "papelada", "precisar", "necessário"]
        if any(kw in user_lower for kw in doc_keywords):
            data_parts.append(f"\nChecklist para Irlanda:")
            data_parts.append("✔ Passaporte válido (mínimo 6 meses)")
            data_parts.append("✔ Seguro saúde internacional")
            data_parts.append("✔ Matrícula confirmada na escola")
            data_parts.append("✔ Comprovante financeiro (€4.200 mínimo)")
            data_parts.append("✔ Carta de aceitação da escola")
            data_parts.append("✔ Passagem aérea")
        
        return "\n".join(data_parts) if data_parts else ""

class DestinoAIChatRequest(BaseModel):
    session_id: Optional[str] = None
    message: str

@api_router.post("/destinoai/chat")
async def destinoai_chat(request: DestinoAIChatRequest):
    """DestinoAI chat endpoint"""
    try:
        session_id = request.session_id or str(uuid.uuid4())
        session = await db.destinoai_sessions.find_one({"session_id": session_id}, {"_id": 0})
        
        if not session:
            session = {"session_id": session_id, "messages": [], "created_at": datetime.now(timezone.utc).isoformat()}
            await db.destinoai_sessions.insert_one(session)
        
        user_msg = {"role": "user", "content": request.message, "timestamp": datetime.now(timezone.utc).isoformat()}
        agent = DestinoAIAgent(session_id)
        response = await agent.process_message(request.message, session.get("messages", []))
        assistant_msg = {"role": "assistant", "content": response, "timestamp": datetime.now(timezone.utc).isoformat()}
        
        await db.destinoai_sessions.update_one(
            {"session_id": session_id},
            {"$push": {"messages": {"$each": [user_msg, assistant_msg]}}}
        )
        
        return {"session_id": session_id, "response": response, "timestamp": assistant_msg["timestamp"]}
    except Exception as e:
        logger.error(f"DestinoAI chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/destinoai/chat/{session_id}/history")
async def destinoai_history(session_id: str):
    session = await db.destinoai_sessions.find_one({"session_id": session_id}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"session_id": session_id, "messages": session.get("messages", [])}

@api_router.delete("/destinoai/chat/{session_id}")
async def destinoai_clear(session_id: str):
    await db.destinoai_sessions.delete_one({"session_id": session_id})
    return {"message": "Session cleared"}

@api_router.get("/destinoai/countries")
async def destinoai_countries():
    countries = await db.destinoai_countries.find({}, {"_id": 0}).to_list(100)
    return {"countries": countries}

@api_router.get("/destinoai/schools")
async def destinoai_schools(country: Optional[str] = None):
    query = {"country": {"$regex": country, "$options": "i"}} if country else {}
    schools = await db.destinoai_schools.find(query, {"_id": 0}).to_list(100)
    return {"schools": schools}

# Include router and add middleware
app.include_router(api_router)
app.include_router(chat_router)

# Initialize chat module
init_chat_module(db, JWT_SECRET)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

async def seed_destinoai_data():
    """Seed DestinoAI data"""
    countries_count = await db.destinoai_countries.count_documents({})
    if countries_count == 0:
        logger.info("Seeding DestinoAI countries...")
        countries_data = [
            {"id": str(uuid.uuid4()), "name": "Irlanda", "name_en": "Ireland", "work_permitted": True, "work_hours": 20, "average_cost": 7500, "currency": "EUR", "popular_cities": ["Dublin", "Cork", "Galway"]},
            {"id": str(uuid.uuid4()), "name": "Malta", "name_en": "Malta", "work_permitted": True, "work_hours": 20, "average_cost": 5500, "currency": "EUR", "popular_cities": ["St. Julian's", "Sliema", "Valletta"]},
            {"id": str(uuid.uuid4()), "name": "Canadá", "name_en": "Canada", "work_permitted": True, "work_hours": 20, "average_cost": 12000, "currency": "CAD", "popular_cities": ["Toronto", "Vancouver", "Montreal"]},
            {"id": str(uuid.uuid4()), "name": "Austrália", "name_en": "Australia", "work_permitted": True, "work_hours": 48, "average_cost": 15000, "currency": "AUD", "popular_cities": ["Sydney", "Melbourne", "Brisbane"]},
            {"id": str(uuid.uuid4()), "name": "Reino Unido", "name_en": "United Kingdom", "work_permitted": False, "work_hours": 0, "average_cost": 10000, "currency": "GBP", "popular_cities": ["Londres", "Manchester", "Edinburgh"]},
        ]
        await db.destinoai_countries.insert_many(countries_data)
    
    schools_count = await db.destinoai_schools.count_documents({})
    if schools_count == 0:
        logger.info("Seeding DestinoAI schools...")
        schools_data = [
            {"id": str(uuid.uuid4()), "name": "Kaplan Dublin", "country": "Irlanda", "city": "Dublin", "courses": ["Inglês Geral", "IELTS"], "price_per_week": 280, "rating": 4.6},
            {"id": str(uuid.uuid4()), "name": "EC Dublin", "country": "Irlanda", "city": "Dublin", "courses": ["Inglês Geral", "Cambridge"], "price_per_week": 260, "rating": 4.5},
            {"id": str(uuid.uuid4()), "name": "Atlas Language School", "country": "Irlanda", "city": "Dublin", "courses": ["Inglês Geral", "IELTS"], "price_per_week": 200, "rating": 4.4},
            {"id": str(uuid.uuid4()), "name": "ISI Dublin", "country": "Irlanda", "city": "Dublin", "courses": ["Inglês Geral"], "price_per_week": 180, "rating": 4.3},
            {"id": str(uuid.uuid4()), "name": "EC Malta", "country": "Malta", "city": "St. Julian's", "courses": ["Inglês Geral", "30+"], "price_per_week": 200, "rating": 4.4},
            {"id": str(uuid.uuid4()), "name": "BELS Malta", "country": "Malta", "city": "St. Paul's Bay", "courses": ["Inglês Geral"], "price_per_week": 160, "rating": 4.3},
            {"id": str(uuid.uuid4()), "name": "ILAC Toronto", "country": "Canadá", "city": "Toronto", "courses": ["Inglês Geral", "Pathway"], "price_per_week": 320, "rating": 4.6},
            {"id": str(uuid.uuid4()), "name": "Kaplan Sydney", "country": "Austrália", "city": "Sydney", "courses": ["Inglês Geral", "IELTS"], "price_per_week": 380, "rating": 4.5},
        ]
        await db.destinoai_schools.insert_many(schools_data)

@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    await setup_ttl_index()
    await seed_destinoai_data()

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
