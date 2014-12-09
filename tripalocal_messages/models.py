from django.db import models

# Create your models here.
class Aliases(models.Model):
    mail = models.CharField(max_length=100)
    destination = models.CharField(max_length=100)
    enabled = models.BooleanField(default = True)

class Domains(models.Model):
    domain = models.CharField(max_length=100)
    transport = models.CharField(max_length=100, default="virtual:")
    enabled = models.BooleanField(default = True)

class Users(models.Model):
    id = models.CharField(max_length=100, primary_key=True)
    name = models.CharField(max_length=100)
    uid = models.IntegerField(default = 5000)
    gid = models.IntegerField(default = 5000)
    home = models.CharField(max_length=100, default = "/var/spool/mail/virtual")
    maildir = models.CharField(max_length=100)
    enabled = models.BooleanField(default = True)
    change_password = models.BooleanField(default = True)
    clear = models.CharField(max_length=100, default = "ChangeMe")
    crypt = models.CharField(max_length=100, null=True)
    quota = models.IntegerField(null=True)