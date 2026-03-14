# STUFF Intercâmbio + DestinoAI - Product Requirements Document

## Original Problem Statement
O usuário criou duas aplicações:
1. **STUFF Intercâmbio** - Plataforma educacional para intercâmbio em Dublin
2. **DestinoAI** - Agente de IA para planejamento de intercâmbio

## What's Been Implemented

### STUFF Intercâmbio
- ✅ Google OAuth Login seguro via Emergent Auth
- ✅ Digital Student Passport multi-página
- ✅ Fluxo de matrícula end-to-end (mockado)
- ✅ Dashboard de progresso do estudante
- ✅ Web Push Notifications
- ✅ 25 escolas reais de Dublin no banco de dados
- ✅ Lista de escolas pública (sem paywall)

### DestinoAI (NOVO)
- ✅ Chat com GPT-4o via Emergent LLM Key
- ✅ Interface de chat moderna e responsiva
- ✅ Sugestões de perguntas pré-definidas
- ✅ Banco de dados de países (5 destinos)
- ✅ Banco de dados de escolas (8 escolas)
- ✅ Fallback responses quando LLM indisponível
- ✅ Histórico de sessões de chat
- ✅ Sistema de contexto com dados relevantes

## Core Features

### Authentication
- Google OAuth via Emergent Auth
- Session management with httpOnly cookies
- Role-based access (student, school, admin)

### DestinoAI Agent
- Conversational AI for study abroad planning
- Profile discovery (age, budget, duration, objectives)
- Destination recommendations
- School suggestions
- Cost calculator
- Document checklist generator
- Complete study plan creation

## Tech Stack
- **Frontend:** React, Tailwind CSS, Lucide Icons
- **Backend:** FastAPI, Motor (MongoDB async)
- **AI:** GPT-4o via emergentintegrations
- **Auth:** Emergent Google OAuth
- **Database:** MongoDB

## API Endpoints

### DestinoAI
- `POST /api/destinoai/chat` - Send message to AI
- `GET /api/destinoai/chat/{session_id}/history` - Get chat history
- `DELETE /api/destinoai/chat/{session_id}` - Clear session
- `GET /api/destinoai/countries` - List countries
- `GET /api/destinoai/schools` - List schools

### Auth
- `POST /api/auth/google/session` - Process Google OAuth
- `GET /api/auth/me` - Get current user
- `POST /api/auth/logout` - Logout

## Database Collections

### destinoai_countries
```json
{
  "id": "uuid",
  "name": "Irlanda",
  "name_en": "Ireland",
  "work_permitted": true,
  "work_hours": 20,
  "average_cost": 7500,
  "currency": "EUR",
  "popular_cities": ["Dublin", "Cork", "Galway"]
}
```

### destinoai_schools
```json
{
  "id": "uuid",
  "name": "Kaplan Dublin",
  "country": "Irlanda",
  "city": "Dublin",
  "courses": ["Inglês Geral", "IELTS"],
  "price_per_week": 280,
  "rating": 4.6
}
```

### destinoai_sessions
```json
{
  "session_id": "uuid",
  "messages": [{"role": "user/assistant", "content": "...", "timestamp": "..."}],
  "created_at": "ISO date"
}
```

## Prioritized Backlog

### P0 - Critical
- [x] Google Login seguro
- [x] DestinoAI MVP funcional

### P1 - High Priority
- [ ] Adicionar mais países e escolas ao banco de dados
- [ ] Gerar PDF do plano de intercâmbio
- [ ] Integração com WhatsApp (Meta Business API)

### P2 - Medium Priority
- [ ] Dashboard de agências
- [ ] CRM de estudantes
- [ ] Sistema de benefícios com parceiros

### P3 - Low Priority
- [ ] App mobile (React Native)
- [ ] Integração com vistos
- [ ] Marketplace de escolas

## Notes
- **Emergent LLM Key:** Budget pode precisar de recarga. Acesse Profile > Universal Key > Add Balance
- **Mocked Services:** Pagamentos (Stripe), Assinaturas digitais (Dropbox Sign), Emails (Resend) estão mockados

## Last Updated
March 14, 2026
