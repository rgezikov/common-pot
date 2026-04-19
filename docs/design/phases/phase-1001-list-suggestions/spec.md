# Phase 1001 — Shopping List: Item Name Suggestions & Duplicate Prevention

## Suggestions

The list remembers every item name ever entered (even after the item is deleted). When typing in the item name field — on both the add form and the edit form — the browser offers matching names as suggestions via the HTML `<datalist>` element.

- Names are stored in a `ListItemSuggestion` model (list + name, unique together).
- A suggestion is recorded when an item is added or edited.
- Suggestions persist across item deletion.

## Duplicate prevention

If the user tries to add an item whose name already exists on the list (case-insensitive) and is not yet ticked off, the item is not added and a warning is shown: `"<name>" is already on the list.`

- Already-checked items are not considered duplicates — you can re-add something that was previously bought and ticked off.
