from django.urls import path
from . import views

urlpatterns = [
    path('', views.student_list, name='student_list'),
    path('create/', views.student_create, name='student_create'),
    path('update/<int:pk>/', views.student_update, name='student_update'),
    path('delete/<int:pk>/', views.student_delete, name='student_delete'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('marks/<int:pk>/', views.marks_detail, name='marks_detail'),
    path('marks/add/<int:student_pk>/', views.marks_create, name='marks_create'),
    path('marks/edit/<int:pk>/', views.marks_update, name='marks_update'),
    path('marks/delete/<int:pk>/', views.marks_delete, name='marks_delete'),
    path('courses/', views.course_list, name='course_list'),
    path('courses/add/', views.course_create, name='course_create'),
    path('courses/edit/<int:pk>/', views.course_update, name='course_update'),
    path('courses/delete/<int:pk>/', views.course_delete, name='course_delete'),
    path('staff/', views.staff_list, name='staff_list_admin'),
    path('staff/add/', views.staff_create, name='staff_create'),
    path('staff/<int:user_pk>/edit/', views.staff_update, name='staff_update'),
    path('staff/<int:user_pk>/delete/', views.staff_delete, name='staff_delete'),
]