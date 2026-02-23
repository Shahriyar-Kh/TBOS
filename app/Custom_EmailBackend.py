from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.core.exceptions import MultipleObjectsReturned

class EmailBackEnd(ModelBackend):
    def authenticate(self, request=None, username=None, password=None, **kwargs):
        UserModel = get_user_model()

        try:
            # Try to get the user by email (username in this case)
            user = UserModel.objects.get(email=username)
        except UserModel.DoesNotExist:
            return None
        except MultipleObjectsReturned:
            # Handle the case where multiple users with the same email exist
            # You can log the error or handle it as needed
            return None  # Or return a specific message if needed

        # Check if the password matches
        if user.check_password(password):
            return user
        return None
