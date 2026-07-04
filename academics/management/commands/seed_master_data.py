import datetime
from django.core.management.base import BaseCommand
from django.db import transaction
from academics.models import AcademicYear, Department, Course, Semester, Section

class Command(BaseCommand):
    help = "Seeds master academic data (Academic Year, Departments, Courses, Semesters, Sections) idempotently."

    def handle(self, *args, **options):
        self.stdout.write("Starting database seeding...")
        
        try:
            with transaction.atomic():
                # 1. Seed Academic Year
                self.stdout.write("Seeding Academic Year...")
                academic_year, created = AcademicYear.objects.get_or_create(
                    academic_year='2026-2027',
                    defaults={
                        'start_date': datetime.date(2026, 6, 1),
                        'end_date': datetime.date(2027, 5, 31),
                        'is_active': False
                    }
                )
                
                if not academic_year.is_active:
                    # Deactivate other active years to prevent clean() validation error
                    AcademicYear.objects.filter(is_active=True).exclude(pk=academic_year.pk).update(is_active=False)
                    academic_year.is_active = True
                    academic_year.save()
                    self.stdout.write(self.style.SUCCESS("Academic Year '2026-2027' is set to ACTIVE."))
                else:
                    self.stdout.write("Academic Year '2026-2027' already active.")

                # 2. Seed Departments
                departments_data = [
                    ("CSE", "Computer Science & Engineering"),
                    ("IT", "Information Technology"),
                    ("ECE", "Electronics & Communication Engineering"),
                    ("EEE", "Electrical & Electronics Engineering"),
                    ("MECH", "Mechanical Engineering"),
                    ("CIVIL", "Civil Engineering"),
                    ("AIDS", "Artificial Intelligence & Data Science"),
                    ("AIML", "Artificial Intelligence & Machine Learning"),
                    ("MCA", "Master of Computer Applications"),
                    ("MBA", "Master of Business Administration"),
                ]
                
                departments_map = {}
                for code, name in departments_data:
                    dept, created = Department.objects.get_or_create(
                        code=code,
                        defaults={"name": name, "status": "ACTIVE"}
                    )
                    departments_map[code] = dept
                    if created:
                        self.stdout.write(self.style.SUCCESS(f"Created Department: {name} ({code})"))
                    else:
                        self.stdout.write(f"Department already exists: {name} ({code})")

                # 3. Seed Courses
                courses_data = [
                    ("BTECH-CSE", "Bachelor of Technology in CSE", "CSE", 4, 8),
                    ("BTECH-IT", "Bachelor of Technology in IT", "IT", 4, 8),
                    ("BTECH-ECE", "Bachelor of Technology in ECE", "ECE", 4, 8),
                    ("BTECH-EEE", "Bachelor of Technology in EEE", "EEE", 4, 8),
                    ("BTECH-MECH", "Bachelor of Technology in MECH", "MECH", 4, 8),
                    ("BTECH-CIVIL", "Bachelor of Technology in CIVIL", "CIVIL", 4, 8),
                    ("BTECH-AIDS", "Bachelor of Technology in AIDS", "AIDS", 4, 8),
                    ("BTECH-AIML", "Bachelor of Technology in AIML", "AIML", 4, 8),
                    ("MCA", "Master of Computer Applications", "MCA", 2, 4),
                    ("MBA", "Master of Business Administration", "MBA", 2, 4),
                ]
                
                for code, name, dept_code, duration_years, total_semesters in courses_data:
                    dept = departments_map[dept_code]
                    course, created = Course.objects.get_or_create(
                        code=code,
                        defaults={
                            "name": name,
                            "department": dept,
                            "duration_years": duration_years,
                            "total_semesters": total_semesters,
                            "status": "ACTIVE"
                        }
                    )
                    if created:
                        self.stdout.write(self.style.SUCCESS(f"Created Course: {name} ({code})"))
                    else:
                        self.stdout.write(f"Course already exists: {name} ({code})")

                    # 4. Automatically create Semesters & Sections
                    for sem_num in range(1, total_semesters + 1):
                        semester, sem_created = Semester.objects.get_or_create(
                            course=course,
                            number=sem_num,
                            defaults={
                                "academic_year": academic_year,
                                "status": "ACTIVE"
                            }
                        )
                        if sem_created:
                            self.stdout.write(self.style.SUCCESS(f"  Created Semester {sem_num} for {code}"))

                        # 5. Automatically create Sections A, B, C
                        for sec_name in ["A", "B", "C"]:
                            section, sec_created = Section.objects.get_or_create(
                                semester=semester,
                                name=sec_name,
                                defaults={
                                    "department": dept,
                                    "capacity": 60
                                }
                            )
                            if sec_created:
                                self.stdout.write(self.style.SUCCESS(f"    Created Section {sec_name} for Sem {sem_num} ({code})"))

            self.stdout.write(self.style.SUCCESS("Database seeding completed successfully!"))
            
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Seeding failed: {str(e)}"))
            raise e
