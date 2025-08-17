from django.shortcuts import render
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from .serializers import (
    UserSerializer, HouseholdSerializer, UserProfileSerializer, 
    NewsSerializer, CreateNewsSerializer, ExpenseSerializer, 
    CreateExpenseSerializer, UpdateExpenseSerializer, TaskSerializer, 
    CreateTaskSerializer, HouseholdMemberSerializer, PersonalExpenseSerializer,
    CreatePersonalExpenseSerializer, MonthlyExpenseSummarySerializer
)
from .models import Household, News, Expense, ExpensePayment, Task, PersonalExpense
from django.db import transaction
from django.db.models import Sum
from decimal import Decimal
import logging
from django.utils import timezone

logger = logging.getLogger(__name__)

@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    logger.info(f"Register attempt with data: {request.data}")
    
    # Verificar si el usuario ya existe
    username = request.data.get('username')
    email = request.data.get('email')
    
    if User.objects.filter(username=username).exists():
        return Response({
            'error': 'El nombre de usuario ya está en uso'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    if User.objects.filter(email=email).exists():
        return Response({
            'error': 'El correo electrónico ya está registrado'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        token = Token.objects.get(user=user)
        logger.info(f"User created successfully: {user.username}")
        return Response({
            'token': token.key,
            'user_id': user.id,
            'username': user.username,
            'email': user.email
        }, status=status.HTTP_201_CREATED)
    
    logger.error(f"Registration errors: {serializer.errors}")
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    logger.info(f"Login attempt for user: {request.data.get('username')}")
    
    username = request.data.get('username')
    password = request.data.get('password')
    
    if username and password:
        user = authenticate(username=username, password=password)
        if user:
            token, _ = Token.objects.get_or_create(user=user)
            
            # Verificar si el usuario tiene una casa actual
            has_household = False
            current_household = None
            
            try:
                profile = user.profile
                if profile.current_household:
                    has_household = True
                    current_household = HouseholdSerializer(profile.current_household).data
                    # NUEVO: Agregar información del creador
                    current_household['is_creator'] = (profile.current_household.created_by == user)
            except:
                pass
            
            logger.info(f"User logged in successfully: {user.username}")
            return Response({
                'token': token.key,
                'user_id': user.id,
                'username': user.username,
                'email': user.email,
                'has_household': has_household,
                'current_household': current_household
            })
        else:
            logger.warning(f"Invalid credentials for user: {username}")
            return Response({
                'error': 'Credenciales inválidas'
            }, status=status.HTTP_401_UNAUTHORIZED)
    else:
        return Response({
            'error': 'Por favor proporciona usuario y contraseña'
        }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_household(request):
    name = request.data.get('name')
    
    if not name:
        return Response({
            'error': 'El nombre de la casa es requerido'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Crear la casa
    household = Household.objects.create(
        name=name,
        created_by=request.user
    )
    household.members.add(request.user)
    
    # Actualizar el perfil del usuario
    profile = request.user.profile
    profile.current_household = household
    profile.save()
    
    serializer = HouseholdSerializer(household)
    response_data = serializer.data
    # NUEVO: Agregar información del creador
    response_data['is_creator'] = True
    
    return Response(response_data, status=status.HTTP_201_CREATED)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def join_household(request):
    code = request.data.get('code')
    
    if not code:
        return Response({
            'error': 'El código es requerido'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        household = Household.objects.get(code=code.upper())
        
        # Verificar si ya es miembro
        if request.user in household.members.all():
            return Response({
                'error': 'Ya eres miembro de esta casa'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Agregar usuario a la casa
        household.members.add(request.user)
        
        # Actualizar el perfil del usuario
        profile = request.user.profile
        profile.current_household = household
        profile.save()
        
        serializer = HouseholdSerializer(household)
        response_data = serializer.data
        # NUEVO: Agregar información del creador
        response_data['is_creator'] = (household.created_by == request.user)
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Household.DoesNotExist:
        return Response({
            'error': 'Código inválido'
        }, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_profile(request):
    try:
        profile = request.user.profile
        serializer = UserProfileSerializer(profile)
        return Response(serializer.data)
    except:
        return Response({
            'current_household': None
        })
    
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_household_news(request):
    try:
        profile = request.user.profile
        if not profile.current_household:
            return Response({
                'error': 'No tienes una casa asignada'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Obtener noticias que no han expirado
        news = News.objects.filter(
            household=profile.current_household,
            expiry_date__gt=timezone.now()
        ).order_by('-created_at')
        
        serializer = NewsSerializer(news, many=True)
        return Response(serializer.data)
        
    except Exception as e:
        logger.error(f"Error getting household news: {e}")
        return Response({
            'error': 'Error al obtener las noticias'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_news(request):
    try:
        profile = request.user.profile
        if not profile.current_household:
            return Response({
                'error': 'No tienes una casa asignada'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = CreateNewsSerializer(data=request.data)
        if serializer.is_valid():
            news = serializer.save(
                created_by=request.user,
                household=profile.current_household
            )
            
            # Devolver la noticia creada con toda la información
            response_serializer = NewsSerializer(news)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
    except Exception as e:
        logger.error(f"Error creating news: {e}")
        return Response({
            'error': 'Error al crear la noticia'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_news(request, news_id):
    try:
        profile = request.user.profile
        if not profile.current_household:
            return Response({
                'error': 'No tienes una casa asignada'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        news = News.objects.get(
            id=news_id,
            household=profile.current_household
        )
        
        # Solo el creador puede eliminar la noticia
        if news.created_by != request.user:
            return Response({
                'error': 'No tienes permisos para eliminar esta noticia'
            }, status=status.HTTP_403_FORBIDDEN)
        
        news.delete()
        return Response({'message': 'Noticia eliminada exitosamente'})
        
    except News.DoesNotExist:
        return Response({
            'error': 'Noticia no encontrada'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error deleting news: {e}")
        return Response({
            'error': 'Error al eliminar la noticia'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_household_expenses(request):
    try:
        profile = request.user.profile
        if not profile.current_household:
            return Response({
                'error': 'No tienes una casa asignada'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        expenses = Expense.objects.filter(household=profile.current_household)
        serializer = ExpenseSerializer(expenses, many=True, context={'request': request})
        return Response(serializer.data)
        
    except Exception as e:
        logger.error(f"Error getting household expenses: {e}")
        return Response({
            'error': 'Error al obtener los gastos'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_expense(request):
    try:
        profile = request.user.profile
        if not profile.current_household:
            return Response({
                'error': 'No tienes una casa asignada'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = CreateExpenseSerializer(data=request.data)
        if serializer.is_valid():
            expense = serializer.save(
                created_by=request.user,
                household=profile.current_household
            )
            
            # Devolver el gasto creado con toda la información
            response_serializer = ExpenseSerializer(expense, context={'request': request})
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
    except Exception as e:
        logger.error(f"Error creating expense: {e}")
        return Response({
            'error': 'Error al crear el gasto'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def pay_expense(request, expense_id):
    try:
        profile = request.user.profile
        if not profile.current_household:
            return Response({
                'error': 'No tienes una casa asignada'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        expense = Expense.objects.get(
            id=expense_id,
            household=profile.current_household
        )
        
        # Verificar si el usuario ya pagó
        if ExpensePayment.objects.filter(expense=expense, user=request.user).exists():
            return Response({
                'error': 'Ya has pagado este gasto'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Verificar si el gasto ya está completamente pagado
        if expense.is_fully_paid():
            return Response({
                'error': 'Este gasto ya está completamente pagado'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        with transaction.atomic():
            # Crear el pago
            payment = ExpensePayment.objects.create(
                expense=expense,
                user=request.user,
                amount_paid=expense.unit_cost
            )
            
            # Actualizar el monto restante
            expense.remaining_amount -= expense.unit_cost
            expense.save()
            
            # NUEVO: Crear gasto personal automático
            now = timezone.now()
            PersonalExpense.objects.create(
                title=f"Pago: {expense.title}",
                description=f"Pago de gasto compartido: {expense.description}",
                cost=expense.unit_cost,
                user=request.user,
                household=profile.current_household,
                source='shared_payment',
                shared_payment=payment,
                month=now.month,
                year=now.year
            )
            
            # Si es gasto único y está completamente pagado, eliminarlo
            if expense.expense_type == 'unique' and expense.is_fully_paid():
                expense.delete()
                return Response({'message': 'Pago registrado y gasto completado'})
            
            # Devolver el gasto actualizado
            response_serializer = ExpenseSerializer(expense, context={'request': request})
            return Response(response_serializer.data)
        
    except Expense.DoesNotExist:
        return Response({
            'error': 'Gasto no encontrado'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error paying expense: {e}")
        return Response({
            'error': 'Error al procesar el pago'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_expense(request, expense_id):
    try:
        profile = request.user.profile
        if not profile.current_household:
            return Response({
                'error': 'No tienes una casa asignada'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        expense = Expense.objects.get(
            id=expense_id,
            household=profile.current_household
        )
        
        # Solo el creador puede editar
        if expense.created_by != request.user:
            return Response({
                'error': 'No tienes permisos para editar este gasto'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Solo gastos permanentes pueden ser editados
        if expense.expense_type != 'permanent':
            return Response({
                'error': 'Solo los gastos permanentes pueden ser editados'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = UpdateExpenseSerializer(expense, data=request.data, partial=True)
        if serializer.is_valid():
            with transaction.atomic():
                # Guardar el nuevo total
                new_total = serializer.validated_data['total_cost']
                
                # Eliminar todos los pagos existentes cuando se edita el gasto
                ExpensePayment.objects.filter(expense=expense).delete()
                
                # Actualizar el gasto
                expense.total_cost = new_total
                expense.remaining_amount = new_total  # Resetear el monto restante al total
                
                # Recalcular el costo unitario
                members_count = expense.household.members.count()
                if members_count > 0:
                    expense.unit_cost = expense.total_cost / members_count
                
                expense.save()
            
            response_serializer = ExpenseSerializer(expense, context={'request': request})
            return Response(response_serializer.data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
    except Expense.DoesNotExist:
        return Response({
            'error': 'Gasto no encontrado'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error updating expense: {e}")
        return Response({
            'error': 'Error al actualizar el gasto'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_expense(request, expense_id):
    try:
        profile = request.user.profile
        if not profile.current_household:
            return Response({
                'error': 'No tienes una casa asignada'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        expense = Expense.objects.get(
            id=expense_id,
            household=profile.current_household
        )
        
        # Solo el creador puede eliminar
        if expense.created_by != request.user:
            return Response({
                'error': 'No tienes permisos para eliminar este gasto'
            }, status=status.HTTP_403_FORBIDDEN)
        
        expense.delete()
        return Response({'message': 'Gasto eliminado exitosamente'})
        
    except Expense.DoesNotExist:
        return Response({
            'error': 'Gasto no encontrado'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error deleting expense: {e}")
        return Response({
            'error': 'Error al eliminar el gasto'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_household_tasks(request):
    try:
        profile = request.user.profile
        if not profile.current_household:
            return Response({
                'error': 'No tienes una casa asignada'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Obtener todas las tareas de la casa que no están completadas
        tasks = Task.objects.filter(
            household=profile.current_household,
            is_completed=False
        ).order_by('due_datetime', '-created_at')
        
        serializer = TaskSerializer(tasks, many=True, context={'request': request})
        return Response(serializer.data)
        
    except Exception as e:
        logger.error(f"Error getting household tasks: {e}")
        return Response({
            'error': 'Error al obtener las tareas'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_household_members(request):
    try:
        profile = request.user.profile
        if not profile.current_household:
            return Response({
                'error': 'No tienes una casa asignada'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Obtener todos los miembros de la casa excepto el usuario actual
        members = profile.current_household.members.exclude(id=request.user.id)
        serializer = HouseholdMemberSerializer(members, many=True)
        return Response(serializer.data)
        
    except Exception as e:
        logger.error(f"Error getting household members: {e}")
        return Response({
            'error': 'Error al obtener los miembros'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_task(request):
    try:
        profile = request.user.profile
        if not profile.current_household:
            return Response({
                'error': 'No tienes una casa asignada'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = CreateTaskSerializer(data=request.data)
        if serializer.is_valid():
            # Verificar que el usuario asignado sea miembro de la casa
            assigned_user_id = serializer.validated_data['assigned_to'].id
            if not profile.current_household.members.filter(id=assigned_user_id).exists():
                return Response({
                    'error': 'El usuario asignado no es miembro de esta casa'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            task = serializer.save(
                created_by=request.user,
                household=profile.current_household
            )
            
            # Devolver la tarea creada con toda la información
            response_serializer = TaskSerializer(task, context={'request': request})
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
    except Exception as e:
        logger.error(f"Error creating task: {e}")
        return Response({
            'error': 'Error al crear la tarea'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def complete_task(request, task_id):
    try:
        profile = request.user.profile
        if not profile.current_household:
            return Response({
                'error': 'No tienes una casa asignada'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        task = Task.objects.get(
            id=task_id,
            household=profile.current_household
        )
        
        # Verificar que solo el usuario asignado puede completar la tarea
        if task.assigned_to != request.user:
            return Response({
                'error': 'Solo el usuario asignado puede completar esta tarea'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Verificar que la tarea no esté ya completada
        if task.is_completed:
            return Response({
                'error': 'Esta tarea ya está completada'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Completar la tarea
        task.is_completed = True
        task.completed_at = timezone.now()
        task.save()
        
        return Response({'message': 'Tarea completada exitosamente'})
        
    except Task.DoesNotExist:
        return Response({
            'error': 'Tarea no encontrada'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error completing task: {e}")
        return Response({
            'error': 'Error al completar la tarea'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_task(request, task_id):
    try:
        profile = request.user.profile
        if not profile.current_household:
            return Response({
                'error': 'No tienes una casa asignada'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        task = Task.objects.get(
            id=task_id,
            household=profile.current_household
        )
        
        # Solo el creador puede eliminar la tarea
        if task.created_by != request.user:
            return Response({
                'error': 'No tienes permisos para eliminar esta tarea'
            }, status=status.HTTP_403_FORBIDDEN)
        
        task.delete()
        return Response({'message': 'Tarea eliminada exitosamente'})
        
    except Task.DoesNotExist:
        return Response({
            'error': 'Tarea no encontrada'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error deleting task: {e}")
        return Response({
            'error': 'Error al eliminar la tarea'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# NUEVAS VISTAS PARA GASTOS PERSONALES
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_personal_expenses(request):
    """Obtiene los gastos personales del mes actual de todos los miembros de la casa"""
    try:
        profile = request.user.profile
        if not profile.current_household:
            return Response({
                'error': 'No tienes una casa asignada'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        now = timezone.now()
        
        # Obtener todos los miembros de la casa
        members = profile.current_household.members.all()
        
        # Construir resumen por cada miembro
        summary = []
        household_total = Decimal('0')
        
        for member in members:
            # Obtener gastos del mes actual
            expenses = PersonalExpense.objects.filter(
                user=member,
                household=profile.current_household,
                month=now.month,
                year=now.year
            ).order_by('-created_at')
            
            # Calcular total del usuario
            user_total = expenses.aggregate(total=Sum('cost'))['total'] or Decimal('0')
            household_total += user_total
            
            member_data = {
                'user_id': member.id,
                'username': member.username,
                'expenses': PersonalExpenseSerializer(expenses, many=True).data,
                'monthly_total': user_total,
                'expense_count': expenses.count()
            }
            summary.append(member_data)
        
        return Response({
            'month': now.month,
            'year': now.year,
            'household_total': household_total,
            'members_summary': summary
        })
        
    except Exception as e:
        logger.error(f"Error getting personal expenses: {e}")
        return Response({
            'error': 'Error al obtener los gastos personales'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_personal_expense(request):
    """Crea un nuevo gasto personal manual"""
    try:
        profile = request.user.profile
        if not profile.current_household:
            return Response({
                'error': 'No tienes una casa asignada'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = CreatePersonalExpenseSerializer(data=request.data)
        if serializer.is_valid():
            now = timezone.now()
            expense = serializer.save(
                user=request.user,
                household=profile.current_household,
                source='manual',
                month=now.month,
                year=now.year
            )
            
            response_serializer = PersonalExpenseSerializer(expense)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
    except Exception as e:
        logger.error(f"Error creating personal expense: {e}")
        return Response({
            'error': 'Error al crear el gasto personal'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_personal_expense(request, expense_id):
    """Elimina un gasto personal (solo si es manual y del propio usuario)"""
    try:
        expense = PersonalExpense.objects.get(
            id=expense_id,
            user=request.user,
            source='manual'  # Solo se pueden eliminar gastos manuales
        )
        
        expense.delete()
        return Response({'message': 'Gasto personal eliminado exitosamente'})
        
    except PersonalExpense.DoesNotExist:
        return Response({
            'error': 'Gasto personal no encontrado o no tienes permisos para eliminarlo'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error deleting personal expense: {e}")
        return Response({
            'error': 'Error al eliminar el gasto personal'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cleanup_monthly_expenses(request):
    """Limpia los gastos del mes anterior (puede ser llamado manualmente o por un cron)"""
    try:
        # Solo admins o un sistema automatizado deberían poder hacer esto
        # Por ahora lo dejamos manual para testing
        PersonalExpense.cleanup_old_expenses()
        
        return Response({
            'message': 'Gastos del mes anterior eliminados exitosamente'
        })
        
    except Exception as e:
        logger.error(f"Error cleaning up expenses: {e}")
        return Response({
            'error': 'Error al limpiar gastos antiguos'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# NUEVO ENDPOINT: Obtener información de la casa actual
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_current_household_info(request):
    try:
        profile = request.user.profile
        if not profile.current_household:
            return Response({
                'error': 'No tienes una casa asignada'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        household = profile.current_household
        serializer = HouseholdSerializer(household)
        response_data = serializer.data
        
        # Agregar información adicional
        response_data['is_creator'] = (household.created_by == request.user)
        response_data['creator_username'] = household.created_by.username
        
        # Obtener lista de miembros
        members = household.members.all()
        members_data = []
        for member in members:
            members_data.append({
                'id': member.id,
                'username': member.username,
                'is_creator': (member == household.created_by),
                'is_current_user': (member == request.user)
            })
        
        response_data['members_detail'] = members_data
        
        return Response(response_data)
        
    except Exception as e:
        logger.error(f"Error getting household info: {e}")
        return Response({
            'error': 'Error al obtener información de la casa'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# NUEVO ENDPOINT: Salir de la casa
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def leave_household(request):
    try:
        profile = request.user.profile
        if not profile.current_household:
            return Response({
                'error': 'No tienes una casa asignada'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        household = profile.current_household
        
        # Verificar que no sea el creador
        if household.created_by == request.user:
            return Response({
                'error': 'No puedes salir de una casa que creaste. Debes eliminarla.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Remover usuario de la casa
        household.members.remove(request.user)
        
        # Limpiar el perfil del usuario
        profile.current_household = None
        profile.save()
        
        return Response({
            'message': 'Has salido de la casa exitosamente'
        })
        
    except Exception as e:
        logger.error(f"Error leaving household: {e}")
        return Response({
            'error': 'Error al salir de la casa'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# NUEVO ENDPOINT: Eliminar casa (solo creador)
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_household(request):
    try:
        profile = request.user.profile
        if not profile.current_household:
            return Response({
                'error': 'No tienes una casa asignada'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        household = profile.current_household
        
        # Verificar que sea el creador
        if household.created_by != request.user:
            return Response({
                'error': 'Solo el creador puede eliminar la casa'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Limpiar los perfiles de todos los miembros
        members = household.members.all()
        for member in members:
            try:
                member_profile = member.profile
                member_profile.current_household = None
                member_profile.save()
                logger.info(f"Cleared household for user: {member.username}")
            except Exception as e:
                logger.error(f"Error clearing household for user {member.username}: {e}")
        
        # Obtener información antes de eliminar
        household_name = household.name
        members_count = members.count()
        
        # Eliminar la casa (esto también eliminará automáticamente noticias, gastos, tareas relacionadas)
        household.delete()
        
        logger.info(f"Household '{household_name}' deleted by {request.user.username}. {members_count} members affected.")
        
        return Response({
            'message': f'Casa "{household_name}" eliminada exitosamente. {members_count} miembros fueron desconectados.'
        })
        
    except Exception as e:
        logger.error(f"Error deleting household: {e}")
        return Response({
            'error': 'Error al eliminar la casa'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)