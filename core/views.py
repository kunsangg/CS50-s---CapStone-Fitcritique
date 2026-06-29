from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
import json
from .forms import UserRegistrationForm
from .models import UserProfile, ChatSession, Message
from .utils.helpers import decode_base64_image, generate_session_title
from .utils.claude import get_claude_response

def index(request):
    if request.user.is_authenticated:
        return redirect('chat')
    return render(request, 'index.html')

def register_view(request):
    if request.user.is_authenticated:
        return redirect('chat')
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            UserProfile.objects.create(user=user)
            login(request, user)
            return redirect('chat')
    else:
        form = UserRegistrationForm()
    return render(request, 'register.html', {'form': form})

def login_view(request):
    if request.user.is_authenticated:
        return redirect('chat')
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('chat')
    else:
        form = AuthenticationForm()
    # Add Tailwind classes to login form fields
    for field in form.fields.values():
        field.widget.attrs.update({'class': 'w-full bg-zinc-900 border border-zinc-700 text-zinc-100 rounded-lg px-4 py-2 mt-1 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500'})
    return render(request, 'login.html', {'form': form})

@login_required
def logout_view(request):
    logout(request)
    return redirect('index')

@login_required
def chat_view(request, session_id=None):
    return render(request, 'chat.html')

@login_required
def history_view(request):
    return render(request, 'history.html')

@login_required
def saved_view(request):
    saved_looks = request.user.saved_looks.select_related('message').order_by('-created_at')
    
    # Pre-parse json content for the template
    import json
    for look in saved_looks:
        if look.message.role == 'assistant':
            try:
                look.message.parsed_content = json.loads(look.message.content)
            except:
                look.message.parsed_content = {}
                
    return render(request, 'saved.html', {'saved_looks': saved_looks})

@login_required
def profile_view(request):
    if request.method == 'POST':
        profile = request.user.profile
        bio = request.POST.get('bio')
        if bio is not None:
            profile.bio = bio
        
        avatar = request.FILES.get('avatar')
        if avatar:
            profile.avatar = avatar
            
        profile.save()
        return redirect('profile')
        
    stats = {
        'total_critiques': Message.objects.filter(session__user=request.user, role='assistant').count(),
        'saved_looks': request.user.saved_looks.count()
    }
    return render(request, 'profile.html', {'stats': stats})

@login_required
def api_chat(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            message_text = data.get('message', '')
            image_base64 = data.get('image', None)
            session_id = data.get('session_id', None)
            
            if not message_text and not image_base64:
                return JsonResponse({'error': 'Message or image required'}, status=400)
            
            # Fetch or create session
            if session_id:
                try:
                    session = ChatSession.objects.get(id=session_id, user=request.user)
                except ChatSession.DoesNotExist:
                    return JsonResponse({'error': 'Session not found'}, status=404)
            else:
                title = generate_session_title(message_text)
                session = ChatSession.objects.create(user=request.user, title=title)
            
            # Save user message
            user_msg = Message(session=session, role='user', content=message_text)
            if image_base64:
                image_file = decode_base64_image(image_base64)
                if image_file:
                    user_msg.image = image_file
            user_msg.save()
            
            # Get history
            history = list(Message.objects.filter(session=session).order_by('created_at').values('role', 'content'))
            # Filter out the message we just added so we don't send it twice, wait get_claude_response expects everything
            # Actually get_claude_response appends the current message. Let's only pass history prior to this message.
            history = history[:-1] 
            
            # Call Claude
            claude_response = get_claude_response(message_text, image_base64, history)
            
            # Save AI message
            if 'error' not in claude_response:
                ai_msg = Message.objects.create(
                    session=session,
                    role='assistant',
                    content=json.dumps(claude_response)
                )
                return JsonResponse({
                    'session_id': session.id,
                    'message_id': ai_msg.id,
                    'response': claude_response
                })
            else:
                return JsonResponse({'error': claude_response['error']}, status=500)
                
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Invalid method'}, status=405)

@login_required
def api_sessions(request):
    if request.method == 'GET':
        sessions = ChatSession.objects.filter(user=request.user).order_by('-updated_at')
        data = [{'id': s.id, 'title': s.title, 'updated_at': s.updated_at.isoformat()} for s in sessions]
        return JsonResponse({'sessions': data})
    return JsonResponse({'error': 'Invalid method'}, status=405)

@login_required
def api_session_detail(request, session_id):
    if request.method == 'GET':
        try:
            session = ChatSession.objects.get(id=session_id, user=request.user)
            messages = Message.objects.filter(session=session).order_by('created_at')
            data = []
            for msg in messages:
                img_url = msg.image.url if msg.image else None
                content = msg.content
                if msg.role == 'assistant':
                    try:
                        content = json.loads(msg.content)
                    except:
                        pass
                data.append({
                    'id': msg.id,
                    'role': msg.role,
                    'content': content,
                    'image': img_url,
                    'created_at': msg.created_at.isoformat()
                })
            return JsonResponse({'messages': data})
        except ChatSession.DoesNotExist:
            return JsonResponse({'error': 'Session not found'}, status=404)
    elif request.method == 'DELETE':
        try:
            session = ChatSession.objects.get(id=session_id, user=request.user)
            session.delete()
            return JsonResponse({'success': True})
        except ChatSession.DoesNotExist:
            return JsonResponse({'error': 'Session not found'}, status=404)
    return JsonResponse({'error': 'Invalid method'}, status=405)

@login_required
def api_save_look(request, session_id):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            message_id = data.get('message_id')
            from .models import SavedLook
            message = Message.objects.get(id=message_id, session__id=session_id, session__user=request.user)
            
            # Create or get saved look
            saved_look, created = SavedLook.objects.get_or_create(
                user=request.user,
                message=message
            )
            return JsonResponse({'success': True, 'created': created})
        except Message.DoesNotExist:
            return JsonResponse({'error': 'Message not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Invalid method'}, status=405)
