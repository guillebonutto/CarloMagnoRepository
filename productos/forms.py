from django import forms
from django.utils.safestring import mark_safe
from productos.models import Color, Producto, Talle

class ProductoForm(forms.ModelForm):
    colores = forms.ModelMultipleChoiceField(
        queryset=Color.objects.all(),
        widget=forms.CheckboxSelectMultiple(),
        label="Colores disponibles",
        required=False
    )

    class Meta:
        model = Producto
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['colores'].label_from_instance = lambda obj: obj.hex_code


class IngresoStockPorLectorForm(forms.Form):
    codigo = forms.CharField(
        label='Código del artículo',
        max_length=50,
        strip=True,
        widget=forms.TextInput(attrs={
            'autofocus': True,
            'autocomplete': 'off',
            'placeholder': 'Escaneá el código del artículo',
        }),
    )
    color = forms.ModelChoiceField(
        label='Color',
        queryset=Color.objects.filter(esta_activo=True).order_by('order', 'nombre'),
    )
    talle = forms.ModelChoiceField(
        label='Talle',
        queryset=Talle.objects.filter(esta_activo=True).order_by('order', 'nombre'),
    )
