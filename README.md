# HOMI API - Documentación Completa

## Información General

**Base URL:** `http://tu-servidor:8000/api/`

**Autenticación:** Token-based authentication
- Header requerido: `Authorization: Token <tu_token>`
- El token se obtiene al hacer login o registro

---

## 📋 Índice de Endpoints

1. [Autenticación](#autenticación)
2. [Gestión de Casas](#gestión-de-casas)
3. [Noticias](#noticias)
4. [Gastos Compartidos](#gastos-compartidos)
5. [Tareas](#tareas)
6. [Gastos Personales](#gastos-personales)

---

## 🔐 Autenticación

### Registrar Usuario
```http
POST /api/register/
```

**Body:**
```json
{
  "username": "string",
  "email": "string",
  "password": "string"
}
```

**Respuesta exitosa (201):**
```json
{
  "token": "abcd1234...",
  "user_id": 1,
  "username": "usuario",
  "email": "usuario@email.com"
}
```

**Errores posibles:**
- `400`: Usuario o email ya existe
- `400`: Datos inválidos

---

### Iniciar Sesión
```http
POST /api/login/
```

**Body:**
```json
{
  "username": "string",
  "password": "string"
}
```

**Respuesta exitosa (200):**
```json
{
  "token": "abcd1234...",
  "user_id": 1,
  "username": "usuario",
  "email": "usuario@email.com",
  "has_household": true,
  "current_household": {
    "id": 1,
    "name": "Mi Casa",
    "code": "ABC123",
    "created_by": 1,
    "created_by_username": "creador",
    "members_count": 4,
    "created_at": "2024-01-01T10:00:00Z",
    "is_creator": true
  }
}
```

**Errores posibles:**
- `401`: Credenciales inválidas

---

## 🏠 Gestión de Casas

### Crear Casa
```http
POST /api/create-household/
```
**Headers:** `Authorization: Token <token>`

**Body:**
```json
{
  "name": "Mi Nueva Casa"
}
```

**Respuesta exitosa (201):**
```json
{
  "id": 1,
  "name": "Mi Nueva Casa",
  "code": "ABC123",
  "created_by": 1,
  "created_by_username": "usuario",
  "members_count": 1,
  "created_at": "2024-01-01T10:00:00Z",
  "is_creator": true
}
```

---

### Unirse a Casa
```http
POST /api/join-household/
```
**Headers:** `Authorization: Token <token>`

**Body:**
```json
{
  "code": "ABC123"
}
```

**Respuesta exitosa (200):**
```json
{
  "id": 1,
  "name": "Casa Existente",
  "code": "ABC123",
  "created_by": 2,
  "created_by_username": "creador",
  "members_count": 2,
  "created_at": "2024-01-01T10:00:00Z",
  "is_creator": false
}
```

**Errores posibles:**
- `404`: Código inválido
- `400`: Ya eres miembro de esta casa

---

### Obtener Información de Casa Actual
```http
GET /api/current-household-info/
```
**Headers:** `Authorization: Token <token>`

**Respuesta exitosa (200):**
```json
{
  "id": 1,
  "name": "Mi Casa",
  "code": "ABC123",
  "created_by": 1,
  "created_by_username": "creador",
  "members_count": 3,
  "created_at": "2024-01-01T10:00:00Z",
  "is_creator": true,
  "creator_username": "creador",
  "members_detail": [
    {
      "id": 1,
      "username": "usuario1",
      "is_creator": true,
      "is_current_user": true
    },
    {
      "id": 2,
      "username": "usuario2",
      "is_creator": false,
      "is_current_user": false
    }
  ]
}
```

---

### Salir de Casa
```http
POST /api/leave-household/
```
**Headers:** `Authorization: Token <token>`

**Respuesta exitosa (200):**
```json
{
  "message": "Has salido de la casa exitosamente"
}
```

**Errores posibles:**
- `400`: No puedes salir de una casa que creaste

---

### Eliminar Casa (Solo Creador)
```http
DELETE /api/delete-household/
```
**Headers:** `Authorization: Token <token>`

**Respuesta exitosa (200):**
```json
{
  "message": "Casa \"Mi Casa\" eliminada exitosamente. 3 miembros fueron desconectados."
}
```

**Errores posibles:**
- `403`: Solo el creador puede eliminar la casa

---

### Obtener Perfil de Usuario
```http
GET /api/user-profile/
```
**Headers:** `Authorization: Token <token>`

**Respuesta exitosa (200):**
```json
{
  "current_household": {
    "id": 1,
    "name": "Mi Casa",
    "code": "ABC123",
    // ... otros campos de casa
  }
}
```

---

## 📰 Noticias

### Obtener Noticias de Casa
```http
GET /api/household-news/
```
**Headers:** `Authorization: Token <token>`

**Respuesta exitosa (200):**
```json
[
  {
    "id": 1,
    "title": "Limpieza General",
    "content": "Este sábado haremos limpieza general de toda la casa.",
    "priority": "normal",
    "expiry_date": "2024-01-15T18:00:00Z",
    "created_by": 1,
    "created_by_username": "usuario",
    "household": 1,
    "created_at": "2024-01-01T10:00:00Z",
    "updated_at": "2024-01-01T10:00:00Z",
    "is_expired": false
  }
]
```

---

### Crear Noticia
```http
POST /api/create-news/
```
**Headers:** `Authorization: Token <token>`

**Body:**
```json
{
  "title": "Título de la noticia",
  "content": "Contenido de la noticia",
  "priority": "normal",
  "expiry_date": "2024-01-15T18:00:00Z"
}
```

**Opciones de prioridad:**
- `urgent`: Urgente
- `normal`: Normal
- `can_wait`: Puede esperar

**Respuesta exitosa (201):**
```json
{
  "id": 1,
  "title": "Título de la noticia",
  "content": "Contenido de la noticia",
  "priority": "normal",
  "expiry_date": "2024-01-15T18:00:00Z",
  "created_by": 1,
  "created_by_username": "usuario",
  "household": 1,
  "created_at": "2024-01-01T10:00:00Z",
  "updated_at": "2024-01-01T10:00:00Z",
  "is_expired": false
}
```

---

### Eliminar Noticia (Solo Creador)
```http
DELETE /api/delete-news/{news_id}/
```
**Headers:** `Authorization: Token <token>`

**Respuesta exitosa (200):**
```json
{
  "message": "Noticia eliminada exitosamente"
}
```

**Errores posibles:**
- `403`: No tienes permisos para eliminar esta noticia
- `404`: Noticia no encontrada

---

## 💰 Gastos Compartidos

### Obtener Gastos de Casa
```http
GET /api/household-expenses/
```
**Headers:** `Authorization: Token <token>`

**Respuesta exitosa (200):**
```json
[
  {
    "id": 1,
    "title": "Compra Supermercado",
    "description": "Compras de la semana",
    "total_cost": 120.00,
    "unit_cost": 30.00,
    "expense_type": "unique",
    "remaining_amount": 60.00,
    "created_by": 1,
    "created_by_username": "usuario",
    "household": 1,
    "created_at": "2024-01-01T10:00:00Z",
    "updated_at": "2024-01-01T10:00:00Z",
    "is_fully_paid": false,
    "payments": [
      {
        "id": 1,
        "user": 1,
        "user_username": "usuario1",
        "amount_paid": 30.00,
        "payment_date": "2024-01-01T11:00:00Z"
      }
    ],
    "members_count": 4,
    "user_has_paid": true
  }
]
```

---

### Crear Gasto
```http
POST /api/create-expense/
```
**Headers:** `Authorization: Token <token>`

**Body:**
```json
{
  "title": "Compra Supermercado",
  "description": "Compras de la semana",
  "total_cost": 120.00,
  "expense_type": "unique"
}
```

**Tipos de gasto:**
- `unique`: Gasto Único (se elimina cuando todos pagan)
- `permanent`: Gasto Permanente (permanece y puede editarse)

**Respuesta exitosa (201):**
```json
{
  "id": 1,
  "title": "Compra Supermercado",
  "description": "Compras de la semana",
  "total_cost": 120.00,
  "unit_cost": 30.00,
  "expense_type": "unique",
  "remaining_amount": 120.00,
  "created_by": 1,
  "created_by_username": "usuario",
  "household": 1,
  "created_at": "2024-01-01T10:00:00Z",
  "updated_at": "2024-01-01T10:00:00Z",
  "is_fully_paid": false,
  "payments": [],
  "members_count": 4,
  "user_has_paid": false
}
```

---

### Pagar Gasto
```http
POST /api/pay-expense/{expense_id}/
```
**Headers:** `Authorization: Token <token>`

**Respuesta exitosa (200):**
- Si el gasto es `unique` y se completa: `{"message": "Pago registrado y gasto completado"}`
- Si el gasto continúa: Devuelve el objeto gasto actualizado

**Errores posibles:**
- `400`: Ya has pagado este gasto
- `400`: Este gasto ya está completamente pagado

---

### Actualizar Gasto (Solo Permanentes)
```http
PUT /api/update-expense/{expense_id}/
```
**Headers:** `Authorization: Token <token>`

**Body:**
```json
{
  "total_cost": 150.00
}
```

**Respuesta exitosa (200):**
```json
{
  // Objeto gasto actualizado con pagos reseteados
}
```

**Errores posibles:**
- `403`: No tienes permisos para editar este gasto
- `400`: Solo los gastos permanentes pueden ser editados

---

### Eliminar Gasto (Solo Creador)
```http
DELETE /api/delete-expense/{expense_id}/
```
**Headers:** `Authorization: Token <token>`

**Respuesta exitosa (200):**
```json
{
  "message": "Gasto eliminado exitosamente"
}
```

---

## ✅ Tareas

### Obtener Tareas de Casa
```http
GET /api/household-tasks/
```
**Headers:** `Authorization: Token <token>`

**Respuesta exitosa (200):**
```json
[
  {
    "id": 1,
    "title": "Limpiar cocina",
    "description": "Limpiar toda la cocina incluyendo electrodomésticos",
    "due_datetime": "2024-01-10T18:00:00Z",
    "assigned_to": 2,
    "assigned_to_username": "usuario2",
    "created_by": 1,
    "created_by_username": "usuario1",
    "household": 1,
    "priority": "high",
    "is_completed": false,
    "completed_at": null,
    "created_at": "2024-01-01T10:00:00Z",
    "updated_at": "2024-01-01T10:00:00Z",
    "is_overdue": false,
    "can_complete_task": false
  }
]
```

---

### Obtener Miembros de Casa
```http
GET /api/household-members/
```
**Headers:** `Authorization: Token <token>`

**Respuesta exitosa (200):**
```json
[
  {
    "id": 2,
    "username": "usuario2"
  },
  {
    "id": 3,
    "username": "usuario3"
  }
]
```

---

### Crear Tarea
```http
POST /api/create-task/
```
**Headers:** `Authorization: Token <token>`

**Body:**
```json
{
  "title": "Limpiar cocina",
  "description": "Limpiar toda la cocina incluyendo electrodomésticos",
  "due_datetime": "2024-01-10T18:00:00Z",
  "assigned_to": 2,
  "priority": "high"
}
```

**Opciones de prioridad:**
- `low`: Baja
- `medium`: Media
- `high`: Alta

**Respuesta exitosa (201):**
```json
{
  // Objeto tarea completo
}
```

---

### Completar Tarea (Solo Usuario Asignado)
```http
POST /api/complete-task/{task_id}/
```
**Headers:** `Authorization: Token <token>`

**Respuesta exitosa (200):**
```json
{
  "message": "Tarea completada exitosamente"
}
```

**Errores posibles:**
- `403`: Solo el usuario asignado puede completar esta tarea
- `400`: Esta tarea ya está completada

---

### Eliminar Tarea (Solo Creador)
```http
DELETE /api/delete-task/{task_id}/
```
**Headers:** `Authorization: Token <token>`

**Respuesta exitosa (200):**
```json
{
  "message": "Tarea eliminada exitosamente"
}
```

---

## 💸 Gastos Personales

### Obtener Gastos Personales del Mes
```http
GET /api/personal-expenses/
```
**Headers:** `Authorization: Token <token>`

**Respuesta exitosa (200):**
```json
{
  "month": 1,
  "year": 2024,
  "household_total": 450.75,
  "members_summary": [
    {
      "user_id": 1,
      "username": "usuario1",
      "expenses": [
        {
          "id": 1,
          "title": "Almuerzo",
          "description": "Almuerzo en restaurante",
          "cost": 25.50,
          "user": 1,
          "user_username": "usuario1",
          "household": 1,
          "source": "manual",
          "source_text": "Gasto Personal",
          "shared_payment": null,
          "created_at": "2024-01-01T12:00:00Z",
          "month": 1,
          "year": 2024
        }
      ],
      "monthly_total": 125.75,
      "expense_count": 5
    }
  ]
}
```

---

### Crear Gasto Personal
```http
POST /api/create-personal-expense/
```
**Headers:** `Authorization: Token <token>`

**Body:**
```json
{
  "title": "Almuerzo",
  "description": "Almuerzo en restaurante",
  "cost": 25.50
}
```

**Respuesta exitosa (201):**
```json
{
  "id": 1,
  "title": "Almuerzo",
  "description": "Almuerzo en restaurante",
  "cost": 25.50,
  "user": 1,
  "user_username": "usuario1",
  "household": 1,
  "source": "manual",
  "source_text": "Gasto Personal",
  "shared_payment": null,
  "created_at": "2024-01-01T12:00:00Z",
  "month": 1,
  "year": 2024
}
```

---

### Eliminar Gasto Personal (Solo Manuales)
```http
DELETE /api/delete-personal-expense/{expense_id}/
```
**Headers:** `Authorization: Token <token>`

**Respuesta exitosa (200):**
```json
{
  "message": "Gasto personal eliminado exitosamente"
}
```

**Errores posibles:**
- `404`: Gasto no encontrado o no tienes permisos (solo gastos manuales propios)

---

### Limpiar Gastos del Mes Anterior
```http
POST /api/cleanup-monthly-expenses/
```
**Headers:** `Authorization: Token <token>`

**Respuesta exitosa (200):**
```json
{
  "message": "Gastos del mes anterior eliminados exitosamente"
}
```

---

## 📝 Notas Importantes

### Códigos de Estado HTTP
- `200`: Operación exitosa
- `201`: Recurso creado exitosamente
- `400`: Error en los datos enviados
- `401`: No autenticado
- `403`: Sin permisos para esta acción
- `404`: Recurso no encontrado
- `500`: Error interno del servidor

### Funcionamiento de Gastos
1. **Gastos Únicos**: Se eliminan automáticamente cuando todos los miembros pagan
2. **Gastos Permanentes**: Permanecen en la lista, pueden editarse (resetea pagos)
3. **Gastos Personales**: Se crean automáticamente al pagar gastos compartidos
4. **Limpieza Mensual**: Los gastos personales se pueden limpiar mensualmente

### Permisos
- **Creador de Casa**: Puede eliminar la casa (desconecta a todos)
- **Miembro**: Puede salir de la casa
- **Creador de Contenido**: Puede eliminar sus propias noticias, gastos y tareas
- **Usuario Asignado**: Solo puede completar tareas asignadas a él

### Fechas
- Todas las fechas están en formato ISO 8601: `YYYY-MM-DDTHH:MM:SSZ`
- Las fechas de vencimiento deben ser futuras
- El sistema maneja automáticamente zonas horarias
