from django.urls import path
from .views import search_notes
from . import views
from .views import add_note
from .views import register_view
from .views import login_view
from .views import index


urlpatterns = [
    path('', login_view, name='login'), 
    path('index/', index, name='index'),
    path('search_notes/', search_notes, name='search_notes'),
    path('add_note/', add_note, name='add_note'),
    path('notes/', views.notes, name='notes'),
    path('register/', register_view, name='register'),
    path('delete_note/<int:note_id>/', views.delete_note, name='delete_note'),
    path('search_collaborator/', views.search_collaborator, name='search_collaborator'),
    path('add_collaborator/<int:user_id>/', views.add_collaborator, name='add_collaborator'),
    path('note_detail/<int:note_id>/', views.note_detail, name='note_detail'),

]
