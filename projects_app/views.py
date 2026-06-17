import json
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Q
from users_app.models import User, Follow
from .models import Project, Contributor, Comment, Like, Share

def auth_required(request):
    if not request.session.get('user_id'):
        return redirect('/')
    return None

def dashboard(request):
    check = auth_required(request)
    if check: return check
    logged_user = User.objects.get(id=request.session['user_id'])

    search = request.GET.get('q', '')
    ptype  = request.GET.get('type', '')

    projects = Project.objects.all().select_related('owner').prefetch_related(
        'likes', 'comments', 'contributors__user'
    ).order_by('-created_at')

    if search:
        projects = projects.filter(
            Q(title__icontains=search) | Q(tech_stack__icontains=search)
        )
    if ptype in ['solo', 'team']:
        projects = projects.filter(project_type=ptype)

    liked_ids = set(Like.objects.filter(user=logged_user).values_list('project_id', flat=True))

    own_projects_count = Project.objects.filter(owner=logged_user).count()
    own_likes_total = sum(p.likes.count() for p in Project.objects.filter(owner=logged_user))
    peers_count = Follow.objects.filter(followed=logged_user).count()

    people_to_follow = User.objects.exclude(id=logged_user.id).exclude(
        id__in=Follow.objects.filter(follower=logged_user).values_list('followed_id', flat=True)
    )[:3]
    following_ids = set(Follow.objects.filter(follower=logged_user).values_list('followed_id', flat=True))

    all_tech = set()
    for p in Project.objects.all():
        all_tech.update(p.tech_list)
    trending = list(all_tech)[:6]

    errors = {}
    for key in ['title', 'description', 'tech_stack', 'project_type']:
        val = request.session.pop(f'proj_err_{key}', None)
        if val:
            errors[key] = val

    context = {
        'logged_user': logged_user,
        'projects': projects,
        'liked_ids': liked_ids,
        'search': search,
        'ptype': ptype,
        'errors': errors,
        'own_projects_count': own_projects_count,
        'own_likes_total': own_likes_total,
        'peers_count': peers_count,
        'people_to_follow': people_to_follow,
        'following_ids': following_ids,
        'trending': trending,
    }
    return render(request, 'dashboard.html', context)

def create_project(request):
    check = auth_required(request)
    if check: return check
    if request.method != 'POST':
        return redirect('/dashboard')
    logged_user = User.objects.get(id=request.session['user_id'])
    errors = Project.objects.project_validator(request.POST)
    if errors:
        for key, val in errors.items():
            request.session[f'proj_err_{key}'] = val
        return redirect('/dashboard')
    project = Project.objects.create(
        title=request.POST['title'].strip(),
        description=request.POST['description'].strip(),
        tech_stack=request.POST['tech_stack'].strip(),
        github_url=request.POST.get('github_url', '').strip(),
        project_type=request.POST['project_type'],
        owner=logged_user
    )
    if request.FILES.get('image'):
        project.image = request.FILES['image']
        project.save()
    for uid in request.POST.getlist('contributors'):
        try:
            contributor_user = User.objects.get(id=uid)
            if contributor_user.id != logged_user.id:
                Contributor.objects.get_or_create(project=project, user=contributor_user)
        except User.DoesNotExist:
            pass
    return redirect(f'/project/{project.id}')

def project_detail(request, project_id):
    check = auth_required(request)
    if check: return check
    logged_user = User.objects.get(id=request.session['user_id'])
    project     = get_object_or_404(Project, id=project_id)
    comments    = Comment.objects.filter(project=project).select_related('user')
    contributors = Contributor.objects.filter(project=project).select_related('user')
    is_liked    = Like.objects.filter(user=logged_user, project=project).exists()
    likes_count = Like.objects.filter(project=project).count()
    all_users   = User.objects.exclude(id=logged_user.id)
    is_following_owner = Follow.objects.filter(follower=logged_user, followed=project.owner).exists()

    context = {
        'logged_user': logged_user,
        'project': project,
        'comments': comments,
        'contributors': contributors,
        'is_liked': is_liked,
        'likes_count': likes_count,
        'all_users': all_users,
        'is_following_owner': is_following_owner,
    }
    return render(request, 'project_detail.html', context)

def edit_project(request, project_id):
    check = auth_required(request)
    if check: return check
    project     = get_object_or_404(Project, id=project_id)
    logged_user = User.objects.get(id=request.session['user_id'])
    if project.owner.id != logged_user.id:
        return redirect('/dashboard')
    if request.method == 'POST':
        errors = Project.objects.project_validator(request.POST)
        if errors:
            for key, val in errors.items():
                request.session[f'edit_err_{key}'] = val
            return redirect(f'/project/edit/{project_id}')
        project.title        = request.POST['title'].strip()
        project.description  = request.POST['description'].strip()
        project.tech_stack   = request.POST['tech_stack'].strip()
        project.github_url   = request.POST.get('github_url', '').strip()
        project.project_type = request.POST['project_type']
        if request.FILES.get('image'):
            project.image = request.FILES['image']
        project.save()
        Contributor.objects.filter(project=project).delete()
        for uid in request.POST.getlist('contributors'):
            try:
                contributor_user = User.objects.get(id=uid)
                if contributor_user.id != logged_user.id:
                    Contributor.objects.get_or_create(project=project, user=contributor_user)
            except User.DoesNotExist:
                pass
        return redirect(f'/project/{project_id}')

    edit_errors = {}
    for key in ['title', 'description', 'tech_stack', 'project_type']:
        val = request.session.pop(f'edit_err_{key}', None)
        if val:
            edit_errors[key] = val
    all_users = User.objects.exclude(id=logged_user.id)
    contributor_ids = set(Contributor.objects.filter(project=project).values_list('user_id', flat=True))
    context = {
        'project': project,
        'errors': edit_errors,
        'all_users': all_users,
        'contributor_ids': contributor_ids,
    }
    return render(request, 'edit_project.html', context)

def delete_project(request, project_id):
    check = auth_required(request)
    if check: return check
    project = get_object_or_404(Project, id=project_id)
    if project.owner.id == request.session['user_id']:
        project.delete()
    return redirect('/dashboard')

# ── AJAX VIEWS ──────────────────────────────────────────────

@require_POST
def like_project(request, project_id):
    if not request.session.get('user_id'):
        return JsonResponse({'error': 'Not authenticated'}, status=401)
    logged_user = User.objects.get(id=request.session['user_id'])
    project     = get_object_or_404(Project, id=project_id)
    like, created = Like.objects.get_or_create(user=logged_user, project=project)
    liked = created
    if not created:
        like.delete()
    likes_count = Like.objects.filter(project=project).count()
    return JsonResponse({'liked': liked, 'likes_count': likes_count})

@require_POST
def comment_project(request, project_id):
    if not request.session.get('user_id'):
        return JsonResponse({'error': 'Not authenticated'}, status=401)
    logged_user = User.objects.get(id=request.session['user_id'])
    project     = get_object_or_404(Project, id=project_id)
    try:
        data = json.loads(request.body)
        content = data.get('content', '').strip()
    except Exception:
        content = request.POST.get('content', '').strip()
    if not content:
        return JsonResponse({'error': 'Comment cannot be empty.'}, status=400)
    comment = Comment.objects.create(content=content, user=logged_user, project=project)
    return JsonResponse({
        'success': True,
        'comment_id': comment.id,
        'content': comment.content,
        'user_name': logged_user.full_name,
        'user_handle': logged_user.handle,
        'user_id': logged_user.id,
        'initials': logged_user.initials,
        'created_at': comment.created_at.strftime("%b %d, %H:%M"),
        'comments_count': project.comments.count(),
    })

@require_POST
def share_project(request, project_id):
    if not request.session.get('user_id'):
        return JsonResponse({'error': 'Not authenticated'}, status=401)
    logged_user = User.objects.get(id=request.session['user_id'])
    project     = get_object_or_404(Project, id=project_id)
    Share.objects.create(user=logged_user, project=project)
    project.share_count += 1
    project.save()
    return JsonResponse({'success': True, 'share_count': project.share_count})


# ── PUBLIC JSON API ─────────────────────────────────────────

def api_projects_list(request):
    projects = Project.objects.all().select_related('owner').order_by('-created_at')
    data = [{
        'id': p.id,
        'title': p.title,
        'description': p.description,
        'tech_stack': p.tech_list,
        'project_type': p.project_type,
        'github_url': p.github_url,
        'owner': p.owner.full_name,
        'owner_handle': p.owner.handle,
        'likes': p.likes.count(),
        'comments': p.comments.count(),
        'shares': p.share_count,
        'created_at': p.created_at.isoformat(),
    } for p in projects]
    return JsonResponse({'count': len(data), 'results': data})

def api_project_detail(request, project_id):
    p = get_object_or_404(Project, id=project_id)
    data = {
        'id': p.id,
        'title': p.title,
        'description': p.description,
        'tech_stack': p.tech_list,
        'project_type': p.project_type,
        'github_url': p.github_url,
        'owner': p.owner.full_name,
        'owner_handle': p.owner.handle,
        'contributors': [c.user.full_name for c in p.contributors.all()],
        'likes': p.likes.count(),
        'comments': p.comments.count(),
        'shares': p.share_count,
        'created_at': p.created_at.isoformat(),
    }
    return JsonResponse(data)