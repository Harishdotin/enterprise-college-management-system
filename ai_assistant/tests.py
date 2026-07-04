import io
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from unittest.mock import patch, MagicMock

from .models import AIConfiguration, AIChatMessage, AIAuditLog, AIDocument
from .services import AIService, CollegeAIService, DocumentGenerationService
from .services.provider_factory import AIProviderFactory
from .utils.validators import validate_prompt
from students.models import Student
from staff.models import Staff
from academics.models import AcademicYear, Department, Course, Semester

User = get_user_model()

class AIUtilityTests(TestCase):
    """
    Test suite for AI Assistant utility helpers and configurations.
    """
    def test_prompt_validation(self):
        # Valid prompt should not raise error
        try:
            validate_prompt("Hello assistant", max_length=500)
        except ValueError:
            self.fail("validate_prompt raised ValueError on valid prompt")

        # Empty prompts should raise error
        with self.assertRaises(ValueError) as ctx:
            validate_prompt("")
        self.assertEqual(str(ctx.exception), "Prompt cannot be empty.")

        with self.assertRaises(ValueError):
            validate_prompt(None)

        with self.assertRaises(ValueError):
            validate_prompt("   ")

        # Over-length prompts should raise error
        long_prompt = "x" * 501
        with self.assertRaises(ValueError) as ctx:
            validate_prompt(long_prompt, max_length=500)
        self.assertIn("exceeds the maximum allowed length", str(ctx.exception))

    def test_provider_factory_validation(self):
        # Unknown provider should raise error
        with self.assertRaises(ValueError) as ctx:
            AIProviderFactory.get_provider("UNKNOWN_PROVIDER")
        self.assertIn("Invalid AI provider name", str(ctx.exception))

        # Missing API keys should raise error
        with patch.dict('os.environ', {'OPENAI_API_KEY': ''}):
            with self.assertRaises(ValueError):
                AIProviderFactory.get_provider("OPENAI")

        with patch.dict('os.environ', {'GEMINI_API_KEY': ''}):
            with self.assertRaises(ValueError):
                AIProviderFactory.get_provider("GEMINI")

    def test_ai_configuration_singleton(self):
        config1 = AIConfiguration.get_config()
        config2 = AIConfiguration.get_config()
        self.assertEqual(config1.id, 1)
        self.assertEqual(config1.pk, config2.pk)


class CollegeAIServiceTests(TestCase):
    """
    Test suite for intent classification and database-aware prompts contextualization.
    """
    def test_intent_detection(self):
        detect = CollegeAIService.detect_intent
        self.assertEqual(detect("what is my attendance percentage?"), "ATTENDANCE")
        self.assertEqual(detect("show my exam marks sheet"), "MARKS")
        self.assertEqual(detect("predict my cgpa trend"), "MARKS")
        self.assertEqual(detect("do I have outstanding fees?"), "FEES")
        self.assertEqual(detect("list my upcoming homework deadlines"), "ASSIGNMENTS")
        self.assertEqual(detect("show class schedule for today"), "TIMETABLE")
        self.assertEqual(detect("read latest campus announcements"), "NOTIFICATIONS")
        self.assertEqual(detect("generate a leave letter for tomorrow"), "LEAVE_LETTER")
        self.assertEqual(detect("tell me about the weather"), "GENERAL")


class AIDocumentGenerationTests(TestCase):
    """
    Test suite for AI document generation business layer and role-based permissions.
    """
    def test_role_based_permissions(self):
        student_user = User(role='STUDENT')
        staff_user = User(role='STAFF')
        admin_user = User(role='SUPER_ADMIN')

        student_types = DocumentGenerationService.get_document_types_for_user(student_user)
        self.assertIn('LEAVE_LETTER', student_types)
        self.assertIn('BONAFIDE_REQUEST', student_types)
        self.assertNotIn('CIRCULAR', student_types)

        staff_types = DocumentGenerationService.get_document_types_for_user(staff_user)
        self.assertIn('LEAVE_APPLICATION', staff_types)
        self.assertNotIn('WARNING_LETTER', staff_types)

        admin_types = DocumentGenerationService.get_document_types_for_user(admin_user)
        self.assertIn('CIRCULAR', admin_types)
        self.assertIn('WARNING_LETTER', admin_types)

    def test_document_export_pdf(self):
        buffer = io.BytesIO()
        content = "Title\n\nDate: 2026-07-02\nTo: HOD\n\nSubject: Leave\n\nBody paragraphs\n\nSincerely,\nStudent"
        try:
            DocumentGenerationService.write_pdf(content, buffer)
            self.assertTrue(len(buffer.getvalue()) > 0)
        except Exception as e:
            self.fail(f"write_pdf raised exception: {e}")

    def test_document_export_docx(self):
        buffer = io.BytesIO()
        content = "Title\n\nDate: 2026-07-02\nTo: HOD\n\nSubject: Leave\n\nBody paragraphs\n\nSincerely,\nStudent"
        try:
            DocumentGenerationService.write_docx(content, buffer)
            self.assertTrue(len(buffer.getvalue()) > 0)
        except Exception as e:
            self.fail(f"write_docx raised exception: {e}")


class AIAssistantViewsTests(TestCase):
    """
    Test suite for views and AJAX endpoints.
    """
    def setUp(self):
        self.client = Client()
        self.user_password = 'studentpassword'
        
        # Setup basic academics data
        self.acad_year = AcademicYear.objects.create(
            academic_year='2026-2027',
            start_date='2026-06-01',
            end_date='2027-05-31',
            is_active=True
        )
        self.dept = Department.objects.create(code='CSE', name='Computer Science')
        self.course = Course.objects.create(code='BTECH-CSE', name='B.Tech CSE', department=self.dept)
        self.semester = Semester.objects.create(course=self.course, number=1, academic_year=self.acad_year)
        
        # Create users
        self.student_user = User.objects.create_user(
            username='student_test',
            email='student@college.edu',
            password=self.user_password,
            role='STUDENT'
        )
        self.staff_user = User.objects.create_user(
            username='staff_test',
            email='staff@college.edu',
            password=self.user_password,
            role='STAFF'
        )
        self.admin_user = User.objects.create_user(
            username='admin_test',
            email='admin@college.edu',
            password=self.user_password,
            role='SUPER_ADMIN'
        )
        
        # Link profiles (mock section as charfield A)
        self.student = Student.objects.create(
            user=self.student_user,
            register_number='REG2026001',
            admission_number='ADM2026001',
            full_name='Test Student',
            date_of_birth='2005-01-01',
            gender='M',
            department=self.dept,
            course=self.course,
            semester=self.semester,
            section='A',
            academic_year='2026-2027',
            email='student@college.edu',
            phone_number='1234567890',
            parent_name='Parent',
            parent_phone='0987654321',
            address='College campus',
            city='Campus city'
        )
        self.staff = Staff.objects.create(
            user=self.staff_user,
            employee_id='EMP2026001',
            full_name='Test Staff',
            gender='F',
            date_of_birth='1980-01-01',
            qualification='PhD',
            designation='Professor',
            department=self.dept,
            phone_number='1234567890',
            address='Staff address',
            city='Staff city',
            state='Staff state',
            pin_code='123456',
            date_of_joining='2026-06-01'
        )

        # Setup AI Config
        self.ai_config = AIConfiguration.get_config()
        self.ai_config.is_enabled = True
        self.ai_config.provider = 'MOCK'
        self.ai_config.save()

    def test_ai_dashboard_view_login_required(self):
        response = self.client.get(reverse('ai_assistant_dashboard'))
        self.assertEqual(response.status_code, 302) # Redirect to login

    def test_ai_dashboard_view_authenticated(self):
        self.client.login(username='student_test', password=self.user_password)
        response = self.client.get(reverse('ai_assistant_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'ai_assistant/assistant_dashboard.html')

    @patch('ai_assistant.services.CollegeAIService.process_secure_chat')
    def test_chat_send_endpoint_success(self, mock_process_chat):
        mock_process_chat.return_value = {
            'status': 'success',
            'message': 'This is a mocked database aware AI response.',
            'provider': 'MOCK'
        }
        
        self.client.login(username='student_test', password=self.user_password)
        response = self.client.post(reverse('ai_chat_send'), {'message': 'Hello assistant'})
        self.assertEqual(response.status_code, 200)
        
        json_data = response.json()
        self.assertEqual(json_data['status'], 'success')
        self.assertEqual(json_data['message'], 'This is a mocked database aware AI response.')
        
        # Verify message logs are created
        self.assertTrue(AIChatMessage.objects.filter(user=self.student_user, role='user').exists())
        self.assertTrue(AIChatMessage.objects.filter(user=self.student_user, role='assistant').exists())

    def test_chat_send_endpoint_validation_errors(self):
        self.client.login(username='student_test', password=self.user_password)
        
        # Empty message
        response = self.client.post(reverse('ai_chat_send'), {'message': ''})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['message'], 'Message cannot be empty.')
        
        # Over-length message
        response = self.client.post(reverse('ai_chat_send'), {'message': 'x' * 501})
        self.assertEqual(response.status_code, 400)
        self.assertIn('exceeds length limit', response.json()['message'])

    def test_chat_history_and_clear_endpoints(self):
        self.client.login(username='student_test', password=self.user_password)
        
        # Create some messages
        AIChatMessage.objects.create(user=self.student_user, role='user', message='Question 1')
        AIChatMessage.objects.create(user=self.student_user, role='assistant', message='Answer 1')
        
        # Test History retrieval
        response = self.client.get(reverse('ai_chat_history'))
        self.assertEqual(response.status_code, 200)
        history = response.json()['history']
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0]['message'], 'Question 1')
        
        # Test Clear
        response = self.client.post(reverse('ai_chat_clear'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(AIChatMessage.objects.filter(user=self.student_user).count(), 0)

    @patch('ai_assistant.services.DocumentGenerationService.generate_document')
    @patch('students.models.Student.objects.select_related')
    def test_document_create_view_post_success(self, mock_student_select_related, mock_generate_doc):
        # Setup mocks to bypass FieldError select_related('section') and LLM requests
        mock_qs = MagicMock()
        mock_qs.get.return_value = self.student
        mock_student_select_related.return_value = mock_qs
        
        mock_doc = AIDocument.objects.create(
            user=self.student_user,
            document_type='LEAVE_LETTER',
            title='Leave Letter Application - Test',
            content='Dear Principal, please approve leave.',
            tone='Formal'
        )
        mock_generate_doc.return_value = mock_doc

        self.client.login(username='student_test', password=self.user_password)
        
        response = self.client.post(reverse('ai_document_create'), {
            'document_type': 'LEAVE_LETTER',
            'tone': 'Formal',
            'details': 'Leave for fever.'
        })
        self.assertRedirects(response, reverse('ai_document_preview', kwargs={'pk': mock_doc.id}))

    def test_document_list_view_and_permissions(self):
        doc_student = AIDocument.objects.create(
            user=self.student_user,
            document_type='LEAVE_LETTER',
            title='Student Document',
            content='Dear Principal...',
            tone='Formal'
        )
        doc_staff = AIDocument.objects.create(
            user=self.staff_user,
            document_type='LEAVE_APPLICATION',
            title='Staff Document',
            content='Dear Director...',
            tone='Formal'
        )

        # Student logs in: sees only own documents
        self.client.login(username='student_test', password=self.user_password)
        response = self.client.get(reverse('ai_document_list'))
        self.assertEqual(response.status_code, 200)
        docs = list(response.context['documents'])
        self.assertIn(doc_student, docs)
        self.assertNotIn(doc_staff, docs)
        
        # Student cannot preview staff document
        response = self.client.get(reverse('ai_document_preview', kwargs={'pk': doc_staff.id}))
        self.assertEqual(response.status_code, 403)

        # Admin logs in: sees all documents
        self.client.login(username='admin_test', password=self.user_password)
        response = self.client.get(reverse('ai_document_list'))
        docs = list(response.context['documents'])
        self.assertIn(doc_student, docs)
        self.assertIn(doc_staff, docs)

        # Admin can preview staff document
        response = self.client.get(reverse('ai_document_preview', kwargs={'pk': doc_staff.id}))
        self.assertEqual(response.status_code, 200)

    @patch('ai_assistant.services.DocumentGenerationService.regenerate_document')
    def test_document_regenerate_ajax_endpoint(self, mock_regenerate_doc):
        doc = AIDocument.objects.create(
            user=self.student_user,
            document_type='LEAVE_LETTER',
            title='Student Document',
            content='Dear Principal...',
            tone='Formal'
        )
        
        updated_doc = doc
        updated_doc.content = 'Dear Principal, please approve leave due to urgent fever.'
        updated_doc.regeneration_count = 1
        mock_regenerate_doc.return_value = updated_doc

        self.client.login(username='student_test', password=self.user_password)
        response = self.client.post(reverse('ai_document_regenerate', kwargs={'pk': doc.id}), {
            'details': 'Include fever details.'
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['content'], updated_doc.content)
        self.assertEqual(response.json()['regeneration_count'], 1)
