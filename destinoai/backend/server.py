from fastapi import FastAPI, APIRouter, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from dotenv import load_dotenv
from pathlib import Path
import os
import uuid
import logging
import json

from emergentintegrations.llm.chat import LlmChat, UserMessage

# Load environment variables
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create FastAPI app
app = FastAPI(title="DestinoAI API", description="AI Study Abroad Planner")
api_router = APIRouter(prefix="/api")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============== MODELS ==============

class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class ChatSession(BaseModel):
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    messages: List[ChatMessage] = []
    student_profile: Optional[Dict[str, Any]] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class SendMessageRequest(BaseModel):
    session_id: Optional[str] = None
    message: str

class Country(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    name_en: str
    work_permitted: bool
    work_hours: int
    average_cost: float
    currency: str = "EUR"
    visa_required: bool = True
    popular_cities: List[str] = []
    pros: List[str] = []
    cons: List[str] = []

class School(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    country: str
    city: str
    courses: List[str]
    price_per_week: float
    currency: str = "EUR"
    rating: float = 4.5
    amenities: List[str] = []
    description: str = ""

class StudentProfile(BaseModel):
    age: Optional[int] = None
    country_interest: Optional[str] = None
    objective: Optional[str] = None  # english, university, work_study
    duration_months: Optional[int] = None
    budget: Optional[float] = None
    english_level: Optional[str] = None  # beginner, intermediate, advanced

class StudyPlan(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    destination: str
    city: str
    school: str
    course: str
    duration_weeks: int
    costs: Dict[str, float]
    total_cost: float
    checklist: List[str]
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

# ============== DESTINOAI TOOLS ==============

async def get_countries() -> List[Dict]:
    """Get all available countries for study abroad"""
    countries = await db.countries.find({}, {"_id": 0}).to_list(100)
    return countries

async def get_country_by_name(name: str) -> Optional[Dict]:
    """Get country details by name"""
    country = await db.countries.find_one(
        {"$or": [{"name": {"$regex": name, "$options": "i"}}, {"name_en": {"$regex": name, "$options": "i"}}]},
        {"_id": 0}
    )
    return country

async def get_schools(country: Optional[str] = None, city: Optional[str] = None) -> List[Dict]:
    """Get schools, optionally filtered by country or city"""
    query = {}
    if country:
        query["country"] = {"$regex": country, "$options": "i"}
    if city:
        query["city"] = {"$regex": city, "$options": "i"}
    schools = await db.schools.find(query, {"_id": 0}).to_list(100)
    return schools

async def calculate_study_cost(
    duration_weeks: int,
    school_price_per_week: float,
    accommodation_per_week: float = 200,
    include_insurance: bool = True,
    include_flight: bool = True
) -> Dict[str, float]:
    """Calculate total study abroad cost"""
    course_cost = duration_weeks * school_price_per_week
    accommodation_cost = duration_weeks * accommodation_per_week
    insurance_cost = 400 if include_insurance else 0
    flight_cost = 700 if include_flight else 0
    
    return {
        "course": course_cost,
        "accommodation": accommodation_cost,
        "insurance": insurance_cost,
        "flight": flight_cost,
        "total": course_cost + accommodation_cost + insurance_cost + flight_cost
    }

def generate_checklist(country: str) -> List[str]:
    """Generate document checklist based on destination country"""
    base_checklist = [
        "✔ Passaporte válido (mínimo 6 meses)",
        "✔ Seguro saúde internacional",
        "✔ Matrícula confirmada na escola",
        "✔ Comprovante de acomodação",
        "✔ Passagem aérea (ida e volta recomendado)",
    ]
    
    country_lower = country.lower()
    
    if "irlanda" in country_lower or "ireland" in country_lower:
        base_checklist.extend([
            "✔ Comprovante financeiro (€4.200 mínimo)",
            "✔ Carta de aceitação da escola",
            "✔ Agendamento GNIB/IRP",
            "✔ Fotos 3x4 para documentos",
        ])
    elif "malta" in country_lower:
        base_checklist.extend([
            "✔ Comprovante financeiro (€48/dia)",
            "✔ Formulário de visto (se aplicável)",
        ])
    elif "canada" in country_lower or "canadá" in country_lower:
        base_checklist.extend([
            "✔ Study Permit aprovado",
            "✔ Biometria realizada",
            "✔ Comprovante financeiro (CAD 10.000/ano)",
        ])
    elif "australia" in country_lower or "austrália" in country_lower:
        base_checklist.extend([
            "✔ Student Visa (subclass 500)",
            "✔ OSHC (seguro saúde obrigatório)",
            "✔ Comprovante financeiro (AUD 24.505/ano)",
        ])
    
    return base_checklist

# ============== AGENT SYSTEM PROMPT ==============

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

# ============== AGENT CLASS ==============

class DestinoAIAgent:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.api_key = os.environ.get('EMERGENT_LLM_KEY')
        self.chat = LlmChat(
            api_key=self.api_key,
            session_id=session_id,
            system_message=DESTINOAI_SYSTEM_PROMPT
        ).with_model("openai", "gpt-4o")
    
    async def process_message(self, user_input: str, conversation_history: List[Dict]) -> str:
        """Process user message and generate response"""
        try:
            # Build context from conversation history
            context = self._build_context(conversation_history)
            
            # Get relevant data based on user input
            data_context = await self._get_relevant_data(user_input)
            
            # Create enriched message
            enriched_message = user_input
            if data_context:
                enriched_message = f"{user_input}\n\n[Dados disponíveis para sua resposta]:\n{data_context}"
            
            # Send message to LLM
            message = UserMessage(text=enriched_message)
            response = await self.chat.send_message(message)
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return "Desculpe, tive um problema ao processar sua mensagem. Pode tentar novamente?"
    
    def _build_context(self, history: List[Dict]) -> str:
        """Build conversation context from history"""
        if not history:
            return ""
        
        context_parts = []
        for msg in history[-10:]:  # Last 10 messages
            role = "Estudante" if msg.get("role") == "user" else "DestinoAI"
            context_parts.append(f"{role}: {msg.get('content', '')}")
        
        return "\n".join(context_parts)
    
    async def _get_relevant_data(self, user_input: str) -> str:
        """Get relevant data based on user input"""
        data_parts = []
        user_lower = user_input.lower()
        
        # Check for country mentions
        country_keywords = ["irlanda", "ireland", "malta", "canada", "canadá", "australia", "austrália", "uk", "reino unido", "país", "destino"]
        if any(kw in user_lower for kw in country_keywords):
            countries = await get_countries()
            if countries:
                data_parts.append("Países disponíveis:")
                for c in countries[:5]:
                    work_info = f"Trabalho: {c.get('work_hours', 0)}h/semana" if c.get('work_permitted') else "Sem permissão de trabalho"
                    data_parts.append(f"- {c.get('name')}: Custo médio €{c.get('average_cost', 0)}, {work_info}")
        
        # Check for school mentions
        school_keywords = ["escola", "school", "curso", "estudar", "aula"]
        if any(kw in user_lower for kw in school_keywords):
            # Try to detect country from message
            country_filter = None
            if "irlanda" in user_lower or "dublin" in user_lower:
                country_filter = "Irlanda"
            elif "malta" in user_lower:
                country_filter = "Malta"
            
            schools = await get_schools(country=country_filter)
            if schools:
                data_parts.append("\nEscolas disponíveis:")
                for s in schools[:5]:
                    data_parts.append(f"- {s.get('name')} ({s.get('city')}): €{s.get('price_per_week', 0)}/semana - {', '.join(s.get('courses', []))}")
        
        # Check for cost mentions
        cost_keywords = ["custo", "preço", "valor", "quanto", "orçamento", "budget"]
        if any(kw in user_lower for kw in cost_keywords):
            costs = await calculate_study_cost(25, 150)  # Default 25 weeks
            data_parts.append(f"\nExemplo de custos (25 semanas):")
            data_parts.append(f"- Curso: €{costs['course']}")
            data_parts.append(f"- Acomodação: €{costs['accommodation']}")
            data_parts.append(f"- Seguro: €{costs['insurance']}")
            data_parts.append(f"- Passagem: €{costs['flight']}")
            data_parts.append(f"- Total estimado: €{costs['total']}")
        
        # Check for checklist/document mentions
        doc_keywords = ["documento", "checklist", "visto", "papelada", "precisar", "necessário"]
        if any(kw in user_lower for kw in doc_keywords):
            country = "Irlanda"  # Default
            if "malta" in user_lower:
                country = "Malta"
            elif "canada" in user_lower or "canadá" in user_lower:
                country = "Canadá"
            
            checklist = generate_checklist(country)
            data_parts.append(f"\nChecklist para {country}:")
            data_parts.extend(checklist)
        
        return "\n".join(data_parts) if data_parts else ""

# ============== API ROUTES ==============

@api_router.post("/chat")
async def send_chat_message(request: SendMessageRequest):
    """Send a message to DestinoAI and get response"""
    try:
        session_id = request.session_id or str(uuid.uuid4())
        
        # Get or create session
        session = await db.chat_sessions.find_one({"session_id": session_id}, {"_id": 0})
        
        if not session:
            session = {
                "session_id": session_id,
                "messages": [],
                "student_profile": {},
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            await db.chat_sessions.insert_one(session)
        
        # Add user message to history
        user_message = {
            "role": "user",
            "content": request.message,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        # Get AI response
        agent = DestinoAIAgent(session_id)
        response = await agent.process_message(request.message, session.get("messages", []))
        
        # Add assistant message to history
        assistant_message = {
            "role": "assistant",
            "content": response,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        # Update session in database
        await db.chat_sessions.update_one(
            {"session_id": session_id},
            {
                "$push": {"messages": {"$each": [user_message, assistant_message]}},
                "$set": {"updated_at": datetime.now(timezone.utc).isoformat()}
            }
        )
        
        return {
            "session_id": session_id,
            "response": response,
            "timestamp": assistant_message["timestamp"]
        }
        
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/chat/{session_id}/history")
async def get_chat_history(session_id: str):
    """Get chat history for a session"""
    session = await db.chat_sessions.find_one({"session_id": session_id}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {
        "session_id": session_id,
        "messages": session.get("messages", []),
        "student_profile": session.get("student_profile", {})
    }

@api_router.delete("/chat/{session_id}")
async def clear_chat_session(session_id: str):
    """Clear chat session and start fresh"""
    await db.chat_sessions.delete_one({"session_id": session_id})
    return {"message": "Session cleared", "session_id": session_id}

@api_router.get("/countries")
async def list_countries():
    """Get all available countries"""
    countries = await get_countries()
    return {"countries": countries}

@api_router.get("/schools")
async def list_schools(country: Optional[str] = None, city: Optional[str] = None):
    """Get schools, optionally filtered"""
    schools = await get_schools(country, city)
    return {"schools": schools}

@api_router.post("/calculate-cost")
async def api_calculate_cost(
    duration_weeks: int = 25,
    school_price_per_week: float = 150,
    accommodation_per_week: float = 200
):
    """Calculate study abroad cost"""
    costs = await calculate_study_cost(
        duration_weeks=duration_weeks,
        school_price_per_week=school_price_per_week,
        accommodation_per_week=accommodation_per_week
    )
    return {"costs": costs}

@api_router.get("/checklist/{country}")
async def get_checklist(country: str):
    """Get document checklist for a country"""
    checklist = generate_checklist(country)
    return {"country": country, "checklist": checklist}

@api_router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "DestinoAI"}

# Include router
app.include_router(api_router)

# Startup event to seed data
@app.on_event("startup")
async def startup_event():
    """Seed initial data on startup"""
    await seed_initial_data()

async def seed_initial_data():
    """Seed countries and schools if not exist"""
    # Check if data already exists
    countries_count = await db.countries.count_documents({})
    if countries_count == 0:
        logger.info("Seeding countries data...")
        countries_data = [
            {
                "id": str(uuid.uuid4()),
                "name": "Irlanda",
                "name_en": "Ireland",
                "work_permitted": True,
                "work_hours": 20,
                "average_cost": 7500,
                "currency": "EUR",
                "visa_required": False,
                "popular_cities": ["Dublin", "Cork", "Galway", "Limerick"],
                "pros": ["Inglês nativo", "Permissão de trabalho", "Cultura acolhedora", "Porta de entrada para Europa"],
                "cons": ["Clima chuvoso", "Custo de vida alto em Dublin", "Acomodação escassa"]
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Malta",
                "name_en": "Malta",
                "work_permitted": True,
                "work_hours": 20,
                "average_cost": 5500,
                "currency": "EUR",
                "visa_required": False,
                "popular_cities": ["St. Julian's", "Sliema", "Valletta", "Gozo"],
                "pros": ["Custo mais baixo", "Clima mediterrâneo", "Praias", "União Europeia"],
                "cons": ["Inglês não é língua nativa", "País pequeno", "Verões muito quentes"]
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Canadá",
                "name_en": "Canada",
                "work_permitted": True,
                "work_hours": 20,
                "average_cost": 12000,
                "currency": "CAD",
                "visa_required": True,
                "popular_cities": ["Toronto", "Vancouver", "Montreal", "Calgary"],
                "pros": ["Alta qualidade de vida", "Possibilidade de imigração", "Multicultural", "Natureza exuberante"],
                "cons": ["Visto mais difícil", "Custo alto", "Inverno rigoroso"]
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Austrália",
                "name_en": "Australia",
                "work_permitted": True,
                "work_hours": 48,
                "average_cost": 15000,
                "currency": "AUD",
                "visa_required": True,
                "popular_cities": ["Sydney", "Melbourne", "Brisbane", "Perth"],
                "pros": ["Clima agradável", "Salário alto", "Qualidade de vida", "Praias incríveis"],
                "cons": ["Muito distante", "Custo alto", "Visto complexo"]
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Reino Unido",
                "name_en": "United Kingdom",
                "work_permitted": False,
                "work_hours": 0,
                "average_cost": 10000,
                "currency": "GBP",
                "visa_required": True,
                "popular_cities": ["Londres", "Manchester", "Liverpool", "Edinburgh"],
                "pros": ["Inglês britânico", "Cultura rica", "Universidades renomadas", "História"],
                "cons": ["Sem permissão de trabalho para estudantes de idiomas", "Custo alto", "Visto necessário"]
            }
        ]
        await db.countries.insert_many(countries_data)
        logger.info(f"Seeded {len(countries_data)} countries")
    
    schools_count = await db.schools.count_documents({})
    if schools_count == 0:
        logger.info("Seeding schools data...")
        schools_data = [
            # Ireland - Dublin
            {"id": str(uuid.uuid4()), "name": "Kaplan Dublin", "country": "Irlanda", "city": "Dublin", "courses": ["Inglês Geral", "Inglês Intensivo", "IELTS"], "price_per_week": 280, "currency": "EUR", "rating": 4.6, "amenities": ["WiFi", "Biblioteca", "Cafeteria"], "description": "Uma das maiores redes de escolas de inglês do mundo"},
            {"id": str(uuid.uuid4()), "name": "EC Dublin", "country": "Irlanda", "city": "Dublin", "courses": ["Inglês Geral", "Inglês para Negócios", "Cambridge"], "price_per_week": 260, "currency": "EUR", "rating": 4.5, "amenities": ["WiFi", "Lounge", "Atividades sociais"], "description": "Escola moderna no centro de Dublin"},
            {"id": str(uuid.uuid4()), "name": "Atlas Language School", "country": "Irlanda", "city": "Dublin", "courses": ["Inglês Geral", "IELTS", "Inglês Acadêmico"], "price_per_week": 200, "currency": "EUR", "rating": 4.4, "amenities": ["WiFi", "Biblioteca", "Jardim"], "description": "Escola familiar com ótimo custo-benefício"},
            {"id": str(uuid.uuid4()), "name": "ISI Dublin", "country": "Irlanda", "city": "Dublin", "courses": ["Inglês Geral", "Pathway", "IELTS"], "price_per_week": 180, "currency": "EUR", "rating": 4.3, "amenities": ["WiFi", "Sala de jogos"], "description": "Escola acessível com boa estrutura"},
            {"id": str(uuid.uuid4()), "name": "Emerald Cultural Institute", "country": "Irlanda", "city": "Dublin", "courses": ["Inglês Geral", "Inglês Executivo", "Teacher Training"], "price_per_week": 300, "currency": "EUR", "rating": 4.7, "amenities": ["WiFi", "Biblioteca", "Jardim", "Cantina"], "description": "Escola premium com campus próprio"},
            # Ireland - Cork
            {"id": str(uuid.uuid4()), "name": "Cork English College", "country": "Irlanda", "city": "Cork", "courses": ["Inglês Geral", "Cambridge", "IELTS"], "price_per_week": 220, "currency": "EUR", "rating": 4.5, "amenities": ["WiFi", "Cafeteria"], "description": "Escola tradicional na segunda maior cidade da Irlanda"},
            # Malta
            {"id": str(uuid.uuid4()), "name": "EC Malta", "country": "Malta", "city": "St. Julian's", "courses": ["Inglês Geral", "Inglês Intensivo", "30+"], "price_per_week": 200, "currency": "EUR", "rating": 4.4, "amenities": ["WiFi", "Piscina", "Terraço"], "description": "Campus moderno com vista para o mar"},
            {"id": str(uuid.uuid4()), "name": "BELS Malta", "country": "Malta", "city": "St. Paul's Bay", "courses": ["Inglês Geral", "Business English"], "price_per_week": 160, "currency": "EUR", "rating": 4.3, "amenities": ["WiFi", "Praia próxima"], "description": "Escola boutique em área tranquila"},
            {"id": str(uuid.uuid4()), "name": "Sprachcaffe Malta", "country": "Malta", "city": "St. Julian's", "courses": ["Inglês Geral", "Intensivo"], "price_per_week": 180, "currency": "EUR", "rating": 4.2, "amenities": ["WiFi", "Piscina", "Clube"], "description": "Resort de idiomas com vida social ativa"},
            # Canada
            {"id": str(uuid.uuid4()), "name": "ILAC Toronto", "country": "Canadá", "city": "Toronto", "courses": ["Inglês Geral", "Pathway", "IELTS"], "price_per_week": 320, "currency": "CAD", "rating": 4.6, "amenities": ["WiFi", "Lounge", "Career Services"], "description": "Uma das maiores escolas do Canadá"},
            {"id": str(uuid.uuid4()), "name": "ILSC Vancouver", "country": "Canadá", "city": "Vancouver", "courses": ["Inglês Geral", "Business English", "Cambridge"], "price_per_week": 340, "currency": "CAD", "rating": 4.5, "amenities": ["WiFi", "Biblioteca", "Atividades"], "description": "Escola renomada com diversos programas"},
            # Australia
            {"id": str(uuid.uuid4()), "name": "Kaplan Sydney", "country": "Austrália", "city": "Sydney", "courses": ["Inglês Geral", "IELTS", "Cambridge"], "price_per_week": 380, "currency": "AUD", "rating": 4.5, "amenities": ["WiFi", "Lounge", "Biblioteca"], "description": "Campus no coração de Sydney"},
            {"id": str(uuid.uuid4()), "name": "Navitas Melbourne", "country": "Austrália", "city": "Melbourne", "courses": ["Inglês Geral", "EAP", "IELTS"], "price_per_week": 360, "currency": "AUD", "rating": 4.4, "amenities": ["WiFi", "Café", "Suporte"], "description": "Escola com foco em progressão acadêmica"},
        ]
        await db.schools.insert_many(schools_data)
        logger.info(f"Seeded {len(schools_data)} schools")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
