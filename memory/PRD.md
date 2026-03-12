# Dublin Study - Plataforma de Intercâmbio Educacional

## Problema Original
Criação de um aplicativo completo de intercâmbio educacional com foco em Dublin, Irlanda, desenvolvido para conectar estudantes diretamente às escolas credenciadas, sem intermediários.

## Arquitetura
- **Backend**: FastAPI + MongoDB + Stripe (emergentintegrations)
- **Frontend**: React + Tailwind CSS + Shadcn UI
- **Auth**: JWT (email/senha) com 3 roles: student, school, admin
- **Payments**: Stripe (test mode)
- **Emails**: MOCKED (logged to console)

## User Personas
1. **Estudante Brasileiro** - Quer estudar inglês em Dublin
2. **Escola de Inglês** - Quer cadastrar cursos e receber matrículas
3. **Administrador** - Gerencia a plataforma, aprova escolas

## Core Requirements (Static)
- Catálogo de escolas com preços transparentes
- Cursos com duração, carga horária e requisitos
- Pagamento online integrado (Stripe)
- Notificação automática por e-mail após pagamento
- Guias de transporte público de Dublin
- Lista de órgãos governamentais
- Guia PPS Number, GNIB/IRP, Passaporte
- Interface multilíngue (PT/EN)
- Painel Admin para gerenciamento
- Área da Escola para gestão de cursos

## Implementado - Janeiro/Março 2026

### Fase 1 - MVP Estudante ✅
- Catálogo de escolas e cursos
- Fluxo de matrícula + pagamento Stripe
- Dashboard do estudante
- Guias (PPS, GNIB, Passaporte)
- Transporte público Dublin
- Interface bilíngue PT/EN

### Fase 2 - Admin + Escola ✅
- **Painel Admin** (/admin)
- **Área da Escola** (/school)
- **Registro de Escola** (/register-school)

### Fase 3 - Branding & Suporte ✅
- Logo STUFF Intercâmbio
- Página STUFF Dúvidas (/duvidas)
- Guia Carteira de Motorista Irlandesa

### Fase 4 - Chat Comunidade ✅
- Chat em Tempo Real (/chat)
- Moderação (Admin)

### Fase 5 - Stripe Connect para Escolas ✅
- Planos de Assinatura
- Dashboard de ganhos

### Fase 6 - Passaporte Digital do Estudante ✅ (Março 2026)
- **Passaporte Digital** (/passport)
  - Emissão automática após pagamento do curso
  - Dados do estudante (nome, foto, nacionalidade)
  - Dados da escola (nome, endereço, contato)
  - Informações do curso (nome, datas, duração, horário)
  - Número de matrícula único (STUFF-YYYY-XXXXX)
  - Status do estudante (Ativo/Inativo/Expirado)
  
- **QR Code de Verificação**
  - Página pública de verificação (/passport/verify/:token)
  - Exibe dados do estudante para terceiros
  - Confirmação de matrícula ativa
  
- **Documentos no Aplicativo**
  - Aba de documentos com:
    - Comprovante de Matrícula
    - Carta da Escola
    - Informações do Curso
    - Passaporte Digital
  
- **Serviços Úteis**
  - Links diretos para PPS, GNIB, NDLS, Revenue
  - Checklist de documentos necessários
  
- **Endpoints Backend (5 novos)**
  - GET /api/passport/my - Obter passaporte do usuário
  - GET /api/passport/all - Listar todos passaportes
  - GET /api/passport/verify/{token} - Verificação pública
  - PUT /api/passport/nationality - Atualizar nacionalidade
  - GET /api/passport/documents/{enrollment_id} - Listar documentos

### Credenciais de Teste
- **Admin**: admin@dublinstudy.com / admin123

### Backend Endpoints (54 total)
- Auth: register, register-school, login, me, profile, upload-avatar
- Schools: list, detail, courses (public)
- Courses: list, detail
- Enrollments: create, list, detail
- Payments: checkout, status, webhook
- Transport: routes
- Services: agencies
- Guides: pps, gnib, passport, driving-license
- Admin: stats, schools, users, enrollments, payments, approve/reject
- School: dashboard, profile, courses CRUD, enrollments, send-letter
- Contact: form submission
- Chat: ws, messages, online, ban-status, delete, ban, unban, bans
- Stripe Connect: plans, subscribe, status, subscription, earnings
- Plus: info, checkout, status, subscribers/count
- **Passport: my, all, verify, nationality, documents** (NEW)
- Seed

## Prioritized Backlog

### P0 - Próximos Passos
- [ ] Integração real de e-mail (SendGrid/Resend) - substituir mock
- [ ] Download do passaporte em PDF

### P1 - Importante
- [ ] Upload de carta PDF (não apenas URL)
- [ ] Edição de perfil da escola (imagem, facilities)
- [ ] Sistema de reviews/avaliações
- [ ] Notificações push

### P2 - Nice to Have
- [ ] Tela de splash com logo STUFF
- [ ] Página "Sobre" institucional
- [ ] Calculadora de custos de vida
- [ ] Novos guias (Revenue, aluguel de imóveis)
- [ ] Seção de depoimentos de estudantes
- [ ] PWA mobile
- [ ] Blog/artigos
- [ ] Mensagens privadas no chat (DM)
- [ ] Grupos de chat por escola/curso

## Tecnologias
- FastAPI 0.110.1
- React 19
- MongoDB (motor)
- Stripe (emergentintegrations)
- Tailwind CSS 3.4
- Shadcn UI
- lucide-react icons
- WebSockets (FastAPI native)
- emoji-picker-react
- **qrcode.react** - QR Code generation (NEW)
