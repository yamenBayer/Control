import imp
from django.contrib import admin
from .models import Notification,PersonProjectRate,PersonTeamRate, ProductPhoto, Product, Profile, Project, Task, Task_suggest, Team, Team_Request

admin.site.register(Task)
admin.site.register(Project)
admin.site.register(Team)
admin.site.register(Profile)
admin.site.register(Team_Request)
admin.site.register(Notification)
admin.site.register(Task_suggest)
admin.site.register(ProductPhoto)
admin.site.register(Product)
admin.site.register(PersonProjectRate) 
admin.site.register(PersonTeamRate)

