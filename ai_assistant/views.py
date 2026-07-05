from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.views.generic import TemplateView, ListView, FormView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.db import connection

from accounts.decorators import RoleRequiredMixin
from students.models import Student
from academics.models import Department, Course
from .models import AIConfiguration, AIChatMessage, AIAuditLog
from .forms import AIConfigForm
from .services import AIServiceLayer, PredictiveIntelligenceService, RecommendationEngine, NaturalLanguageSearchParser

from django.utils.html import escape
from ai_assistant.services.ai_service import AIService

def db_check(request):
    return HttpResponse(connection.settings_dict["ENGINE"])

# ----------------- AI CHAT API -----------------
class AIChatSendView(LoginRequiredMixin, View):
    def post(self, request):
        user_message = request.POST.get('message', '').strip()
        
        # 1. Validation: reject empty
        if not user_message:
            return JsonResponse({'status': 'error', 'message': 'Message cannot be empty.'}, status=400)

        # 2. Validation: limit length to 500 characters to prevent abuse/spam
        if len(user_message) > 500:
            return JsonResponse({'status': 'error', 'message': 'Message exceeds length limit of 500 characters.'}, status=400)

        # 3. Input Sanitization (XSS prevention)
        sanitized_message = escape(user_message)

        # 4. Protect configuration check
        config = AIConfiguration.get_config()
        if not config.is_enabled:
            return JsonResponse({
                'status': 'error',
                'message': 'AI Assistant is currently offline. Admin can activate it from settings.'
            })

        # Save user message
        user_chat = AIChatMessage.objects.create(
            user=request.user, 
            role='user', 
            message=sanitized_message
        )

        # 5. Call service layer securely with database awareness
        try:
            from .services import CollegeAIService
            service_result = CollegeAIService.process_secure_chat(request.user, sanitized_message)
            
            if service_result['status'] == 'success':
                bot_response = service_result['message']
            else:
                bot_response = service_result.get('message', 'A model parsing issue occurred.')
        except Exception as e:
            import traceback
            traceback.print_exc()

            return JsonResponse({
                "status": "error",
                "message": str(e)
            }, status=500)

        # Save bot response
        bot_chat = AIChatMessage.objects.create(
            user=request.user, 
            role='assistant', 
            message=bot_response
        )

        return JsonResponse({
            'status': 'success', 
            'message': bot_response,
            'timestamp': bot_chat.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        })


class AIChatHistoryView(LoginRequiredMixin, View):
    def get(self, request):
        # Fetch last 50 messages for chat history
        msgs = AIChatMessage.objects.filter(user=request.user).order_by('timestamp')[:50]
        history = [
            {
                'role': m.role, 
                'message': m.message, 
                'timestamp': m.timestamp.strftime('%Y-%m-%d %H:%M:%S')
            } 
            for m in msgs
        ]
        return JsonResponse({'status': 'success', 'history': history})


class AIChatClearView(LoginRequiredMixin, View):
    def post(self, request):
        # Delete message log for user
        AIChatMessage.objects.filter(user=request.user).delete()
        return JsonResponse({'status': 'success', 'message': 'Chat history cleared successfully.'})


# ----------------- PERFORMANCE & RISK PREDICTIONS -----------------
class AIPredictionsView(LoginRequiredMixin, ListView):
    model = Student
    template_name = 'ai_assistant/predictions.html'
    context_object_name = 'students'
    paginate_by = 10

    def get_queryset(self):
        # If student, limit to themselves
        if self.request.user.role == 'STUDENT':
            student = getattr(self.request.user, 'student_profile', None)
            return Student.objects.filter(id=student.id) if student else Student.objects.none()
        
        # Staff: limit to department
        if self.request.user.role == 'STAFF':
            staff = getattr(self.request.user, 'staff_profile', None)
            if staff:
                return Student.objects.filter(department=staff.department)
        
        return Student.objects.filter(status='ACTIVE')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        student_list = context['students']
        
        # Bind predictions & risk levels dynamically
        predictions_data = []
        for s in student_list:
            perf = PredictiveIntelligenceService.predict_student_performance(s)
            risk = PredictiveIntelligenceService.analyze_attendance_risk(s)
            recs = RecommendationEngine.get_student_recommendations(s)
            predictions_data.append({
                'student': s,
                'gpa': perf['predicted_gpa'],
                'prob': perf['pass_probability'],
                'risk': risk['level'],
                'risk_pct': risk['pct'],
                'action': risk['action'],
                'recs': recs
            })
            
        context['predictions_list'] = predictions_data
        
        # Role-based recommendations summary
        if self.request.user.role == 'STUDENT':
            student = getattr(self.request.user, 'student_profile', None)
            if student:
                context['dashboard_recs'] = RecommendationEngine.get_student_recommendations(student)
        elif self.request.user.role == 'STAFF':
            staff = getattr(self.request.user, 'staff_profile', None)
            if staff:
                context['dashboard_recs'] = RecommendationEngine.get_staff_recommendations(staff)
        else:
            context['dashboard_recs'] = RecommendationEngine.get_admin_recommendations()
            
        return context


# ----------------- SMART NL SEARCH -----------------
class AISearchView(LoginRequiredMixin, TemplateView):
    template_name = 'ai_assistant/search.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        query = self.request.GET.get('q', '').strip()
        context['query'] = query
        
        if query:
            results, title = NaturalLanguageSearchParser.parse_and_query(query)
            context['results'] = results
            context['search_title'] = title
        return context


# ----------------- SMART ANALYTICS & INSIGHTS -----------------
class AIAnalyticsDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'ai_assistant/analytics.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Department performance averages
        depts = Department.objects.all()
        dept_stats = []
        for d in depts:
            courses = Course.objects.filter(department=d)
            students = Student.objects.filter(course__in=courses)
            
            # Predict average GPA
            gpas = []
            for s in students:
                perf = PredictiveIntelligenceService.predict_student_performance(s)
                gpas.append(perf['predicted_gpa'])
            avg_gpa = sum(gpas) / len(gpas) if gpas else 0.0
            dept_stats.append({
                'dept': d,
                'avg_gpa': round(avg_gpa, 2),
                'students_count': students.count()
            })
            
        context['dept_performance'] = dept_stats
        
        # Overall risk ratio
        total_active = Student.objects.filter(status='ACTIVE')
        high_risk = 0
        for s in total_active:
            risk = PredictiveIntelligenceService.analyze_attendance_risk(s)
            if risk['level'] == 'HIGH':
                high_risk += 1
                
        context['overall_high_risk_count'] = high_risk
        context['overall_active_count'] = total_active.count()
        return context


# ----------------- AI CONFIGURATION -----------------
class AIConfigView(LoginRequiredMixin, RoleRequiredMixin, FormView):
    template_name = 'ai_assistant/config.html'
    form_class = AIConfigForm
    success_url = reverse_lazy('ai_config')
    roles = ['SUPER_ADMIN']

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['instance'] = AIConfiguration.get_config()
        return kwargs

    def form_valid(self, form):
        form.save()
        messages.success(self.request, "AI configuration rules updated successfully.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['audit_logs'] = AIAuditLog.objects.all()[:15]
        return context


# ----------------- AI ASSISTANT DASHBOARD -----------------
class AIAssistantDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'ai_assistant/assistant_dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['suggested_prompts'] = [
            "What is my attendance percentage?",
            "Show my upcoming assignment deadlines",
            "Generate a leave letter for tomorrow",
            "Predict my GPA trend",
        ]
        return context


# ----------------- AI DOCUMENT GENERATION SUITE -----------------
import io
from django.db.models import Q
from django.views.generic import ListView, DetailView
from .models import AIDocument
from .services import DocumentGenerationService

class AIDocumentListView(LoginRequiredMixin, ListView):
    model = AIDocument
    template_name = 'ai_assistant/document_list.html'
    context_object_name = 'documents'
    paginate_by = 10

    def get_queryset(self):
        user = self.request.user
        if user.role == 'SUPER_ADMIN':
            qs = AIDocument.objects.select_related('user').all()
        else:
            qs = AIDocument.objects.filter(user=user)

        # Search query (Step 9)
        q = self.request.GET.get('q', '').strip()
        if q:
            qs = qs.filter(Q(title__icontains=q) | Q(content__icontains=q))

        doc_type = self.request.GET.get('doc_type', '').strip()
        if doc_type:
            qs = qs.filter(document_type=doc_type)

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['document_types'] = DocumentGenerationService.get_document_types_for_user(self.request.user)
        context['q'] = self.request.GET.get('q', '')
        context['doc_type'] = self.request.GET.get('doc_type', '')
        return context


class AIDocumentCreateView(LoginRequiredMixin, TemplateView):
    template_name = 'ai_assistant/document_create.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['document_types'] = DocumentGenerationService.get_document_types_for_user(self.request.user)
        context['tones'] = ['Formal', 'Professional', 'Friendly', 'Strict', 'Administrative']
        return context

    def post(self, request, *args, **kwargs):
        doc_type = request.POST.get('document_type', '').strip()
        tone = request.POST.get('tone', 'Formal').strip()
        details = request.POST.get('details', '').strip()

        if not doc_type or not details:
            messages.error(request, "Document type and details are required.")
            return self.get(request, *args, **kwargs)

        try:
            doc = DocumentGenerationService.generate_document(
                user=request.user,
                document_type=doc_type,
                tone=tone,
                request_details=details
            )
            messages.success(request, f"Document '{doc.title}' generated successfully!")
            return redirect('ai_document_preview', pk=doc.id)
        except PermissionDenied as e:
            messages.error(request, str(e))
            return self.get(request, *args, **kwargs)
        except Exception as e:
            messages.error(request, f"Failed to generate document: {str(e)}")
            return self.get(request, *args, **kwargs)


class AIDocumentPreviewView(LoginRequiredMixin, DetailView):
    model = AIDocument
    template_name = 'ai_assistant/document_preview.html'
    context_object_name = 'document'

    def get_object(self, queryset=None):
        doc = super().get_object(queryset)
        # Permission validation
        if self.request.user.role != 'SUPER_ADMIN' and doc.user != self.request.user:
            raise PermissionDenied("You are not authorized to view this document.")
        return doc


class AIDocumentRegenerateView(LoginRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        details = request.POST.get('details', '').strip()
        if not details:
            return JsonResponse({'status': 'error', 'message': 'Details are required for regeneration.'}, status=400)

        try:
            doc = DocumentGenerationService.regenerate_document(request.user, pk, details)
            return JsonResponse({
                'status': 'success',
                'content': doc.content,
                'regeneration_count': doc.regeneration_count
            })
        except PermissionDenied as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=403)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


class AIDocumentDownloadView(LoginRequiredMixin, View):
    def get(self, request, pk, *args, **kwargs):
        fmt = request.GET.get('format', 'txt').strip().lower()
        try:
            doc = AIDocument.objects.get(id=pk)
        except AIDocument.DoesNotExist:
            raise PermissionDenied("Document does not exist.")

        if request.user.role != 'SUPER_ADMIN' and doc.user != request.user:
            raise PermissionDenied("You are not authorized to download this document.")

        safe_title = doc.title.replace(" ", "_").lower()

        if fmt == 'pdf':
            buffer = io.BytesIO()
            DocumentGenerationService.write_pdf(doc.content, buffer)
            buffer.seek(0)
            return FileResponse(buffer, as_attachment=True, filename=f"{safe_title}.pdf")

        elif fmt == 'docx':
            buffer = io.BytesIO()
            DocumentGenerationService.write_docx(doc.content, buffer)
            buffer.seek(0)
            response = HttpResponse(buffer.getvalue(), content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
            response['Content-Disposition'] = f'attachment; filename="{safe_title}.docx"'
            return response

        else:
            response = HttpResponse(doc.content, content_type='text/plain; charset=utf-8')
            response['Content-Disposition'] = f'attachment; filename="{safe_title}.txt"'
            return response


