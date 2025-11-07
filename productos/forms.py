from django import forms
from django.utils.safestring import mark_safe
from productos.models import Producto, Color

class ProductoForm(forms.ModelForm):
    colores = forms.ModelMultipleChoiceField(
        queryset=Color.objects.all(),
        widget=forms.CheckboxSelectMultiple(),
        label="Colores disponibles"
    )

    class Meta:
        model = Producto
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['colores'].label_from_instance = lambda obj: obj.hex_code
