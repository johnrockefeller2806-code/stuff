import React, { useState } from 'react';
import { useLanguage } from '../context/LanguageContext';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { Button } from '../components/ui/button';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from '../components/ui/accordion';
import { 
  HelpCircle, 
  MessageCircle, 
  Send, 
  CheckCircle,
  GraduationCap,
  CreditCard,
  FileText,
  Plane,
  Home,
  Briefcase
} from 'lucide-react';
import { toast } from 'sonner';

const LOGO_URL = "https://customer-assets.emergentagent.com/job_dublin-study/artifacts/o9gnc0xi_WhatsApp%20Image%202026-01-11%20at%2023.59.07.jpeg";
const HERO_IMAGE_URL = "https://customer-assets.emergentagent.com/job_dublin-exchange/artifacts/498i1soq_WhatsApp%20Image%202026-01-12%20at%2000.30.29.jpeg";

export const StuffDuvidas = () => {
  const { language } = useLanguage();
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    subject: '',
    message: ''
  });
  const [submitted, setSubmitted] = useState(false);
  const [loading, setLoading] = useState(false);

  const faqs = [
    {
      category: language === 'pt' ? 'Sobre o Intercâmbio' : 'About Exchange',
      icon: GraduationCap,
      questions: [
        {
          q: language === 'pt' ? 'Quanto tempo dura um intercâmbio na Irlanda?' : 'How long does an exchange in Ireland last?',
          a: language === 'pt' 
            ? 'Os cursos variam de 8 a 25 semanas. O mais comum é o curso de 25 semanas, que permite trabalhar meio período (20h/semana durante aulas, 40h nas férias).'
            : 'Courses range from 8 to 25 weeks. The most common is the 25-week course, which allows part-time work (20h/week during classes, 40h during holidays).'
        },
        {
          q: language === 'pt' ? 'Preciso saber inglês para fazer intercâmbio?' : 'Do I need to know English to exchange?',
          a: language === 'pt'
            ? 'Não! As escolas aceitam alunos de todos os níveis, desde iniciante até avançado. Você fará um teste de nivelamento no primeiro dia.'
            : 'No! Schools accept students of all levels, from beginner to advanced. You will take a placement test on the first day.'
        },
        {
          q: language === 'pt' ? 'Qual a diferença entre a STUFF e uma agência tradicional?' : 'What is the difference between STUFF and a traditional agency?',
          a: language === 'pt'
            ? 'Na STUFF, você fala diretamente com a escola, sem intermediários. Isso significa preços mais baixos, transparência total e comunicação direta. Não cobramos comissões escondidas.'
            : 'At STUFF, you talk directly to the school, without intermediaries. This means lower prices, full transparency and direct communication. We do not charge hidden commissions.'
        }
      ]
    },
    {
      category: language === 'pt' ? 'Pagamento e Matrícula' : 'Payment and Enrollment',
      icon: CreditCard,
      questions: [
        {
          q: language === 'pt' ? 'Como funciona o pagamento?' : 'How does payment work?',
          a: language === 'pt'
            ? 'O pagamento é feito 100% online, de forma segura via Stripe. Você pode pagar com cartão de crédito internacional. Após a confirmação, você recebe um e-mail imediatamente.'
            : 'Payment is 100% online, securely via Stripe. You can pay with an international credit card. After confirmation, you receive an email immediately.'
        },
        {
          q: language === 'pt' ? 'Em quanto tempo recebo a carta da escola?' : 'How long does it take to receive the school letter?',
          a: language === 'pt'
            ? 'Após a confirmação do pagamento, a escola envia a carta oficial em até 5 dias úteis. Esta carta é necessária para seu processo de visto.'
            : 'After payment confirmation, the school sends the official letter within 5 business days. This letter is required for your visa process.'
        },
        {
          q: language === 'pt' ? 'Posso parcelar o pagamento?' : 'Can I pay in installments?',
          a: language === 'pt'
            ? 'O parcelamento depende do seu cartão de crédito. Algumas bandeiras oferecem parcelamento automático. Também aceitamos pagamento em duas parcelas em casos especiais.'
            : 'Installment payment depends on your credit card. Some brands offer automatic installments. We also accept payment in two installments in special cases.'
        }
      ]
    },
    {
      category: language === 'pt' ? 'Documentação' : 'Documentation',
      icon: FileText,
      questions: [
        {
          q: language === 'pt' ? 'Preciso de visto para estudar na Irlanda?' : 'Do I need a visa to study in Ireland?',
          a: language === 'pt'
            ? 'Brasileiros não precisam de visto prévio para cursos de até 90 dias. Para cursos mais longos, você entra como turista e faz o registro (GNIB/IRP) já na Irlanda.'
            : 'Brazilians do not need a prior visa for courses up to 90 days. For longer courses, you enter as a tourist and register (GNIB/IRP) in Ireland.'
        },
        {
          q: language === 'pt' ? 'O que é o GNIB/IRP?' : 'What is GNIB/IRP?',
          a: language === 'pt'
            ? 'É o registro de imigração obrigatório para estudantes não-europeus. Você precisa agendar no site do INIS e comparecer com seus documentos. O custo é €300.'
            : 'It is the mandatory immigration registration for non-European students. You need to book on the INIS website and attend with your documents. The cost is €300.'
        },
        {
          q: language === 'pt' ? 'O que é o PPS Number?' : 'What is the PPS Number?',
          a: language === 'pt'
            ? 'É como o CPF irlandês. Você precisa dele para trabalhar legalmente e para algumas questões fiscais. O processo é gratuito e você agenda online.'
            : 'It is like the Irish CPF. You need it to work legally and for some tax matters. The process is free and you book online.'
        }
      ]
    },
    {
      category: language === 'pt' ? 'Vida na Irlanda' : 'Life in Ireland',
      icon: Home,
      questions: [
        {
          q: language === 'pt' ? 'Quanto custa viver em Dublin?' : 'How much does it cost to live in Dublin?',
          a: language === 'pt'
            ? 'O custo médio mensal é de €800-1200, incluindo acomodação compartilhada (€400-700), alimentação (€200-300), transporte (€100) e lazer (€100-200).'
            : 'The average monthly cost is €800-1200, including shared accommodation (€400-700), food (€200-300), transport (€100) and leisure (€100-200).'
        },
        {
          q: language === 'pt' ? 'Posso trabalhar enquanto estudo?' : 'Can I work while studying?',
          a: language === 'pt'
            ? 'Sim! Com o visto de estudante (Stamp 2), você pode trabalhar 20 horas por semana durante as aulas e 40 horas nas férias (junho-setembro e dezembro-janeiro).'
            : 'Yes! With the student visa (Stamp 2), you can work 20 hours per week during classes and 40 hours during holidays (June-September and December-January).'
        },
        {
          q: language === 'pt' ? 'Como é o clima na Irlanda?' : 'What is the weather like in Ireland?',
          a: language === 'pt'
            ? 'O clima é temperado oceânico. Espere chuva frequente, temperaturas entre 5-20°C e pouca neve. Traga casacos impermeáveis e roupas em camadas!'
            : 'The climate is oceanic temperate. Expect frequent rain, temperatures between 5-20°C and little snow. Bring waterproof coats and layered clothing!'
        }
      ]
    },
    {
      category: language === 'pt' ? 'Trabalho' : 'Work',
      icon: Briefcase,
      questions: [
        {
          q: language === 'pt' ? 'É fácil encontrar trabalho em Dublin?' : 'Is it easy to find work in Dublin?',
          a: language === 'pt'
            ? 'Dublin tem muitas oportunidades, especialmente em hospitalidade, varejo e tecnologia. O salário mínimo é €12.70/hora. Ter inglês intermediário ajuda muito.'
            : 'Dublin has many opportunities, especially in hospitality, retail and technology. The minimum wage is €12.70/hour. Having intermediate English helps a lot.'
        },
        {
          q: language === 'pt' ? 'Preciso de currículo em inglês?' : 'Do I need a resume in English?',
          a: language === 'pt'
            ? 'Sim! Prepare um CV no formato irlandês (sem foto, 1-2 páginas). Muitas escolas oferecem workshops de CV gratuitos para ajudar os alunos.'
            : 'Yes! Prepare a CV in Irish format (no photo, 1-2 pages). Many schools offer free CV workshops to help students.'
        }
      ]
    }
  ];

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      const API_URL = process.env.REACT_APP_BACKEND_URL;
      const response = await fetch(`${API_URL}/api/contact`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      });
      
      if (!response.ok) {
        throw new Error('Failed to send message');
      }
      
      setSubmitted(true);
      toast.success(language === 'pt' ? 'Mensagem enviada com sucesso!' : 'Message sent successfully!');
    } catch (error) {
      console.error('Error submitting contact form:', error);
      toast.error(language === 'pt' ? 'Erro ao enviar mensagem. Tente novamente.' : 'Error sending message. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  return (
    <div className="min-h-screen bg-slate-50" data-testid="duvidas-page">
      {/* Header with Logo Only */}
      <div className="bg-gradient-to-br from-blue-900 to-blue-800 text-white py-16">
        <div className="max-w-7xl mx-auto px-6 md:px-12 lg:px-24">
          <div className="flex flex-col items-center text-center">
            <img 
              src={LOGO_URL} 
              alt="STUFF Intercâmbio" 
              className="h-24 md:h-32 w-auto object-contain bg-white rounded-2xl p-3 shadow-xl mb-6"
              data-testid="duvidas-logo"
            />
            <p className="text-blue-100 text-lg md:text-xl max-w-2xl">
              {language === 'pt' ? 'Tire todas as suas dúvidas sobre intercâmbio' : 'Get all your exchange questions answered'}
            </p>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 md:px-12 lg:px-24 py-12">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* FAQ Section */}
          <div className="lg:col-span-2 space-y-8">
            <div>
              <h2 className="font-serif text-2xl font-semibold text-slate-900 mb-2">
                {language === 'pt' ? 'Perguntas Frequentes' : 'Frequently Asked Questions'}
              </h2>
              <p className="text-slate-500">
                {language === 'pt' 
                  ? 'Encontre respostas para as dúvidas mais comuns sobre intercâmbio na Irlanda'
                  : 'Find answers to the most common questions about exchange in Ireland'}
              </p>
            </div>

            {faqs.map((section, sectionIndex) => (
              <Card key={sectionIndex} className="border-slate-100">
                <CardHeader className="pb-2">
                  <CardTitle className="font-serif flex items-center gap-2 text-lg">
                    <div className="p-2 bg-blue-100 rounded-lg">
                      <section.icon className="h-5 w-5 text-blue-700" />
                    </div>
                    {section.category}
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <Accordion type="single" collapsible className="w-full">
                    {section.questions.map((item, index) => (
                      <AccordionItem key={index} value={`item-${sectionIndex}-${index}`}>
                        <AccordionTrigger className="text-left text-sm font-medium hover:no-underline">
                          {item.q}
                        </AccordionTrigger>
                        <AccordionContent className="text-slate-600 text-sm">
                          {item.a}
                        </AccordionContent>
                      </AccordionItem>
                    ))}
                  </Accordion>
                </CardContent>
              </Card>
            ))}
          </div>

          {/* Contact Form */}
          <div className="lg:col-span-1">
            <div className="sticky top-24">
              <Card className="border-slate-100 shadow-lg">
                <CardHeader>
                  <CardTitle className="font-serif flex items-center gap-2">
                    <MessageCircle className="h-5 w-5 text-blue-600" />
                    {language === 'pt' ? 'Não encontrou sua dúvida?' : "Didn't find your question?"}
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {submitted ? (
                    <div className="text-center py-8">
                      <div className="w-16 h-16 bg-emerald-100 rounded-full flex items-center justify-center mx-auto mb-4">
                        <CheckCircle className="h-8 w-8 text-emerald-600" />
                      </div>
                      <h3 className="font-semibold text-slate-900 mb-2">
                        {language === 'pt' ? 'Mensagem Enviada!' : 'Message Sent!'}
                      </h3>
                      <p className="text-slate-500 text-sm mb-4">
                        {language === 'pt' 
                          ? 'Responderemos em até 24 horas úteis.'
                          : 'We will respond within 24 business hours.'}
                      </p>
                      <Button 
                        variant="outline" 
                        onClick={() => {
                          setSubmitted(false);
                          setFormData({ name: '', email: '', subject: '', message: '' });
                        }}
                      >
                        {language === 'pt' ? 'Enviar outra mensagem' : 'Send another message'}
                      </Button>
                    </div>
                  ) : (
                    <form onSubmit={handleSubmit} className="space-y-4">
                      <div className="space-y-2">
                        <Label htmlFor="name">{language === 'pt' ? 'Nome' : 'Name'}</Label>
                        <Input
                          id="name"
                          name="name"
                          value={formData.name}
                          onChange={handleChange}
                          required
                          className="h-10"
                          data-testid="contact-name"
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="email">Email</Label>
                        <Input
                          id="email"
                          name="email"
                          type="email"
                          value={formData.email}
                          onChange={handleChange}
                          required
                          className="h-10"
                          data-testid="contact-email"
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="subject">{language === 'pt' ? 'Assunto' : 'Subject'}</Label>
                        <Input
                          id="subject"
                          name="subject"
                          value={formData.subject}
                          onChange={handleChange}
                          required
                          className="h-10"
                          data-testid="contact-subject"
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="message">{language === 'pt' ? 'Mensagem' : 'Message'}</Label>
                        <Textarea
                          id="message"
                          name="message"
                          value={formData.message}
                          onChange={handleChange}
                          required
                          rows={4}
                          data-testid="contact-message"
                        />
                      </div>
                      <Button 
                        type="submit" 
                        className="w-full bg-blue-600 hover:bg-blue-500"
                        disabled={loading}
                        data-testid="contact-submit"
                      >
                        {loading ? (
                          language === 'pt' ? 'Enviando...' : 'Sending...'
                        ) : (
                          <>
                            <Send className="h-4 w-4 mr-2" />
                            {language === 'pt' ? 'Enviar Mensagem' : 'Send Message'}
                          </>
                        )}
                      </Button>
                    </form>
                  )}
                </CardContent>
              </Card>

              {/* Quick Contact */}
              <Card className="border-slate-100 mt-4">
                <CardContent className="p-4">
                  <p className="text-sm text-slate-500 mb-2">
                    {language === 'pt' ? 'Precisa de ajuda urgente?' : 'Need urgent help?'}
                  </p>
                  <a 
                    href="mailto:contato@stuffintercambio.com"
                    className="text-blue-600 hover:text-blue-700 font-medium text-sm"
                  >
                    contato@stuffintercambio.com
                  </a>
                </CardContent>
              </Card>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
