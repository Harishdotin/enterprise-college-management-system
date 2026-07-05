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

                # 2. Cleanup obsolete MECH and CIVIL departments and courses (renamed to ME and CE)
                # Since we checked that no students are using them, we can safely delete them.
                self.stdout.write("Cleaning up obsolete database entries...")
                Course.objects.filter(code__in=["BTECH-MECH", "BTECH-CIVIL"]).delete()
                Department.objects.filter(code__in=["MECH", "CIVIL"]).delete()

                # 3. Seed Departments
                departments_data = [
                    # Mandatory Engineering Departments
                    ("IT", "Information Technology"),
                    ("CSE", "Computer Science & Engineering"),
                    ("ECE", "Electronics & Communication Engineering"),
                    ("EEE", "Electrical & Electronics Engineering"),
                    ("ME", "Mechanical Engineering"),
                    ("CE", "Civil Engineering"),
                    # Additional Departments
                    ("AIDS", "Artificial Intelligence & Data Science"),
                    ("AIML", "Artificial Intelligence & Machine Learning"),
                    ("CSBS", "Computer Science & Business Systems"),
                    ("BME", "Biomedical Engineering"),
                    ("AERO", "Aeronautical Engineering"),
                    ("AUTO", "Automobile Engineering"),
                    ("MTRX", "Mechatronics Engineering"),
                    ("RA", "Robotics & Automation"),
                    ("CHE", "Chemical Engineering"),
                    # Keep MCA and MBA for existing data support
                    ("MCA", "Master of Computer Applications"),
                    ("MBA", "Master of Business Administration"),
                ]
                
                departments_map = {}
                for code, name in departments_data:
                    dept, created = Department.objects.get_or_create(
                        code=code,
                        defaults={"name": name, "status": "ACTIVE"}
                    )
                    # Update name if code exists but name is old/different
                    if not created and dept.name != name:
                        dept.name = name
                        dept.save()
                    departments_map[code] = dept
                    if created:
                        self.stdout.write(self.style.SUCCESS(f"Created Department: {name} ({code})"))
                
                # 4. Seed Degrees (Courses) and their semesters/sections
                degrees_data = [
                    ("BE", "Bachelor of Engineering", 4, 8),
                    ("BTECH", "Bachelor of Technology", 4, 8),
                    ("ME", "Master of Engineering", 2, 4),
                    ("MTECH", "Master of Technology", 2, 4),
                    ("DIPLOMA", "Diploma", 3, 6),
                    ("PHD", "Doctor of Philosophy", 3, 6),
                ]
                
                # Populate standard degrees for all engineering departments
                for code, dept_name in departments_data:
                    # MCA offers MCA, MBA offers MBA
                    if code == "MCA":
                        course_definitions = [("MCA", "Master of Computer Applications", 2, 4)]
                    elif code == "MBA":
                        course_definitions = [("MBA", "Master of Business Administration", 2, 4)]
                    else:
                        course_definitions = [
                            (deg_code, deg_fullname, duration, sem_count)
                            for deg_code, deg_fullname, duration, sem_count in degrees_data
                        ]
                    
                    dept = departments_map[code]
                    for deg_code, deg_fullname, duration, sem_count in course_definitions:
                        course_code = f"{deg_code}-{code}" if deg_code not in ["MCA", "MBA"] else deg_code
                        course_name = f"{deg_fullname} in {dept.name}" if deg_code not in ["MCA", "MBA"] else deg_fullname
                        
                        course, created = Course.objects.get_or_create(
                            code=course_code,
                            defaults={
                                "name": course_name,
                                "department": dept,
                                "duration_years": duration,
                                "total_semesters": sem_count,
                                "status": "ACTIVE"
                            }
                        )
                        # Sync course name if old BTECH names exist
                        if not created and course.name != course_name:
                            course.name = course_name
                            course.save()
                            
                        if created:
                            self.stdout.write(self.style.SUCCESS(f"Created Course: {course_name} ({course_code})"))

                        # 5. Automatically create Semesters & Sections
                        for sem_num in range(1, sem_count + 1):
                            semester, sem_created = Semester.objects.get_or_create(
                                course=course,
                                number=sem_num,
                                defaults={
                                    "academic_year": academic_year,
                                    "status": "ACTIVE"
                                }
                            )
                            
                            # Automatically create Sections A, B, C
                            for sec_name in ["A", "B", "C"]:
                                section, sec_created = Section.objects.get_or_create(
                                    semester=semester,
                                    name=sec_name,
                                    defaults={
                                        "department": dept,
                                        "capacity": 60
                                    }
                                )

            self.stdout.write(self.style.SUCCESS("Database seeding completed successfully!"))
            
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Seeding failed: {str(e)}"))
            raise e
