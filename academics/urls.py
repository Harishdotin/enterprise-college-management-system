from django.urls import path
from . import views

urlpatterns = [
    # Academic Years
    path('years/', views.AcademicYearListView.as_view(), name='year_list'),
    path('years/add/', views.AcademicYearCreateView.as_view(), name='year_add'),
    path('years/<int:pk>/edit/', views.AcademicYearUpdateView.as_view(), name='year_edit'),
    path('years/<int:pk>/delete/', views.AcademicYearDeleteView.as_view(), name='year_delete'),
    
    # Departments
    path('departments/', views.DepartmentListView.as_view(), name='department_list'),
    path('departments/add/', views.DepartmentCreateView.as_view(), name='department_add'),
    path('departments/<int:pk>/edit/', views.DepartmentUpdateView.as_view(), name='department_edit'),
    path('departments/<int:pk>/delete/', views.DepartmentDeleteView.as_view(), name='department_delete'),
    
    # Courses
    path('courses/', views.CourseListView.as_view(), name='course_list'),
    path('courses/add/', views.CourseCreateView.as_view(), name='course_add'),
    path('courses/<int:pk>/edit/', views.CourseUpdateView.as_view(), name='course_edit'),
    path('courses/<int:pk>/delete/', views.CourseDeleteView.as_view(), name='course_delete'),
    
    # Semesters
    path('semesters/', views.SemesterListView.as_view(), name='semester_list'),
    path('semesters/add/', views.SemesterCreateView.as_view(), name='semester_add'),
    path('semesters/<int:pk>/edit/', views.SemesterUpdateView.as_view(), name='semester_edit'),
    path('semesters/<int:pk>/delete/', views.SemesterDeleteView.as_view(), name='semester_delete'),
    
    # Sections
    path('sections/', views.SectionListView.as_view(), name='section_list'),
    path('sections/add/', views.SectionCreateView.as_view(), name='section_add'),
    path('sections/<int:pk>/edit/', views.SectionUpdateView.as_view(), name='section_edit'),
    path('sections/<int:pk>/delete/', views.SectionDeleteView.as_view(), name='section_delete'),
    
    # Subjects
    path('subjects/', views.SubjectListView.as_view(), name='subject_list'),
    path('subjects/add/', views.SubjectCreateView.as_view(), name='subject_add'),
    path('subjects/<int:pk>/edit/', views.SubjectUpdateView.as_view(), name='subject_edit'),
    path('subjects/<int:pk>/delete/', views.SubjectDeleteView.as_view(), name='subject_delete'),
    
    # Classes
    path('classes/', views.ClassListView.as_view(), name='class_list'),
    path('classes/add/', views.ClassCreateView.as_view(), name='class_add'),
    path('classes/<int:pk>/edit/', views.ClassUpdateView.as_view(), name='class_edit'),
    path('classes/<int:pk>/delete/', views.ClassDeleteView.as_view(), name='class_delete'),
    
    # Faculty Subject Assignment
    path('assignments/', views.FacultyAssignmentListView.as_view(), name='faculty_assignment_list'),
    path('assignments/add/', views.FacultyAssignmentCreateView.as_view(), name='faculty_assignment_add'),
    path('assignments/<int:pk>/edit/', views.FacultyAssignmentUpdateView.as_view(), name='faculty_assignment_edit'),
    path('assignments/<int:pk>/delete/', views.FacultyAssignmentDeleteView.as_view(), name='faculty_assignment_delete'),
]
