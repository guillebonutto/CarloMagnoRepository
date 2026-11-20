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
    talles = forms.ModelMultipleChoiceField(
        queryset=Talle.objects.all(),
        widget=forms.CheckboxSelectMultiple(),
        label="Talles disponibles",
        required=False,
    )

    class Meta:
        model = Producto
        fields = [
            'codigo',
            'nombre',
            'descripcion',
            'precio',
            'categoria',
            'marca',
            'imagen',
            'esta_activo',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['colores'].label_from_instance = lambda obj: obj.hex_code
        self.fields['colores'].queryset = Color.objects.order_by('order', 'nombre')
        self.fields['talles'].queryset = Talle.objects.order_by('order', 'nombre')
        if self.instance.pk:
            stock_variants = self.instance.stock_items.all()
            self.initial['colores'] = stock_variants.values_list(
                'color_id', flat=True,
            ).distinct()
            self.initial['talles'] = stock_variants.values_list(
                'talle_id', flat=True,
            ).distinct()

    def save(self, commit=True):
        product = super().save(commit=commit)
        if commit:
            product.sync_stock_variants(
                self.cleaned_data['colores'],
                self.cleaned_data['talles'],
            )
        return product


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
