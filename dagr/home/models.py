from django.db import models

class DAGR(models.Model):
    GUID = models.CharField(max_length=255, primary_key=True)
    docName = models.CharField(max_length=255)
    storePath = models.CharField(max_length=255)
    docSize = models.FloatField()
    createTime = models.DateField()
    docCreator = models.CharField(max_length=255)
    docParent = models.CharField(max_length=255)
    docChild = models.CharField(max_length=255)

class Categories(models.Model):
    category = models.CharField(max_length=255, primary_key=True)
    docID = models.ForeignKey(DAGR)

class Keywords(models.Model):
    keywords = models.CharField(max_length=255, primary_key=True)
    docID = models.ForeignKey(DAGR)
