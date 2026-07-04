import io
import time
import os
import logging
from datetime import date
from typing import Any, Dict, Optional, Tuple
from django.utils import timezone
from django.core.exceptions import PermissionDenied

from accounts.models import User
from students.models import Student
from staff.models import Staff
from ai_assistant.models import AIDocument
from ai_assistant.services.ai_service import AIService

# Setup logger
logger = logging.getLogger("ai_assistant")

# Supported document categories and configurations
DOCUMENT_PERMISSIONS = {
    'STUDENT': ['LEAVE_LETTER', 'BONAFIDE_REQUEST', 'INTERNSHIP_REQUEST', 'SCHOLARSHIP_REQUEST'],
    'STAFF': ['LEAVE_APPLICATION', 'MEETING_MINUTES', 'INTERNAL_REPORT', 'CLASS_REPORT'],
    'SUPER_ADMIN': [
        'LEAVE_LETTER', 'BONAFIDE_REQUEST', 'INTERNSHIP_REQUEST', 'SCHOLARSHIP_REQUEST',
        'LEAVE_APPLICATION', 'MEETING_MINUTES', 'INTERNAL_REPORT', 'CLASS_REPORT',
        'CIRCULAR', 'OFFICIAL_NOTICE', 'EVENT_ANNOUNCEMENT', 'WARNING_LETTER'
    ]
}

DOCUMENT_TITLES = {
    'LEAVE_LETTER': 'Leave Letter Application',
    'BONAFIDE_REQUEST': 'Bonafide Certificate Request',
    'INTERNSHIP_REQUEST': 'Internship Permission Request',
    'SCHOLARSHIP_REQUEST': 'Scholarship Recommendation Request',
    'LEAVE_APPLICATION': 'Staff Leave Application Letter',
    'MEETING_MINUTES': 'Departmental Minutes of Meeting',
    'INTERNAL_REPORT': 'Internal Progress Report',
    'CLASS_REPORT': 'Academic Class Report',
    'CIRCULAR': 'Official Campus Circular',
    'OFFICIAL_NOTICE': 'Official Administration Notice',
    'EVENT_ANNOUNCEMENT': 'Campus Event Announcement',
    'WARNING_LETTER': 'Student Academic Warning Letter'
}

class DocumentGenerationService:
    """
    DocumentGenerationService securely resolves user contexts, coordinates LLM calls, 
    and handles file compilation for PDFs, Word files, and plain text.
    """

    @staticmethod
    def get_document_types_for_user(user: User) -> list:
        """
        Return the list of document types that this user is authorized to create.
        """
        role = user.role
        return DOCUMENT_PERMISSIONS.get(role, [])

    @classmethod
    def generate_document(cls, user: User, document_type: str, tone: str, request_details: str) -> AIDocument:
        """
        Verify permissions, gather DB details, call AI, save, and return the document object.
        """
        start_time = time.time()
        
        # 1. Permission Validation
        allowed_types = cls.get_document_types_for_user(user)
        if document_type not in allowed_types:
            raise PermissionDenied(f"Your role '{user.role}' is not authorized to create a '{document_type}' document.")

        # 2. Database Integration Context Gathering
        db_context, display_title = cls._gather_database_context(user, document_type)

        # 3. Build Prompt Template
        system_instruction = (
            "You are a professional document drafting assistant for our College Management System.\n"
            "Your task is to draft formal college documents based on context, user requests, and preferred tone.\n"
            "The generated document must follow this layout:\n"
            "----------------------------------\n"
            "[TITLE]\n\n"
            "Date: [Current Date]\n"
            "To: [Recipient / Designation / Department]\n\n"
            "Subject: [Clear summary of letter]\n\n"
            "Dear [Recipient Name],\n\n"
            "[Body Paragraphs - Professional, containing all context data and specific request details]\n\n"
            "Yours faithfully / Sincerely,\n"
            "[Signature Placeholder]\n"
            "[Designation / Registration Details]\n"
            "----------------------------------\n"
            "Do NOT include other conversational text or pleasantries outside the letter border. Output ONLY the complete drafted document."
        )

        prompt = (
            f"Document Type: {DOCUMENT_TITLES.get(document_type, 'Official Document')}\n"
            f"Tone: {tone}\n"
            f"Database Context:\n{db_context}\n"
            f"Specific Details Requested by User: {request_details}\n\n"
            f"Draft the document now:"
        )

        # 4. Generate Document Content via AI Service
        ai_service = AIService()
        service_result = ai_service.process_chat_query(
            user_name=user.username,
            raw_prompt=prompt,
            system_instruction=system_instruction
        )

        if service_result['status'] != 'success':
            raise RuntimeError(f"AI generation failed: {service_result.get('message', 'Unknown Error')}")

        document_content = service_result['message']
        execution_time_ms = int((time.time() - start_time) * 1000)

        # 5. Save Document to History
        doc = AIDocument.objects.create(
            user=user,
            document_type=document_type,
            title=f"{DOCUMENT_TITLES.get(document_type, 'Document')} - {timezone.now().strftime('%b %d, %Y')}",
            content=document_content,
            tone=tone,
            regeneration_count=0
        )

        # 6. Structured log
        logger.info(
            f"[DOCUMENT GENERATION] User: {user.username} | Type: {document_type} | "
            f"Tone: {tone} | Latency: {execution_time_ms}ms | Provider: {service_result.get('provider', 'GEMINI')}"
        )

        return doc

    @classmethod
    def regenerate_document(cls, user: User, document_id: int, request_details: str) -> AIDocument:
        """
        Regenerate content for an existing document, respecting ownership and incrementing counts.
        """
        start_time = time.time()
        
        # Verify ownership
        try:
            doc = AIDocument.objects.get(id=document_id)
        except AIDocument.DoesNotExist:
            raise PermissionDenied("Document does not exist.")

        if user.role != 'SUPER_ADMIN' and doc.user != user:
            raise PermissionDenied("You are not authorized to regenerate this document.")

        db_context, display_title = cls._gather_database_context(doc.user, doc.document_type)

        system_instruction = (
            "You are a professional document drafting assistant for our College Management System.\n"
            "Please revise the previous drafted document based on the request details."
        )

        prompt = (
            f"Original Draft:\n{doc.content}\n\n"
            f"Revision Details: {request_details}\n"
            f"Format requirements: Maintain same layout (Title, Date, To, Subject, Body, Signature)."
        )

        ai_service = AIService()
        service_result = ai_service.process_chat_query(
            user_name=user.username,
            raw_prompt=prompt,
            system_instruction=system_instruction
        )

        if service_result['status'] != 'success':
            raise RuntimeError(f"AI regeneration failed: {service_result.get('message', 'Unknown Error')}")

        doc.content = service_result['message']
        doc.regeneration_count += 1
        doc.save()

        execution_time_ms = int((time.time() - start_time) * 1000)
        logger.info(
            f"[DOCUMENT REGENERATION] User: {user.username} | ID: {doc.id} | "
            f"Count: {doc.regeneration_count} | Latency: {execution_time_ms}ms"
        )

        return doc

    @staticmethod
    def _gather_database_context(user: User, document_type: str) -> Tuple[str, str]:
        """
        Extract user records and college global variables securely.
        """
        college_name = "Apex Engineering College"
        principal_name = "Dr. Richard Branson"
        today_str = date.today().strftime('%B %d, %Y')
        
        context_lines = [
            f"- Current Date: {today_str}",
            f"- College Name: {college_name}",
            f"- Principal Name: {principal_name}"
        ]

        display_title = DOCUMENT_TITLES.get(document_type, "Official Document")

        # Student contextual metadata
        if user.role == 'STUDENT':
            try:
                student = Student.objects.select_related('department', 'course', 'semester', 'section').get(user=user)
                context_lines.extend([
                    f"- Student Name: {student.full_name}",
                    f"- Register Number: {student.register_number}",
                    f"- Department: {student.department.name} ({student.department.code})",
                    f"- Course: {student.course.name}",
                    f"- Semester: Semester {student.semester.number}",
                    f"- Section: {student.section.name}"
                ])
            except Student.DoesNotExist:
                context_lines.append(f"- Student Name: {user.get_full_name() or user.username}")
        
        # Staff context
        elif user.role == 'STAFF':
            try:
                staff = Staff.objects.select_related('department').get(user=user)
                context_lines.extend([
                    f"- Faculty Name: {staff.full_name}",
                    f"- Designation: {staff.designation}",
                    f"- Department: {staff.department.name} ({staff.department.code})"
                ])
            except Staff.DoesNotExist:
                context_lines.extend([
                    f"- Faculty Name: {user.get_full_name() or user.username}",
                    f"- Designation: Lecturer"
                ])

        # Admin context
        elif user.role == 'SUPER_ADMIN':
            context_lines.append(f"- Authorized Admin: {user.get_full_name() or user.username}")

        return "\n".join(context_lines), display_title

    # --- Export PDF, DOCX, TXT helpers ---

    @staticmethod
    def write_pdf(content: str, buffer: io.BytesIO) -> None:
        """
        Generate a professional formatted PDF document from string content using ReportLab.
        """
        from reportlab.lib.pagesizes import letter
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=54, leftMargin=54,
            topMargin=54, bottomMargin=54
        )

        styles = getSampleStyleSheet()
        
        # Define clean, professional custom styles
        body_style = ParagraphStyle(
            name='FormalBody',
            parent=styles['Normal'],
            fontSize=11,
            leading=16,
            textColor=colors.HexColor('#1F2937'),
            spaceAfter=12
        )

        story = []

        # Split content into paragraphs and append to story
        lines = content.strip().split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                story.append(Spacer(1, 10))
            else:
                # Basic escape HTML
                safe_line = line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                story.append(Paragraph(safe_line, body_style))
                
        doc.build(story)

    @staticmethod
    def write_docx(content: str, buffer: io.BytesIO) -> None:
        """
        Generate a Word Document (.docx) from string content using python-docx.
        """
        from docx import Document
        from docx.shared import Pt, Inches

        doc = Document()
        
        # Configure standard document margins
        sections = doc.sections
        for section in sections:
            section.top_margin = Inches(1)
            section.bottom_margin = Inches(1)
            section.left_margin = Inches(1)
            section.right_margin = Inches(1)

        # Style configurations
        style = doc.styles['Normal']
        font = style.font
        font.name = 'Arial'
        font.size = Pt(11)

        # Write lines
        lines = content.strip().split('\n')
        for line in lines:
            doc.add_paragraph(line.strip())

        doc.save(buffer)
