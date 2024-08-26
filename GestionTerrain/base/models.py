from django.db import models
from django.contrib.auth.models import User
import os

def choix_terrain_upload_path(instance, filename):
    return f'uploads/{instance.refMessage.refMessage}/{filename}'

def message_upload_path(instance, filename):
    return f'uploads/{instance.refMessage}/{filename}'


class Message(models.Model):
    refMessage = models.CharField(max_length=20, primary_key=True)
    dateMessage = models.DateField()
    objet = models.CharField(max_length=100)
    fichierPDFMessage = models.FileField(upload_to=message_upload_path)

    def __str__(self):
        return self.refMessage

class ChoixTerrain(models.Model):
    choixID = models.AutoField(primary_key=True)
    geo = models.CharField(max_length=100, default="")
    secteur = models.CharField(max_length=100)
    surface = models.FloatField()
    commune = models.CharField(max_length=100)
    province = models.CharField(max_length=100)
    quartier = models.CharField(max_length=100, blank=True, null=True)  # Optional field
    dateChoix = models.DateField()
    PV = models.FileField(upload_to=choix_terrain_upload_path)
    extrait_PA = models.FileField(upload_to=choix_terrain_upload_path)
    extrait_CarteRisques = models.FileField(upload_to=choix_terrain_upload_path)
    refFonciere = models.CharField(max_length=100)
    refMessage = models.OneToOneField(Message, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.choixID)

    def get_uploaded_files(self):
        folder_path = os.path.join('uploads', self.refMessage.refMessage)
        if os.path.exists(folder_path) and os.path.isdir(folder_path):
            return [filename for filename in os.listdir(folder_path) if filename.endswith('.pdf')]
        return []
    
class Participant(models.Model):
    cin = models.CharField(max_length=20, primary_key=True)
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    mail = models.EmailField()
    role = models.CharField(max_length=100)

    def is_linked_to_any_commission(self):
        return Commission.objects.filter(participants=self).exists()
    def __str__(self):
        return f"{self.nom} {self.prenom}"

class Commission(models.Model):
    id_commission = models.AutoField(primary_key=True)
    participants = models.ManyToManyField(Participant)
    choixTerrains = models.ManyToManyField(ChoixTerrain)
    refMessage = models.ForeignKey(Message, on_delete=models.CASCADE)

    def __str__(self):
        return f"Commission {self.id_commission} for {self.refMessage.refMessage}"

class ResponsableAgence(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.user.username

class ChefImmediat(models.Model):
    responsable = models.OneToOneField(ResponsableAgence, on_delete=models.CASCADE)

class Rapport(models.Model):
    rapportID = models.AutoField(primary_key=True)
    nomRapport = models.CharField(max_length=100)
    dateRapport = models.DateField()
    emplacementRapport = models.CharField(max_length=255)
    choixTerrain = models.ForeignKey(ChoixTerrain, on_delete=models.CASCADE)

    def __str__(self):
        return self.nomRapport
