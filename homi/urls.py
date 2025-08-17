from django.urls import path
from . import views

urlpatterns = [
    # Registro y login de usuarios
    path('register/', views.register, name='register'),
    path('login/', views.login, name='login'),
    
    # Crear y unirse a casas
    path('create-household/', views.create_household, name='create_household'),
    path('join-household/', views.join_household, name='join_household'),
    
    # Crear perfil de usuario
    path('user-profile/', views.get_user_profile, name='user_profile'),
    
    # Gestión de casas
    path('current-household-info/', views.get_current_household_info, name='current_household_info'),
    path('leave-household/', views.leave_household, name='leave_household'),
    path('delete-household/', views.delete_household, name='delete_household'),
    
    # CRUD de noticias
    path('household-news/', views.get_household_news, name='household_news'),
    path('create-news/', views.create_news, name='create_news'),
    path('delete-news/<int:news_id>/', views.delete_news, name='delete_news'),
    
    # CRUD de gastos compartidos
    path('household-expenses/', views.get_household_expenses, name='household_expenses'),
    path('create-expense/', views.create_expense, name='create_expense'),
    path('pay-expense/<int:expense_id>/', views.pay_expense, name='pay_expense'),
    path('update-expense/<int:expense_id>/', views.update_expense, name='update_expense'),
    path('delete-expense/<int:expense_id>/', views.delete_expense, name='delete_expense'),
    
    # CRUD de tareas
    path('household-tasks/', views.get_household_tasks, name='household_tasks'),
    path('household-members/', views.get_household_members, name='household_members'),
    path('create-task/', views.create_task, name='create_task'),
    path('complete-task/<int:task_id>/', views.complete_task, name='complete_task'),
    path('delete-task/<int:task_id>/', views.delete_task, name='delete_task'),
    
    # Gastos personales mensuales
    path('personal-expenses/', views.get_personal_expenses, name='personal_expenses'),
    path('create-personal-expense/', views.create_personal_expense, name='create_personal_expense'),
    path('delete-personal-expense/<int:expense_id>/', views.delete_personal_expense, name='delete_personal_expense'),
    path('cleanup-monthly-expenses/', views.cleanup_monthly_expenses, name='cleanup_monthly_expenses'),
]