
from django.urls import path
from .views import GoogleSigninView, EmailPasswordSignupView, EmailPasswordLoginView, AdminLoginView, AuthenticatedUserView, CustomTokenView

urlpatterns = [
    path('google-signin/', GoogleSigninView.as_view(), name='google_signin'),
    path('signup/', EmailPasswordSignupView.as_view(), name='email_pass_signup'),
    path('login/', EmailPasswordLoginView.as_view(), name='email_pass_login'),
    path('login/admin/', AdminLoginView.as_view()),
    path('token/', CustomTokenView.as_view(), name='token_obtain_pair'),
    path('me/', AuthenticatedUserView.as_view(), name='auth_user_info'),
]
