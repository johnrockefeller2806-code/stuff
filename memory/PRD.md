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

## Implementado - Janeiro 2025

### Fase 1 - MVP Estudante ✅
- Catálogo de escolas e cursos
- Fluxo de matrícula + pagamento Stripe
- Dashboard do estudante
- Guias (PPS, GNIB, Passaporte)
- Transporte público Dublin
- Interface bilíngue PT/EN

### Fase 2 - Admin + Escola ✅
- **Painel Admin** (/admin)
  - Dashboard com estatísticas
  - Aprovar/rejeitar escolas
  - Ver todos usuários
  - Ver todas matrículas
  - Ver todos pagamentos
  
- **Área da Escola** (/school)
  - Dashboard com estatísticas
  - CRUD de cursos
  - Ver matrículas recebidas
  - Enviar carta de aceitação
  - Perfil da escola

- **Registro de Escola** (/register-school)
  - Cadastro de nova escola
  - Status pendente até aprovação admin

### Credenciais de Teste
- **Admin**: admin@dublinstudy.com / admin123

### Backend Endpoints (34 total)
- Auth: register, register-school, login, me
- Schools: list, detail, courses (public)
- Courses: list, detail
- Enrollments: create, list, detail
- Payments: checkout, status, webhook
- Transport: routes
- Services: agencies
- Guides: pps, gnib, passport
- Admin: stats, schools, users, enrollments, payments, approve/reject
- School: dashboard, profile, courses CRUD, enrollments, send-letter
- Seed

## Prioritized Backlog

### P0 - Próximos Passos
- [ ] Integração real de e-mail (SendGrid/Resend)
- [ ] Stripe Connect (pagamento direto para escola + comissão)

### P1 - Importante
- [ ] Upload de carta PDF (não apenas URL)
- [ ] Edição de perfil da escola (imagem, facilities)
- [ ] Sistema de reviews/avaliações
- [ ] Notificações push

### P2 - Nice to Have
- [ ] Chat/suporte integrado
- [ ] Calculadora de custos de vida
- [ ] PWA mobile
- [ ] Blog/artigos

## Tecnologias
- FastAPI 0.110.1
- React 19
- MongoDB (motor)
- Stripe (emergentintegrations)
- Tailwind CSS 3.4
- Shadcn UI
- lucide-react icons
