from django.contrib import admin
from .models import TimetableSlot

@admin.register(TimetableSlot)
class TimetableSlotAdmin(admin.ModelAdmin):
    list_display = ('day', 'start_time', 'end_time', 'subject', 'classroom', 'section', 'faculty')
    list_filter = ('day', 'classroom', 'faculty')
    search_fields = ('subject__name', 'subject__code', 'classroom')
