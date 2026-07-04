from typing import Any

class PromptBuilder:
    """
    PromptBuilder compiles modular system instructions (personas) and templates 
    for students, staff, admins, leave drafting, assignment aid, and summaries.
    """

    def get_system_prompt(self, role: str) -> str:
        """
        Resolve the system instruction based on role type.
        """
        role = role.upper()
        if role == "STUDENT":
            return (
                "You are an AI Student Assistant for our College Management System.\n"
                "Your objective is to provide friendly, clear, and encouraging academic advice.\n"
                "Focus on explaining grades, guidelines, timetables, and assignments, while maintaining a supportive student-mentor persona."
            )
        elif role == "STAFF" or role == "FACULTY":
            return (
                "You are an AI Faculty Assistant for our College Management System.\n"
                "Provide professional guidance, summary statistics, and administrative suggestions.\n"
                "Your tone should be formal, helpful, and concise, serving as a productivity aide."
            )
        elif role == "SUPER_ADMIN" or role == "ADMIN":
            return (
                "You are an AI Admin Assistant for our College Management System.\n"
                "Your objective is to provide executive decision support, financial insights overview, and database health advice.\n"
                "Tone: professional, authoritative, and data-centric."
            )
        elif role == "LEAVE_LETTER":
            return (
                "You are a formal document generator specializing in professional leave letters for college students and staff.\n"
                "Generate structurally correct, formal letters including placeholders where details are missing."
            )
        elif role == "ASSIGNMENT_HELP":
            return (
                "You are an educational tutor assisting users in understanding, planning, and structuring college assignments.\n"
                "Provide questions, study references, hints, and step-by-step guidance. Do not write the final answers directly."
            )
        elif role == "NOTICE_SUMMARY":
            return (
                "You are a summarization assistant. Condense raw campus announcements into bulleted notice updates.\n"
                "Extract dates, times, deadlines, and key points precisely."
            )
        else:
            return (
                "You are a helpful AI Assistant for our College Management System.\n"
                "Provide clear, accurate, and context-aware responses to queries regarding campus life, timetables, fees, and marks."
            )

    def student_assistant(self, query: str, context: str = "") -> str:
        return (
            f"Context Information:\n{context}\n\n"
            f"Student Query: {query}\n"
            f"Response:"
        )

    def faculty_assistant(self, query: str, context: str = "") -> str:
        return (
            f"Context Information:\n{context}\n\n"
            f"Faculty Query: {query}\n"
            f"Response:"
        )

    def admin_assistant(self, query: str, context: str = "") -> str:
        return (
            f"Context Information:\n{context}\n\n"
            f"Admin Query: {query}\n"
            f"Response:"
        )

    def leave_letter_generator(self, reason: str, start_date: str, end_date: str, recipient_name: str) -> str:
        return (
            f"Draft a formal college leave letter.\n"
            f"Recipient: {recipient_name}\n"
            f"Date Range: {start_date} to {end_date}\n"
            f"Reason: {reason}\n"
            f"Generate letter:"
        )

    def notice_summarizer(self, content: str) -> str:
        return (
            f"Please summarize the following campus announcement into a clean bulleted notice:\n\n"
            f"{content}"
        )

    def assignment_helper(self, topic: str, criteria: str = "") -> str:
        return (
            f"Topic: {topic}\n"
            f"Grading Criteria: {criteria}\n"
            f"Generate assignment guidance, hints, and structure guidelines:"
        )

    def attendance_insights(self, attendance_pct: float, trend: str = "") -> str:
        return (
            f"Student Attendance: {attendance_pct}%\n"
            f"Attendance Trend: {trend}\n"
            f"Analyze attendance risk level and provide recommendations:"
        )

    def marks_prediction(self, subjects_grades: str) -> str:
        return (
            f"Semester Grades Summary:\n{subjects_grades}\n"
            f"Predict upcoming academic semester GPA and grade performance:"
        )
