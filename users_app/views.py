import bcrypt
import requests
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q
from .models import User, Skill, UserSkill, Follow
import re
from projects_app.models import Project, Like, Comment, Share, Contributor

AVATAR_COLORS = ['#1a3a6e', '#c2410c', '#1e3a8a', '#166534', '#7f1d1d', '#4338ca']

def avatar_color(user_id):
    return AVATAR_COLORS[user_id % len(AVATAR_COLORS)]

def landing(request):
    if request.session.get('user_id'):
        return redirect('/dashboard')
    stats = {
        'developers': User.objects.count(),
        'projects': Project.objects.count(),
        'cities': User.objects.exclude(location='').values('location').distinct().count(),
    }
    return render(request, 'about.html', {'stats': stats})



def index(request):
    if request.session.get('user_id'):
        return redirect('/dashboard')
    errors = {}
    login_errors = {}
    for key in ['full_name', 'email', 'password', 'github_url']:
        val = request.session.pop(f'err_{key}', None)
        if val:
            errors[key] = val
    val = request.session.pop('login_err_email', None)
    if val:
        login_errors['email'] = val
    stats = {
        'developers': User.objects.count(),
        'projects': Project.objects.count(),
        'cities': User.objects.exclude(location='').values('location').distinct().count(),
    }
    return render(request, 'index.html', {
        'errors': errors, 'login_errors': login_errors, 'stats': stats
    })

def register(request):
    if request.method != 'POST':
        return redirect('/')
    errors = User.objects.register_validator(request.POST)
    if errors:
        for key, val in errors.items():
            request.session[f'err_{key}'] = val
        return redirect('/')
    pw_hash = bcrypt.hashpw(request.POST['password'].encode(), bcrypt.gensalt()).decode()
    user = User.objects.create(
        full_name=request.POST['full_name'].strip(),
        email=request.POST['email'],
        password=pw_hash,
        github_url=request.POST.get('github_url', '').strip(),
    )
    request.session['user_id'] = user.id
    return redirect('/dashboard')

def login(request):
    if request.method != 'POST':
        return redirect('/auth')
    errors = User.objects.login_validator(request.POST)
    if errors:
        for key, val in errors.items():
            request.session[f'login_err_{key}'] = val
        return redirect('/auth')
    user = User.objects.get(email=request.POST['email'])
    request.session['user_id'] = user.id
    return redirect('/dashboard')

def logout(request):
    request.session.flush()
    return redirect('/')

def auth_required(request):
    if not request.session.get('user_id'):
        return redirect('/')
    return None

def profile(request, user_id):
    check = auth_required(request)
    if check: return check
    logged_user  = User.objects.get(id=request.session['user_id'])
    profile_user = get_object_or_404(User, id=user_id)

    user_skills    = UserSkill.objects.filter(user=profile_user).select_related('skill')
    own_projects   = Project.objects.filter(owner=profile_user).order_by('-created_at')
    contributions  = Contributor.objects.filter(user=profile_user).select_related('project').order_by('-id')
    liked_projects = Like.objects.filter(user=profile_user).select_related('project').order_by('-created_at')

    total_likes = sum(p.likes.count() for p in own_projects)
    peers_count = Follow.objects.filter(followed=profile_user).count()
    is_following = Follow.objects.filter(follower=logged_user, followed=profile_user).exists()

    context = {
        'logged_user': logged_user,
        'profile_user': profile_user,
        'user_skills': user_skills,
        'own_projects': own_projects,
        'contributions': contributions,
        'liked_projects': liked_projects,
        'total_likes': total_likes,
        'peers_count': peers_count,
        'is_following': is_following,
        'avatar_color': avatar_color(profile_user.id),
    }
    return render(request, 'profile.html', context)

def edit_profile(request):
    check = auth_required(request)
    if check: return check
    if request.method != 'POST':
        return redirect(f"/profile/{request.session['user_id']}")
    user = User.objects.get(id=request.session['user_id'])
    user.bio        = request.POST.get('bio', '').strip()
    user.role_title = request.POST.get('role_title', '').strip()
    user.github_url = request.POST.get('github_url', '').strip()
    user.location   = request.POST.get('location', '').strip()
    if request.FILES.get('avatar'):
        user.avatar = request.FILES['avatar']
    user.save()

    UserSkill.objects.filter(user=user).delete()
    skills_raw = request.POST.get('skills', '')
    for skill_name in skills_raw.split(','):
        skill_name = skill_name.strip()
        if skill_name:
            skill, _ = Skill.objects.get_or_create(name=skill_name)
            UserSkill.objects.get_or_create(user=user, skill=skill)
    return redirect(f"/profile/{user.id}")

def follow_user(request, user_id):
    check = auth_required(request)
    if check: return check
    logged_user = User.objects.get(id=request.session['user_id'])
    target = get_object_or_404(User, id=user_id)
    if logged_user.id != target.id:
        follow, created = Follow.objects.get_or_create(follower=logged_user, followed=target)
        if not created:
            follow.delete()
    return redirect(f'/profile/{user_id}')

def developers(request):
    check = auth_required(request)
    if check: return check
    logged_user = User.objects.get(id=request.session['user_id'])
    search = request.GET.get('q', '')
    skill_filter = request.GET.get('skill', '')

    all_devs = User.objects.exclude(id=logged_user.id).prefetch_related('skills__skill')
    if search:
        all_devs = all_devs.filter(
            Q(full_name__icontains=search) | Q(handle__icontains=search)
        )
    if skill_filter:
        all_devs = all_devs.filter(skills__skill__name=skill_filter).distinct()

    all_skills = Skill.objects.all().order_by('name')
    devs_with_color = [(d, avatar_color(d.id)) for d in all_devs]

    context = {
        'logged_user': logged_user,
        'devs_with_color': devs_with_color,
        'all_skills': all_skills,
        'search': search,
        'skill_filter': skill_filter,
    }
    return render(request, 'developers.html', context)

def about(request):
    logged_user = None
    if request.session.get('user_id'):
        logged_user = User.objects.get(id=request.session['user_id'])
    return render(request, 'about.html', {'logged_user': logged_user})
def github_login(request):
    github_auth_url = (
        f"https://github.com/login/oauth/authorize"
        f"?client_id={settings.GITHUB_CLIENT_ID}"
        f"&redirect_uri={settings.GITHUB_CALLBACK_URL}"
        f"&scope=read:user user:email"
    )
    return redirect(github_auth_url)


def github_callback(request):
    code = request.GET.get('code')
    if not code:
        return redirect('/auth')

    # Step 1: exchange the code for an access token
    token_response = requests.post(
        'https://github.com/login/oauth/access_token',
        data={
            'client_id': settings.GITHUB_CLIENT_ID,
            'client_secret': settings.GITHUB_CLIENT_SECRET,
            'code': code,
            'redirect_uri': settings.GITHUB_CALLBACK_URL,
        },
        headers={'Accept': 'application/json'}
    )
    token_data = token_response.json()
    access_token = token_data.get('access_token')

    if not access_token:
        return redirect('/auth')

    # Step 2: fetch the GitHub profile
    profile_response = requests.get(
        'https://api.github.com/user',
        headers={'Authorization': f'Bearer {access_token}'}
    )
    profile = profile_response.json()

    github_id = str(profile.get('id'))
    github_username = profile.get('login', '')
    full_name = profile.get('name') or github_username
    github_profile_url = profile.get('html_url', '')

    # GitHub may not return a public email — fetch separately if missing
    email = profile.get('email')
    if not email:
        emails_response = requests.get(
            'https://api.github.com/user/emails',
            headers={'Authorization': f'Bearer {access_token}'}
        )
        emails_data = emails_response.json()
        primary = next((e for e in emails_data if e.get('primary')), None)
        email = primary['email'] if primary else f"{github_username}@users.noreply.github.com"

    # Step 3: find existing user, else create one automatically
    user = User.objects.filter(github_id=github_id).first()

    if not user:
        user = User.objects.filter(email=email).first()

    if not user:
        handle = generate_unique_handle(github_username)
        user = User.objects.create(
            full_name=full_name,
            email=email,
            password='',
            handle=handle,
            github_id=github_id,
            github_url=github_profile_url,
            bio=f"Joined via GitHub ({github_username})",
        )
    else:
        if not user.github_id:
            user.github_id = github_id
            user.save()

    request.session['user_id'] = user.id
    return redirect('/dashboard')


def generate_unique_handle(github_username):
    base = re.sub(r'[^a-zA-Z0-9]', '', github_username).lower() or 'dev'
    candidate = base
    i = 1
    while User.objects.filter(handle=candidate).exists():
        candidate = f"{base}{i}"
        i += 1
    return candidate