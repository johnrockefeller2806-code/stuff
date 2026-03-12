from fastapi import FastAPI, APIRouter, HTTPException, Depends, Request, UploadFile, File
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

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user = await db.users.find_one({"id": payload["sub"]}, {"_id": 0, "password": 0})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def get_admin_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    user = await get_current_user(credentials)
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user

async def get_school_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    user = await get_current_user(credentials)
    if user.get("role") != "school":
        raise HTTPException(status_code=403, detail="School access required")
    return user

async def get_optional_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if not credentials:
        return None
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user = await db.users.find_one({"id": payload["sub"]}, {"_id": 0, "password": 0})
        return user
    except:
        return None

# ============== AUTH ROUTES ==============

@api_router.post("/auth/register", response_model=TokenResponse)
async def register(user_data: UserCreate):
    existing = await db.users.find_one({"email": user_data.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email já cadastrado")
    
    user_id = str(uuid.uuid4())
    user = {
        "id": user_id,
        "name": user_data.name,
        "email": user_data.email,
        "password": hash_password(user_data.password),
        "role": "student",  # Always student for regular registration
        "plan": "free",  # Plano gratuito por padrão
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.users.insert_one(user)
    
    token = create_token(user_id, user_data.email, "student")
    return TokenResponse(
        access_token=token,
        user=UserResponse(
            id=user_id,
            name=user_data.name,
            email=user_data.email,
            role="student",
            plan="free",
            created_at=user["created_at"]
        )
    )

@api_router.post("/auth/register-school", response_model=TokenResponse)
async def register_school(data: SchoolRegister):
    """Register a new school account"""
    existing = await db.users.find_one({"email": data.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email já cadastrado")
    
    user_id = str(uuid.uuid4())
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

@api_router.post("/auth/login", response_model=TokenResponse)
async def login(credentials: UserLogin):
    user = await db.users.find_one({"email": credentials.email})
    if not user or not verify_password(credentials.password, user["password"]):
        raise HTTPException(status_code=401, detail="Email ou senha incorretos")
    
    role = user.get("role", "student")
    token = create_token(user["id"], user["email"], role)
    return TokenResponse(
        access_token=token,
        user=UserResponse(
            id=user["id"],
            name=user["name"],
            email=user["email"],
            role=role,
            school_id=user.get("school_id"),
            plan=user.get("plan", "free"),
            plan_purchased_at=user.get("plan_purchased_at"),
            created_at=user["created_at"]
        )
    )

@api_router.get("/auth/me")
async def get_me(user: dict = Depends(get_current_user)):
    return UserResponse(
        id=user["id"],
        name=user["name"],
        email=user["email"],
        role=user.get("role", "student"),
        school_id=user.get("school_id"),
        plan=user.get("plan", "free"),
        plan_purchased_at=user.get("plan_purchased_at"),
        created_at=user["created_at"],
        avatar=user.get("avatar")
    )

@api_router.put("/auth/profile")
async def update_profile(data: UserProfileUpdate, user: dict = Depends(get_current_user)):
    """Update user profile (name and avatar)"""
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    
    if not update_data:
        raise HTTPException(status_code=400, detail="No data to update")
    
    await db.users.update_one(
        {"id": user["id"]},
        {"$set": update_data}
    )
    
    updated_user = await db.users.find_one({"id": user["id"]}, {"_id": 0, "password": 0})
    return UserResponse(
        id=updated_user["id"],
        name=updated_user["name"],
        email=updated_user["email"],
        role=updated_user.get("role", "student"),
        school_id=updated_user.get("school_id"),
        plan=updated_user.get("plan", "free"),
        plan_purchased_at=updated_user.get("plan_purchased_at"),
        created_at=updated_user["created_at"],
        avatar=updated_user.get("avatar")
    )

@api_router.post("/auth/upload-avatar")
async def upload_avatar(file: UploadFile = File(...), user: dict = Depends(get_current_user)):
    """Upload profile avatar image"""
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
    await db.users.update_one(
        {"id": user["id"]},
        {"$set": {"avatar": avatar_data}}
    )
    
    logger.info(f"Avatar uploaded for user {user['id']}")
    
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
    
    # Seed Schools (all approved for demo)
    schools = [
        School(
            id="school-1",
            name="Dublin Language Institute",
            description="Uma das escolas de inglês mais conceituadas de Dublin, com mais de 20 anos de experiência em ensino de idiomas para estudantes internacionais.",
            description_en="One of Dublin's most renowned English schools, with over 20 years of experience teaching languages to international students.",
            address="35 Dame Street, Dublin 2",
            phone="+353 1 234 5678",
            email="info@dli.ie",
            image_url="https://images.unsplash.com/photo-1580582932707-520aed937b7b?w=800&q=80",
            rating=4.8,
            reviews_count=342,
            accreditation=["ACELS", "QQI", "MEI"],
            facilities=["Wi-Fi", "Biblioteca", "Sala de estudos", "Cafeteria", "Computadores"],
            status="approved"
        ),
        School(
            id="school-2",
            name="Emerald Cultural Institute",
            description="Escola de prestígio localizada em casarões georgianos históricos, oferecendo programas intensivos de inglês e preparação para exames.",
            description_en="Prestigious school located in historic Georgian mansions, offering intensive English programs and exam preparation.",
            address="10 Palmerston Park, Dublin 6",
            phone="+353 1 234 5679",
            email="info@eci.ie",
            image_url="https://images.unsplash.com/photo-1562774053-701939374585?w=800&q=80",
            rating=4.9,
            reviews_count=428,
            accreditation=["ACELS", "QQI", "IALC", "EAQUALS"],
            facilities=["Jardim", "Wi-Fi", "Biblioteca", "Sala multimídia", "Lounge"],
            status="approved"
        ),
        School(
            id="school-3",
            name="Atlas Language School",
            description="Escola moderna no coração de Dublin, conhecida por seu método comunicativo e ambiente internacional diversificado.",
            description_en="Modern school in the heart of Dublin, known for its communicative method and diverse international environment.",
            address="Portobello House, Dublin 8",
            phone="+353 1 234 5680",
            email="info@atlas.ie",
            image_url="https://images.unsplash.com/photo-1497366216548-37526070297c?w=800&q=80",
            rating=4.7,
            reviews_count=256,
            accreditation=["ACELS", "QQI", "Marketing English in Ireland"],
            facilities=["Wi-Fi", "Terraço", "Sala de jogos", "Cozinha compartilhada"],
            status="approved"
        ),
        School(
            id="school-4",
            name="ISI Dublin",
            description="International Study Institute oferece cursos de inglês geral e profissional em localização privilegiada no centro da cidade.",
            description_en="International Study Institute offers general and professional English courses in a prime city center location.",
            address="4 Meetinghouse Lane, Dublin 7",
            phone="+353 1 234 5681",
            email="info@isi.ie",
            image_url="https://images.unsplash.com/photo-1541339907198-e08756dedf3f?w=800&q=80",
            rating=4.6,
            reviews_count=189,
            accreditation=["ACELS", "QQI"],
            facilities=["Wi-Fi", "Computadores", "Área social", "Aulas online"],
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
    logger.info("📧 EMAIL: Seu Passaporte Digital está pronto!")
    logger.info(f"   To: {user['email']}")
    
    return passport.model_dump()

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

@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    await setup_ttl_index()

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
