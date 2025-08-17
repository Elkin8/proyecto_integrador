from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Household, UserProfile, News, Expense, ExpensePayment, Task, PersonalExpense

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'password')
    
    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        return user

class HouseholdSerializer(serializers.ModelSerializer):
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    members_count = serializers.IntegerField(source='members.count', read_only=True)
    
    class Meta:
        model = Household
        fields = ('id', 'name', 'code', 'created_by', 'created_by_username', 
                 'members_count', 'created_at')
        read_only_fields = ('code', 'created_by', 'created_at')

class UserProfileSerializer(serializers.ModelSerializer):
    current_household = HouseholdSerializer(read_only=True)
    
    class Meta:
        model = UserProfile
        fields = ('current_household',)

class NewsSerializer(serializers.ModelSerializer):
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    is_expired = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = News
        fields = ('id', 'title', 'content', 'priority', 'expiry_date', 
                 'created_by', 'created_by_username', 'household', 
                 'created_at', 'updated_at', 'is_expired')
        read_only_fields = ('created_by', 'household', 'created_at', 'updated_at')

class CreateNewsSerializer(serializers.ModelSerializer):
    class Meta:
        model = News
        fields = ('title', 'content', 'priority', 'expiry_date')

class ExpensePaymentSerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = ExpensePayment
        fields = ('id', 'user', 'user_username', 'amount_paid', 'payment_date')
        read_only_fields = ('user', 'payment_date')

class ExpenseSerializer(serializers.ModelSerializer):
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    is_fully_paid = serializers.BooleanField(read_only=True)
    payments = ExpensePaymentSerializer(many=True, read_only=True)
    members_count = serializers.IntegerField(source='household.members.count', read_only=True)
    user_has_paid = serializers.SerializerMethodField()
    
    class Meta:
        model = Expense
        fields = ('id', 'title', 'description', 'total_cost', 'unit_cost', 
                 'expense_type', 'remaining_amount', 'created_by', 'created_by_username',
                 'household', 'created_at', 'updated_at', 'is_fully_paid', 'payments',
                 'members_count', 'user_has_paid')
        read_only_fields = ('created_by', 'household', 'created_at', 'updated_at',
                           'unit_cost', 'remaining_amount')
    
    def get_user_has_paid(self, obj):
        request = self.context.get('request')
        if request and request.user:
            return obj.payments.filter(user=request.user).exists()
        return False

class CreateExpenseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Expense
        fields = ('title', 'description', 'total_cost', 'expense_type')

class UpdateExpenseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Expense
        fields = ('total_cost',)  # Solo permitir actualizar el costo total

class TaskSerializer(serializers.ModelSerializer):
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    assigned_to_username = serializers.CharField(source='assigned_to.username', read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)
    can_complete_task = serializers.SerializerMethodField()
    
    class Meta:
        model = Task
        fields = ('id', 'title', 'description', 'due_datetime', 'assigned_to',
                 'assigned_to_username', 'created_by', 'created_by_username',
                 'household', 'priority', 'is_completed', 'completed_at',
                 'created_at', 'updated_at', 'is_overdue', 'can_complete_task')
        read_only_fields = ('created_by', 'household', 'created_at', 'updated_at',
                           'is_completed', 'completed_at')
    
    def get_can_complete_task(self, obj):
        request = self.context.get('request')
        if request and request.user:
            return obj.can_complete(request.user)
        return False

class CreateTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ('title', 'description', 'due_datetime', 'assigned_to', 'priority')

class HouseholdMemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username')

# NUEVOS SERIALIZERS PARA GASTOS PERSONALES
class PersonalExpenseSerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(source='user.username', read_only=True)
    source_text = serializers.SerializerMethodField()
    
    class Meta:
        model = PersonalExpense
        fields = ('id', 'title', 'description', 'cost', 'user', 'user_username',
                 'household', 'source', 'source_text', 'shared_payment',
                 'created_at', 'month', 'year')
        read_only_fields = ('user', 'household', 'created_at', 'month', 'year', 
                           'source', 'shared_payment')
    
    def get_source_text(self, obj):
        if obj.source == 'manual':
            return 'Gasto Personal'
        elif obj.source == 'shared_payment':
            return 'Pago de Gasto Compartido'
        return obj.source

class CreatePersonalExpenseSerializer(serializers.ModelSerializer):
    class Meta:
        model = PersonalExpense
        fields = ('title', 'description', 'cost')

class MonthlyExpenseSummarySerializer(serializers.Serializer):
    """Serializer para el resumen mensual de gastos"""
    user_id = serializers.IntegerField()
    username = serializers.CharField()
    expenses = PersonalExpenseSerializer(many=True)
    monthly_total = serializers.DecimalField(max_digits=10, decimal_places=2)
    expense_count = serializers.IntegerField()