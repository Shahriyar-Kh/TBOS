from django.contrib.auth.decorators import login_required
from django.shortcuts import render,redirect
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import authenticate,login,logout
from app.Custom_EmailBackend import EmailBackEnd

def REGISTER(request):
    if request.method == "POST":
        uname = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        print(uname,email,password)

        #check email
        if User.objects.filter(email=email).exists():
            messages.warning(request,"Email are Already Exist ! ")
            return redirect('register')

        #check Username
        if User.objects.filter(username=uname).exists():
            messages.warning(request,"Username are Already Exist ! ")
            return redirect('register')

        user= User(
            username=uname,
            email=email,
        )
        user.set_password(password)
        user.save()
        messages.success(request, 'User Successfully Added ! ')

        return redirect('login')

    return render(request,'registration/register.html')


def DOLOGIN(request):
    if request.method == "POST":
        email=request.POST.get("email")
        password=request.POST.get("password")

        user=EmailBackEnd.authenticate(request,username=email,
                                       password=password)
        if user is not None:
            login(request,user)
            return redirect("home")
        else:
            messages.error(request,"Email and Password Are Invalid! ")
            return redirect('login')


def PROFILE(request):
    return render(request,"registration/profile.html")

@login_required
def PROFILE_UPDATE(request):
    if request.method == "POST":
            username = request.POST.get('username')
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            email = request.POST.get('email')
            password = request.POST.get('password')
            user_id = request.user.id

            user = User.objects.get(id=user_id)
            user.first_name = first_name
            user.last_name = last_name
            user.username = username
            user.email = email

            # Update password if provided
            if password is not None and password != "":
                user.set_password(password)

            user.save()
            messages.success(request, 'Profile has been successfully updated.')
            return redirect('/')  # Redirect to profile page
