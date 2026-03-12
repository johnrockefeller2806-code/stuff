# STUFF Intercâmbio - Plataforma de Intercâmbio Educacional

## Última Atualização: 12 de Março de 2026

## Problema Original
Plataforma completa de intercâmbio educacional para Dublin, Irlanda - conectando estudantes brasileiros diretamente às escolas credenciadas.

## Arquitetura
- **Backend**: FastAPI + MongoDB + Stripe
- **Frontend**: React 19 + Tailwind CSS + Shadcn UI
- **Auth**: JWT com 3 roles (student, school, admin)
- **Payments**: Stripe com Split 20/80 (STUFF/Escola)
- **Push**: Web Push Notifications (pywebpush)

---

## IMPLEMENTADO - Sessão 12/03/2026

### 1. Passaporte Digital Visual ✅
- **Rota**: `/passport/view/:token`
- Design estilo passaporte real (3 páginas)
- Capa: STUFF Intercâmbio - International Student
- Página de dados: Nome, nacionalidade, foto, datas
- Página do curso: Escola, curso, QR Code, status
- Verificação pública via QR Code

### 2. Sistema de Contrato Digital ✅
- **Rota**: `/contract/:enrollmentId`
- Geração automática do contrato com termos
- Assinatura via checkbox + área de desenho opcional
- Registro legal (IP, data, hora, user-agent)
- Email de confirmação (MOCK)

### 3. Split de Pagamento 20/80 ✅
- 20% taxa STUFF Intercâmbio
- 80% repasse direto para escola
- Cálculo automático exibido no contrato

### 4. Dashboard de Acompanhamento ✅
- **Rota**: `/enrollment/:enrollmentId`
- Timeline visual: Contrato → Pagamento → Passaporte → Carta
- Status em tempo real (Pendente/Ação Necessária/Processando/Concluído)
- Barra de progresso animada
- Botões de ação contextuais

### 5. Notificações Push ✅
- Service Worker configurado (`/public/sw.js`)
- Hook React `usePushNotifications.js`
- Componente `NotificationToggle.js`
- Banner de prompt no Dashboard
- Notificações automáticas:
  - Contrato assinado
  - Pagamento confirmado
  - Passaporte pronto
  - Carta em processamento

### 6. Emails Automáticos (MOCK) ✅
- Contrato assinado
- Pagamento confirmado (com detalhes do split)
- Passaporte Digital pronto (com link)
- Carta da escola em processamento

---

## ENDPOINTS NOVOS

### Passaporte Digital
- `GET /api/passport/my` - Obter passaporte do usuário
- `GET /api/passport/view/:token` - Visualizar passaporte (público)
- `GET /api/passport/verify/:token` - Verificar passaporte (público)
- `POST /api/passport/simulate-payment` - Simular pagamento (teste)

### Contrato
- `GET /api/contract/:enrollmentId` - Obter contrato
- `POST /api/contract/:enrollmentId/sign` - Assinar contrato

### Fluxo de Matrícula
- `POST /api/enrollment/full-flow` - Criar matrícula + contrato
- `POST /api/enrollment/:id/simulate-full-flow` - Simular fluxo completo

### Push Notifications
- `GET /api/push/vapid-key` - Chave pública VAPID
- `POST /api/push/subscribe` - Registrar dispositivo
- `DELETE /api/push/unsubscribe` - Cancelar assinatura
- `GET /api/push/status` - Verificar status

---

## CREDENCIAIS DE TESTE

### Usuários
- **Admin**: admin@dublinstudy.com / admin123
- **Teste**: tracker.test@gmail.com / Test123!

### URLs de Teste
- Passaporte: `https://thirsty-knuth-2.preview.emergentagent.com/passport/view/335fd3a7-6029-41ea-8822-8dfc33c7ff0a`

---

## PRÓXIMAS INTEGRAÇÕES (Precisa API Keys)

### P0 - Crítico
- [ ] **Dropbox Sign** - Assinatura digital com validade jurídica
- [ ] **Resend** - Envio de emails reais
- [ ] **Onfido** - Reconhecimento facial (login + periódico)

### P1 - Importante
- [ ] **Twilio WhatsApp** - Notificações por WhatsApp
- [ ] Stripe Connect real para split
- [ ] Download do passaporte em PDF

### P2 - Nice to Have
- [ ] PWA completo
- [ ] Notificações por SMS

---

## TECNOLOGIAS UTILIZADAS
- FastAPI 0.110.1
- React 19
- MongoDB (motor)
- Stripe (emergentintegrations)
- Tailwind CSS 3.4
- Shadcn UI
- lucide-react
- qrcode.react
- pywebpush
- WebSockets

---

## NOTAS PARA PRÓXIMA SESSÃO

1. **Para integrar Dropbox Sign**: Criar conta em https://app.hellosign.com e obter API Key + Client ID

2. **Para integrar Resend**: Criar conta em https://resend.com e obter API Key

3. **Para integrar Onfido**: Criar conta em https://dashboard.onfido.com e obter API Token

4. **Fluxo desejado pelo cliente**:
   - Verificação facial no primeiro login
   - Verificação facial periódica (diário/semanal)
   - Bloqueio total se não passar na verificação
