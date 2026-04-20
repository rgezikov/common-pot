from django.contrib import admin
from .models import Pot, Member, Drop, Split, CompotUser, PlaceholderClaim, ShoppingList, ListMember, Item, ListItemSuggestion

admin.site.register(Pot)
admin.site.register(Member)
admin.site.register(Drop)
admin.site.register(Split)
admin.site.register(CompotUser)
admin.site.register(PlaceholderClaim)
admin.site.register(ShoppingList)
admin.site.register(ListMember)
admin.site.register(Item)
admin.site.register(ListItemSuggestion)
