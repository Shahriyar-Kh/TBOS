from django.contrib.auth import get_user_model

User = get_user_model()


class AccountService:
    @staticmethod
    def register_user(validated_data: dict) -> "User":
        return User.objects.create_user(**validated_data)

    @staticmethod
    def change_password(user, new_password: str) -> None:
        user.set_password(new_password)
        user.save(update_fields=["password"])

    @staticmethod
    def update_profile(user, validated_data: dict) -> "User":
        profile_data = validated_data.pop("profile", {})
        for attr, value in validated_data.items():
            setattr(user, attr, value)
        user.save()

        if profile_data:
            profile = user.profile
            for attr, value in profile_data.items():
                setattr(profile, attr, value)
            profile.save()

        return user

    @staticmethod
    def deactivate_user(user) -> None:
        user.is_active = False
        user.save(update_fields=["is_active"])

    @staticmethod
    def activate_user(user) -> None:
        user.is_active = True
        user.save(update_fields=["is_active"])
