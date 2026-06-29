from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import base64
from .forms import UserRegistrationForm
from .models import UserProfile, ChatSession, Message
from .utils.helpers import decode_base64_image, generate_session_title
from .utils.llm import get_fashion_critique

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
@csrf_exempt
def chat_api(request):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)
    
    # Parse request
    text = request.POST.get("message", "").strip()
    session_id = request.POST.get("session_id")
    image_file = request.FILES.get("image")
    
    if not text and not image_file:
        return JsonResponse({"error": "No input provided"}, status=400)
    
    # Get or create session
    if session_id:
        try:
            session = ChatSession.objects.get(
                id=session_id, user=request.user
            )
        except ChatSession.DoesNotExist:
            return JsonResponse({"error": "Session not found"}, 
                                status=404)
    else:
        # Auto-title from first message
        title = text[:50] if text else "Outfit Upload"
        session = ChatSession.objects.create(
            user=request.user, 
            title=title
        )
    
    # Save user message
    user_message = Message.objects.create(
        session=session,
        role="user",
        content=text
    )
    if image_file:
        user_message.image = image_file
        user_message.save()
    
    # Build conversation history from DB
    past_messages = Message.objects.filter(
        session=session
    ).exclude(id=user_message.id).order_by("created_at")
    
    conversation_history = []
    for msg in past_messages:
        role = "user" if msg.role == "user" else "model"
        conversation_history.append({
            "role": role,
            "parts": [{"text": msg.content or ""}]
        })
    
    # Add current message
    conversation_history.append({
        "role": "user",
        "parts": [{"text": text or "Please critique my outfit in the image."}]
    })
    
    # Handle image
    image_base64 = None
    image_mime_type = None
    if image_file:
        image_file.seek(0)
        image_base64 = base64.b64encode(image_file.read()).decode("utf-8")
        image_mime_type = image_file.content_type
    
    # Call Gemini
    try:
        critique = get_fashion_critique(
            conversation_history, 
            image_base64, 
            image_mime_type
        )
    except Exception as e:
        error_msg = str(e)
        if "rate limit" in error_msg.lower() or "429" in error_msg:
            return JsonResponse({
                "error": "Too many requests. Please wait a moment and try again."
            }, status=429)
        return JsonResponse({"error": error_msg}, status=500)
    
    # Save assistant message
    assistant_content = json.dumps(critique)
    assistant_message = Message.objects.create(
        session=session,
        role="assistant",
        content=assistant_content
    )
    
    return JsonResponse({
        "session_id": session.id,
        "message_id": assistant_message.id,
        "critique": critique
    })

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


@login_required
@csrf_exempt
def save_look(request):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)
    
    import json as pyjson
    body = pyjson.loads(request.body)
    message_id = body.get("message_id")
    
    try:
        message = Message.objects.get(id=message_id, 
                                      session__user=request.user)
    except Message.DoesNotExist:
        return JsonResponse({"error": "Message not found"}, status=404)
    
    from .models import SavedLook
    look, created = SavedLook.objects.get_or_create(
        user=request.user,
        message=message
    )
    
    return JsonResponse({
        "saved": True, 
        "created": created,
        "look_id": look.id
    })

@login_required
def saved_critiques_view(request):
    from .models import SavedLook
    looks = SavedLook.objects.filter(
        user=request.user
    ).select_related("message", "message__session").order_by("-created_at")
    
    saved_data = []
    for look in looks:
        try:
            import json as pyjson
            critique = pyjson.loads(look.message.content)
            saved_data.append({
                "id": look.id,
                "session_title": look.message.session.title,
                "created_at": look.created_at.strftime("%b %d, %Y"),
                "critique": critique,
                "has_image": bool(look.message.image)
            })
        except Exception:
            continue
    
    return render(request, "saved.html", {"saved_looks": saved_data})

import requests as req
@login_required  
def style_trends_view(request):
    return render(request, "trends.html")

@login_required
def fetch_trends_api(request):
    category = request.GET.get('category')
    
    if category:
        query = f"{category} outfit apparel clothing model"
    else:
        queries = [
            "streetwear fashion outfit apparel model",
            "minimalist clothing outfit model",
            "luxury fashion editorial outfit",
            "y2k clothing apparel outfit",
            "korean fashion streetwear outfit model"
        ]
        import random
        query = random.choice(queries)
    
    from django.conf import settings
    access_key = getattr(settings, "UNSPLASH_ACCESS_KEY", None)
    
    if not access_key:
        return JsonResponse({"error": "Unsplash API key not configured"}, status=500)
        
    url = "https://api.unsplash.com/search/photos"
    
    params = {
        "query": query,
        "per_page": 20,
        "orientation": "portrait",
        "content_filter": "high"
    }
    headers = {"Authorization": f"Client-ID {access_key}"}
    
    try:
        response = req.get(url, params=params, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        photos = []
        for photo in data.get("results", []):
            photos.append({
                "id": photo["id"],
                "url": photo["urls"]["regular"],
                "thumb": photo["urls"]["small"],
                "alt": photo.get("alt_description", "Fashion photo"),
                "photographer": photo["user"]["name"],
                "photographer_url": photo["user"]["links"]["html"],
                "unsplash_url": photo["links"]["html"]
            })
        
        return JsonResponse({"photos": photos, "query": query})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
