from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib import messages
from django.utils import timezone
from django.core.mail import send_mail
from django.template.loader import render_to_string
from .models import Region, Category, Organization, TimeSlot, Booking
from django.db.models import Q, F
from datetime import timedelta
from .forms import SignUpForm

def homepage(request):
    regions = Region.objects.all()
    categories = Category.objects.all()
    
    search_query = request.GET.get('search', '')
    organizations = Organization.objects.all()
    if search_query:
        organizations = organizations.filter(
            Q(name__icontains=search_query) |
            Q(address__icontains=search_query) |
            Q(region__name__icontains=search_query)
        )
    
    context = {
        'regions': regions,
        'categories': categories,
        'organizations': organizations[:10],
        'search_query': search_query,
    }
    return render(request, 'navbat/home.html', context)

def organization_list(request):
    regions = Region.objects.all()
    categories = Category.objects.all()
    
    region_id = request.GET.get('region')
    category_id = request.GET.get('category')
    organizations = Organization.objects.all()
    
    if region_id:
        organizations = organizations.filter(region__id=region_id)
    if category_id:
        organizations = organizations.filter(category__id=category_id)
    
    context = {
        'regions': regions,
        'categories': categories,
        'organizations': organizations,
        'selected_region': region_id,
        'selected_category': category_id,
    }
    return render(request, 'navbat/organization_list.html', context)

@login_required
def book_slot(request, organization_id):
    organization = get_object_or_404(Organization, id=organization_id)
    
    today = timezone.now()
    end_date = today + timedelta(days=7)
    time_slots = TimeSlot.objects.filter(
        organization=organization,
        start_time__range=[today, end_date],
        is_booked=False,
        current_bookings__lt=F('max_bookings')
    ).order_by('start_time')
    
    if request.method == 'POST':
        time_slot_id = request.POST.get('time_slot')
        time_slot = get_object_or_404(TimeSlot, id=time_slot_id, organization=organization)
        
        if time_slot.is_available():
            booking = Booking.objects.create(
                user=request.user,
                time_slot=time_slot,
                status='pending'
            )
            time_slot.current_bookings += 1
            if time_slot.current_bookings >= time_slot.max_bookings:
                time_slot.is_booked = True
            time_slot.save()
            
            # Email xabarnomasi
            subject = 'Navbat tasdiqlash - NavbatYo‘q.uz'
            message = render_to_string('navbat/emails/booking_confirmation.html', {
                'user': request.user,
                'organization': organization,
                'time_slot': time_slot,
                'booking_code': booking.booking_code,
            })
            send_mail(
                subject,
                message,
                'sizning.email@gmail.com',  # DEFAULT_FROM_EMAIL
                [request.user.email],
                html_message=message,
            )
            
            messages.success(request, f"Navbat muvaffaqiyatli band qilindi! Kod: {booking.booking_code}")
            return redirect('my_bookings')
        else:
            messages.error(request, "Bu vaqt oralig‘i allaqachon band qilingan.")
    
    context = {
        'organization': organization,
        'time_slots': time_slots,
    }
    return render(request, 'navbat/book.html', context)

@login_required
def my_bookings(request):
    bookings = Booking.objects.filter(user=request.user).select_related('time_slot__organization').order_by('-created_at')
    
    context = {
        'bookings': bookings,
    }
    return render(request, 'navbat/my_bookings.html', context)

@login_required
def cancel_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    
    if request.method == 'POST':
        if booking.status not in ['cancelled', 'completed']:
            booking.status = 'cancelled'
            booking.save()
            
            time_slot = booking.time_slot
            time_slot.current_bookings -= 1
            time_slot.is_booked = False
            time_slot.save()
            
            # Email xabarnomasi
            subject = 'Navbat bekor qilindi - NavbatYo‘q.uz'
            message = render_to_string('navbat/emails/booking_cancellation.html', {
                'user': request.user,
                'organization': booking.time_slot.organization,
                'time_slot': booking.time_slot,
                'booking_code': booking.booking_code,
            })
            send_mail(
                subject,
                message,
                'sizning.email@gmail.com',  # DEFAULT_FROM_EMAIL
                [request.user.email],
                html_message=message,
            )
            
            messages.success(request, "Navbat muvaffaqiyatli bekor qilindi.")
        else:
            messages.error(request, "Bu navbatni bekor qilib bo‘lmaydi.")
        return redirect('my_bookings')
    
    context = {
        'booking': booking,
    }
    return render(request, 'navbat/cancel_booking.html', context)

def signup(request):
    if request.user.is_authenticated:
        return redirect('homepage')
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            
            # Email xabarnomasi
            subject = 'Xush kelibsiz - NavbatYo‘q.uz'
            message = render_to_string('navbat/emails/welcome_email.html', {
                'user': user,
            })
            send_mail(
                subject,
                message,
                'sizning.email@gmail.com',  # DEFAULT_FROM_EMAIL
                [user.email],
                html_message=message,
            )
            
            messages.success(request, "Ro‘yxatdan o‘tish muvaffaqiyatli! Xush kelibsiz!")
            return redirect('homepage')
        else:
            messages.error(request, "Iltimos, formadagi xatolarni tuzating.")
    else:
        form = SignUpForm()
    return render(request, 'navbat/signup.html', {'form': form})





from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib import messages
from django.utils import timezone
from django.core.mail import send_mail
from django.template.loader import render_to_string
from .models import Region, Category, Organization, TimeSlot, Booking, Profile
from django.db.models import Q, F
from datetime import timedelta
from .forms import SignUpForm, ProfileForm
from twilio.rest import Client
from django.conf import settings

def homepage(request):
    regions = Region.objects.all()
    categories = Category.objects.all()
    
    search_query = request.GET.get('search', '')
    organizations = Organization.objects.all()
    if search_query:
        organizations = organizations.filter(
            Q(name__icontains=search_query) |
            Q(address__icontains=search_query) |
            Q(region__name__icontains=search_query)
        )
    
    context = {
        'regions': regions,
        'categories': categories,
        'organizations': organizations[:10],
        'search_query': search_query,
    }
    return render(request, 'navbat/home.html', context)

def organization_list(request):
    regions = Region.objects.all()
    categories = Category.objects.all()
    
    region_id = request.GET.get('region')
    category_id = request.GET.get('category')
    organizations = Organization.objects.all()
    
    if region_id:
        organizations = organizations.filter(region__id=region_id)
    if category_id:
        organizations = organizations.filter(category__id=category_id)
    
    context = {
        'regions': regions,
        'categories': categories,
        'organizations': organizations,
        'selected_region': region_id,
        'selected_category': category_id,
    }
    return render(request, 'navbat/organization_list.html', context)

@login_required
def book_slot(request, organization_id):
    organization = get_object_or_404(Organization, id=organization_id)
    
    today = timezone.now()
    end_date = today + timedelta(days=7)
    time_slots = TimeSlot.objects.filter(
        organization=organization,
        start_time__range=[today, end_date],
        is_booked=False,
        current_bookings__lt=F('max_bookings')
    ).order_by('start_time')
    
    if request.method == 'POST':
        time_slot_id = request.POST.get('time_slot')
        time_slot = get_object_or_404(TimeSlot, id=time_slot_id, organization=organization)
        
        if time_slot.is_available():
            booking = Booking.objects.create(
                user=request.user,
                time_slot=time_slot,
                status='pending'
            )
            time_slot.current_bookings += 1
            if time_slot.current_bookings >= time_slot.max_bookings:
                time_slot.is_booked = True
            time_slot.save()
            
            # Email xabarnomasi
            subject = 'Navbat tasdiqlash - NavbatYo‘q.uz'
            message = render_to_string('navbat/emails/booking_confirmation.html', {
                'user': request.user,
                'organization': organization,
                'time_slot': time_slot,
                'booking_code': booking.booking_code,
            })
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [request.user.email],
                html_message=message,
            )
            
            # SMS xabarnomasi
            if request.user.profile.phone_number:
                client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
                sms_message = (
                    f"NavbatYo‘q.uz: Navbatingiz tasdiqlandi!\n"
                    f"Tashkilot: {organization.name}\n"
                    f"Vaqt: {time_slot.start_time.strftime('%Y-%m-%d %H:%M')}\n"
                    f"Kod: {booking.booking_code}"
                )
                try:
                    client.messages.create(
                        body=sms_message,
                        from_=settings.TWILIO_PHONE_NUMBER,
                        to=request.user.profile.phone_number
                    )
                except Exception as e:
                    messages.error(request, f"SMS yuborishda xato: {str(e)}")
            
            messages.success(request, f"Navbat muvaffaqiyatli band qilindi! Kod: {booking.booking_code}")
            return redirect('my_bookings')
        else:
            messages.error(request, "Bu vaqt oralig‘i allaqachon band qilingan.")
    
    context = {
        'organization': organization,
        'time_slots': time_slots,
    }
    return render(request, 'navbat/book.html', context)

@login_required
def my_bookings(request):
    bookings = Booking.objects.filter(user=request.user).select_related('time_slot__organization').order_by('-created_at')
    
    context = {
        'bookings': bookings,
    }
    return render(request, 'navbat/my_bookings.html', context)

@login_required
def cancel_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    
    if request.method == 'POST':
        if booking.status not in ['cancelled', 'completed']:
            booking.status = 'cancelled'
            booking.save()
            
            time_slot = booking.time_slot
            time_slot.current_bookings -= 1
            time_slot.is_booked = False
            time_slot.save()
            
            # Email xabarnomasi
            subject = 'Navbat bekor qilindi - NavbatYo‘q.uz'
            message = render_to_string('navbat/emails/booking_cancellation.html', {
                'user': request.user,
                'organization': booking.time_slot.organization,
                'time_slot': booking.time_slot,
                'booking_code': booking.booking_code,
            })
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [request.user.email],
                html_message=message,
            )
            
            # SMS xabarnomasi
            if request.user.profile.phone_number:
                client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
                sms_message = (
                    f"NavbatYo‘q.uz: Navbatingiz bekor qilindi.\n"
                    f"Tashkilot: {booking.time_slot.organization.name}\n"
                    f"Vaqt: {booking.time_slot.start_time.strftime('%Y-%m-%d %H:%M')}\n"
                    f"Kod: {booking.booking_code}"
                )
                try:
                    client.messages.create(
                        body=sms_message,
                        from_=settings.TWILIO_PHONE_NUMBER,
                        to=request.user.profile.phone_number
                    )
                except Exception as e:
                    messages.error(request, f"SMS yuborishda xato: {str(e)}")
            
            messages.success(request, "Navbat muvaffaqiyatli bekor qilindi.")
        else:
            messages.error(request, "Bu navbatni bekor qilib bo‘lmaydi.")
        return redirect('my_bookings')
    
    context = {
        'booking': booking,
    }
    return render(request, 'navbat/cancel_booking.html', context)

def signup(request):
    if request.user.is_authenticated:
        return redirect('homepage')
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Profilni avtomatik yaratish
            Profile.objects.create(user=user)
            login(request, user)
            
            # Email xabarnomasi
            subject = 'Xush kelibsiz - NavbatYo‘q.uz'
            message = render_to_string('navbat/emails/welcome_email.html', {
                'user': user,
            })
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                html_message=message,
            )
            
            # SMS xabarnomasi
            profile = user.profile
            if profile.phone_number:
                client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
                sms_message = (
                    f"NavbatYo‘q.uz: Xush kelibsiz, {user.username}!\n"
                    f"Platformamizda ro‘yxatdan o‘tdingiz. Saytimizga tashrif buyuring!"
                )
                try:
                    client.messages.create(
                        body=sms_message,
                        from_=settings.TWILIO_PHONE_NUMBER,
                        to=profile.phone_number
                    )
                except Exception as e:
                    messages.error(request, f"SMS yuborishda xato: {str(e)}")
            
            messages.success(request, "Ro‘yxatdan o‘tish muvaffaqiyatli! Xush kelibsiz!")
            return redirect('homepage')
        else:
            messages.error(request, "Iltimos, formadagi xatolarni tuzating.")
    else:
        form = SignUpForm()
    return render(request, 'navbat/signup.html', {'form': form})

@login_required
def profile(request):
    profile = request.user.profile
    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Profil muvaffaqiyatli yangilandi!")
            return redirect('profile')
        else:
            messages.error(request, "Iltimos, formadagi xatolarni tuzating.")
    else:
        form = ProfileForm(instance=profile)
    
    context = {
        'form': form,
        'profile': profile,
    }
    return render(request, 'navbat/profile.html', context)
import requests

def send_sms(phone_number, message):
    url = "https://notify.eskiz.uz/api/message/sms/send"
    headers = {"Authorization": f"Bearer your-eskiz-token"}
    data = {
        "mobile_phone": phone_number,
        "message": message,
        "from": "4546",  # Eskiz tomonidan berilgan sender ID
    }
    response = requests.post(url, headers=headers, data=data)
    return response.json()