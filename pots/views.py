import datetime
from decimal import Decimal, InvalidOperation
from django.shortcuts import render, redirect, get_object_or_404
from .models import Pot, Member, Drop, Split
from .telegram_auth import verify_telegram_auth, get_telegram_user, login_required
from .splits import calculate_splits
from .balances import calculate_balances, calculate_settlements


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
    members = list(pot.members.all())
    drops = list(pot.drops.select_related('paid_by').prefetch_related('splits').order_by('-date', '-created_at'))
    balances = calculate_balances(members, drops)
    member_names = {m.id: m.name for m in members}
    settlements = calculate_settlements(balances, member_names)
    balance_rows = sorted(
        [{'name': member_names[mid], 'amount': amt} for mid, amt in balances.items()],
        key=lambda r: r['amount'],
        reverse=True,
    )
    return render(request, 'pot_detail.html', {
        'pot': pot,
        'members': members,
        'drops': drops,
        'balance_rows': balance_rows,
        'settlements': settlements,
    })


@login_required
def add_drop(request, token):
    pot = get_object_or_404(Pot, invite_token=token)
    user = get_telegram_user(request)
    members = list(pot.members.all())
    current_member = next((m for m in members if m.telegram_user_id == user['id']), None)
    if current_member is None:
        return redirect('pot_detail', token=token)

    if request.method == 'POST':
        description = request.POST.get('description', '').strip()
        amount_str = request.POST.get('amount', '').strip()
        date_str = request.POST.get('date', '').strip()
        paid_by_id = request.POST.get('paid_by', '').strip()

        errors = []
        try:
            amount = Decimal(amount_str)
            if amount <= 0:
                errors.append('Amount must be positive')
        except InvalidOperation:
            errors.append('Invalid amount')
            amount = None

        try:
            date = datetime.date.fromisoformat(date_str)
        except ValueError:
            errors.append('Invalid date')
            date = None

        weights = {}
        for member in members:
            w_str = request.POST.get(f'weight_{member.id}', '').strip()
            try:
                w = Decimal(w_str) if w_str else Decimal('0')
                if w < 0:
                    w = Decimal('0')
            except InvalidOperation:
                w = Decimal('0')
            weights[member.id] = w

        # All blank means equal split among everyone
        if all(w == 0 for w in weights.values()):
            weights = {m.id: Decimal('1') for m in members}

        try:
            splits = calculate_splits(amount or Decimal('0'), weights) if amount else None
            if splits is None and not errors:
                errors.append('Invalid amount')
        except ValueError as e:
            errors.append(str(e))
            splits = None

        if not description:
            errors.append('Description is required')

        if not errors and amount and date and splits:
            try:
                paid_by = pot.members.get(id=paid_by_id)
            except Member.DoesNotExist:
                paid_by = current_member

            drop = Drop.objects.create(
                pot=pot,
                description=description,
                amount=amount,
                paid_by=paid_by,
                date=date,
            )
            for member_id, share in splits.items():
                Split.objects.create(drop=drop, member_id=member_id, amount=share)
            return redirect('pot_detail', token=token)

        return render(request, 'add_drop.html', {
            'pot': pot,
            'members': members,
            'errors': errors,
            'today': datetime.date.today().isoformat(),
        })

    return render(request, 'add_drop.html', {
        'pot': pot,
        'members': members,
        'today': datetime.date.today().isoformat(),
    })


def drop_detail(request, token, drop_id):
    pot = get_object_or_404(Pot, invite_token=token)
    drop = get_object_or_404(Drop, id=drop_id, pot=pot)
    splits = drop.splits.select_related('member').all()
    return render(request, 'drop_detail.html', {'pot': pot, 'drop': drop, 'splits': splits})


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
