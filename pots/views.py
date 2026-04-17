from django.shortcuts import render, redirect, get_object_or_404
from .models import Pot, Member
from .telegram_auth import verify_telegram_auth, get_telegram_user, login_required


def home(request):
    user = get_telegram_user(request)
    pots = []
    if user:
        pots = Pot.objects.filter(members__telegram_user_id=user['id'])
    return render(request, 'home.html', {'user': user, 'pots': pots})


def telegram_login(request):
    data = request.GET.dict()
    if not verify_telegram_auth(data):
        return render(request, 'auth_failed.html', status=403)
    request.session['telegram_user'] = {
        'id': int(data['id']),
        'first_name': data.get('first_name', ''),
        'last_name': data.get('last_name', ''),
        'username': data.get('username', ''),
    }
    next_url = request.session.pop('next', None)
    return redirect(next_url or 'home')


def logout(request):
    request.session.flush()
    return redirect('home')


@login_required
def create_pot(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        if name:
            user = get_telegram_user(request)
            pot = Pot.objects.create(name=name, description=description)
            Member.objects.create(
                pot=pot,
                telegram_user_id=user['id'],
                name=f"{user['first_name']} {user.get('last_name', '')}".strip(),
            )
            return redirect('pot_detail', token=pot.invite_token)
    return render(request, 'create_pot.html')


def pot_detail(request, token):
    pot = get_object_or_404(Pot, invite_token=token)
    members = pot.members.all()
    return render(request, 'pot_detail.html', {'pot': pot, 'members': members})


@login_required
def join_pot(request, token):
    pot = get_object_or_404(Pot, invite_token=token)
    user = get_telegram_user(request)
    Member.objects.get_or_create(
        pot=pot,
        telegram_user_id=user['id'],
        defaults={'name': f"{user['first_name']} {user.get('last_name', '')}".strip()},
    )
    return redirect('pot_detail', token=pot.invite_token)
