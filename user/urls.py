
from django.urls import path
from .views import GoogleSigninView, EmailPasswordSignupView, EmailPasswordLoginView  # Import the view

urlpatterns = [
    path('google-signin/', GoogleSigninView.as_view(), name='google_signin'),
    path('signup/', EmailPasswordSignupView.as_view(), name='email_pass_signup'),
    path('login/', EmailPasswordLoginView.as_view(), name='email_pass_login'),
]
