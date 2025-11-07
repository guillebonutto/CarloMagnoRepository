# Crear archivo: productos/customer_auth.py

from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.db import transaction
from .models import Cliente, Direccion
from django import forms

# ========== FORMULARIOS ==========

class RegistroForm(forms.Form):
    # Datos de cuenta
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nombre de usuario'
        })
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'correo@ejemplo.com'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Contraseña'
        })
    )
    password_confirm = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirmar contraseña'
        }),
        label='Confirmar contraseña'
    )
    
    # Datos personales
    tratamiento = forms.ChoiceField(
        choices=Cliente.TRATAMIENTO_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    nombre = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nombre'
        })
    )
    apellidos = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Apellidos'
        })
    )
    
    # Preferencias
    boletin = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label='Quiero recibir el boletín con ofertas'
    )
    ofertas_asociados = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label='Acepto recibir ofertas de asociados'
    )
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')
        
        if password and password_confirm and password != password_confirm:
            raise forms.ValidationError('Las contraseñas no coinciden')
        
        return cleaned_data
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('Este nombre de usuario ya está en uso')
        return username
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Este email ya está registrado')
        if Cliente.objects.filter(email=email).exists():
            raise forms.ValidationError('Este email ya está registrado')
        return email


class LoginForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nombre de usuario o email'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Contraseña'
        })
    )
    recordar = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label='Recordarme'
    )


class DireccionClienteForm(forms.ModelForm):
    class Meta:
        model = Direccion
        fields = ['nombre', 'apellidos', 'direccion', 'codigo_postal', 'ciudad', 'pais', 'telefono', 'es_predeterminada']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre'}),
            'apellidos': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Apellidos'}),
            'direccion': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Dirección completa', 'rows': 3}),
            'codigo_postal': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Código Postal'}),
            'ciudad': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ciudad'}),
            'pais': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'País', 'value': 'Argentina'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Teléfono'}),
            'es_predeterminada': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


# ========== VISTAS ==========

def registro_cliente(request):
    """Vista de registro para nuevos clientes"""
    if request.user.is_authenticated:
        return redirect('perfil_cliente')
    
    if request.method == 'POST':
        form = RegistroForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Crear usuario de Django
                    user = User.objects.create_user(
                        username=form.cleaned_data['username'],
                        email=form.cleaned_data['email'],
                        password=form.cleaned_data['password'],
                        first_name=form.cleaned_data['nombre'],
                        last_name=form.cleaned_data['apellidos']
                    )
                    
                    # Crear perfil de cliente
                    cliente = Cliente.objects.create(
                        tratamiento=form.cleaned_data['tratamiento'],
                        nombre=form.cleaned_data['nombre'],
                        apellidos=form.cleaned_data['apellidos'],
                        email=form.cleaned_data['email'],
                        boletin=form.cleaned_data.get('boletin', False),
                        ofertas_asociados=form.cleaned_data.get('ofertas_asociados', False),
                        activado=True
                    )
                    
                    # Asociar usuario con cliente (puedes agregar un campo user en Cliente)
                    # O usar una relación OneToOne si prefieres
                    
                    # Login automático después del registro
                    login(request, user)
                    messages.success(request, f'¡Bienvenido {user.first_name}! Tu cuenta ha sido creada exitosamente.')
                    return redirect('inicio')
            except Exception as e:
                messages.error(request, f'Error al crear la cuenta: {str(e)}')
    else:
        form = RegistroForm()
    
    return render(request, 'registro.html', {'form': form})


def login_cliente(request):
    """Vista de login para clientes"""
    if request.user.is_authenticated:
        return redirect('perfil_cliente')
    
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            recordar = form.cleaned_data.get('recordar', False)
            
            # Intentar autenticar con username
            user = authenticate(request, username=username, password=password)
            
            # Si falla, intentar con email
            if user is None:
                try:
                    user_obj = User.objects.get(email=username)
                    user = authenticate(request, username=user_obj.username, password=password)
                except User.DoesNotExist:
                    pass
            
            if user is not None:
                login(request, user)
                
                # Configurar duración de la sesión
                if not recordar:
                    request.session.set_expiry(0)  # Cierra sesión al cerrar navegador
                else:
                    request.session.set_expiry(1209600)  # 2 semanas
                
                messages.success(request, f'¡Bienvenido de nuevo, {user.first_name}!')
                
                # Redirigir a la página anterior o al perfil
                next_url = request.GET.get('next', 'inicio')
                return redirect(next_url)
            else:
                messages.error(request, 'Usuario o contraseña incorrectos')
    else:
        form = LoginForm()
    
    return render(request, 'login.html', {'form': form})


def logout_cliente(request):
    """Cerrar sesión del cliente"""
    logout(request)
    messages.success(request, 'Has cerrado sesión correctamente')
    return redirect('inicio')


@login_required(login_url='login_cliente')
def perfil_cliente(request):
    """Vista del perfil del cliente"""
    try:
        cliente = Cliente.objects.get(email=request.user.email)
    except Cliente.DoesNotExist:
        # Si no existe el perfil de cliente, crearlo
        cliente = Cliente.objects.create(
            nombre=request.user.first_name,
            apellidos=request.user.last_name,
            email=request.user.email,
            activado=True
        )
    
    direcciones = cliente.direcciones.all()
    
    # Obtener pedidos del cliente (cuando implementes el modelo de pedidos)
    # pedidos = Pedido.objects.filter(cliente=cliente).order_by('-fecha_pedido')
    
    context = {
        'cliente': cliente,
        'direcciones': direcciones,
        # 'pedidos': pedidos,
    }
    
    return render(request, 'perfil.html', context)


@login_required(login_url='login_cliente')
def editar_perfil(request):
    """Editar información del perfil"""
    try:
        cliente = Cliente.objects.get(email=request.user.email)
    except Cliente.DoesNotExist:
        messages.error(request, 'No se encontró tu perfil')
        return redirect('perfil_cliente')
    
    if request.method == 'POST':
        # Actualizar datos
        cliente.tratamiento = request.POST.get('tratamiento')
        cliente.nombre = request.POST.get('nombre')
        cliente.apellidos = request.POST.get('apellidos')
        cliente.boletin = request.POST.get('boletin') == 'on'
        cliente.ofertas_asociados = request.POST.get('ofertas_asociados') == 'on'
        cliente.save()
        
        # Actualizar usuario de Django
        request.user.first_name = cliente.nombre
        request.user.last_name = cliente.apellidos
        request.user.save()
        
        messages.success(request, 'Perfil actualizado correctamente')
        return redirect('perfil_cliente')
    
    return render(request, 'editar_perfil.html', {'cliente': cliente})


@login_required(login_url='login_cliente')
def agregar_direccion(request):
    """Agregar nueva dirección"""
    try:
        cliente = Cliente.objects.get(email=request.user.email)
    except Cliente.DoesNotExist:
        messages.error(request, 'No se encontró tu perfil')
        return redirect('perfil_cliente')
    
    if request.method == 'POST':
        form = DireccionClienteForm(request.POST)
        if form.is_valid():
            direccion = form.save(commit=False)
            direccion.cliente = cliente
            
            # Si es predeterminada, quitar predeterminada de las demás
            if direccion.es_predeterminada:
                cliente.direcciones.update(es_predeterminada=False)
            
            direccion.save()
            messages.success(request, 'Dirección agregada correctamente')
            return redirect('perfil_cliente')
    else:
        form = DireccionClienteForm()
    
    return render(request, 'direccion_form.html', {
        'form': form,
        'title': 'Agregar Dirección'
    })


@login_required(login_url='login_cliente')
def editar_direccion(request, direccion_id):
    """Editar dirección existente"""
    try:
        cliente = Cliente.objects.get(email=request.user.email)
        direccion = cliente.direcciones.get(id=direccion_id)
    except (Cliente.DoesNotExist, Direccion.DoesNotExist):
        messages.error(request, 'Dirección no encontrada')
        return redirect('perfil_cliente')
    
    if request.method == 'POST':
        form = DireccionClienteForm(request.POST, instance=direccion)
        if form.is_valid():
            direccion = form.save(commit=False)
            
            # Si es predeterminada, quitar predeterminada de las demás
            if direccion.es_predeterminada:
                cliente.direcciones.exclude(id=direccion.id).update(es_predeterminada=False)
            
            direccion.save()
            messages.success(request, 'Dirección actualizada correctamente')
            return redirect('perfil_cliente')
    else:
        form = DireccionClienteForm(instance=direccion)
    
    return render(request, 'direccion_form.html', {
        'form': form,
        'title': 'Editar Dirección'
    })


@login_required(login_url='login_cliente')
def eliminar_direccion(request, direccion_id):
    """Eliminar dirección"""
    try:
        cliente = Cliente.objects.get(email=request.user.email)
        direccion = cliente.direcciones.get(id=direccion_id)
        direccion.delete()
        messages.success(request, 'Dirección eliminada correctamente')
    except (Cliente.DoesNotExist, Direccion.DoesNotExist):
        messages.error(request, 'Dirección no encontrada')
    
    return redirect('perfil_cliente')