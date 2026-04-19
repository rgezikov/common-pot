import ast
import datetime
import operator
from decimal import Decimal, InvalidOperation
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
import csv
import io
from .models import Pot, CompotUser, Member, Drop, Split, PlaceholderClaim, ShoppingList, ListMember, Item
from .telegram_auth import verify_telegram_auth, verify_telegram_webapp_auth, get_telegram_user, login_required
from .splits import calculate_splits
from .balances import calculate_balances, calculate_settlements
from .telegram_notify import notify_drop_added


def home(request):
    user = get_telegram_user(request)
    pots = []
    lists = []
    if user:
        pots = Pot.objects.filter(members__user__telegram_user_id=user['id'])
        lists = ShoppingList.objects.filter(members__user__telegram_user_id=user['id'])
    return render(request, 'home.html', {'user': user, 'pots': pots, 'lists': lists})


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
            compot_user, _ = CompotUser.objects.get_or_create(
                telegram_user_id=user['id'],
                defaults={
                    'name': f"{user['first_name']} {user.get('last_name', '')}".strip(),
                    'telegram_username': user.get('username', '').lower(),
                },
            )
            Member.objects.create(pot=pot, user=compot_user)
            return redirect('pot_detail', token=pot.invite_token)
    return render(request, 'create_pot.html')


def pot_detail(request, token):
    pot = get_object_or_404(Pot, invite_token=token)
    members = list(pot.members.prefetch_related('drops_paid', 'splits').all())
    for m in members:
        m.can_remove = not m.drops_paid.exists() and not m.splits.exists()
    drops = list(pot.drops.select_related('paid_by').prefetch_related('splits').order_by('-date', '-time', '-created_at'))
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
                time=fields['time'],
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
    time_str = request.POST.get('time', '').strip()
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

    try:
        time = datetime.time.fromisoformat(time_str) if time_str else datetime.time(0, 0)
    except ValueError:
        time = datetime.time(0, 0)

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
        'time': time,
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
            drop.time = fields['time']
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
    placeholders = pot.members.filter(user__is_placeholder=True).select_related('user')
    return render(request, 'rename_pot.html', {'pot': pot, 'placeholders': placeholders})


def _sync_member_username(member, user):
    """Update telegram_username if the user has set or changed it since joining."""
    username = user.get('username', '').lower()
    if username and member.user.telegram_username != username:
        member.user.telegram_username = username
        member.user.save(update_fields=['telegram_username'])


@login_required
def delete_pot(request, token):
    pot = get_object_or_404(Pot, invite_token=token)
    if request.method == 'POST':
        pot.drops.all().delete()  # cascades to splits; clears PROTECT references on members
        pot.delete()
        return redirect('home')
    return redirect('rename_pot', token=token)


@login_required
def join_pot(request, token):
    pot = get_object_or_404(Pot, invite_token=token)
    user = get_telegram_user(request)
    compot_user, _ = CompotUser.objects.get_or_create(
        telegram_user_id=user['id'],
        defaults={
            'name': f"{user['first_name']} {user.get('last_name', '')}".strip(),
            'telegram_username': user.get('username', '').lower(),
        },
    )
    member, created = Member.objects.get_or_create(pot=pot, user=compot_user)
    if not created:
        _sync_member_username(member, user)
    return redirect('pot_detail', token=pot.invite_token)


@login_required
def add_placeholder(request, token):
    pot = get_object_or_404(Pot, invite_token=token)
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        if name:
            compot_user = CompotUser.objects.create(name=name, is_placeholder=True)
            Member.objects.create(pot=pot, user=compot_user)
    return redirect('rename_pot', token=token)


@login_required
def generate_claim_link(request, token, member_id):
    pot = get_object_or_404(Pot, invite_token=token)
    member = get_object_or_404(Member, id=member_id, pot=pot, user__is_placeholder=True)
    if request.method == 'POST':
        PlaceholderClaim.objects.filter(member=member).delete()
        claim = PlaceholderClaim.objects.create(
            member=member,
            expires_at=timezone.now() + datetime.timedelta(hours=1),
        )
        claim_url = request.build_absolute_uri(f'/claim/{claim.token}/')
        return render(request, 'claim_link.html', {'pot': pot, 'member': member, 'claim_url': claim_url})
    return redirect('rename_pot', token=token)


@login_required
def claim_placeholder(request, claim_token):
    claim = get_object_or_404(PlaceholderClaim, token=claim_token)
    if not claim.is_valid():
        return render(request, 'claim_expired.html')

    pot = claim.member.pot
    user = get_telegram_user(request)

    # Block if claimer already has a slot in this pot
    if Member.objects.filter(pot=pot, user__telegram_user_id=user['id']).exists():
        return render(request, 'claim_already_member.html', {'pot': pot})

    if request.method == 'POST':
        placeholder_user = claim.member.user
        existing_user = CompotUser.objects.filter(telegram_user_id=user['id']).first()

        if existing_user:
            # Claimer already has a CompotUser — reassign the member slot to it
            # and delete the now-orphaned placeholder CompotUser
            claim.member.user = existing_user
            claim.member.save(update_fields=['user'])
            placeholder_user.delete()
        else:
            # First time claiming — fill in the placeholder CompotUser
            placeholder_user.telegram_user_id = user['id']
            placeholder_user.name = f"{user['first_name']} {user.get('last_name', '')}".strip()
            placeholder_user.telegram_username = user.get('username', '').lower()
            placeholder_user.is_placeholder = False
            placeholder_user.save()

        claim.delete()
        return redirect('pot_detail', token=pot.invite_token)

    return render(request, 'claim_confirm.html', {'pot': pot, 'member': claim.member})


# --- Shopping lists ---

def _get_list_member(shopping_list, user):
    """Return ListMember for the current user in this list, or None."""
    return ListMember.objects.filter(shopping_list=shopping_list, user__telegram_user_id=user['id']).first()


@login_required
def create_list(request):
    user = get_telegram_user(request)
    compot_user = CompotUser.objects.filter(telegram_user_id=user['id']).first()
    if not compot_user:
        return redirect('home')
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        if name:
            shopping_list = ShoppingList.objects.create(name=name, created_by=compot_user)
            ListMember.objects.create(shopping_list=shopping_list, user=compot_user)
            return redirect('list_detail', token=shopping_list.invite_token)
    return render(request, 'create_list.html')


@login_required
def join_list(request, token):
    shopping_list = get_object_or_404(ShoppingList, invite_token=token)
    user = get_telegram_user(request)
    compot_user = CompotUser.objects.filter(telegram_user_id=user['id']).first()
    if not compot_user:
        return redirect('home')
    ListMember.objects.get_or_create(shopping_list=shopping_list, user=compot_user)
    return redirect('list_detail', token=token)


@login_required
def list_detail(request, token):
    shopping_list = get_object_or_404(ShoppingList, invite_token=token)
    user = get_telegram_user(request)
    list_member = _get_list_member(shopping_list, user)
    if not list_member:
        return redirect('join_list', token=token)
    items = shopping_list.items.select_related('checked_by__user').order_by('checked', 'created_at')
    return render(request, 'list_detail.html', {
        'list': shopping_list,
        'items': items,
        'list_member': list_member,
    })


@login_required
def add_item(request, token):
    shopping_list = get_object_or_404(ShoppingList, invite_token=token)
    user = get_telegram_user(request)
    list_member = _get_list_member(shopping_list, user)
    if not list_member:
        return redirect('join_list', token=token)
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        name = name[:1].upper() + name[1:]
        note = request.POST.get('note', '').strip()
        if name:
            Item.objects.create(shopping_list=shopping_list, name=name, note=note)
    return redirect('list_detail', token=token)


@login_required
def toggle_item(request, token, item_id):
    shopping_list = get_object_or_404(ShoppingList, invite_token=token)
    user = get_telegram_user(request)
    list_member = _get_list_member(shopping_list, user)
    if not list_member:
        return redirect('join_list', token=token)
    item = get_object_or_404(Item, id=item_id, shopping_list=shopping_list)
    if request.method == 'POST':
        item.checked = not item.checked
        item.checked_by = list_member if item.checked else None
        item.save(update_fields=['checked', 'checked_by'])
    return redirect('list_detail', token=token)


@login_required
def edit_item(request, token, item_id):
    shopping_list = get_object_or_404(ShoppingList, invite_token=token)
    user = get_telegram_user(request)
    list_member = _get_list_member(shopping_list, user)
    if not list_member:
        return redirect('join_list', token=token)
    item = get_object_or_404(Item, id=item_id, shopping_list=shopping_list)
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        name = name[:1].upper() + name[1:]
        note = request.POST.get('note', '').strip()
        if name:
            item.name = name
            item.note = note
            item.save(update_fields=['name', 'note'])
            return redirect('list_detail', token=token)
    return render(request, 'edit_item.html', {'list': shopping_list, 'item': item})


@login_required
def delete_item(request, token, item_id):
    shopping_list = get_object_or_404(ShoppingList, invite_token=token)
    user = get_telegram_user(request)
    list_member = _get_list_member(shopping_list, user)
    if not list_member:
        return redirect('join_list', token=token)
    item = get_object_or_404(Item, id=item_id, shopping_list=shopping_list)
    if request.method == 'POST':
        item.delete()
    return redirect('list_detail', token=token)


@login_required
def list_settings(request, token):
    shopping_list = get_object_or_404(ShoppingList, invite_token=token)
    user = get_telegram_user(request)
    list_member = _get_list_member(shopping_list, user)
    if not list_member:
        return redirect('join_list', token=token)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'rename':
            name = request.POST.get('name', '').strip()
            if name:
                shopping_list.name = name
                shopping_list.save(update_fields=['name'])
                return redirect('list_detail', token=token)
        elif action == 'delete':
            shopping_list.delete()
            return redirect('home')
    return render(request, 'list_settings.html', {'list': shopping_list})


@login_required
def import_items(request, token):
    shopping_list = get_object_or_404(ShoppingList, invite_token=token)
    user = get_telegram_user(request)
    list_member = _get_list_member(shopping_list, user)
    if not list_member:
        return redirect('join_list', token=token)
    if request.method == 'POST' and request.FILES.get('file'):
        f = request.FILES['file']
        text = f.read().decode('utf-8', errors='replace')
        reader = csv.reader(io.StringIO(text))
        for row in reader:
            if not row:
                continue
            name = row[0].strip()
            note = row[1].strip() if len(row) > 1 else ''
            if name:
                Item.objects.create(shopping_list=shopping_list, name=name, note=note)
    return redirect('list_detail', token=token)
