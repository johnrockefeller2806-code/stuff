import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import { useLanguage } from '../context/LanguageContext';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import { Skeleton } from '../components/ui/skeleton';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '../components/ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../components/ui/select';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '../components/ui/table';
import { 
  GraduationCap, 
  BookOpen,
  Users,
  Euro,
  Plus,
  Edit,
  Trash2,
  Send,
  CheckCircle,
  Clock,
  AlertCircle,
  Building2,
  FileText
} from 'lucide-react';
import { toast } from 'sonner';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export const SchoolDashboard = () => {
  const navigate = useNavigate();
  const { user, isSchool, loading: authLoading } = useAuth();
  const { language } = useLanguage();
  
  const [dashboard, setDashboard] = useState(null);
  const [courses, setCourses] = useState([]);
  const [enrollments, setEnrollments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');
  
  // Course dialog
  const [courseDialogOpen, setCourseDialogOpen] = useState(false);
  const [editingCourse, setEditingCourse] = useState(null);
  const [courseForm, setCourseForm] = useState({
    name: '',
    name_en: '',
    description: '',
    description_en: '',
    duration_weeks: 25,
    hours_per_week: 15,
    level: 'all_levels',
    price: 0,
    requirements: [],
    includes: [],
    start_dates: [],
    available_spots: 20
  });
  
  // Letter dialog
  const [letterDialogOpen, setLetterDialogOpen] = useState(false);
  const [selectedEnrollment, setSelectedEnrollment] = useState(null);
  const [letterUrl, setLetterUrl] = useState('');

  useEffect(() => {
    if (!authLoading && !isSchool) {
      navigate('/');
      return;
    }
    if (isSchool) {
      fetchData();
    }
  }, [isSchool, authLoading]);

  const fetchData = async () => {
    try {
      const [dashboardRes, coursesRes, enrollmentsRes] = await Promise.all([
        axios.get(`${API}/school/dashboard`),
        axios.get(`${API}/school/courses`),
        axios.get(`${API}/school/enrollments`)
      ]);
      setDashboard(dashboardRes.data);
      setCourses(coursesRes.data);
      setEnrollments(enrollmentsRes.data);
    } catch (error) {
      console.error('Error fetching school data:', error);
      toast.error('Erro ao carregar dados');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateCourse = () => {
    setEditingCourse(null);
    setCourseForm({
      name: '',
      name_en: '',
      description: '',
      description_en: '',
      duration_weeks: 25,
      hours_per_week: 15,
      level: 'all_levels',
      price: 0,
      requirements: [],
      includes: [],
      start_dates: [],
      available_spots: 20
    });
    setCourseDialogOpen(true);
  };

  const handleEditCourse = (course) => {
    setEditingCourse(course);
    setCourseForm({
      name: course.name,
      name_en: course.name_en,
      description: course.description,
      description_en: course.description_en,
      duration_weeks: course.duration_weeks,
      hours_per_week: course.hours_per_week,
      level: course.level,
      price: course.price,
      requirements: course.requirements || [],
      includes: course.includes || [],
      start_dates: course.start_dates || [],
      available_spots: course.available_spots
    });
    setCourseDialogOpen(true);
  };

  const handleSaveCourse = async () => {
    try {
      if (editingCourse) {
        await axios.put(`${API}/school/courses/${editingCourse.id}`, courseForm);
        toast.success('Curso atualizado!');
      } else {
        await axios.post(`${API}/school/courses`, courseForm);
        toast.success('Curso criado!');
      }
      setCourseDialogOpen(false);
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erro ao salvar curso');
    }
  };

  const handleDeleteCourse = async (courseId) => {
    if (!confirm('Tem certeza que deseja excluir este curso?')) return;
    try {
      await axios.delete(`${API}/school/courses/${courseId}`);
      toast.success('Curso excluído');
      fetchData();
    } catch (error) {
      toast.error('Erro ao excluir curso');
    }
  };

  const handleSendLetter = async () => {
    if (!selectedEnrollment || !letterUrl) return;
    try {
      await axios.put(
        `${API}/school/enrollments/${selectedEnrollment.id}/send-letter?letter_url=${encodeURIComponent(letterUrl)}`
      );
      toast.success('Carta enviada com sucesso!');
      setLetterDialogOpen(false);
      setLetterUrl('');
      setSelectedEnrollment(null);
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erro ao enviar carta');
    }
  };

  const openLetterDialog = (enrollment) => {
    setSelectedEnrollment(enrollment);
    setLetterUrl('');
    setLetterDialogOpen(true);
  };

  const getStatusBadge = (status) => {
    const config = {
      pending: { label: 'Pendente', className: 'bg-amber-100 text-amber-800', icon: Clock },
      paid: { label: 'Pago', className: 'bg-emerald-100 text-emerald-800', icon: CheckCircle },
      approved: { label: 'Aprovado', className: 'bg-emerald-100 text-emerald-800', icon: CheckCircle },
      active: { label: 'Ativo', className: 'bg-emerald-100 text-emerald-800', icon: CheckCircle },
      inactive: { label: 'Inativo', className: 'bg-slate-100 text-slate-800', icon: Clock },
    };
    const c = config[status] || config.pending;
    return (
      <Badge className={`${c.className} gap-1`}>
        <c.icon className="h-3 w-3" />
        {c.label}
      </Badge>
    );
  };

  const getLevelLabel = (level) => {
    const labels = {
      all_levels: 'Todos os níveis',
      beginner: 'Iniciante',
      intermediate: 'Intermediário',
      advanced: 'Avançado',
    };
    return labels[level] || level;
  };

  if (authLoading || loading) {
    return (
      <div className="min-h-screen bg-slate-50 py-12" data-testid="school-loading">
        <div className="max-w-7xl mx-auto px-6 md:px-12 lg:px-24">
          <Skeleton className="h-12 w-64 mb-8" />
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
            {[1, 2, 3, 4].map(i => <Skeleton key={i} className="h-32 rounded-xl" />)}
          </div>
          <Skeleton className="h-96 rounded-xl" />
        </div>
      </div>
    );
  }

  const school = dashboard?.school;
  const stats = dashboard?.stats;
  const isPending = school?.status === 'pending';

  return (
    <div className="min-h-screen bg-slate-50" data-testid="school-dashboard">
      {/* Header */}
      <div className="bg-emerald-900 text-white py-12">
        <div className="max-w-7xl mx-auto px-6 md:px-12 lg:px-24">
          <div className="flex items-center gap-3 mb-2">
            <div className="p-2 bg-emerald-700 rounded-lg">
              <Building2 className="h-6 w-6" />
            </div>
            <div>
              <h1 className="font-serif text-3xl md:text-4xl font-bold">
                {school?.name || 'Minha Escola'}
              </h1>
              {getStatusBadge(school?.status)}
            </div>
          </div>
          <p className="text-emerald-200">Gerencie seus cursos e matrículas</p>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 md:px-12 lg:px-24 py-8">
        {/* Pending Alert */}
        {isPending && (
          <Card className="border-amber-200 bg-amber-50 mb-8">
            <CardContent className="p-6 flex items-center gap-4">
              <AlertCircle className="h-8 w-8 text-amber-600" />
              <div>
                <h3 className="font-semibold text-amber-900">Aguardando Aprovação</h3>
                <p className="text-sm text-amber-700">
                  Sua escola está em análise. Você poderá criar cursos após a aprovação.
                </p>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 -mt-12 mb-8">
          <Card className="border-slate-100 shadow-lg" data-testid="stat-courses">
            <CardContent className="p-6 flex items-center gap-4">
              <div className="p-3 bg-blue-100 rounded-xl">
                <BookOpen className="h-6 w-6 text-blue-700" />
              </div>
              <div>
                <p className="text-sm text-slate-500">Cursos</p>
                <p className="text-2xl font-bold text-slate-900">{stats?.total_courses || 0}</p>
              </div>
            </CardContent>
          </Card>
          
          <Card className="border-slate-100 shadow-lg" data-testid="stat-enrollments">
            <CardContent className="p-6 flex items-center gap-4">
              <div className="p-3 bg-emerald-100 rounded-xl">
                <GraduationCap className="h-6 w-6 text-emerald-700" />
              </div>
              <div>
                <p className="text-sm text-slate-500">Matrículas</p>
                <p className="text-2xl font-bold text-slate-900">{stats?.total_enrollments || 0}</p>
              </div>
            </CardContent>
          </Card>
          
          <Card className="border-slate-100 shadow-lg" data-testid="stat-pending-letters">
            <CardContent className="p-6 flex items-center gap-4">
              <div className="p-3 bg-amber-100 rounded-xl">
                <FileText className="h-6 w-6 text-amber-700" />
              </div>
              <div>
                <p className="text-sm text-slate-500">Cartas Pendentes</p>
                <p className="text-2xl font-bold text-slate-900">{stats?.pending_letters || 0}</p>
              </div>
            </CardContent>
          </Card>
          
          <Card className="border-slate-100 shadow-lg" data-testid="stat-revenue">
            <CardContent className="p-6 flex items-center gap-4">
              <div className="p-3 bg-purple-100 rounded-xl">
                <Euro className="h-6 w-6 text-purple-700" />
              </div>
              <div>
                <p className="text-sm text-slate-500">Receita</p>
                <p className="text-2xl font-bold text-slate-900">
                  €{(stats?.total_revenue || 0).toLocaleString()}
                </p>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <TabsList className="bg-white border border-slate-100 p-1">
            <TabsTrigger value="overview" data-testid="tab-overview">Visão Geral</TabsTrigger>
            <TabsTrigger value="courses" data-testid="tab-courses">Cursos</TabsTrigger>
            <TabsTrigger value="enrollments" data-testid="tab-enrollments">
              Matrículas
              {stats?.pending_letters > 0 && (
                <Badge className="ml-2 bg-amber-500 text-white">{stats?.pending_letters}</Badge>
              )}
            </TabsTrigger>
          </TabsList>

          {/* Overview Tab */}
          <TabsContent value="overview">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* School Info */}
              <Card className="border-slate-100">
                <CardHeader>
                  <CardTitle className="font-serif">Informações da Escola</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <Label className="text-slate-500">Nome</Label>
                    <p className="font-medium">{school?.name}</p>
                  </div>
                  <div>
                    <Label className="text-slate-500">Endereço</Label>
                    <p className="font-medium">{school?.address}</p>
                  </div>
                  <div>
                    <Label className="text-slate-500">Telefone</Label>
                    <p className="font-medium">{school?.phone || '-'}</p>
                  </div>
                  <div>
                    <Label className="text-slate-500">Email</Label>
                    <p className="font-medium">{school?.email}</p>
                  </div>
                  {school?.accreditation?.length > 0 && (
                    <div>
                      <Label className="text-slate-500">Acreditações</Label>
                      <div className="flex flex-wrap gap-2 mt-1">
                        {school.accreditation.map((acc, i) => (
                          <Badge key={i} variant="secondary">{acc}</Badge>
                        ))}
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Recent Enrollments */}
              <Card className="border-slate-100">
                <CardHeader>
                  <CardTitle className="font-serif flex items-center gap-2">
                    <GraduationCap className="h-5 w-5" />
                    Matrículas Recentes
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {enrollments.slice(0, 5).map((enrollment) => (
                      <div key={enrollment.id} className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                        <div>
                          <p className="font-medium text-sm">{enrollment.user_name}</p>
                          <p className="text-xs text-slate-500">{enrollment.course_name}</p>
                        </div>
                        <div className="flex items-center gap-2">
                          {enrollment.status === 'paid' && !enrollment.letter_sent && (
                            <Button 
                              size="sm" 
                              variant="outline"
                              onClick={() => openLetterDialog(enrollment)}
                            >
                              <Send className="h-3 w-3 mr-1" />
                              Enviar Carta
                            </Button>
                          )}
                          {enrollment.letter_sent && (
                            <Badge className="bg-emerald-100 text-emerald-800">
                              <CheckCircle className="h-3 w-3 mr-1" />
                              Carta Enviada
                            </Badge>
                          )}
                          {getStatusBadge(enrollment.status)}
                        </div>
                      </div>
                    ))}
                    {enrollments.length === 0 && (
                      <p className="text-slate-500 text-center py-4">Nenhuma matrícula ainda</p>
                    )}
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* Courses Tab */}
          <TabsContent value="courses">
            <Card className="border-slate-100">
              <CardHeader className="flex flex-row items-center justify-between">
                <CardTitle className="font-serif">Meus Cursos</CardTitle>
                <Button 
                  onClick={handleCreateCourse}
                  disabled={isPending}
                  className="bg-emerald-900 hover:bg-emerald-800"
                  data-testid="create-course-btn"
                >
                  <Plus className="h-4 w-4 mr-2" />
                  Novo Curso
                </Button>
              </CardHeader>
              <CardContent>
                {courses.length === 0 ? (
                  <div className="text-center py-12">
                    <BookOpen className="h-12 w-12 text-slate-300 mx-auto mb-4" />
                    <p className="text-slate-500">Nenhum curso cadastrado</p>
                    {!isPending && (
                      <Button 
                        onClick={handleCreateCourse}
                        className="mt-4 bg-emerald-900 hover:bg-emerald-800"
                      >
                        <Plus className="h-4 w-4 mr-2" />
                        Criar Primeiro Curso
                      </Button>
                    )}
                  </div>
                ) : (
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Nome</TableHead>
                        <TableHead>Duração</TableHead>
                        <TableHead>Nível</TableHead>
                        <TableHead>Preço</TableHead>
                        <TableHead>Vagas</TableHead>
                        <TableHead>Status</TableHead>
                        <TableHead>Ações</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {courses.map((course) => (
                        <TableRow key={course.id} data-testid={`course-row-${course.id}`}>
                          <TableCell className="font-medium">{course.name}</TableCell>
                          <TableCell>{course.duration_weeks} semanas</TableCell>
                          <TableCell>{getLevelLabel(course.level)}</TableCell>
                          <TableCell>€{course.price.toLocaleString()}</TableCell>
                          <TableCell>{course.available_spots}</TableCell>
                          <TableCell>{getStatusBadge(course.status || 'active')}</TableCell>
                          <TableCell>
                            <div className="flex gap-2">
                              <Button 
                                size="sm" 
                                variant="outline"
                                onClick={() => handleEditCourse(course)}
                              >
                                <Edit className="h-4 w-4" />
                              </Button>
                              <Button 
                                size="sm" 
                                variant="outline"
                                className="text-red-600 hover:text-red-700"
                                onClick={() => handleDeleteCourse(course.id)}
                              >
                                <Trash2 className="h-4 w-4" />
                              </Button>
                            </div>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Enrollments Tab */}
          <TabsContent value="enrollments">
            <Card className="border-slate-100">
              <CardHeader>
                <CardTitle className="font-serif">Matrículas</CardTitle>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Aluno</TableHead>
                      <TableHead>Email</TableHead>
                      <TableHead>Curso</TableHead>
                      <TableHead>Início</TableHead>
                      <TableHead>Valor</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Carta</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {enrollments.map((enrollment) => (
                      <TableRow key={enrollment.id}>
                        <TableCell className="font-medium">{enrollment.user_name}</TableCell>
                        <TableCell>{enrollment.user_email}</TableCell>
                        <TableCell>{enrollment.course_name}</TableCell>
                        <TableCell>{new Date(enrollment.start_date).toLocaleDateString()}</TableCell>
                        <TableCell>€{enrollment.price.toLocaleString()}</TableCell>
                        <TableCell>{getStatusBadge(enrollment.status)}</TableCell>
                        <TableCell>
                          {enrollment.status === 'paid' && !enrollment.letter_sent ? (
                            <Button 
                              size="sm"
                              onClick={() => openLetterDialog(enrollment)}
                              className="bg-amber-600 hover:bg-amber-500"
                            >
                              <Send className="h-4 w-4 mr-1" />
                              Enviar
                            </Button>
                          ) : enrollment.letter_sent ? (
                            <Badge className="bg-emerald-100 text-emerald-800">
                              <CheckCircle className="h-3 w-3 mr-1" />
                              Enviada
                            </Badge>
                          ) : (
                            <span className="text-slate-400 text-sm">-</span>
                          )}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
                {enrollments.length === 0 && (
                  <p className="text-slate-500 text-center py-8">Nenhuma matrícula</p>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>

      {/* Course Dialog */}
      <Dialog open={courseDialogOpen} onOpenChange={setCourseDialogOpen}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="font-serif">
              {editingCourse ? 'Editar Curso' : 'Novo Curso'}
            </DialogTitle>
          </DialogHeader>
          
          <div className="space-y-4 py-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Nome (PT)</Label>
                <Input
                  value={courseForm.name}
                  onChange={(e) => setCourseForm({...courseForm, name: e.target.value})}
                  placeholder="Inglês Geral - 25 semanas"
                  data-testid="course-name"
                />
              </div>
              <div className="space-y-2">
                <Label>Nome (EN)</Label>
                <Input
                  value={courseForm.name_en}
                  onChange={(e) => setCourseForm({...courseForm, name_en: e.target.value})}
                  placeholder="General English - 25 weeks"
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label>Descrição (PT)</Label>
              <Textarea
                value={courseForm.description}
                onChange={(e) => setCourseForm({...courseForm, description: e.target.value})}
                rows={3}
              />
            </div>

            <div className="space-y-2">
              <Label>Descrição (EN)</Label>
              <Textarea
                value={courseForm.description_en}
                onChange={(e) => setCourseForm({...courseForm, description_en: e.target.value})}
                rows={3}
              />
            </div>

            <div className="grid grid-cols-3 gap-4">
              <div className="space-y-2">
                <Label>Duração (semanas)</Label>
                <Input
                  type="number"
                  value={courseForm.duration_weeks}
                  onChange={(e) => setCourseForm({...courseForm, duration_weeks: parseInt(e.target.value)})}
                />
              </div>
              <div className="space-y-2">
                <Label>Horas/Semana</Label>
                <Input
                  type="number"
                  value={courseForm.hours_per_week}
                  onChange={(e) => setCourseForm({...courseForm, hours_per_week: parseInt(e.target.value)})}
                />
              </div>
              <div className="space-y-2">
                <Label>Vagas</Label>
                <Input
                  type="number"
                  value={courseForm.available_spots}
                  onChange={(e) => setCourseForm({...courseForm, available_spots: parseInt(e.target.value)})}
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Nível</Label>
                <Select 
                  value={courseForm.level} 
                  onValueChange={(v) => setCourseForm({...courseForm, level: v})}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all_levels">Todos os níveis</SelectItem>
                    <SelectItem value="beginner">Iniciante</SelectItem>
                    <SelectItem value="intermediate">Intermediário</SelectItem>
                    <SelectItem value="advanced">Avançado</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Preço (EUR)</Label>
                <Input
                  type="number"
                  step="0.01"
                  value={courseForm.price}
                  onChange={(e) => setCourseForm({...courseForm, price: parseFloat(e.target.value)})}
                  data-testid="course-price"
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label>Datas de Início (uma por linha, formato YYYY-MM-DD)</Label>
              <Textarea
                value={courseForm.start_dates.join('\n')}
                onChange={(e) => setCourseForm({
                  ...courseForm, 
                  start_dates: e.target.value.split('\n').filter(d => d.trim())
                })}
                placeholder="2025-01-13&#10;2025-02-10&#10;2025-03-10"
                rows={3}
              />
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setCourseDialogOpen(false)}>
              Cancelar
            </Button>
            <Button 
              onClick={handleSaveCourse}
              className="bg-emerald-900 hover:bg-emerald-800"
              data-testid="save-course-btn"
            >
              {editingCourse ? 'Salvar' : 'Criar Curso'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Letter Dialog */}
      <Dialog open={letterDialogOpen} onOpenChange={setLetterDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="font-serif">Enviar Carta de Aceitação</DialogTitle>
            <DialogDescription>
              Para: {selectedEnrollment?.user_name} ({selectedEnrollment?.user_email})
            </DialogDescription>
          </DialogHeader>
          
          <div className="py-4 space-y-4">
            <div className="space-y-2">
              <Label>URL da Carta (PDF)</Label>
              <Input
                value={letterUrl}
                onChange={(e) => setLetterUrl(e.target.value)}
                placeholder="https://..."
                data-testid="letter-url"
              />
              <p className="text-xs text-slate-500">
                Insira o link para o PDF da carta de aceitação
              </p>
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setLetterDialogOpen(false)}>
              Cancelar
            </Button>
            <Button 
              onClick={handleSendLetter}
              disabled={!letterUrl}
              className="bg-emerald-900 hover:bg-emerald-800"
              data-testid="send-letter-btn"
            >
              <Send className="h-4 w-4 mr-2" />
              Enviar Carta
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};
