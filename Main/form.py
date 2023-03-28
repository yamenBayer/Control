from django import forms
from Main.models import Profile, Project, Team,Task

class TeamForm(forms.ModelForm):
    class Meta:
        model = Team
        fields=['title']

class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields=['title']

class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields=['title']

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields=['title']