from django.forms import ModelForm
from django import forms
from .models import *

class TerrainForm(ModelForm):
    class Meta :
        model = ChoixTerrain
        fields = ['secteur', 'commune', 'province', 'quartier', 'dateChoix', 'PV', 'extrait_PA', 'extrait_CarteRisques', 'refFonciere']

        labels = {
            'secteur': 'Secteur',
            'commune': 'Commune',
            'province': 'Province',
            'quartier': 'Quartier',
            'dateChoix': 'Date de Choix',
            'PV': 'PV',
            'extrait_PA': 'Extrait de PA',
            'extrait_CarteRisques': 'Extrait de la Carte Risques',
            'refFonciere': 'Reference Fonciere',
        }

        widgets = {
            'dateChoix': forms.DateInput(attrs={'type': 'date'}),
            'PV': forms.ClearableFileInput(attrs={'multiple': False}),
            'extrait_PA': forms.ClearableFileInput(attrs={'multiple': False}),
            'extrait_CarteRisques': forms.ClearableFileInput(attrs={'multiple': False}),
        }

class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['refMessage', 'dateMessage', 'objet', 'fichierPDFMessage']
        labels = {
            'refMessage': 'Reference Message',
            'dateMessage': 'Date Message',
            'objet': 'Object',
            'fichierPDFMessage': 'Fichier PDF de Message',
        }
        widgets = {
            'dateMessage': forms.DateInput(attrs={'type': 'date'}),
            'fichierPDFMessage': forms.ClearableFileInput(attrs={'multiple': False}),
        }

class CommissionForm(forms.Form):
    refMessage = forms.ModelChoiceField(queryset=Message.objects.all(), label="Reference de Terrain")
    participant_cin = forms.CharField(max_length=20, label="CIN")
    participant_nom = forms.CharField(max_length=100, label="Nom")
    participant_prenom = forms.CharField(max_length=100, label="Prenom")
    participant_mail = forms.EmailField(label="Email")
    participant_role = forms.CharField(max_length=100, label="Role")


class SearchCommissionForm(forms.Form):
    refMessage = forms.ModelChoiceField(queryset=Message.objects.all(), label="Reference de Terrain")
