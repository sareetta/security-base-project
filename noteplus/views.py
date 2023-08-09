from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseForbidden
from django.db import connection
from django.http import JsonResponse
from django.contrib.auth.models import User
from .models import Note
from .models import SharedNote
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.shortcuts import get_object_or_404

@login_required
def index(request):
    return render(request, 'index.html')


@login_required
def add_note(request):
    if request.method == 'POST':
        title = request.POST['title']
        content = request.POST['content']
        Note.objects.create(user=request.user, title=title, content=content)
        return redirect('notes') 
    else:
        return render(request, 'add_note.html') 
    

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('index')
        else:
            messages.error(request, 'Wrong username or password')
            return render(request, 'login.html')
    else:
        return render(request, 'login.html')
    
def register_view(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already taken')
            return render(request, 'register.html')

        user = User.objects.create_user(username, '', password)
        login(request, user)
        messages.success(request, 'User created and logged in')
        return redirect('index')

    return render(request, 'register.html')
    
@login_required
def search_notes(request):
    search_term = request.GET.get('search_term', '').strip()

    with connection.cursor() as cursor:
        # VULN1: Possibility for SQL injection if the input is malicious
        query = f"SELECT * FROM noteplus_note WHERE LOWER(title) LIKE LOWER('%%{search_term}%%') OR LOWER(content) LIKE LOWER('%%{search_term}%%')"
        cursor.execute(query)
        result = cursor.fetchall()

        # FIX: Django's ORM automatically escapes the parameters
        #notes = Note.objects.filter(user=request.user, content__icontains=search_term)
        #result = [{'title': note.title, 'content': note.content, 'created_at': note.created_at} for note in notes]

    notes = [{'id': r[0], 'title': r[1], 'content': r[2], 'created_at': r[3]} for r in result]

    

    return render(request, 'search_results.html', {'notes': notes, 'search_term': search_term})
    

@login_required
def search_collaborator(request):
    if request.method == 'GET':
        search_term = request.GET.get('username', '').strip()
        # VULN3: This will include all the user info including passwords
        users = User.objects.values() if search_term == "" else User.objects.filter(username__icontains=search_term).values()

        # FIX: To avoid exposing sensitive user information, explicitly select only the safe fields:
        #users = User.objects.values('username', 'email') if search_term == "" else User.objects.filter(username__icontains=search_term).values('username', 'email')

        return render(request, 'search_collaborator.html', {'users': users})

@login_required
def notes(request):
    notes = Note.objects.filter(user=request.user)
    return render(request, 'notes.html', {'notes': notes})

@login_required
def delete_note(request, note_id):
    # VULN5: Any user can delete any note
    Note.objects.get(id=note_id).delete()  
    return HttpResponse('Note deleted')

    # FIX:
    # note = Note.objects.get(id=note_id)
        #if request.user == note.user:  # Only the note's owner can delete it
        #note.delete()
            #return HttpResponse('Note deleted')
        #else:
            #return HttpResponse('Unauthorized', status=401)


@login_required
def add_collaborator(request, user_id):
    collaborator = get_object_or_404(User, pk=user_id)

    if request.method == 'POST':
        note_content = request.POST.get('note_content', '')

        new_note = Note.objects.create(title="Shared Note with " + collaborator.username, content=note_content, user=request.user)

        SharedNote.objects.create(note=new_note, shared_with=collaborator)

        return redirect('note_detail', note_id=new_note.id)

@login_required
def note_detail(request, note_id):
    note = get_object_or_404(Note, pk=note_id)

    if note.user != request.user and not SharedNote.objects.filter(note=note, shared_with=request.user).exists():
        return HttpResponseForbidden("You do not have permission to view this note.")
    
    return render(request, 'note_detail.html', {'note': note})

