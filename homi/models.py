from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework.authtoken.models import Token
from django.utils import timezone
from datetime import datetime
import random
import string

# Señal para crear token automáticamente
@receiver(post_save, sender=User)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)

# Modelo para las casas/hogares
class Household(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=6, unique=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_households')
    members = models.ManyToManyField(User, related_name='households')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def save(self, *args, **kwargs):
        if not self.code:
            # Generar código único de 6 caracteres
            while True:
                code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
                if not Household.objects.filter(code=code).exists():
                    self.code = code
                    break
        super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        """Sobrescribir delete para limpiar perfiles de usuarios"""
        # Limpiar current_household de todos los perfiles de miembros
        for member in self.members.all():
            try:
                profile = member.profile
                if profile.current_household == self:
                    profile.current_household = None
                    profile.save()
            except:
                pass
        
        # Llamar al delete original que eliminará la casa y todos los datos relacionados (CASCADE)
        super().delete(*args, **kwargs)
    
    def __str__(self):
        return f"{self.name} ({self.code})"

# Modelo para el perfil de usuario
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    current_household = models.ForeignKey(Household, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username}'s profile"

# Crear perfil automáticamente
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

# Modelo para las noticias
class News(models.Model):
    PRIORITY_CHOICES = [
        ('urgent', 'Urgente'),
        ('normal', 'Normal'),
        ('can_wait', 'Puede esperar'),
    ]
    
    title = models.CharField(max_length=200)
    content = models.TextField()
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='normal')
    expiry_date = models.DateTimeField()
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_news')
    household = models.ForeignKey(Household, on_delete=models.CASCADE, related_name='news')  # CASCADE aquí
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'News'
    
    def __str__(self):
        return f"{self.title} - {self.household.name}"
    
    def is_expired(self):
        from django.utils import timezone
        return timezone.now() > self.expiry_date


# Modelo para los gastos compartidos
class Expense(models.Model):
    EXPENSE_TYPE_CHOICES = [
        ('unique', 'Gasto Único'),
        ('permanent', 'Gasto Permanente'),
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    total_cost = models.DecimalField(max_digits=10, decimal_places=2)
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2)
    expense_type = models.CharField(max_length=10, choices=EXPENSE_TYPE_CHOICES, default='unique')
    remaining_amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_expenses')
    household = models.ForeignKey(Household, on_delete=models.CASCADE, related_name='expenses')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.household.name}"
    
    def save(self, *args, **kwargs):
        # Calcular costo unitario y monto restante automáticamente
        if self.household:
            members_count = self.household.members.count()
            if members_count > 0:
                self.unit_cost = self.total_cost / members_count
                # Si es un gasto nuevo, el monto restante es el total
                if not self.pk:
                    self.remaining_amount = self.total_cost
        super().save(*args, **kwargs)
    
    def is_fully_paid(self):
        return self.remaining_amount <= 0

# Modelo para el registro de pagos
class ExpensePayment(models.Model):
    expense = models.ForeignKey(Expense, on_delete=models.CASCADE, related_name='payments')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='expense_payments')
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['expense', 'user']  
        ordering = ['-payment_date']
    
    def __str__(self):
        return f"{self.user.username} pagó {self.amount_paid} para {self.expense.title}"

# Modelo para las tareas del hogar
class Task(models.Model):
    PRIORITY_CHOICES = [
        ('low', 'Baja'),
        ('medium', 'Media'),
        ('high', 'Alta'),
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    due_datetime = models.DateTimeField()  # Fecha y hora máxima
    assigned_to = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assigned_tasks')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_tasks')
    household = models.ForeignKey(Household, on_delete=models.CASCADE, related_name='tasks')  # CASCADE aquí
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['due_datetime', '-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.household.name}"
    
    def is_overdue(self):
        from django.utils import timezone
        return timezone.now() > self.due_datetime and not self.is_completed
    
    def can_complete(self, user):
        return self.assigned_to == user and not self.is_completed

# NUEVO MODELO: Gastos Personales Mensuales
class PersonalExpense(models.Model):
    EXPENSE_SOURCE_CHOICES = [
        ('manual', 'Manual'),  # Agregado manualmente
        ('shared_payment', 'Pago de Gasto Compartido'),  # Viene de un pago de gasto compartido
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    cost = models.DecimalField(max_digits=10, decimal_places=2)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='personal_expenses')
    household = models.ForeignKey(Household, on_delete=models.CASCADE, related_name='personal_expenses')  # CASCADE aquí
    source = models.CharField(max_length=20, choices=EXPENSE_SOURCE_CHOICES, default='manual')
    # Referencia al pago de gasto compartido si aplica
    shared_payment = models.ForeignKey(ExpensePayment, on_delete=models.SET_NULL, null=True, blank=True, related_name='personal_expense')
    created_at = models.DateTimeField(auto_now_add=True)
    month = models.IntegerField()  # Mes del gasto (1-12)
    year = models.IntegerField()   # Año del gasto
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'household', 'month', 'year']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.user.username} - ${self.cost}"
    
    def save(self, *args, **kwargs):
        # Si no se especifica mes y año, usar el actual
        if not self.month or not self.year:
            now = timezone.now()
            self.month = now.month
            self.year = now.year
        super().save(*args, **kwargs)
    
    @classmethod
    def get_current_month_expenses(cls, user, household):
        """Obtiene los gastos del mes actual para un usuario en una casa"""
        now = timezone.now()
        return cls.objects.filter(
            user=user,
            household=household,
            month=now.month,
            year=now.year
        )
    
    @classmethod
    def get_monthly_total(cls, user, household, month=None, year=None):
        """Obtiene el total de gastos de un mes específico"""
        if not month or not year:
            now = timezone.now()
            month = now.month
            year = now.year
        
        expenses = cls.objects.filter(
            user=user,
            household=household,
            month=month,
            year=year
        )
        
        total = expenses.aggregate(total=models.Sum('cost'))['total']
        return total if total else 0
    
    @classmethod
    def cleanup_old_expenses(cls):
        """Elimina gastos del mes anterior - Se puede llamar desde un cron job"""
        now = timezone.now()
        # Calcular el mes anterior
        if now.month == 1:
            prev_month = 12
            prev_year = now.year - 1
        else:
            prev_month = now.month - 1
            prev_year = now.year
        
        # Eliminar gastos del mes anterior
        cls.objects.filter(
            month=prev_month,
            year=prev_year
        ).delete()