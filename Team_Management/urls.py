from . import views
from django.urls import path
from Team_Management.views import TaskJson
from django.contrib.staticfiles.storage import staticfiles_storage
from django.views.generic.base import RedirectView

urlpatterns = [
    path('', views.toHome, name="Home"),
    path('Tasks_Json/', TaskJson.as_view(), name="TasksJsonView"),
    path('favicon.ico', RedirectView.as_view(url=staticfiles_storage.url('img\Logo.png'))),
    path('signup', views.signup, name="signup"),
    path('login', views.log_in, name="login"),
    path('signout', views.signout, name="signout"),
    path('activate/<uidb64>/<token>', views.activate, name="activate"),
    path('createTeam', views.create_team, name="createTeam"),
    path('reqJoinTeam/<tid>', views.reqJoinTeam, name="reqJoinTeam"),
    path('toViewTeam/<tid>', views.toViewTeam, name="toViewTeam"),
    path('toViewMembers/<tid>', views.toViewMembers, name="toViewMembers"),
    path('addMembers/<uid>', views.addMembers, name="addMembers"),
    path('addProjectMember/<pid>', views.addProjectMember, name="addProjectMember"),
    path('changeProjectLeader/<pid>', views.changeProjectLeader, name="changeProjectLeader"),
    path('addTask/<pid>', views.addTask, name="addTask"),
    path('addProject/<tid>', views.addProject, name="addProject"),
    path('toViewProject/<pid>', views.toViewProject, name="toViewProject"),
    path('taskDelete/<tid>', views.taskDelete, name="taskDelete"),
    path('memberRemove/<tm>/<mid>', views.memberRemove, name="memberRemove"),
    path('memberPromote/<tm>/<mid>', views.memberPromote, name="memberPromote"),
    path('teamRemove/<tm>', views.teamRemove, name="teamRemove"),
    path('leaveTeam/<tm>/<mem>', views.leaveTeam, name="leaveTeam"),
    path('JoinTeam/<reqId>', views.JoinTeam, name="JoinTeam"),
    path('RequestReject/<id>', views.RequestReject, name="RequestReject"),
    path('toViewTeam_Req', views.toViewTeam_Req, name="toViewTeam_Req"),
    path('saveTaskChanges/<tid>/<pValue>/<pid>', views.saveTaskChanges, name="saveTaskChanges"),
    path('finishTask/<tid>/<pValue>/<pid>', views.finishTask, name="finishTask"),
    path('finishProject/<pid>', views.finishProject, name="finishProject"),
    path('projectDelete/<pid>', views.projectDelete, name="projectDelete"),
    path('changePhoto', views.changePhoto, name="changePhoto"),
    path('changeTeamPhoto/<tid>', views.changeTeamPhoto, name="changeTeamPhoto"),
    path('changeRole', views.changeRole, name="changeRole"),
    path('toViewNotifications', views.toViewNotifications, name="toViewNotifications"),
    path('getMessages/<tm>', views.getMessages, name="getMessages"),
    path('realtime', views.realtime, name="realtime"),
    path('removeNoty/<id>', views.removeNoty, name="removeNoty"),
    path('taskSearch', views.taskSearch, name="taskSearch"),
    path('teamSearch', views.teamSearch, name="teamSearch"),
    path('profileSearch', views.profileSearch, name="profileSearch"),
    path('suggestion/<tid>', views.suggestion, name="suggestion"),
    path('toViewSuggestion', views.toViewSuggestion, name="toViewSuggestion"),
    path('applySuggestion/<sid>', views.applySuggestion, name="applySuggestion"),
    path('rejectSuggestion/<sid>', views.rejectSuggestion, name="rejectSuggestion"),
    path('taskDeadlineExtend/<tid>', views.taskDeadlineExtend, name="taskDeadlineExtend"),

    path("password_reset", views.password_reset_request, name="password_reset"),
    path("findPeople", views.find_people, name="findPeople"),
    path("findTeams", views.find_teams, name="findTeams"),
    path("shop", views.shop, name="shop"),
    path("profile", views.profile, name="profile"),
    path("toMyTeams", views.toMyTeams, name="toMyTeams"),

    
]
