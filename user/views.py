import string
import random
import time
from django.shortcuts import render, redirect
from django.contrib import auth
from django.contrib.auth.models import User
from django.urls import reverse
from django.http import JsonResponse, HttpResponse
from django.core.mail import send_mail
from .forms import LoginForm, RegForm, ChangeNicknameForm, BindEmailForm, ChangePasswordForm, ForgotPasswordForm
from .models import Profile

from PIL import Image, ImageDraw, ImageFont
import io


# def login_for_medal(request):
#     login_form = LoginForm(request.POST, request=request)
#     data = {}
#     if login_form.is_valid():
#         user = login_form.cleaned_data['user']
#         auth.login(request, user)
#         data['status'] = 'SUCCESS'
#     else:
#         data['status'] = 'ERROR'
#     return JsonResponse(data)


def login(request):
    if request.method == 'POST':
        form = LoginForm(request.POST, request=request)
        # login_form = LoginForm(request.POST)
        if form.is_valid():
            input_captcha = request.POST.get('captcha').upper()
            captcha = request.session['captcha'].upper()
            if input_captcha == captcha:
                user = form.cleaned_data['user']
                auth.login(request, user)
                del request.session['captcha']
                return redirect(request.GET.get('from', reverse('home')))
            else:
                form = LoginForm()
    else:
        form = LoginForm()

    context = dict()
    context['login_form'] = form
    return render(request, 'user/login.html', context)


def register(request):
    if request.method == 'POST':
        reg_form = RegForm(request.POST, request=request)
        if reg_form.is_valid():
            username = reg_form.cleaned_data['username']
            email = reg_form.cleaned_data['email']
            password = reg_form.cleaned_data['password']
            # 创建用户
            user = User.objects.create_user(username, email, password)
            user.save()
            # 清除session
            del request.session['register_code']
            # 登录用户
            user = auth.authenticate(username=username, password=password)
            auth.login(request, user)
            return redirect(request.GET.get('from', reverse('home')))
    else:
        reg_form = RegForm()

    context = dict()
    context['reg_form'] = reg_form
    return render(request, 'user/register.html', context)


def logout(request):
    auth.logout(request)
    return redirect(request.GET.get('from', reverse('home')))


def user_info(request):
    context = {}
    return render(request, 'user/user_info.html', context)
    

def change_nickname(request):
    redirect_to = request.GET.get('from', reverse('home'))

    if request.method == 'POST':
        form = ChangeNicknameForm(request.POST, user=request.user)
        if form.is_valid():
            nickname_new = form.cleaned_data['nickname_new']
            profile, created = Profile.objects.get_or_create(user=request.user)
            profile.nickname = nickname_new
            profile.save()
            return redirect(redirect_to)
    else:
        form = ChangeNicknameForm()

    context = dict()
    context['page_title'] = '修改昵称'
    context['form_title'] = '修改昵称'
    context['submit_text'] = '修改'
    context['form'] = form
    context['return_back_url'] = redirect_to
    return render(request, 'form.html', context)


def bind_email(request):
    redirect_to = request.GET.get('from', reverse('home'))

    if request.method == 'POST':
        form = BindEmailForm(request.POST, request=request)
        if form.is_valid():
            email = form.cleaned_data['email']
            request.user.email = email
            request.user.save()
            # 清除session
            del request.session['bind_email_code']
            return redirect(redirect_to)
    else:
        form = BindEmailForm()

    context = dict()
    context['page_title'] = '绑定邮箱'
    context['form_title'] = '绑定邮箱'
    context['submit_text'] = '绑定'
    context['form'] = form
    context['return_back_url'] = redirect_to
    return render(request, 'user/bind_email.html', context)


def send_verification_code(request):
    email = request.GET.get('email', '')
    send_for = request.GET.get('send_for', '')
    data = {}

    if email != '':
        # 生成验证码
        code = ''.join(random.sample(string.ascii_letters + string.digits, 4))
        now = int(time.time())
        send_code_time = request.session.get('send_code_time', 0)
        # 设置验证码5分钟后失效
        if now - send_code_time < 60 * 5:
            data['status'] = 'ERROR'
        else:
            request.session[send_for] = code
            request.session['send_code_time'] = now
            
            # 发送邮件
            send_mail(
                '绑定邮箱',
                '验证码：%s（有效期为5分钟）' % code,
                'yuumoon_com@foxmail.com',
                [email],
                fail_silently=False,
            )
            data['status'] = 'SUCCESS'
    else:
        data['status'] = 'ERROR'
    return JsonResponse(data)


def change_password(request):
    redirect_to = reverse('home')
    if request.method == 'POST':
        form = ChangePasswordForm(request.POST, user=request.user)
        if form.is_valid():
            user = request.user
            old_password = form.cleaned_data['old_password']
            new_password = form.cleaned_data['new_password']
            if new_password != old_password:
                user.set_password(new_password)
                user.save()
                auth.logout(request)
                return redirect(redirect_to)
            else:
                form = ChangePasswordForm()
    else:
        form = ChangePasswordForm()

    context = dict()
    context['page_title'] = '修改密码'
    context['form_title'] = '修改密码'
    context['submit_text'] = '修改'
    context['form'] = form
    context['return_back_url'] = redirect_to
    return render(request, 'form.html', context)


def forgot_password(request):
    redirect_to = reverse('login')
    if request.method == 'POST':
        form = ForgotPasswordForm(request.POST, request=request)
        if form.is_valid():
            email = form.cleaned_data['email']
            new_password = form.cleaned_data['new_password']
            user = User.objects.get(email=email)
            user.set_password(new_password)
            user.save()
            # 清除session
            del request.session['forgot_password_code']
            return redirect(redirect_to)
    else:
        form = ForgotPasswordForm()

    context = dict()
    context['page_title'] = '重置密码'
    context['form_title'] = '重置密码'
    context['submit_text'] = '重置'
    context['form'] = form
    context['return_back_url'] = redirect_to
    return render(request, 'user/forgot_password.html', context)


def captcha(request):
    bg_color = (random.randrange(20, 100), random.randrange(20, 100), random.randrange(20, 100))
    width = 100
    height = 40

    im = Image.new('RGB', (width, height), bg_color)

    draw = ImageDraw.Draw(im)

    for i in range(0, 100):
        x = random.randrange(0, width)
        y = random.randrange(0, width)
        fill = (random.randrange(0, 255), 255, random.randrange(0, 255))
        draw.point((x, y), fill=fill)

    code_str = '123456789qwertyuiplkjhgfdsazxcvbnm987654321LKJHGFDSAQWERTYUIPMNBVCXZ'
    rand_str = ''

    for i in range(0, 4):
        rand_str += code_str[random.randrange(0, len(code_str))]

    font = ImageFont.truetype(r'./static/fonts/wenquanyizhenghei.ttf', 28)

    def fonts_color():
        font_color = (255, random.randrange(0, 255), random.randrange(0, 255))
        return font_color

    draw.text((5, 2), rand_str[0], font=font, fill=fonts_color())
    draw.text((25, 2), rand_str[1], font=font, fill=fonts_color())
    draw.text((50, 2), rand_str[2], font=font, fill=fonts_color())
    draw.text((75, 2), rand_str[3], font=font, fill=fonts_color())

    del draw

    request.session['captcha'] = rand_str

    buf = io.BytesIO()
    im.save(buf, 'png')

    return HttpResponse(buf.getvalue(), content_type="img/png")
