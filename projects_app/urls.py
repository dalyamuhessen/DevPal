from django.urls import path
from . import views

urlpatterns = [
    path('dashboard', views.dashboard, name='dashboard'),
    path('project/create', views.create_project, name='create_project'),
    path('project/<int:project_id>', views.project_detail, name='project_detail'),
    path('project/edit/<int:project_id>', views.edit_project, name='edit_project'),
    path('project/delete/<int:project_id>', views.delete_project, name='delete_project'),

    # AJAX (used by the front-end)
    path('api/projects/<int:project_id>/like/', views.like_project, name='like_project'),
    path('api/projects/<int:project_id>/comment/', views.comment_project, name='comment_project'),
    path('api/projects/<int:project_id>/share/', views.share_project, name='share_project'),

    # Public REST API (rubric requirement)
    path('api/projects/', views.api_projects_list, name='api_projects_list'),
    path('api/projects/<int:project_id>/', views.api_project_detail, name='api_project_detail'),
]