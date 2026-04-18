import ast
import datetime
import operator
from decimal import Decimal, InvalidOperation
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from .models import Pot, Member, Drop, Split
from .telegram_auth import verify_telegram_auth, verify_telegram_webapp_auth, get_telegram_user, login_required
from .splits import calculate_splits
from .balances import calculate_balances, calculate_settlements
from .telegram_notify import notify_drop_added


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


@csrf_exempt
def webapp_auth(request):
    """Authenticate via Telegram WebApp initData (used by Mini App / WebView)."""
    if request.method != 'POST':
        return JsonResponse({'ok': False}, status=405)
    init_data = request.POST.get('init_data', '')
    user = verify_telegram_webapp_auth(init_data)
    if not user:
        return JsonResponse({'ok': False}, status=403)
    request.session['telegram_user'] = user
    next_url = request.session.pop('next', None)
    return JsonResponse({'ok': True, 'next': next_url})


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
                telegram_username=user.get('username', ''),
            )
            return redirect('pot_detail', token=pot.invite_token)
    return render(request, 'create_pot.html')


def pot_detail(request, token):
    pot = get_object_or_404(Pot, invite_token=token)
    members = list(pot.members.prefetch_related('drops_paid', 'splits').all())
    for m in members:
        m.can_remove = not m.drops_paid.exists() and not m.splits.exists()
    drops = list(pot.drops.select_related('paid_by').prefetch_related('splits').order_by('-date', '-created_at'))
    balances = calculate_balances(members, drops)
    member_names = {m.id: m.name for m in members}
    settlements = calculate_settlements(balances, member_names)
    balance_rows = sorted(
        [{'name': member_names[mid], **v} for mid, v in balances.items()],
        key=lambda r: r['balance'],
        reverse=True,
    )
    drops_total = sum(d.amount for d in drops)
    return render(request, 'pot_detail.html', {
        'pot': pot,
        'members': members,
        'drops': drops,
        'drops_total': drops_total,
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
    _sync_member_username(current_member, user)

    if request.method == 'POST':
        fields, errors = _parse_drop_form(request, members)
        if not errors:
            try:
                paid_by = pot.members.get(id=fields['paid_by_id'])
            except Member.DoesNotExist:
                paid_by = current_member
            drop = Drop.objects.create(
                pot=pot,
                description=fields['description'],
                amount=fields['amount'],
                paid_by=paid_by,
                date=fields['date'],
            )
            for member_id, share in fields['splits'].items():
                Split.objects.create(drop=drop, member_id=member_id, amount=share)
            notify_drop_added(pot, drop)
            return redirect('pot_detail', token=token)

        return render(request, 'add_drop.html', {
            'pot': pot, 'members': members,
            'current_member': current_member,
            'errors': errors, 'today': datetime.date.today().isoformat(),
        })

    return render(request, 'add_drop.html', {
        'pot': pot, 'members': members,
        'current_member': current_member,
        'today': datetime.date.today().isoformat(),
    })


_SAFE_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.USub: operator.neg,
}


def _eval_formula(expr):
    """Safely evaluate a numeric arithmetic expression. Returns Decimal or raises ValueError."""
    def _eval(node):
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return Decimal(str(node.value))
        if isinstance(node, ast.BinOp) and type(node.op) in _SAFE_OPS:
            return _SAFE_OPS[type(node.op)](_eval(node.left), _eval(node.right))
        if isinstance(node, ast.UnaryOp) and type(node.op) in _SAFE_OPS:
            return _SAFE_OPS[type(node.op)](_eval(node.operand))
        raise ValueError("Invalid formula")
    try:
        tree = ast.parse(expr, mode='eval')
        return _eval(tree.body)
    except Exception:
        raise ValueError("Invalid formula")


def _parse_drop_form(request, members):
    """Parse and validate drop form POST data. Returns (fields_dict, errors)."""
    description = request.POST.get('description', '').strip()
    amount_str = request.POST.get('amount', '').strip()
    date_str = request.POST.get('date', '').strip()
    paid_by_id = request.POST.get('paid_by', '').strip()

    errors = []

    try:
        if amount_str.startswith('='):
            amount = _eval_formula(amount_str[1:]).quantize(Decimal('0.01'))
        else:
            amount = Decimal(amount_str)
        if amount <= 0:
            errors.append('Amount must be positive')
    except (InvalidOperation, ValueError):
        errors.append('Invalid amount')
        amount = None

    try:
        date = datetime.date.fromisoformat(date_str)
    except ValueError:
        errors.append('Invalid date')
        date = None

    if not description:
        errors.append('Description is required')

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

    if all(w == 0 for w in weights.values()):
        weights = {m.id: Decimal('1') for m in members}

    splits = None
    if amount and not errors:
        try:
            splits = calculate_splits(amount, weights)
        except ValueError as e:
            errors.append(str(e))

    return {
        'description': description,
        'amount': amount,
        'date': date,
        'paid_by_id': paid_by_id,
        'splits': splits,
    }, errors


def drop_detail(request, token, drop_id):
    pot = get_object_or_404(Pot, invite_token=token)
    drop = get_object_or_404(Drop, id=drop_id, pot=pot)
    splits = drop.splits.select_related('member').all()
    return render(request, 'drop_detail.html', {'pot': pot, 'drop': drop, 'splits': splits})


@login_required
def edit_drop(request, token, drop_id):
    pot = get_object_or_404(Pot, invite_token=token)
    drop = get_object_or_404(Drop, id=drop_id, pot=pot)
    members = list(pot.members.all())
    existing_splits = {s.member_id: s.amount for s in drop.splits.all()}

    if request.method == 'POST':
        fields, errors = _parse_drop_form(request, members)
        if not errors:
            try:
                paid_by = pot.members.get(id=fields['paid_by_id'])
            except Member.DoesNotExist:
                paid_by = drop.paid_by
            drop.description = fields['description']
            drop.amount = fields['amount']
            drop.paid_by = paid_by
            drop.date = fields['date']
            drop.save()
            drop.splits.all().delete()
            for member_id, share in fields['splits'].items():
                Split.objects.create(drop=drop, member_id=member_id, amount=share)
            return redirect('drop_detail', token=token, drop_id=drop.id)

        member_weights = [(m, request.POST.get(f'weight_{m.id}', '')) for m in members]
        return render(request, 'edit_drop.html', {
            'pot': pot, 'drop': drop, 'members': members,
            'errors': errors, 'member_weights': member_weights,
        })

    member_weights = [(m, existing_splits.get(m.id, '')) for m in members]
    return render(request, 'edit_drop.html', {
        'pot': pot, 'drop': drop, 'members': members,
        'member_weights': member_weights,
    })


@login_required
def delete_drop(request, token, drop_id):
    pot = get_object_or_404(Pot, invite_token=token)
    drop = get_object_or_404(Drop, id=drop_id, pot=pot)
    if request.method == 'POST':
        drop.delete()
        return redirect('pot_detail', token=token)
    return redirect('drop_detail', token=token, drop_id=drop_id)


@login_required
def remove_member(request, token, member_id):
    pot = get_object_or_404(Pot, invite_token=token)
    member = get_object_or_404(Member, id=member_id, pot=pot)
    if request.method == 'POST':
        has_drops = member.drops_paid.exists() or member.splits.exists()
        if not has_drops:
            member.delete()
    return redirect('pot_detail', token=token)


def service_worker(request):
    """Minimal service worker — required for Chrome Android Add to Home Screen."""
    js = "self.addEventListener('fetch', function(e) {});"
    return HttpResponse(js, content_type='application/javascript')


def pot_manifest(request, token):
    """Web app manifest for adding a pot to the home screen."""
    pot = get_object_or_404(Pot, invite_token=token)
    import json as _json
    manifest = {
        'name': pot.name,
        'short_name': pot.name,
        'start_url': f'/pot/{token}/',
        'display': 'standalone',
        'background_color': '#111827',
        'theme_color': '#111827',
    }
    return JsonResponse(manifest, content_type='application/manifest+json')


def help_page(request):
    back_url = request.GET.get('back', '/')
    return render(request, 'help.html', {'back_url': back_url})


def pot_report(request, token):
    pot = get_object_or_404(Pot, invite_token=token)
    members = list(pot.members.all())
    drops = list(pot.drops.select_related('paid_by').prefetch_related('splits__member').order_by('date', 'created_at'))
    balances = calculate_balances(members, drops)
    member_names = {m.id: m.name for m in members}
    settlements = calculate_settlements(balances, member_names)
    balance_rows = sorted(
        [{'name': member_names[mid], **v} for mid, v in balances.items()],
        key=lambda r: r['balance'],
        reverse=True,
    )
    drops_total = sum(d.amount for d in drops)
    return render(request, 'pot_report.html', {
        'pot': pot,
        'drops': drops,
        'drops_total': drops_total,
        'balance_rows': balance_rows,
        'settlements': settlements,
        'generated_date': datetime.date.today(),
    })


@login_required
def rename_pot(request, token):
    pot = get_object_or_404(Pot, invite_token=token)
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        if name:
            pot.name = name
            pot.description = request.POST.get('description', '').strip()
            pot.save()
            return redirect('pot_detail', token=token)
    return render(request, 'rename_pot.html', {'pot': pot})


def _sync_member_username(member, user):
    """Update telegram_username if the user has set or changed it since joining."""
    username = user.get('username', '').lower()
    if username and member.telegram_username != username:
        member.telegram_username = username
        member.save(update_fields=['telegram_username'])


@login_required
def join_pot(request, token):
    pot = get_object_or_404(Pot, invite_token=token)
    user = get_telegram_user(request)
    member, created = Member.objects.get_or_create(
        pot=pot,
        telegram_user_id=user['id'],
        defaults={
            'name': f"{user['first_name']} {user.get('last_name', '')}".strip(),
            'telegram_username': user.get('username', '').lower(),
        },
    )
    if not created:
        _sync_member_username(member, user)
    return redirect('pot_detail', token=pot.invite_token)
