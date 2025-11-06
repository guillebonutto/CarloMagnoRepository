from django.shortcuts import render, redirect
from django.core.mail import send_mail
from django.conf import settings

def contact(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        message = request.POST.get('message')
        
        # Aquí puedes agregar la lógica para enviar el email
        # send_mail(
        #     f'Nuevo mensaje de {name}',
        #     message,
        #     email,
        #     [settings.EMAIL_HOST_USER],
        #     fail_silently=False,
        # )
        
        return redirect('contact')
    return render(request, 'contacto.html')
