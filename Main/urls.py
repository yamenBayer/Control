from . import views
from django.urls import path
from django.contrib.staticfiles.storage import staticfiles_storage

urlpatterns = [


    # Authintication
    path("password_reset", views.password_reset_request, name="password_reset"),
    path('signup', views.signup, name="signup"),
    path('login', views.log_in, name="login"),
    path('signout', views.signout, name="signout"),
    path('activate/<uidb64>/<token>', views.activate, name="activate"),

    # Notification
    path('RequestReject/<id>', views.RequestReject, name="RequestReject"),
    path('toViewTeam_Req', views.toViewTeam_Req, name="toViewTeam_Req"),
    path('toViewTask_Req', views.toViewTask_Req, name="toViewTask_Req"),
    path('toViewNotifications', views.toViewNotifications, name="toViewNotifications"),
    path('getMessages/<tm>', views.getMessages, name="getMessages"),
    path('suggestion/<tid>', views.suggestion, name="suggestion"),
    path('toViewSuggestion', views.toViewSuggestion, name="toViewSuggestion"),

    # Main
    path('', views.toHome, name="Home"),
    path("findPeople", views.find_people, name="findPeople"),
    path("findTeams", views.find_teams, name="findTeams"),
    path('taskSearch', views.taskSearch, name="taskSearch"),

    
    # Profile
    path("profile", views.profile, name="profile"),
    path('changePhoto', views.changePhoto, name="changePhoto"),
    path('changeRole', views.changeRole, name="changeRole"),

    # Team
    path('JoinTeam/<reqId>', views.JoinTeam, name="JoinTeam"),
    path("toMyTeams", views.toMyTeams, name="toMyTeams"),
    path('toViewTeam/<tid>', views.toViewTeam, name="toViewTeam"),
    path('teamRemove/<tm>', views.teamRemove, name="teamRemove"),
    path('leaveTeam/<tm>/<mem>', views.leaveTeam, name="leaveTeam"),
    path('changeTeamPhoto/<tid>', views.changeTeamPhoto, name="changeTeamPhoto"),
    path('createTeam', views.create_team, name="createTeam"),
    path('reqJoinTeam/<tid>', views.reqJoinTeam, name="reqJoinTeam"),

    # Project
    path('projects/done/<tid>', views.doneProjects, name="doneProjects"),
    path('products/<tid>', views.teamProducts, name="teamProducts"),
    path('changeProjectLeader/<pid>', views.changeProjectLeader, name="changeProjectLeader"),
    path('addProject/<tid>', views.addProject, name="addProject"),
    path('toViewProject/<pid>', views.toViewProject, name="toViewProject"),
    path('finishProject/<pid>', views.finishProject, name="finishProject"),
    path('projectDelete/<pid>', views.projectDelete, name="projectDelete"),
    path('projectRecover/<pid>', views.projectRecover, name="projectRecover"),
    path('members/<tid>/<pid>', views.toViewProjectMembers, name="toViewProjectMembers"),
    path('convert/<pid>', views.convert, name="convert"),

    # Members
    path('members/<tid>', views.toViewMembers, name="toViewMembers"),
    path('addMembers/<uid>', views.addMembers, name="addMembers"),
    path('addProjectMember/<pid>', views.addProjectMember, name="addProjectMember"),
    path('memberRemove/<tm>/<mid>', views.memberRemove, name="memberRemove"),
    path('projectMemberRemove/<pid>/<mid>', views.projectMemberRemove, name="projectMemberRemove"),
    path('memberPromote/<tm>/<mid>', views.memberPromote, name="memberPromote"),

    # Task
    path('toViewTasks/<pid>', views.toViewTasks, name="toViewTasks"),
    path('toViewMyTasks/<pid>', views.toViewMyTasks, name="toViewMyTasks"),
    path('toViewDoneTasks/<pid>', views.toViewDoneTasks, name="toViewDoneTasks"),
    path('toViewMyDoneTasks/<pid>', views.toViewMyDoneTasks, name="toViewMyDoneTasks"),
    path('toViewPendingTasks/<pid>', views.toViewPendingTasks, name="toViewPendingTasks"),
    path('toViewOutdatedTasks/<pid>', views.toViewOutdatedTasks, name="toViewOutdatedTasks"),
    path('addTask/<pid>', views.addTask, name="addTask"),
    path('taskDelete/<tid>/<type>', views.taskDelete, name="taskDelete"),
    path('applySuggestion/<sid>', views.applySuggestion, name="applySuggestion"),
    path('rejectSuggestion/<sid>', views.rejectSuggestion, name="rejectSuggestion"),
    path('taskDeadlineExtend/<tid>', views.taskDeadlineExtend, name="taskDeadlineExtend"),
    path('saveTaskChanges/<tid>/<pid>', views.saveTaskChanges, name="saveTaskChanges"),
    path('finishTask/<tid>', views.finishTask, name="finishTask"),
    path('applyTask/<tid>', views.applyTask, name="applyTask"),
    path('recoverTask/<tid>', views.recoverTask, name="recoverTask"),


]
