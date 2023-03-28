from datetime import date
from json import dumps
from tempfile import template
from turtle import title
from Main.form import ProjectForm, TeamForm,TaskForm
from unicodedata import name
from django.shortcuts import redirect, render
from Main.models import  ProductPhoto, Notification, PersonTeamRate, Product, Project, Task, Task_suggest, Team,Profile, Team_Request
from django.views.generic import View
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import authenticate ,login,logout
from Main.serializers import ProfileSerializer
from Project import settings
from django.core.mail import send_mail,EmailMessage,BadHeaderError
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode,urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_text
from . tokens import generate_token
from django.contrib.auth.context_processors import auth
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.forms import PasswordResetForm
from django.db.models.query_utils import Q
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
import json
import requests
from django.utils import timezone


# Public variables
myProfile = None

def rev(query):
  array = []

  for object in reversed(query):
    array.append(object)

  return array

def get_active_users(project):
  users = []
  count = project.members.all().count()
  for task in Task.objects.filter(project = project).order_by('-modified_Date'):
    if count == 0:
      break
    if task.forUser not in users:
        users.append(task.forUser)
        count-=1
  return users

def increase_members_rate(members):
    for member in members:
      member.projects += 1
      member.save()

def decrease_members_rate(members):
    for member in members:
      member.projects -= 1
      member.save()

def get_home_values():
  inprogress_projects = Project.objects.filter(is_Done=False, members = myProfile).count()
  inprogress_tasks = Task.objects.filter(is_Done=False, forUser = myProfile).count()

  latest_projects = Project.objects.filter(members=myProfile).order_by('-started_Date')[:5]
  latest_tasks = rev(Task.objects.filter(project__in=latest_projects,dependsOn=None).order_by('-created_Date')[:5])

  return inprogress_projects, inprogress_tasks, latest_projects, latest_tasks

def project_update(project):
  values = value = 0
  projectdaysLeft_update(project)
  for tasks in Task.objects.filter(project = project):
    value = tasks.progress[:-1]
    value = int('0' + value)
    values += value
  if Task.objects.filter(project = project).count():
    values = values/Task.objects.filter(project = project).count()
  values = float(f'{values:.2f}')
  values = str(values)
  values = values+"%"
  project.progress = values
  project.save()

def projectdaysLeft_update(project):
  project.days_left = project.deadLine - (date.today() - project.started_Date).days
  if project.days_left < 0 and project.is_Outdated == False:
    project.is_Outdated = True
    for member in project.members.all():
      member.o_projects += 1
      member.save()
    project.team.o_projects += 1
    project.team.save()
  project.save()

def send_push_notification(subscription, message):
    headers = {'Authorization': f'Bearer {settings.WEBPUSH_VAPID_PRIVATE_KEY}'}
    payload = {
        'subscription': subscription,
        'payload': json.dumps({'title': 'New Notification', 'message': message}),
    }
    response = requests.post(settings.WEBPUSH_SENDER_URL, headers=headers, json=payload)
    if response.status_code == 201:
        print('Notification sent successfully')
    else:
        print('Failed to send notification')


def Update(request):
  global myProfile
  try:
    myProfile = Profile.objects.get(owner = request.user)
  except:
    pass

class EmailBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        UserModel = get_user_model()
        try:
            user = UserModel.objects.get(email=username)
        except UserModel.DoesNotExist:
          try:
            user = UserModel.objects.get(username=username)
          except UserModel.DoesNotExist:
            return None
        if user.check_password(password):
          return user
        return None

def getlatestProjects(team):
    project = rev(Project.objects.filter(team = team, members = myProfile,is_Done=False).order_by('-started_Date')[:3])
    return project

def Broadcast(array, title):
  for member in array:
    noty = Notification(title = title,forUser = member)
    noty.save()


def getFlag():
  flag = False
  if Notification.objects.filter(forUser = myProfile,isSeen = False).exists() or Team_Request.objects.filter(userToJoin = myProfile, isUser = False).exists() or Task_suggest.objects.filter(forUser = myProfile).exists():
    flag = True
  teams = getProfileTeams(myProfile)
  for team in teams:
    if team.leader == myProfile:
      if Team_Request.objects.filter(teamToJoin = team, isUser = True).exists():
        flag = True
        break
  return flag

def checkMembership(person, teams):
  result = False
  counter = 0
  peak = len(teams)
  print(peak)
  for team in teams:
    if person in team.members.all():
      counter += 1

  if counter == peak:
    result = True

  return result

def getListNames(people):
  names = []
  for person in people:
    names.append(person.title)

  return names

def getMyPeople(prof, myTeams):
  myPeople = []
  final = []
  if myTeams:
    for team in myTeams:
      # if team.leader == prof:
        for person in team.members.all():
          if person not in myPeople:
            myPeople.append(person)

  for member in myPeople:
    if checkMembership(member, myTeams):
      final.append(member)

  return final

def getProfileRate(prof):
      tasksNum = Task.objects.filter(forUser = prof,is_Done = True).count()
      rate = 0
      if (Task.objects.filter(forUser = prof).count() > 0):
        rate = tasksNum/Task.objects.filter(forUser = prof).count()
      rate *= 100
      rate = "{:.2f}".format(rate)
      rate = float(rate)
      prof.doneTasksNum = tasksNum
      prof.rated = rate
      prof.save()
      pass

def getProfileTeams(prof):
  teams = []
  all_teams = Team.objects.all()
  for team_ins in all_teams:
    if prof in team_ins.members.all():
        teams.append(team_ins)
  return teams

def UpdateProject(project):
    values = value = 0
    for tasks in Task.objects.filter(project = project):
          value = tasks.progress[:-1]
          value = int(value)
          values += value
    if Task.objects.filter(project = project).count():
            values = values/Task.objects.filter(project = project).count()
    values = float(f'{values:.2f}')
    values = str(values)
    values = values+"%"
    project.progress = values
    project.days_left = project.deadLine - (date.today() - project.started_Date).days
    project.save()

def UpdateTasks(tasks):
  for task in tasks:
    task.days_left = task.deadLine - (date.today() - task.created_Date).days
    if task.days_left < 0 and not task.is_Outdated and not task.is_Done and not task.pending:
      task.is_Outdated = True
      task.forUser.o_tasks += 1
      task.project.o_tasks += 1
      task.forUser.save()
      task.project.save()
    elif task.days_left >= 0 and task.is_Outdated and not task.is_Done:
      task.is_Outdated = False
    task.save()

def UpdateTask(task):
  if task:
    task.days_left = task.deadLine - (date.today() - task.created_Date).days
    if task.days_left < 0 and not task.is_Outdated and not task.is_Done and not task.pending:
      task.is_Outdated = True
      task.forUser.o_tasks += 1
      task.project.o_tasks += 1
      task.forUser.save()
      task.project.save()
    elif task.days_left >= 0 and task.is_Outdated and not task.is_Done:
      task.is_Outdated = False
    task.save()


def toHome(request):
    if request.user.username == "admin":
          logout(request)
    if request.user.is_authenticated:
      Update(request)
      notysCount,teamNoty,flag,taskNoty,suggNoty = getNotifications()
      myTeams = getProfileTeams(myProfile)
      inprogress_projects,inprogress_tasks,latest_projects,latest_tasks = get_home_values()
      return render(request , 'index.html',{
      'myProfile':myProfile,
      'myTeams':myTeams,
      'latest_projects': latest_projects,
      'latest_tasks': latest_tasks,
      'inprogress_projects': inprogress_projects,
      'inprogress_tasks': inprogress_tasks,

      'notysCount': notysCount,
      'teamNoty': teamNoty,
      'flag': flag,
      'taskNoty': taskNoty,
      'suggNoty': suggNoty,


      })

    return redirect('login')

def getTasksReq():
    pending_tasks = []

    user_Teams = Team.objects.filter(members=myProfile)
    user_projects = Project.objects.filter(team__in=user_Teams)

    for project in user_projects:
      if project.projectLeader == myProfile or project.team.leader == myProfile:
        tasks = Task.objects.filter(project__in=user_projects, pending=True)
        for task in tasks:
          pending_tasks.append(task)
    return pending_tasks

def getNotifications():
  notysCount = teamNoty = suggNoty = notyCount2 = taskNoty = 0
  flag = False
  notyCount = Team_Request.objects.filter(userToJoin = myProfile, isUser = False).count()
  teams = getProfileTeams(myProfile)
  for team in teams:
    notyCount2 = Team_Request.objects.filter(teamToJoin = team, isUser = True).count()
  teamNoty = notyCount + notyCount2

  notysCount = Notification.objects.filter(forUser = myProfile, toBeSeen = False).count()
  suggNoty = Task_suggest.objects.filter(forUser = myProfile).count()
  taskNoty = getTasksReq()
  if taskNoty is not None:
    taskNoty = len(taskNoty)
  else:
    taskNoty = 0

  flag = getFlag()

  return notysCount,teamNoty,flag,taskNoty,suggNoty



def changePhoto(request):
  if request.user.is_authenticated:
    if request.method == "POST":
      img = request.FILES.get('img')
      try:
        Update(request)

      except Exception:
        return redirect('Home')
      myProfile.photo = img
      myProfile.save()
  return redirect('profile')

def changeTeamPhoto(request, tid):
  if request.user.is_authenticated:
    if request.method == "POST":
      img = request.FILES.get('img')
      team = Team.objects.get(id = tid)
      team.photo = img
      team.save()
  return redirect('toViewTeam', tid)

def changeRole(request):
  if request.user.is_authenticated:
    if request.method == "POST":
      role = request.POST['role']
      try:
        Update(request)
      except Exception:
        return redirect('Home')
      myProfile.role = role
      myProfile.save()
  return redirect('profile')


def suggestion(request, tid):
  if request.user.is_authenticated:
      newUser = request.POST['sugg']
      try:
        Update(request)
      except Exception:
        return redirect('Home')
      user1 = None
      if User.objects.filter(username = newUser).exists():
        user1 = User.objects.get(username = newUser)
        prof = Profile.objects.get(owner = user1)
        task = None
        if Task.objects.filter(id = tid).exists():
          task = Task.objects.get(id = tid)
          if Task_suggest.objects.filter(task = task, fromUser = myProfile, forUser = prof).exists():
            messages.info(request, 'Suggestion request already sent!')
            return redirect('toViewProject', task.project.id)
          else:
            suggReq = Task_suggest(task = task, fromUser = myProfile, forUser = prof)
            suggReq.save()
            messages.info(request, 'Suggestion request sent successfully!')
            return redirect('toViewProject', task.project.id)
  return redirect('Home')



def getMessages(request, tm):
  if request.user.is_authenticated:
    team = Team.objects.get(title = tm)
    Msg = team.messages.all()
    return JsonResponse({"Msg":list(Msg.values())})

def signup(request):
  if request.user.is_authenticated:
    return redirect('Home')
  if request.method == "POST":
    uname = request.POST['uname']
    fname = request.POST['fname']
    lname = request.POST['lname']
    email = request.POST['email']
    role = request.POST['role']
    pass1 = request.POST['pswd1']
    pass2 = request.POST['pswd2']
    img = request.FILES.get('img')

    if User.objects.filter(username=uname):
      messages.error(request,"Username is already exist!")
      return redirect('signup')

    elif User.objects.filter(email=email):
      messages.error(request,"Email is already exist!")
      return redirect('signup')

    elif len(uname)>10:
      messages.error(request,"Username must be under 10 characters!")
      return redirect('signup')

    elif len(pass1)<8:
      messages.error(request,"Password must be at least 8 characters!")
      return redirect('signup')

    elif pass1 != pass2:
      messages.error(request, "passwoed didn't match!")
      return redirect('signup')

    elif not uname.isalnum():
       messages.error(request, "Username must be Alpha-Numeric!")
       return redirect('signup')
    else:
       my_user = User.objects.create_user(uname,email,pass1)
       my_user.first_name = fname
       my_user.last_name = lname
       my_user.is_active = False
       my_user.save()

       title = fname + ' ' + lname
       new_profile = Profile(title = title,owner = my_user,role = role)
       print(img)
       if(img):
         new_profile.photo = img
       new_profile.save()


    #    messages.success(request,"We have send you a confirmation email, please check your email.")
    # # email
    #    subject = "Welcome to Control"
    #    message = "Hello " + my_user.first_name + " \n" + "Thank you for visiting our website.\nWe have also send you a confirmation email, please confirm your email address to activate your account.\n\nControl Team "
    #    from_email = settings.EMAIL_HOST_USER
    #    to_list = [my_user.email]
    #    send_mail(subject, message, from_email, to_list, fail_silently =False)


    # # send confirmation email
    #    current_site = get_current_site(request)
    #    email_subject = "Confirm your email @ CONTROL"
    #    email_message = render_to_string('email_confirmation.html',{
    #      'name': my_user.first_name,
    #      'domain': current_site.domain,
    #      'uid': urlsafe_base64_encode(force_bytes(my_user.pk)),
    #      'token': generate_token.make_token(my_user)
    #     })
    #    email = EmailMessage(
    #      email_subject,
    #      email_message,
    #      settings.EMAIL_HOST_USER,
    #      [my_user.email]
    #    )
    #    email.fail_silently = True
    #    email.send()

       return redirect('login')


  return render(request, "auth/signup.html")




def log_in(request):
   if request.user.is_authenticated:
    return redirect('Home')
   if request.method == "POST":
      username = request.POST['uname']
      pass1 = request.POST['pswd1']

      user = authenticate(username=username, password=pass1)
      if user is not None:
        if user.is_active:
          login(request, user)
          global myProfile
          try:
            Update(request)
          except:
            pass
          return redirect('Home')
        else:
          messages.error(request, "The account is not activated yet!")
          return redirect('login')

      messages.error(request, "Incorrect information!")
      return redirect('login')

   return render(request, "auth/login.html")



def signout(request):
    logout(request)
    return redirect('Home')

def activate(request, uidb64, token):
  try:
    uid = force_text(urlsafe_base64_decode(uidb64))
    my_user = User.objects.get(pk=uid)
  except(TypeError,ValueError,OverflowError,User.DoesNotExist):
    my_user = None

  if my_user is not None and generate_token.check_token(my_user,token):
    my_user.is_active = True
    my_user.save()
    return render(request,'auth/activationSucess.html')
  else:
    return render(request, "auth/activationFailed.html")



def create_team(request):
  if request.method == "POST":
    teamTitle = request.POST['title']
    if Team.objects.filter(title = teamTitle).exists():
      messages.error(request, "Team name already exists!")
      return redirect('findTeams')
    else:
      form = TeamForm(request.POST)
      new_Team = form.save(commit=False)
      new_Team.title = request.POST['title']
      new_Team.short = request.POST['logo']
      new_Team.description = request.POST['description']
      Update(request)
      new_Team.leader = myProfile

      new_Team.save()

      new_Team.members.add(myProfile)
      if not PersonTeamRate.objects.filter(person = myProfile, team = new_Team.title).exists():
        newPersonTeamRate = PersonTeamRate(person = myProfile, team = new_Team.title)
        newPersonTeamRate.save()
      return redirect('toViewTeam', new_Team.id)


  else:
      print(request,"error")

def reqJoinTeam(request, tid):
  if request.user.is_authenticated:
    if Team.objects.filter(id = tid).exists():
      team = Team.objects.get(id = tid)
      try:
        Update(request)
      except Exception:
        return redirect('findTeams')
      if Team_Request.objects.filter(userToJoin = myProfile, teamToJoin = team).exists():
          messages.warning(request, "Request Already sent!")
          return redirect('findTeams')
      else:
          joinRequest = Team_Request(userToJoin = myProfile, teamToJoin = team, isUser = True)
          joinRequest.save()
          messages.success(request, "Request successfully sent!")
          return redirect('findTeams')
    else:
      messages.error(request, "Team not found!")
      return redirect('findTeams')
  return redirect('Home')



def toViewTeam(request, tid):
  if request.user.is_authenticated:
    if Profile.objects.filter(owner = request.user).exists():
      try:
        Update(request)
        notysCount,teamNoty,flag,taskNoty,suggNoty = getNotifications()
      except Exception:
        return redirect('Home')
      team = Team.objects.get(id = tid)
      myTeams = getProfileTeams(myProfile)
      all_Projects = Project.objects.filter(team = team, is_Done = False).order_by('-started_Date')
      latest_projects = getlatestProjects(team)
      # projectsRate = 0
      for project in all_Projects:
        project_update(project)

        # projectsRate = total/Project.objects.filter(team = team).count()


      # dataDictionary = {
      #   "projectsRate": projectsRate
      # }

      # dataJSON = dumps(dataDictionary)
      latest_products = rev(Product.objects.filter(team=team).order_by('-created_Date')[:3])
      inprogress_projects = Project.objects.filter(is_Done=False, team = team).count()
      return render(request, "Team/TeamMain.html", {
        'team':team,
        'myTeams':myTeams,
        'all_Projects': all_Projects,
        'latest_projects': latest_projects,
        'latest_products': latest_products,
        # 'dataJSON': dataJSON,
        'myProfile':myProfile,
        'inprogress_projects':inprogress_projects,

              'notysCount': notysCount,
      'teamNoty': teamNoty,
      'flag': flag,
      'taskNoty': taskNoty,
      'suggNoty': suggNoty,
        })

  return redirect('Home')

def toViewMembers(request, tid):
  if request.user.is_authenticated:
    Update(request)
    notysCount,teamNoty,flag,taskNoty,suggNoty = getNotifications()
    if Team.objects.filter(id = tid).exists():
      team = Team.objects.get(id = tid)
      myTeams = getProfileTeams(myProfile)
      all_Projects = Project.objects.filter(team = team, is_Done = False).order_by('-started_Date')
      latest_projects = getlatestProjects(team)
      return render(request, "Team/Members.html", {
        'team':team,
        'myTeams':myTeams,
        'all_Projects': all_Projects,
        'latest_projects': latest_projects,
        'myProfile':myProfile,

              'notysCount': notysCount,
      'teamNoty': teamNoty,
      'flag': flag,
      'taskNoty': taskNoty,
      'suggNoty': suggNoty,
        })
  return redirect('Home')

def toViewProjectMembers(request, tid, pid):
  if request.user.is_authenticated:
    Update(request)
    notysCount,teamNoty,flag,taskNoty,suggNoty = getNotifications()
    if Team.objects.filter(id = tid).exists():
      team = Team.objects.get(id = tid)
      project = Project.objects.get(id = pid)
      myTeams = getProfileTeams(myProfile)
      all_Projects = Project.objects.filter(team = team, is_Done = False).order_by('-started_Date')
      latest_projects = getlatestProjects(team)
      return render(request, "Project/Members.html", {
        'team':team,
        'project':project,
        'myTeams':myTeams,
        'all_Projects': all_Projects,
        'latest_projects': latest_projects,
        'myProfile':myProfile,

              'notysCount': notysCount,
      'teamNoty': teamNoty,
      'flag': flag,
      'taskNoty': taskNoty,
      'suggNoty': suggNoty,

        })
  return redirect('Home')


def doneProjects(request, tid):
  if request.user.is_authenticated:
    Update(request)
    notysCount,teamNoty,flag,taskNoty,suggNoty = getNotifications()
    print(myProfile)
    if Team.objects.filter(id = tid).exists():
      team = Team.objects.get(id = tid)
      myTeams = getProfileTeams(myProfile)
      complated_Projects = Project.objects.filter(team = team, is_Done = True)
      all_Projects = Project.objects.filter(team = team, is_Done = False).order_by('-started_Date')
      latest_projects = getlatestProjects(team)
      return render(request, "Team/Complated_Projects.html", {
        'team':team,
        'myTeams':myTeams,
        'all_Projects': all_Projects,
        'latest_projects': latest_projects,
        'complated_Projects': complated_Projects,
        'myProfile':myProfile,

              'notysCount': notysCount,
      'teamNoty': teamNoty,
      'flag': flag,
      'taskNoty': taskNoty,
      'suggNoty': suggNoty,
        })
  return redirect('Home')

def teamProducts(request, tid):
  if request.user.is_authenticated:
    Update(request)
    notysCount,teamNoty,flag,taskNoty,suggNoty = getNotifications()
    if Team.objects.filter(id = tid).exists():
      team = Team.objects.get(id = tid)
      myTeams = getProfileTeams(myProfile)
      all_Projects = Project.objects.filter(team = team, is_Done = False).order_by('-started_Date')
      latest_projects = getlatestProjects(team)
      all_products = Product.objects.filter(team = team).order_by('-created_Date')
      return render(request, "Team/Products.html", {
        'team':team,
        'myTeams':myTeams,
        'all_Projects': all_Projects,
        'latest_projects': latest_projects,
        'all_products': all_products,
        'myProfile':myProfile,

              'notysCount': notysCount,
      'teamNoty': teamNoty,
      'flag': flag,
      'taskNoty': taskNoty,
      'suggNoty': suggNoty,
        })
  return redirect('Home')



def toViewProject(request, pid):
  if request.user.is_authenticated:
    Update(request)
    notysCount,teamNoty,flag,taskNoty,suggNoty = getNotifications()
    myTeams = getProfileTeams(myProfile)
    if Project.objects.filter(id = pid, is_Done = False).exists():
      project = Project.objects.get(id = pid)
      UpdateProject(project)
      team = project.team
      if myProfile == team.leader or myProfile in project.members.all():
        all_Projects = Project.objects.filter(team = team, is_Done = False).order_by('-started_Date')
        latest_projects = getlatestProjects(team)
        active_users = get_active_users(project)
        inprogress_tasks = Task.objects.filter(is_Done=False, project = project).count()
        return render(request, "Project/ProjectMain.html", {
            'myProfile':myProfile,
            'team':team,
            'myTeams':myTeams,
            'all_Projects':all_Projects,
            'latest_projects':latest_projects,
            'project':project,
            'active_users':active_users,
            'inprogress_tasks':inprogress_tasks,

                  'notysCount': notysCount,
      'teamNoty': teamNoty,
      'flag': flag,
      'taskNoty': taskNoty,
      'suggNoty': suggNoty,
            })
    else:
      messages.error(request, 'This project cannot be accessed, or it is already finished!')
  return redirect('Home')

def addMembers(request, uid):
  if request.method == "POST":
    try:
      Update(request)
    except Profile.DoesNotExist:
      return redirect('Home')
    teamTitle = request.POST['team']
    team = Team.objects.get(title = teamTitle)


    if Profile.objects.filter(id = uid).exists():
        try:
          userProf = Profile.objects.get(id = uid)
        except Profile.DoesNotExist:
          return redirect('findPeople')
        for member in team.members.all():
          if userProf == member:
              messages.error(request, "User already in the team!")
              return redirect('findPeople')
        if Team_Request.objects.filter(userToJoin = userProf, teamToJoin = team).exists():
          messages.error(request, "Request Already sent!")
          return redirect('findPeople')
        else:
          joinRequest = Team_Request(userToJoin = userProf, teamToJoin = team)
          joinRequest.save()
          messages.error(request, "Request successfully sent!")
          return redirect('findPeople')
    else:
        messages.error(request, "User not found!")
        return redirect('findPeople')

def addProjectMember(request, pid):
  if request.user.is_authenticated:
    username = request.POST['username']
    try:
      project = Project.objects.get(id = pid)
      Update(request)
      member = Profile.objects.get(owner = User.objects.get(username = username))
    except Project.DoesNotExist or Profile.DoesNotExist or User.DoesNotExist:
      return redirect('Home')

    if myProfile == project.projectLeader or myProfile == project.team.leader:
      project.members.add(member)
      project.save()

  return redirect('toViewProject', pid)

def addTask(request, pid):
  if request.user.is_authenticated:
    if request.method == "POST":
      Update(request)
      project = Project.objects.get(id = pid)
      if project.team.leader == myProfile:
        form = TaskForm(request.POST)
        new_Task = form.save(commit=False)
        new_Task.author = myProfile
        new_Task.project = project
        new_Task.title = request.POST['title']
        uname = request.POST['forUser']
        user = User.objects.get(username = uname)
        userProfile = Profile.objects.get(owner = user)
        new_Task.forUser = userProfile
        new_Task.description = request.POST['description']
        new_Task.deadLine = request.POST['deadLine']
        new_Task.team = project.team
        depend = request.POST['depend']
        if depend is not None and depend != "":
          dependOnTask = Task.objects.get(id = depend)
          if dependOnTask is not None:
            new_Task.dependsOn = dependOnTask
        new_Task.save()
        new_noty = Notification(title = "There is a new task for you. |  Project name: "+new_Task.project.title+" | Task number: "+str(new_Task.id) ,forUser = new_Task.forUser)
        new_noty.save()
        print(new_Task.modified_Date)

        return redirect('toViewTasks',pid)

  return redirect('Home')


def convert(request, pid):
  if request.user.is_authenticated:
    if request.method == "POST":
      Update(request)
      project = Project.objects.get(id = pid)
      if project.team.leader == myProfile or project.projectLeader == myProfile:

        title = request.POST['title']
        type = request.POST['type']
        description = request.POST['description']
        price = request.POST['price']
        link = request.POST['link']
        img1 = request.FILES.get('img1')
        img2 = request.FILES.get('img2')
        img3 = request.FILES.get('img3')

        new_product = Product(
          title = title,
          description = description,
          type = type,
          price = price,
          team = project.team,
          link = link
        )

        new_product.save()
        img_1 = ProductPhoto(title="img_"+str(project.id), photo = img1)
        img_2 = ProductPhoto(title="img_"+str(project.id), photo = img2)
        img_3 = ProductPhoto(title="img_"+str(project.id), photo = img3)
        img_1.save()
        img_2.save()
        img_3.save()

        new_product.photos.add(img_1)
        new_product.photos.add(img_2)
        new_product.photos.add(img_3)
        new_product.save()

        Broadcast(project.team.members.all(), "The project with name: "+project.title+" has been converted to product ("+str(new_product.title)+") successfully")

        tid = project.team.id
        project.delete()
        return redirect('teamProducts',tid)

  return redirect('Home')

def addProject(request, tid):
  if request.user.is_authenticated:
    if request.method == "POST":
      Update(request)
      team = Team.objects.get(id = tid)
      if myProfile == team.leader or myProfile in team.admins.all():
        form = ProjectForm(request.POST)
        new_Project = form.save(commit=False)

        new_Project.team = team
        new_Project.title = request.POST['title']
        new_Project.description = request.POST['description']
        new_Project.deadLine = request.POST['deadLine']
        memberOwner = request.POST['projectLeader']

        if memberOwner == "Me":
          p_leader = myProfile
        else:
          owner = User.objects.get(username = memberOwner)
          try:
            p_leader = Profile.objects.get(owner = owner)
          except Profile.DoesNotExist:
            return redirect('toViewTeam', tid)

        new_Project.projectLeader = p_leader
        new_Project.save()

        new_Project.members.add(p_leader)
        if p_leader != myProfile:
          new_Project.members.add(myProfile)


        return redirect('toViewProject', new_Project.id)
  return redirect('Home')

def taskDelete(request, tid, type):
  if request.user.is_authenticated:
    Update(request)
    if Task.objects.filter(id=tid).exists():
      task = Task.objects.get(id=tid)
      if task.project.projectLeader == myProfile or task.project.team.leader == myProfile:
        task.delete()
      match type:
        case "0":
            return redirect('Home')
        case "1":
            return redirect('toViewTasks',task.project.id)
        case "2":
            return redirect('toViewMyTasks',task.project.id)
        case "3":
            return redirect('toViewDoneTasks',task.project.id)
        case "4":
            return redirect('toViewMyDoneTasks',task.project.id)
        case "5":
            return redirect('toViewOutdatedTasks',task.project.id)

    return redirect('Home')

def projectDelete(request, pid):
    if request.user.is_authenticated:
      Update(request)
      if Project.objects.filter(id=pid).exists():
        project = Project.objects.get(id=pid)
        team = project.team
        if team.leader == myProfile or project.projectLeader == myProfile:
          project.delete()
          messages.error(request, "Project deleted successfully!")
        else:
          messages.error(request, "You need premessions!")
      return redirect('toViewTeam', team.id)
    else:
     return redirect('Home')

def projectRecover(request, pid):
    if request.user.is_authenticated:
      Update(request)
      if Project.objects.filter(id=pid).exists():
        project = Project.objects.get(id=pid)
        team = project.team
        if team.leader == myProfile or project.projectLeader == myProfile:
          project.is_Done = False
          project.team.projects -= 1
          project.team.save()
          project.save()
          decrease_members_rate(project.members.all())
        else:
          messages.error(request, "You need premessions!")
      return redirect('toViewProject', project.id)

    return redirect('Home')

def memberRemove(request,tm, mid):
  if request.user.is_authenticated:
    try:
      Update(request)
    except Exception:
      return redirect('Home')
    team = Team.objects.get(id = tm)
    if team.leader == myProfile:
      user = Profile.objects.get(id = mid)
      noty = Notification(title = team.leader.owner.username+" kicked you out of the " + team.title, forUser = user)
      team.members.remove(user)
      noty.save()
    return redirect('toViewMembers', team.id)

def projectMemberRemove(request,pid, mid):
  if request.user.is_authenticated:
    try:
      Update(request)
    except Exception:
      return redirect('Home')
    project = Project.objects.get(id = pid)
    if project.projectLeader == myProfile:
      user = Profile.objects.get(id = mid)
      noty = Notification(title = project.projectLeader.owner.username+" kicked you out of the project: " + project.title, forUser = user)
      project.members.remove(user)
      noty.save()
    return redirect('toViewProjectMembers', project.team.id, project.id)

def memberPromote(request,tm, mid):
  if request.user.is_authenticated:
    try:
      Update(request)
    except Exception:
      return redirect('Home')
    team = Team.objects.get(id = tm)
    if team.leader == myProfile:
      user = Profile.objects.get(id = mid)
      noty = Notification(title = team.leader.owner.username+" promoted you to be an admin in " + team.title, forUser = user)
      team.admins.add(user)
      noty.save()
    return redirect('toViewMembers', team.id)

def teamRemove(request, tm):
  if request.user.is_authenticated:
    try:
      Update(request)
      team = Team.objects.get(id = tm)
    except Exception:
      return redirect('Home')

    if team.leader == myProfile:
      for member in team.members.all():
        if member != myProfile:
          noty = Notification(title = myProfile.owner.username +" disassembled " + team.title, forUser = member)
          noty.save()
      team.delete()
  return redirect('Home')

def leaveTeam(request,tm, mem):
  if request.user.is_authenticated:
    try:
      Update(request)
      user2 = Profile.objects.get(id = mem)
      team = Team.objects.get(id = tm)
    except Exception:
      return redirect('Home')

    if myProfile == user2:
      if user2 in team.members.all():
        team.members.remove(user2)
        noty = Notification(title = user2.owner.username +" left " + team.title, forUser = team.leader)
        noty.save()
  return redirect('Home')

def toViewTeam_Req(request):
  if request.user.is_authenticated:
    team_req = []
    try:
      Update(request)
      notysCount,teamNoty,flag,taskNoty,suggNoty = getNotifications()
    except Exception:
      return redirect('Home')
    myTeams = getProfileTeams(myProfile)

    team = team_req_noty2 = team_req_noty = None
    if Team_Request.objects.filter(userToJoin = myProfile, isUser = False).exists():
      t_req = Team_Request.objects.filter(userToJoin = myProfile, isUser = False)
      for tr in t_req:
        team_req.append(tr)

    if Team.objects.filter(leader = myProfile):
      teams = Team.objects.filter(leader = myProfile)
      for team in teams:
        t_req = Team_Request.objects.filter(teamToJoin = team, isUser = True)
        for tr in t_req:
          team_req.append(tr)


    return render(request,"Notifications/Team_Requests.html",{
      'team_req':team_req,
      'myProfile':myProfile,
      'new_Team':team,
      'myTeams':myTeams,

            'notysCount': notysCount,
      'teamNoty': teamNoty,
      'flag': flag,
      'taskNoty': taskNoty,
      'suggNoty': suggNoty,
      })
  else:
    return redirect('Home')

def toViewTask_Req(request):
  if request.user.is_authenticated:
    Update(request)
    notysCount,teamNoty,flag,taskNoty,suggNoty = getNotifications()
    pending_tasks = getTasksReq()
    myTeams = getProfileTeams(myProfile)

    return render(request,"Notifications/Task_Approve_Requests.html",{
      'pending_tasks':pending_tasks,
      'myProfile':myProfile,
      'myTeams':myTeams,

            'notysCount': notysCount,
      'teamNoty': teamNoty,
      'flag': flag,
      'taskNoty': taskNoty,
      'suggNoty': suggNoty,
      })
  else:
    return redirect('Home')

def toViewNotifications(request):
  if request.user.is_authenticated:
    try:
      Update(request)
      notysCount,teamNoty,flag,taskNoty,suggNoty = getNotifications()
    except Exception:
      return redirect('Home')
    myTeams = getProfileTeams(myProfile)

    notifications = Notification.objects.filter(forUser = myProfile).order_by('-created_Date')[:25]
    Notification.objects.filter(forUser = myProfile).exclude(id__in=notifications.values('id')).delete()
    notifications = rev(notifications)

    for noty in notifications:
      if noty.isSeen == False:
        if noty.toBeSeen == False:
          noty.toBeSeen = True
        else:
          noty.isSeen = True
      noty.save()

    return render(request,"Notifications/Notification.html",{
    'myTeams':myTeams,
    'notifications':notifications,
    'myProfile':myProfile,

          'notysCount': notysCount,
      'teamNoty': teamNoty,
      'flag': flag,
      'taskNoty': taskNoty,
      'suggNoty': suggNoty,
    })
  else:
    return redirect('Home')


def toViewSuggestion(request):
  if request.user.is_authenticated:
    try:
      Update(request)
      notysCount,teamNoty,flag,taskNoty,suggNoty = getNotifications()
    except Exception:
      return redirect('Home')
    myTeams = getProfileTeams(myProfile)
    suggRequest = Task_suggest.objects.filter(forUser = myProfile)
    return render(request,"Notifications/Suggest_Requests.html",{
      'suggRequest':suggRequest,
      'myProfile':myProfile,
      'myTeams':myTeams,

            'notysCount': notysCount,
      'teamNoty': teamNoty,
      'flag': flag,
      'taskNoty': taskNoty,
      'suggNoty': suggNoty,
      })
  else:
    return redirect('Home')

def applySuggestion(request, sid):
  if request.user.is_authenticated:
    if Profile.objects.filter(owner = request.user).exists():
      try:
        Update(request)
      except Exception:
        return redirect('Home')
      suggReq = Task_suggest.objects.filter(id = sid)
      if suggReq.exists():
        suggRequest = Task_suggest.objects.get(id = sid)
        if suggRequest is not None:
          if myProfile == suggRequest.forUser:
            task = suggRequest.task
            task.forUser = suggRequest.forUser
            task.save()
            noty = Notification(title = "[ ^_^ ] "+ suggRequest.forUser.owner.username+" accept your suggest to do the task with number: "+str(suggRequest.task.id), forUser = suggRequest.fromUser)
            noty.save()
            suggRequest.delete()
            if Task_suggest.objects.filter(task = suggRequest.task).exists():
              Task_suggest.objects.filter(task = suggRequest.task).delete()
            return redirect('toViewSuggestion')
  return redirect('Home')

def rejectSuggestion(request, sid):
  if request.user.is_authenticated:
    try:
      Update(request)
    except Exception:
      return redirect('Home')
    suggReq = Task_suggest.objects.filter(id = sid)
    if suggReq.exists():
      suggRequest = Task_suggest.objects.get(id = sid)
      if myProfile == suggRequest.forUser:
        noty = Notification(title = "[ x_x ] "+ suggRequest.forUser.owner.username+" reject your suggest to do the task with number: "+str(suggRequest.task.id), forUser = suggRequest.fromUser)
        noty.save()
        suggRequest.delete()
        return redirect('toViewSuggestion')
  return redirect('Home')



def JoinTeam(request, reqId):
  if request.user.is_authenticated:
    try:
      noty = Team_Request.objects.get(id = reqId)
    except Exception:
      return redirect('toViewTeam_Req')
    Update(request)
    user = noty.userToJoin
    team = noty.teamToJoin
    if (noty.isUser and myProfile == team.leader) or (noty.isUser == False and myProfile == user):
      team.members.add(user)
      if not PersonTeamRate.objects.filter(person = user, team = team.title).exists():
        newPersonTeamRate = PersonTeamRate(person = user, team = team.title)
        newPersonTeamRate.save()
      noty = Notification(title = user.owner.username+" joined "+team.title , forUser = team.leader)
      noty2 = Notification(title = "You are now "+team.title+ " member!", forUser = user)
      noty.save()
      noty2.save()
      Team_Request.objects.get(id = reqId).delete()
    return redirect('toViewTeam_Req')
  return redirect('Home')

def RequestReject(request, id):
  if request.user.is_authenticated:
    if Team_Request.objects.filter(id = id).exists():
      teamReq = Team_Request.objects.get(id = id)
      if teamReq.isUser:
        noty = Notification(title = teamReq.teamToJoin.title+" reject your request to join the team", forUser = teamReq.userToJoin)
      else:
        noty = Notification(title = teamReq.userToJoin.owner.username+" reject your request to join " + teamReq.teamToJoin.title, forUser = teamReq.teamToJoin.leader)

      noty.save()
      teamReq.delete()


    return redirect('toViewTeam_Req')


def saveTaskChanges(request, tid,pid):
  if request.user.is_authenticated:
    pValue = request.POST['process']
    project = Project.objects.get(id = pid)
    task = Task.objects.get(id = tid)
    if int(pValue) < 0:
      pValue = '0'
    if int(pValue) > 100:
      pValue = '100'
    value = pValue + '%'
    task.progress = value
    task.modified_Date = timezone.now()
    task.save()
    project_update(project)
    if task.is_Outdated:
      return redirect('toViewOutdatedTasks',project.id)
    return redirect('toViewTasks',project.id)
  else:
    return redirect('Home')

def finishTask(request, tid):
  if request.user.is_authenticated:
    task = Task.objects.get(id = tid)
    project = task.project
    if task.forUser == myProfile or task.project.projectLeader == myProfile or task.project.team.leader == myProfile:
      task.is_Done = True
      task.pending = False
      task.finishedDate = task.modified_Date.date()
      for task2 in Task.objects.filter(project = project):
        if task2.dependsOn == task:
          task2.dependsOn = None
          task2.created_Date = date.today()
          task2.save()
      task.modified_Date = timezone.now()
      task.save()
      noty = Notification(title = task.forUser.owner.username+" finished the task with number: " + str(task.id),forUser = project.team.leader)
      noty.save()
      if not task.is_Outdated:
        task.forUser.tasks += 1
        task.project.tasks += 1
        task.project.save()
        task.forUser.save()

      return redirect('toViewTasks',project.id)

    return redirect('Home')

def applyTask(request, tid):
  if request.user.is_authenticated:
    task = Task.objects.get(id = tid)
    project = task.project
    if task.forUser == myProfile or task.project.projectLeader == myProfile or task.project.team.leader == myProfile:
      task.pending = True
      task.modified_Date = timezone.now()
      task.save()
      noty = Notification(title = task.forUser.owner.username+" applied the task with number: " + str(task.id),forUser = project.team.leader)
      noty.save()

    return redirect('toViewTasks',project.id)

  return redirect('Home')

def recoverTask(request, tid):
  if request.user.is_authenticated:
    task = Task.objects.get(id = tid)
    project = task.project
    if task.forUser == myProfile or task.project.projectLeader == myProfile or task.project.team.leader == myProfile:
      task.pending = False
      task.modified_Date = timezone.now()
      task.save()
      noty = Notification(title = task.forUser.owner.username+" recover the task with number: " + str(task.id),forUser = project.team.leader)
      noty.save()

    return redirect('toViewTasks',project.id)

  return redirect('Home')

def taskSearch(request):
  if request.user.is_authenticated:

    try:
      Update(request)
    except Exception:
      return redirect('Home')
    myTeams = getProfileTeams(myProfile)
    if request.method == "POST":
      searchResault = request.POST['search']
      if searchResault.isnumeric():
        if Task.objects.filter(id = searchResault).exists():
          newTask = Task.objects.get(id = searchResault)
          if myProfile in newTask.project.members.all():
            UpdateTask(newTask)
            return render(request,'Search.html',{'myTeams':myTeams,'task':newTask,'myProfile':myProfile})
          else:
            messages.error(request, "You are not allowed to see the task!")
            return render(request,'Search.html',{'myTeams':myTeams,'task':None,'myProfile':myProfile})
        else:
          messages.error(request, "Task Not Found!")
          return render(request,'Search.html',{'myTeams':myTeams,'task':None,'myProfile':myProfile})
      else:
        messages.error(request, "You must input a number in the search!")
        return render(request,'Search.html',{'myTeams':myTeams,'task':None,'myProfile':myProfile})

    return redirect('Home')
  else:
    return redirect('login')




def password_reset_request(request):
	if request.method == "POST":
		password_reset_form = PasswordResetForm(request.POST)
		if password_reset_form.is_valid():
			data = password_reset_form.cleaned_data['email']
			associated_users = User.objects.filter(Q(email=data))
			if associated_users.exists():

				for user in associated_users:
					subject = "Password Reset Requested"
					email_template_name = "Password/password_reset_email.txt"
					c = {
          "email":user.email,
					'domain':get_current_site(request).domain,
					'site_name': 'CONTROL',
					"uid": urlsafe_base64_encode(force_bytes(user.pk)),
					"user": user,
					'token': default_token_generator.make_token(user),
					'protocol': 'http',
					}
					email = render_to_string(email_template_name, c)
					try:
						send_mail(subject, email, settings.EMAIL_HOST_USER , [user.email], fail_silently=False)
					except BadHeaderError:
						return HttpResponse('Invalid header found.')
					return redirect ("/password_reset/done/")


	password_reset_form = PasswordResetForm()
	return render(request=request, template_name="Password/password_reset.html", context={"password_reset_form":password_reset_form})


def taskDeadlineExtend(request, tid):
  if Task.objects.filter(id = tid).exists():
    task = Task.objects.get(id = tid)
    if request.method == "POST":
      extendedAmount = request.POST['deadLine']
      extendedAmountINT = int(extendedAmount)
      task.deadLine = task.deadLine + extendedAmountINT
      task.save()
      if task.is_Outdated:
        return redirect('toViewOutdatedTasks',task.project.id)
      return redirect('toViewTasks',task.project.id)
  return redirect('toViewTeam')

def find_teams(request):
  if request.user.is_authenticated:
    Update(request)
    notysCount,teamNoty,flag,taskNoty,suggNoty = getNotifications()
    teams = Team.objects.filter()
    myTeams = getProfileTeams(myProfile)
    requestedTeams = []
    for team in teams:
      if Team_Request.objects.filter(userToJoin = myProfile, teamToJoin = team).exists():
        requestedTeams.append(team)

    names = getListNames(teams)

    context = {
            'ListNames' : names,
    }
    namesData = dumps(context)

    return render(request, "Discover/Find_Teams.html",{
      'teams':teams,
      'myTeams':myTeams,
      'namesData':namesData,
      'requestedTeams':requestedTeams,
      'myProfile':myProfile,

            'notysCount': notysCount,
      'teamNoty': teamNoty,
      'flag': flag,
      'taskNoty': taskNoty,
      'suggNoty': suggNoty,
      })
  return redirect('login')

def find_people(request):
  canInvite = False
  if request.user.is_authenticated:
    Update(request)
    notysCount,teamNoty,flag,taskNoty,suggNoty = getNotifications()
    people = Profile.objects.filter()
    myTeams = getProfileTeams(myProfile)
    inviteTeams = []
    myPeople = getMyPeople(myProfile, myTeams)
    if myTeams:
      for team in myTeams:
        if myProfile == team.leader:
          canInvite = True
          inviteTeams.append(team)

    names = getListNames(people)

    context = {
            'ListNames' : names,
    }
    namesData = dumps(context)

    return render(request, "Discover/Find_People.html",{
      'inviteTeams':inviteTeams,
      'people':people,
      'canInvite':canInvite,
      'myTeams':myTeams,
      'namesData':namesData,
      'myPeople':myPeople,
      'myProfile':myProfile,

            'notysCount': notysCount,
      'teamNoty': teamNoty,
      'flag': flag,
      'taskNoty': taskNoty,
      'suggNoty': suggNoty,
      })
  return redirect('login')

def profile(request):
  if request.user.is_authenticated:
    try:
      Update(request)
    except Exception:
      return redirect('Home')
    myTeams = getProfileTeams(myProfile)
    getProfileRate(myProfile)
    return render(request, "Profile.html", {'myProfile':myProfile,'myTeams':myTeams})
  else:
    return redirect('Home')

def toMyTeams(request):
  if request.user.is_authenticated:
    try:
      Update(request)
    except Exception:
      return redirect('Home')
    myTeams = getProfileTeams(myProfile)
    return render(request, "MyTeams.html", {'myTeams':myTeams,'myProfile':myProfile})
  else:
    return redirect('Home')

def changeProjectLeader(request, pid):
  if request.user.is_authenticated:
    try:
      Update(request)
      project = Project.objects.get(id = pid)
      username = request.POST['newProjectLeader']
      newProjectLeader = Profile.objects.get(owner = User.objects.get(username = username))
    except Profile.DoesNotExist or Project.DoesNotExist or User.DoesNotExist:
      return redirect('Home')
    if myProfile == project.team.leader:
      project.projectLeader = newProjectLeader
      project.save()
  return redirect('toViewProject', pid)

def finishProject(request, pid):
  if request.user.is_authenticated:
    Update(request)
    project = Project.objects.get(id = pid)
    if project.projectLeader == myProfile or project.team.leader == myProfile:
      project.is_Done = True
      project.finishedDate = date.today()
      project.save()
      project.team.projects += 1
      project.team.save()
      increase_members_rate(project.members.all())
      Broadcast(project.team.members.all(), title = myProfile.owner.username+" finished the project with name: " + str(project.title))
      return redirect('doneProjects',project.team.id)
  return redirect('Home')

def toViewTasks(request, pid):
  if request.user.is_authenticated:
    Update(request)
    notysCount,teamNoty,flag,taskNoty,suggNoty = getNotifications()
    myTeams = getProfileTeams(myProfile)
    if Project.objects.filter(id = pid).exists():
      project = Project.objects.get(id = pid)
      team = project.team
      tasks = Task.objects.filter(project = project, is_Done = False, is_Outdated = False,pending=False).order_by('-created_Date')
      UpdateTasks(tasks)
      if myProfile == team.leader or myProfile in project.members.all():
        all_Projects = Project.objects.filter(team = team, members = myProfile)
        latest_projects = getlatestProjects(team)
        return render(request, "Project/TaskMain.html", {
            'location': 'Tasks (In Process)',
            'myProfile':myProfile,
            'team':team,
            'myTeams':myTeams,
            'all_Projects':all_Projects,
            'latest_projects':latest_projects,
            'tasks':tasks,
            'project':project,

                  'notysCount': notysCount,
      'teamNoty': teamNoty,
      'flag': flag,
      'taskNoty': taskNoty,
      'suggNoty': suggNoty,
            })
  return redirect('Home')

def toViewMyTasks(request, pid):
  if request.user.is_authenticated:
    Update(request)
    notysCount,teamNoty,flag,taskNoty,suggNoty = getNotifications()
    myTeams = getProfileTeams(myProfile)
    if Project.objects.filter(id = pid).exists():
      project = Project.objects.get(id = pid)
      team = project.team
      tasks = Task.objects.filter(project = project, forUser = myProfile, is_Done = False, is_Outdated = False,pending=False).order_by('-created_Date')
      UpdateTasks(tasks)
      if myProfile == team.leader or myProfile in project.members.all():
        all_Projects = Project.objects.filter(team = team, is_Done = False).order_by('-started_Date')
        latest_projects = getlatestProjects(team)
        return render(request, "Project/TaskMain.html", {
            'location': 'My Tasks (In Process)',
            'myProfile':myProfile,
            'team':team,
            'myTeams':myTeams,
            'all_Projects':all_Projects,
            'latest_projects':latest_projects,
            'tasks':tasks,
            'project':project,

                  'notysCount': notysCount,
      'teamNoty': teamNoty,
      'flag': flag,
      'taskNoty': taskNoty,
      'suggNoty': suggNoty,
            })
  return redirect('Home')

def toViewDoneTasks(request, pid):
  if request.user.is_authenticated:
    Update(request)
    myTeams = getProfileTeams(myProfile)
    if Project.objects.filter(id = pid).exists():
      project = Project.objects.get(id = pid)
      team = project.team
      tasks = Task.objects.filter(project = project, is_Done = True,pending=False).order_by('-created_Date')
      UpdateTasks(tasks)
      if myProfile == team.leader or myProfile in project.members.all():
        all_Projects = Project.objects.filter(team = team, is_Done = False).order_by('-started_Date')
        latest_projects = getlatestProjects(team)
        return render(request, "Project/TaskMain.html", {
            'location': 'Tasks (Completed)',
            'myProfile':myProfile,
            'team':team,
            'myTeams':myTeams,
            'all_Projects':all_Projects,
            'latest_projects':latest_projects,
            'tasks':tasks,
            'project':project
            })
  return redirect('Home')

def toViewMyDoneTasks(request, pid):
  if request.user.is_authenticated:
    Update(request)
    notysCount,teamNoty,flag,taskNoty,suggNoty = getNotifications()
    myTeams = getProfileTeams(myProfile)
    if Project.objects.filter(id = pid).exists():
      project = Project.objects.get(id = pid)
      team = project.team
      tasks = Task.objects.filter(project = project, forUser = myProfile, is_Done = True,pending=False).order_by('-created_Date')
      UpdateTasks(tasks)
      if myProfile == team.leader or myProfile in project.members.all():
        all_Projects = Project.objects.filter(team = team, is_Done = False).order_by('-started_Date')
        latest_projects = getlatestProjects(team)
        return render(request, "Project/TaskMain.html", {
            'location': 'My Tasks (Completed)',
            'myProfile':myProfile,
            'team':team,
            'myTeams':myTeams,
            'all_Projects':all_Projects,
            'latest_projects':latest_projects,
            'tasks':tasks,
            'project':project,

                  'notysCount': notysCount,
      'teamNoty': teamNoty,
      'flag': flag,
      'taskNoty': taskNoty,
      'suggNoty': suggNoty,
            })
  return redirect('Home')

def toViewOutdatedTasks(request, pid):
  if request.user.is_authenticated:
    Update(request)
    notysCount,teamNoty,flag,taskNoty,suggNoty = getNotifications()
    myTeams = getProfileTeams(myProfile)
    if Project.objects.filter(id = pid).exists():
      project = Project.objects.get(id = pid)
      team = project.team
      tasks = Task.objects.filter(project = project, forUser = myProfile, is_Outdated = True,pending=False).order_by('-created_Date')
      UpdateTasks(tasks)
      if myProfile == team.leader or myProfile in project.members.all():
        all_Projects = Project.objects.filter(team = team, is_Done = False).order_by('-started_Date')
        latest_projects = getlatestProjects(team)
        return render(request, "Project/Outdated.html", {
            'location': 'Outdated Tasks',
            'myProfile':myProfile,
            'team':team,
            'myTeams':myTeams,
            'all_Projects':all_Projects,
            'latest_projects':latest_projects,
            'tasks':tasks,
            'project':project,

                  'notysCount': notysCount,
      'teamNoty': teamNoty,
      'flag': flag,
      'taskNoty': taskNoty,
      'suggNoty': suggNoty,
            })
  return redirect('Home')

def toViewPendingTasks(request, pid):
  if request.user.is_authenticated:
    Update(request)
    notysCount,teamNoty,flag,taskNoty,suggNoty = getNotifications()
    myTeams = getProfileTeams(myProfile)
    if Project.objects.filter(id = pid).exists():
      project = Project.objects.get(id = pid)
      team = project.team
      tasks = Task.objects.filter(project = project, forUser = myProfile, pending = True).order_by('-created_Date')
      UpdateTasks(tasks)
      if myProfile == team.leader or myProfile in project.members.all():
        all_Projects = Project.objects.filter(team = team, is_Done = False).order_by('-started_Date')
        latest_projects = getlatestProjects(team)
        return render(request, "Project/Pending.html", {
            'location': 'Pending Tasks',
            'myProfile':myProfile,
            'team':team,
            'myTeams':myTeams,
            'all_Projects':all_Projects,
            'latest_projects':latest_projects,
            'tasks':tasks,
            'project':project,

                  'notysCount': notysCount,
      'teamNoty': teamNoty,
      'flag': flag,
      'taskNoty': taskNoty,
      'suggNoty': suggNoty,
            })
  return redirect('Home')