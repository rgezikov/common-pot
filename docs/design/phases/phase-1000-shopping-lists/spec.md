# Phase 1000 — Shared Shopping Lists

> Collaborative checklists for groups, independent of expense tracking.

## Use case

A group (e.g. a sailing crew) creates a shopping list before a marina stop. Members add items they need to buy. In the supermarket, people pick up items and tick them off.

## Concept

A **list** is a standalone object, separate from pots. Any registered Common Pot user can create a list. Members are invited the same way as to a pot — via an invite link. All members can add items, edit items, edit item notes, and tick items off.

## Data model

- **List** — name, invite token, created by
- **ListMember** — list + CompotUser (same membership pattern as pots)
- **Item** — list, name, note (optional), checked (bool), checked by (ListMember, nullable)

## Features

- Create a list (any registered user)
- Invite others via link (same join-by-link flow as pots)
- Add items with an optional note (e.g. "2 kg", "the good one")
- Edit item name or note
- Tick/untick items — shows who checked it
- Delete items
- Delete list

## Constraints

- No Telegram bot support — web only
- No connection to pots or expense tracking
- No per-item assignment — anyone can tick anything

## Import from file

Items can be bulk-imported from a CSV file. The first column is the item name, the second column (optional) is the note. Extra columns are ignored. Items are appended to the existing list.

## Tasks

- Add List, ListMember, Item models
- Home screen: show lists alongside pots
- Create list flow
- Join list via invite link
- List detail: items with tick/untick, add item form
- Edit and delete items
- List settings: invite link, rename, delete
- Import items from CSV file (name, optional note)
