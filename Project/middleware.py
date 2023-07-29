from django.shortcuts import redirect
from django.urls import reverse

class AuthenticationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        if request.user.is_superuser and not ('admin' in request.path):
            if request.path != reverse('logout_login'):
                return redirect(reverse('logout_login'))


        if not request.user.is_authenticated and not request.path.startswith(reverse('login')) and not request.path.startswith('/admin'):
            return redirect(reverse('login'))

        response = self.get_response(request)
        return response

