from datetime import date
from json import dumps
from tempfile import template
from turtle import title
from Team_Management.form import ProjectForm, TeamForm,TaskForm
from unicodedata import name
from django.conf import settings
from django.shortcuts import redirect, render
from Team_Management.models import  Notification, PersonTeamRate, Project, Task, Task_suggest, Team,Profile, Team_Request
from django.views.generic import View
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import authenticate ,login,logout
from Team_Management.serializers import ProfileSerializer
from myApp import settings
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

def getFlag(prof):
  flag = False
  if Notification.objects.filter(forUser = prof,isSeen = False).exists() or Team_Request.objects.filter(userToJoin = prof, isUser = False).exists() or Task_suggest.objects.filter(forUser = prof).exists():
    flag = True
  teams = getProfileTeams(prof)
  for team in teams:
    if team.leader == prof:
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
    values = str(values)
    values = values+"%"
    project.progress = values
    project.dyas_Left = project.deadLine - (date.today() - project.started_Date).days
    project.save()
    
    
def toHome(request):
    if request.user.username == "admin":
          logout(request)
    if request.user.is_authenticated:
      profile = Profile.objects.get(owner = request.user)
      myTeams = getProfileTeams(profile)

      return render(request , 'index.html',{
      'myProfile':profile,
      'myTeams':myTeams
      })
      
    return render(request , 'index.html')

def realtime(request):
  notysCount = teamNoty = suggNoty = notyCount2 = 0
  flag = False
  if request.user.is_authenticated:
    profile = Profile.objects.get(owner = request.user)
    notyCount = Team_Request.objects.filter(userToJoin = profile, isUser = False).count()
    teams = getProfileTeams(profile)
    for team in teams:
      notyCount2 = Team_Request.objects.filter(teamToJoin = team, isUser = True).count()
    teamNoty = notyCount + notyCount2

    notysCount = Notification.objects.filter(forUser = profile, toBeSeen = False).count()
    suggNoty = Task_suggest.objects.filter(forUser = profile).count()
    flag = getFlag(profile)
    
  
  return JsonResponse({
    'notysCount':notysCount,
    'teamNoty':teamNoty,
    'flag':flag,
    'suggNoty':suggNoty
    })


class TaskJson(View):
    def get(self , *args  , **kwargs):
      tasks = list(Task.objects.values())
      return JsonResponse({'data' : tasks}, safe=False)

def changePhoto(request):
  if request.user.is_authenticated:
    if request.method == "POST":
      img = request.FILES.get('img')
      try:
        myProfile = Profile.objects.get(owner = request.user)
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
        myProfile = Profile.objects.get(owner = request.user)
      except Exception:
        return redirect('Home')
      myProfile.role = role
      myProfile.save()
  return redirect('profile')


def suggestion(request, tid):
  if request.user.is_authenticated:
      newUser = request.POST['sugg']
      try:
        myProfile = Profile.objects.get(owner = request.user)
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


       messages.success(request,"We have send you a confirmation email, please check your email.")
    # email 
       subject = "Welcome to CONTROL"
       message = "Hello " + my_user.first_name + " \n" + "Thank you for visiting our website.\n We have also send you a confirmation email, please confirm your email address to activate your account.\n\n UDTeam "
       from_email = settings.EMAIL_HOST_USER
       to_list = [my_user.email]
       send_mail(subject, message, from_email, to_list, fail_silently =True)


    # send confirmation email 
       current_site = get_current_site(request)
       email_subject = "Confirm your email @ CONTROL"
       email_message = render_to_string('email_confirmation.html',{
         'name': my_user.first_name,
         'domain': current_site.domain,
         'uid': urlsafe_base64_encode(force_bytes(my_user.pk)),
         'token': generate_token.make_token(my_user)
        })
       email = EmailMessage(
         email_subject,
         email_message,
         settings.EMAIL_HOST_USER,
         [my_user.email]
       )
       email.fail_silently = True
       email.send()

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
      profile = Profile.objects.get(owner = request.user)
      new_Team.leader = profile

      new_Team.save()

      new_Team.members.add(profile)
      if not PersonTeamRate.objects.filter(person = profile, team = new_Team.title).exists():
        newPersonTeamRate = PersonTeamRate(person = profile, team = new_Team.title)
        newPersonTeamRate.save()
      return redirect('toViewTeam', new_Team.id)  
              

  else:
      print(request,"error")

def reqJoinTeam(request, tid):
  if request.user.is_authenticated:
    if Team.objects.filter(id = tid).exists():
      team = Team.objects.get(id = tid)
      try:
        userProf = Profile.objects.get(owner = request.user)
      except Exception:
        return redirect('findTeams')
      if Team_Request.objects.filter(userToJoin = userProf, teamToJoin = team).exists():
          messages.error(request, "Request Already sent!")
          return redirect('findTeams')
      else:
          joinRequest = Team_Request(userToJoin = userProf, teamToJoin = team, isUser = True)
          joinRequest.save()
          messages.error(request, "Request successfully sent!")
          return redirect('findTeams') 
    else:
      messages.error(request, "Team not found!")
      return redirect('findTeams')
  return redirect('Home')
 


def toViewTeam(request, tid):
  if request.user.is_authenticated:
    if Profile.objects.filter(owner = request.user).exists():
      try:
        myProfile = Profile.objects.get(owner = request.user)
      except Exception:
        return redirect('Home')      
      team = Team.objects.get(id = tid)
      myTeams = getProfileTeams(myProfile)
      all_Projects = Project.objects.filter(team = team).order_by('started_Date')
      projectsRate = 0
      if all_Projects.exists():
        for project in all_Projects:
          values = value = total = 0
          project.dyas_Left = project.deadLine - (date.today() - project.started_Date).days
          for tasks in Task.objects.filter(project = project):
            value = tasks.progress[:-1]
            value = int('0' + value)
            values += value
          if Task.objects.filter(project = project).count():
            values = values/Task.objects.filter(project = project).count()
          total += values
          values = str(values)
          values = values+"%"
          project.progress = values
          
          project.save()

        projectsRate = total/Project.objects.filter(team = team).count()
      
      print(projectsRate)
      dataDictionary = {
        "projectsRate": projectsRate
      }

      dataJSON = dumps(dataDictionary)
        
      return render(request, "Team/TeamMain.html", {
        'team':team,
        'myTeams':myTeams,
        'all_Projects': all_Projects,
        'dataJSON': dataJSON,
        'myProfile':myProfile
        }) 

  return redirect('Home')

def toViewMembers(request, tid):
  if request.user.is_authenticated:
    profile = Profile.objects.get(owner = request.user)
    if Team.objects.filter(id = tid).exists():
      team = Team.objects.get(id = tid)
      myTeams = getProfileTeams(profile)
      all_Projects = Project.objects.filter(team = team)
      return render(request, "Team/Members.html", {
        'team':team,
        'myTeams':myTeams,
        'all_Projects': all_Projects,
        'myProfile':profile
        }) 
  return redirect('Home')

def toViewProject(request, pid):
  if request.user.is_authenticated:
    profile = Profile.objects.get(owner = request.user) 
    myTeams = getProfileTeams(profile)
    if Project.objects.filter(id = pid).exists():
      project = Project.objects.get(id = pid)
      UpdateProject(project)   
      team = project.team
      projectTasks = Task.objects.filter(project = project)
      if profile == team.leader or profile in project.members.all():
        all_Projects = Project.objects.filter(team = team)
        return render(request, "Team/ProjectMain.html", {
            'myProfile':profile,
            'team':team,
            'myTeams':myTeams,
            'all_Projects':all_Projects,
            'projectTasks':projectTasks,
            'project':project
            })  
  return redirect('Home')

def toViewTasks(request, pid):
  if request.user.is_authenticated:
    profile = Profile.objects.get(owner = request.user)
    if Project.objects.filter(id = pid).exists():
      project = Project.objects.get(id = pid)
      team = project.team
  for member in team.members.all():
        if member == profile:
          ldr = team.leader
          all_Tasks = Task.objects.filter(author = ldr, project= project).order_by('created_Date')
          my_Tasks = Task.objects.filter(forUser = profile, project= project).order_by('created_Date')
          if all_Tasks.exists():
            for task in all_Tasks:
              if task.is_Done == False:
                task.dyas_Left = task.deadLine - (date.today() - task.created_Date).days
                task.save()
          if my_Tasks.exists():
            for task in my_Tasks:
              if task.is_Done == False:
                task.dyas_Left = task.deadLine - (date.today() - task.created_Date).days
                task.save()
  pass

def addMembers(request, uid):
  if request.method == "POST":
    try:
      prof = Profile.objects.get(owner = request.user)
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
      profile = Profile.objects.get(owner = request.user)
      member = Profile.objects.get(owner = User.objects.get(username = username)) 
    except Project.DoesNotExist or Profile.DoesNotExist or User.DoesNotExist:
      return redirect('Home')

    if profile == project.projectLeader or profile == project.team.leader:
      project.members.add(member)
      project.save()
  
  return redirect('toViewProject', pid)

def addTask(request, pid):
  if request.user.is_authenticated:
    if request.method == "POST":
      profile = Profile.objects.get(owner = request.user)
      project = Project.objects.get(id = pid)
      if project.team.leader == profile:
        form = TaskForm(request.POST)
        new_Task = form.save(commit=False)
        new_Task.author = profile
        new_Task.project = project
        new_Task.title = request.POST['title']
        uname = request.POST['forUser']
        user = User.objects.get(username = uname)
        userProfile = Profile.objects.get(owner = user)
        new_Task.forUser = userProfile
        new_Task.description = request.POST['description']
        new_Task.deadLine = request.POST['deadLine']
        team = Team.objects.get(leader = profile)
        new_Task.team = team
        depend = request.POST['depend']
        if depend is not None and depend != "":
          dependOnTask = Task.objects.get(id = depend)
          if dependOnTask is not None:
            new_Task.dependsOn = dependOnTask
        new_Task.save()
        new_noty = Notification(title = "There is a new task for you. |  Project name: "+new_Task.project.title+" | Task number: "+str(new_Task.id) ,forUser = new_Task.forUser)
        new_noty.save()
        print(new_noty.title)
        return redirect('toViewProject',pid) 

  return redirect('Home') 

def addProject(request, tid):
  if request.user.is_authenticated:
    if request.method == "POST": 
      profile = Profile.objects.get(owner = request.user)
      team = Team.objects.get(id = tid)
      if profile == team.leader or profile in team.admins.all():
        form = ProjectForm(request.POST)
        new_Project = form.save(commit=False)

        new_Project.team = team
        new_Project.title = request.POST['title']
        new_Project.deschription = request.POST['description']
        new_Project.deadLine = request.POST['deadLine']
        memberOwner = request.POST['projectLeader']

        if memberOwner == "Me":
          p_leader = profile
        else:
          owner = User.objects.get(username = memberOwner)
          try:
            p_leader = Profile.objects.get(owner = owner)
          except Profile.DoesNotExist:
            return redirect('toViewTeam', tid)
        
        new_Project.projectLeader = p_leader
        new_Project.save()
        
        new_Project.members.add(p_leader)
        if p_leader != profile:
          new_Project.members.add(profile)

        
        return redirect('toViewProject', new_Project.id)  
  return redirect('Home')  

def taskDelete(request, tid):
  if request.user.is_authenticated:
    profile = Profile.objects.get(owner = request.user)
    if Task.objects.filter(id=tid, author = profile).exists():
      pid = Task.objects.get(id=tid, author = profile).project.id
      Task.objects.filter(id=tid, author = profile).delete()
      return redirect('toViewProject',pid)
    return redirect('Home')

def projectDelete(request, pid):
    if request.user.is_authenticated:
      profile = Profile.objects.get(owner = request.user)
      if Project.objects.filter(id=pid).exists():
        project = Project.objects.get(id=pid)
        team = project.team
        if team.leader == profile:
          project.delete()
      return redirect('toViewTeam', team.id)
    else:
     return redirect('Home') 

def memberRemove(request,tm, mid):
  if request.user.is_authenticated:
    try:
      prof = Profile.objects.get(owner = request.user)
    except Exception:
      return redirect('Home')
    team = Team.objects.get(id = tm)
    if team.leader == prof:
      user = Profile.objects.get(id = mid)
      noty = Notification(title = team.leader.owner.username+" kicked you out of the " + team.title, forUser = user)
      team.members.remove(user)
      noty.save()
    return redirect('toViewMembers', team.id) 

def memberPromote(request,tm, mid):
  if request.user.is_authenticated:
    try:
      prof = Profile.objects.get(owner = request.user)
    except Exception:
      return redirect('Home')
    team = Team.objects.get(id = tm)
    if team.leader == prof:
      user = Profile.objects.get(id = mid)
      noty = Notification(title = team.leader.owner.username+" promoted you to be an admin in " + team.title, forUser = user)
      team.admins.add(user)
      noty.save()
    return redirect('toViewMembers', team.id) 

def teamRemove(request, tm):
  if request.user.is_authenticated:
    try:
      prof = Profile.objects.get(owner = request.user)
      team = Team.objects.get(id = tm)
    except Exception:
      return redirect('Home')

    if team.leader == prof:
      for member in team.members.all():
        if member != prof:
          noty = Notification(title = prof.owner.username +" disassembled " + team.title, forUser = member)
          noty.save()
      team.delete()
  return redirect('Home')

def leaveTeam(request,tm, mem):
  if request.user.is_authenticated:
    try:
      profile = Profile.objects.get(owner = request.user)
      user2 = Profile.objects.get(id = mem)
      team = Team.objects.get(id = tm)
    except Exception:
      return redirect('Home')

    if profile == user2:
      if user2 in team.members.all():
        team.members.remove(user2)
        noty = Notification(title = user2.owner.username +" left " + team.title, forUser = team.leader)
        noty.save()
  return redirect('Home')

def toViewTeam_Req(request):
  if request.user.is_authenticated:
    team_req = []
    try:
      prof = Profile.objects.get(owner = request.user)
    except Exception:
      return redirect('Home')
    myTeams = getProfileTeams(prof)
    
    team = team_req_noty2 = team_req_noty = None
    if Team_Request.objects.filter(userToJoin = prof, isUser = False).exists():
      t_req = Team_Request.objects.filter(userToJoin = prof, isUser = False)
      for tr in t_req:
        team_req.append(tr)

    if Team.objects.filter(leader = prof):
      teams = Team.objects.filter(leader = prof)
      for team in teams:
        t_req = Team_Request.objects.filter(teamToJoin = team, isUser = True)
        for tr in t_req:
          team_req.append(tr)


    return render(request,"Notifications/Team_Requests.html",{
      'team_req':team_req,
      'myProfile':prof,
      'new_Team':team,
      'myTeams':myTeams
      })
  else:
    return redirect('Home')

def toViewNotifications(request):
  if request.user.is_authenticated:
    try:
      prof = Profile.objects.get(owner = request.user)
    except Exception:
      return redirect('Home')
    myTeams = getProfileTeams(prof)
    
    notifications = Notification.objects.filter(forUser = prof)
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
    'myProfile':prof
    })
  else:
    return redirect('Home')


def toViewSuggestion(request):
  if request.user.is_authenticated:
    try:
      prof = Profile.objects.get(owner = request.user)
    except Exception:
      return redirect('Home')
    myTeams = getProfileTeams(prof)
    suggRequest = Task_suggest.objects.filter(forUser = prof)
    return render(request,"Notifications/Suggest_Requests.html",{
      'suggRequest':suggRequest,
      'myProfile':prof,
      'myTeams':myTeams
      })
  else:
    return redirect('Home')

def applySuggestion(request, sid):
  if request.user.is_authenticated:
    if Profile.objects.filter(owner = request.user).exists():
      try:
        prof = Profile.objects.get(owner = request.user)
      except Exception:
        return redirect('Home')
      suggReq = Task_suggest.objects.filter(id = sid)
      if suggReq.exists():
        suggRequest = Task_suggest.objects.get(id = sid)
        if suggRequest is not None:
          if prof == suggRequest.forUser:
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
      prof = Profile.objects.get(owner = request.user)
    except Exception:
      return redirect('Home')
    suggReq = Task_suggest.objects.filter(id = sid)
    if suggReq.exists():
      suggRequest = Task_suggest.objects.get(id = sid)
      if prof == suggRequest.forUser:
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
    profile = Profile.objects.get(owner = request.user)
    user = noty.userToJoin
    team = noty.teamToJoin
    if (noty.isUser and profile == team.leader) or (noty.isUser == False and profile == user):
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
      
      teamReq.delete()
      noty.save()
      
    return redirect('toViewTeam_Req')

def removeNoty(request, id):
  if request.user.is_authenticated:
    if Notification.objects.filter(id = id).exists():
      Notification.objects.get(id = id).delete()
  return redirect('toViewNotifications')

def saveTaskChanges(request, tid, pValue,pid):
  if request.user.is_authenticated:
    project = Project.objects.get(id = pid)
    task = Task.objects.get(id = tid)
    task.progress = pValue
    task.save()
    return redirect('toViewProject',project.id)
  else:
    return redirect('Home')

def finishTask(request, pValue,tid ,pid):
  if request.user.is_authenticated:
    project = Project.objects.get(id = pid)
    task = Task.objects.get(id = tid)
    task.progress = pValue
    task.is_Done = True
    task.finishedDate = date.today()
    for task2 in Task.objects.filter(project = project):
      if task2.dependsOn == task:
        task2.dependsOn = None
        task2.created_Date = date.today()
        task2.save()
    task.save()
    noty = Notification(title = task.forUser.owner.username+" finished the task with number: " + str(task.id),forUser = project.team.leader)
    noty.save()
    return redirect('toViewProject',project.id)
  else:
    return redirect('Home')

def taskSearch(request):
  canInvite = False
  if request.user.is_authenticated:
    searchResault = request.POST['search']
    try:
      prof = Profile.objects.get(owner = request.user)
    except Exception:
      return redirect('Home')
    myTeams = getProfileTeams(prof)
    inviteTeams = []
    if myTeams: 
      for team in myTeams:
        if prof == team.leader:
          canInvite = True
          inviteTeams.append(team)
    newTask = teams = people = None
    if request.method == "POST":
           
      if searchResault.isnumeric():    
        if Task.objects.filter(id = searchResault).exists():
          
          newTask = Task.objects.get(id = searchResault)
          newTask.dyas_Left = newTask.deadLine - (date.today() - newTask.created_Date).days
          newTask.save()
          project = newTask.project
          for member in project.team.members.all():
            if member == prof:
              return render(request,'Search.html',{'myTeams':myTeams,'newTask':newTask,'myProfile':prof})
 
      if Team.objects.filter(title = searchResault).exists():
        teams = Team.objects.filter(title = searchResault)
        return render(request,'Search.html',{'myTeams':myTeams,'teams':teams,'myProfile':prof})
    
      if Team.objects.filter(short = searchResault).exists():
        teams = Team.objects.filter(short = searchResault)
        return render(request,'Search.html',{'myTeams':myTeams,'teams':teams,'myProfile':prof})
    
      if User.objects.filter(username = searchResault).exists():
        people = Profile.objects.filter(owner = User.objects.get(username = searchResault))
      elif User.objects.filter(first_name = searchResault).exists():
        people = []
        users = User.objects.filter(first_name = searchResault)
        for user in users:
          people.append(Profile.objects.get(owner = user))
      elif User.objects.filter(last_name = searchResault).exists():
        people = []
        users = User.objects.filter(last_name = searchResault)
        for user in users:
          people.append(Profile.objects.get(owner = user))
      elif Profile.objects.filter(title = searchResault).exists():
        people = Profile.objects.filter(title = searchResault)

      if people is not None:
        return render(request,'Search.html',{
          'myTeams':myTeams,
          'myProfile':prof,
          'canInvite':canInvite,
          'people':people,
          'inviteTeams':inviteTeams
          })

    return render(request,'Search.html',{'myTeams':myTeams,'myProfile':prof})
  else:
    return redirect('login')


def teamSearch(request):
  searchResault = request.POST['search']
  teams = None
  if request.method == "POST":
    prof = None
    if request.user.is_authenticated:
      try:
        prof = Profile.objects.get(owner = request.user)
      except Exception:
        return redirect('Home') 
    myTeams = getProfileTeams(prof)       
    if Team.objects.filter(title = searchResault).exists():
      teams = Team.objects.filter(title = searchResault)
      return render(request,'Search.html',{'myTeams':myTeams,'teams':teams,'myProfile':prof})
    
    if Team.objects.filter(short = searchResault).exists():
      teams = Team.objects.filter(short = searchResault)
      return render(request,'Search.html',{'myTeams':myTeams,'teams':teams,'myProfile':prof})
    

  return render(request,'Search.html',{'myProfile':prof})


def profileSearch(request):
  prof = None
  canInvite = False
  if request.user.is_authenticated:
    try:
      prof = Profile.objects.get(owner = request.user)
    except Exception:
      return redirect('Home')   
  myTeams = getProfileTeams(prof)
  inviteTeams = []
  if myTeams: 
    for team in myTeams:
      if prof == team.leader:
        canInvite = True
        inviteTeams.append(team)
  searchResault = request.POST['search']
  if searchResault != '':
    people = None
    if request.method == "POST":       
      if User.objects.filter(username = searchResault).exists():
        people = Profile.objects.filter(owner = User.objects.get(username = searchResault))
      elif User.objects.filter(first_name = searchResault).exists():
        people = []
        users = User.objects.filter(first_name = searchResault)
        for user in users:
          people.append(Profile.objects.get(owner = user))
      elif User.objects.filter(last_name = searchResault).exists():
        people = []
        users = User.objects.filter(last_name = searchResault)
        for user in users:
          people.append(Profile.objects.get(owner = user))
      elif Profile.objects.filter(title = searchResault).exists():
        people = Profile.objects.filter(title = searchResault)

      return render(request,'Search.html',{
        'myTeams':myTeams,
        'myProfile':prof,
        'canInvite':canInvite,
        'people':people,
        'inviteTeams':inviteTeams
        })

  return render(request,'Search.html',{
    'myTeams':myTeams,
    'myProfile':prof,
    'canInvite':canInvite,
    'inviteTeams':inviteTeams
    })
      
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
      return redirect('toViewProject',task.project.id)
  return redirect('toViewTeam')

def find_teams(request):
  profile = None
  if request.user.is_authenticated:
    profile = Profile.objects.get(owner = request.user)
  teams = Team.objects.filter()
  myTeams = getProfileTeams(profile)
  requestedTeams = []
  for team in teams:
    if Team_Request.objects.filter(userToJoin = profile, teamToJoin = team).exists():
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
    'myProfile':profile
    })

def find_people(request):
  profile = None
  canInvite = False
  if request.user.is_authenticated:
    profile = Profile.objects.get(owner = request.user)
  people = Profile.objects.filter()
  myTeams = getProfileTeams(profile)
  inviteTeams = []
  myPeople = getMyPeople(profile, myTeams)
  if myTeams: 
    for team in myTeams:
      if profile == team.leader:
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
    'myProfile':profile
    })

def shop(request):
  profile = None
  if request.user.is_authenticated:
    profile = Profile.objects.get(owner = request.user)
  myTeams = getProfileTeams(profile)
  return render(request, "Shop/Shop.html", {'myTeams':myTeams,'myProfile':profile})

def profile(request):
  if request.user.is_authenticated:
    try:
      prof = Profile.objects.get(owner = request.user)
    except Exception:
      return redirect('Home')
    myTeams = getProfileTeams(prof)
    getProfileRate(prof)
    return render(request, "Profile.html", {'myProfile':prof,'myTeams':myTeams})
  else:
    return redirect('Home')

def toMyTeams(request):
  if request.user.is_authenticated:
    try:
      prof = Profile.objects.get(owner = request.user)
    except Exception:
      return redirect('Home')
    myTeams = getProfileTeams(prof)
    return render(request, "MyTeams.html", {'myTeams':myTeams,'myProfile':prof})
  else:
    return redirect('Home')

def changeProjectLeader(request, pid):
  if request.user.is_authenticated:
    try:
      profile = Profile.objects.get(owner = request.user)
      project = Project.objects.get(id = pid)
      username = request.POST['newProjectLeader']
      newProjectLeader = Profile.objects.get(owner = User.objects.get(username = username))
    except Profile.DoesNotExist or Project.DoesNotExist or User.DoesNotExist:
      return redirect('Home')
    if profile == project.team.leader:
      project.projectLeader = newProjectLeader
      project.save()
  return redirect('toViewProject', pid)

def finishProject(request):
  pass