from django.urls import path
from . import views

urlpatterns = [
    path('grid/', views.TimetableListView.as_view(), name='timetable_grid'),
    path('slots/add/', views.TimetableSlotCreateView.as_view(), name='timetable_slot_add'),
    path('slots/<int:pk>/edit/', views.TimetableSlotUpdateView.as_view(), name='timetable_slot_edit'),
    path('slots/<int:pk>/delete/', views.TimetableSlotDeleteView.as_view(), name='timetable_slot_delete'),
]
