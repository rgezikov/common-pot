import uuid
import datetime
from django.db import models


class Pot(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    invite_token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    telegram_chat_id = models.BigIntegerField(null=True, blank=True, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class CompotUser(models.Model):
    telegram_user_id = models.BigIntegerField(null=True, blank=True, unique=True)
    name = models.CharField(max_length=100)
    telegram_username = models.CharField(max_length=100, blank=True)
    is_placeholder = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class PlaceholderClaim(models.Model):
    member = models.OneToOneField('Member', on_delete=models.CASCADE, related_name='claim')
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    expires_at = models.DateTimeField()

    def is_valid(self):
        from django.utils import timezone
        return timezone.now() < self.expires_at

    def __str__(self):
        return f"Claim for {self.member}"


class Member(models.Model):
    pot = models.ForeignKey(Pot, on_delete=models.CASCADE, related_name='members')
    user = models.ForeignKey(CompotUser, on_delete=models.PROTECT, related_name='memberships')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('pot', 'user')

    # Proxy properties so templates and most code need no changes
    @property
    def name(self):
        return self.user.name

    @property
    def telegram_user_id(self):
        return self.user.telegram_user_id

    @property
    def telegram_username(self):
        return self.user.telegram_username

    def __str__(self):
        return f"{self.user.name} ({self.pot.name})"


class Drop(models.Model):
    SOURCE_WEB = 'web'
    SOURCE_TELEGRAM = 'telegram'
    SOURCE_CHOICES = [(SOURCE_WEB, 'Web'), (SOURCE_TELEGRAM, 'Telegram')]

    pot = models.ForeignKey(Pot, on_delete=models.CASCADE, related_name='drops')
    description = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    paid_by = models.ForeignKey(Member, on_delete=models.PROTECT, related_name='drops_paid')
    date = models.DateField()
    time = models.TimeField(default=datetime.time)
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default=SOURCE_WEB)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def was_edited(self):
        return (self.updated_at - self.created_at) > datetime.timedelta(seconds=5)

    def __str__(self):
        return f"{self.description} ({self.amount})"


class ShoppingList(models.Model):
    name = models.CharField(max_length=200)
    invite_token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    created_by = models.ForeignKey(CompotUser, on_delete=models.PROTECT, related_name='lists_created')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class ListMember(models.Model):
    shopping_list = models.ForeignKey(ShoppingList, on_delete=models.CASCADE, related_name='members')
    user = models.ForeignKey(CompotUser, on_delete=models.PROTECT, related_name='list_memberships')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('shopping_list', 'user')

    def __str__(self):
        return f"{self.user.name} ({self.shopping_list.name})"


class Item(models.Model):
    shopping_list = models.ForeignKey(ShoppingList, on_delete=models.CASCADE, related_name='items')
    name = models.CharField(max_length=200)
    note = models.CharField(max_length=200, blank=True)
    checked = models.BooleanField(default=False)
    checked_by = models.ForeignKey(ListMember, on_delete=models.SET_NULL, null=True, blank=True, related_name='checked_items')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class ListItemSuggestion(models.Model):
    shopping_list = models.ForeignKey(ShoppingList, on_delete=models.CASCADE, related_name='suggestions')
    name = models.CharField(max_length=200)

    class Meta:
        unique_together = ('shopping_list', 'name')

    def __str__(self):
        return self.name


class Split(models.Model):
    drop = models.ForeignKey(Drop, on_delete=models.CASCADE, related_name='splits')
    member = models.ForeignKey(Member, on_delete=models.PROTECT, related_name='splits')
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.member.name}: {self.amount}"
