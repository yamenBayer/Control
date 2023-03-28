from datetime import datetime
from email.policy import default
from django.db import models
from django.conf import settings
from django.contrib.auth.models import User


class Profile(models.Model):
    title = models.CharField(max_length=25)
    owner = models.OneToOneField(User, related_name='owner' , on_delete= models.CASCADE)
    role = models.CharField(max_length=25,default="None")
    photo = models.ImageField(upload_to='static/cover-images/%y/%m/%d/',default = 'static/cover-images/default/Login.png')
    isPrime = models.BooleanField(default = False)
    tasks = models.IntegerField(default=0)
    o_tasks = models.IntegerField(default=0)
    projects = models.IntegerField(default=0)
    o_projects = models.IntegerField(default=0)
    fullRate = models.CharField(max_length=100,default="0%")

    def __str__(self):
        return self.title

class ProductPhoto(models.Model):
    title = models.CharField(max_length=50)
    photo = models.ImageField(upload_to='static/products-images/%y/%m/%d/',default = 'static/products-images/default/product.png')

    def __str__(self):
        return self.title



   

class Team(models.Model):
    title = models.CharField(max_length=25, unique = True)
    short = models.CharField(max_length=7, default = '')
    photo = models.ImageField(upload_to='static/team-images/%y/%m/%d/',default = 'static/team-images/default/defaultTeam.jpg')
    leader = models.ForeignKey(Profile, related_name='leader' , on_delete= models.CASCADE)
    members = models.ManyToManyField(Profile, related_name='members')
    admins = models.ManyToManyField(Profile, related_name='admins')
    description = models.TextField()
    created_Date = models.DateField(default=datetime.now)
    projects = models.IntegerField(default=0)
    o_projects = models.IntegerField(default=0)

    def __str__(self):
        return self.title

class Product(models.Model):
    title = models.CharField(max_length=50, unique=True)
    description = models.TextField()
    type = models.CharField(max_length=50)
    price = models.FloatField(default = 0)
    photos = models.ManyToManyField(ProductPhoto, related_name='photos')
    created_Date = models.DateField(default=datetime.now)
    team = models.ForeignKey(Team, related_name='TeamForProduct', on_delete=models.CASCADE)
    link = models.CharField(max_length=500)

    def __str__(self):
        return self.title
    
class Team_Request(models.Model):
    title = models.CharField(max_length=15,default="Team Request")
    teamToJoin = models.ForeignKey(Team, related_name='Team_to_join', on_delete=models.CASCADE)
    userToJoin = models.ForeignKey(Profile, related_name='User_to_join', on_delete= models.CASCADE)
    isUser = models.BooleanField(default=False)
    created_Date = models.DateField(default=datetime.now)
    
    def __str__(self):
        return self.title



class Project(models.Model):
    title = models.CharField(max_length=50, unique = True)
    team = models.ForeignKey(Team, related_name='TeamForProject', on_delete=models.CASCADE)
    projectLeader = models.ForeignKey(Profile, related_name='projectLeader' , on_delete= models.CASCADE)
    progress = models.CharField(max_length=100,default="0%")
    description = models.TextField() 
    members = models.ManyToManyField(Profile, related_name='projectMembers')   
    is_Done = models.BooleanField(default=False)
    is_Outdated = models.BooleanField(default=False)
    started_Date = models.DateField(default=datetime.now)
    finishedDate = models.DateField(default=datetime.now)
    deadLine = models.IntegerField(default=1)
    days_left = models.IntegerField(default=0)
    tasks = models.IntegerField(default=0)
    o_tasks = models.IntegerField(default=0)


    def __str__(self):
        return self.title


    
class Task(models.Model):
    title = models.CharField(max_length=100)
    author = models.ForeignKey(Profile, related_name='author' , on_delete= models.CASCADE)
    forUser = models.ForeignKey(Profile, related_name='TaskUser', on_delete= models.CASCADE)
    project = models.ForeignKey(Project, related_name='Project', on_delete=models.CASCADE)
    description = models.TextField()    
    created_Date = models.DateField(default=datetime.now)
    modified_Date = models.DateTimeField(auto_now_add=True, blank=True)
    finishedDate = models.DateField(default=datetime.now)
    deadLine = models.IntegerField(default=1)
    is_Done = models.BooleanField(default=False)
    is_Outdated = models.BooleanField(default=False)
    pending = models.BooleanField(default=False)
    days_left = models.IntegerField(default=0)
    progress = models.CharField(max_length=100,default="0%")
    dependsOn = models.ForeignKey('self', related_name='dependTask', on_delete=models.CASCADE, null = True, blank=True)
    suggestion = models.ForeignKey(Profile, related_name='suggest_to', on_delete=models.CASCADE, null = True, blank=True)


    def __str__(self):
        return self.title

class PersonProjectRate(models.Model):
    person = models.ForeignKey(Profile, related_name='personProjectRate', on_delete=models.CASCADE)
    project = models.CharField(max_length=50)
    tasksNum = models.IntegerField(default=0)
    doneTasksNum = models.IntegerField(default=0)
    rate = models.CharField(max_length=100,default="0%")

    def __str__(self):
        return self.person.owner.username +" | "+ self.project

class PersonTeamRate(models.Model):
    person = models.ForeignKey(Profile, related_name='personTeamRate', on_delete=models.CASCADE, null = True)
    team = models.CharField(max_length=50)
    projectNum = models.IntegerField(default=0)
    doneProjectNum = models.IntegerField(default=0)
    rate = models.CharField(max_length=100,default="0%")

    def __str__(self):
        return self.person.owner.username +" | "+ self.team

class Notification(models.Model):
    title = models.CharField(max_length=10000,default="Task Notification")
    created_Date = models.DateField(default=datetime.now)
    toBeSeen = models.BooleanField(default=False)
    isSeen = models.BooleanField(default=False)
    forUser = models.ForeignKey(Profile, related_name='forUserNoty', on_delete= models.CASCADE)

class Task_suggest(models.Model):
    task = models.ForeignKey(Task, related_name='suggested_Task',on_delete=models.CASCADE)
    fromUser = models.ForeignKey(Profile, related_name='suggFromUser', on_delete=models.CASCADE)
    forUser = models.ForeignKey(Profile, related_name='suggForUser', on_delete= models.CASCADE)
    created_Date = models.DateField(default=datetime.now)
