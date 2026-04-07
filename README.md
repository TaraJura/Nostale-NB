NB Monitor:

<img width="801" height="490" alt="image" src="https://github.com/user-attachments/assets/8f4da6e7-8b16-44f0-89e3-a6ebe1eeb73d" />

# NosTale Market Bot

A Python bot for NosTale that does two things on the in-game NosBazar (player auction house):

1. **Auto-relist** your own listings, undercutting the cheapest competitor by 1 gold (with a `min_price` floor so you never sell at a loss).
2. **Monitor profitability** of items you might buy from NosMall (premium currency shop) or NPC vendors and resell on NosBazar — sorted gold-per-ND so the most profitable flips appear at the top.

Both modes share the same item configuration list and the same `phoenixapi` connection layer.

---

## Features

### Relist mode (default)
- Continuously polls market prices for items in your inventory.
- Undercuts the cheapest non-self listing by 1 gold.
- Refuses to undercut below your configured `min_price` (floor protection).
- Calculates listing tax automatically.
- Runs across multiple items / multiple characters in one process.

### Monitor mode (`-monitor`)
- Polls cheapest NosBazar listing for every configured item.
- Computes profitability against either:
  - **NosMall ND cost** → shown as `gold/ND` (e.g. `27,596 g/ND`)
  - **NPC gold cost** → shown as multiplier (e.g. `6.7x`)
- Renders a sorted box-drawing table with the most profitable items on top.
- **Automatically opens the NosBazar window in-game** by replaying the NPC interaction packets — no need to click anything before starting.
- **Auto-recovers** when you walk away from / back to the Bibi Basar NPC. While the NPC is unreachable it sits in a quiet "waiting state" and only sends the lightweight 4-packet open sequence — never spams search packets.
- Color-coded warnings (yellow for partial timeouts, red for complete failures, green for success).
- Configurable refresh interval (`--refresh N`, default 30s).

---

## Setup Guide

### Prerequisites

1. **Install Python** ([python.org](https://www.python.org/downloads/)) — make sure to tick "Add Python to PATH".
2. **Install PyWin32**:
   ```
   pip install pywin32
   ```
3. **Download PhoenixAPI** from [github.com/hatz2/PhoenixAPI](https://github.com/hatz2/PhoenixAPI) and extract it (e.g. to `C:\NosTale\PhoenixAPI`).

### Install the bot

Copy `nostale_market_bot.py` to `C:\NosTale\PhoenixAPI\python` (or wherever your PhoenixAPI installation lives — the script needs to be able to import `phoenixapi`).

The repo includes a local `phoenixapi/` folder for development on Linux/WSL2 — on Windows you can rely on the PhoenixAPI installation instead.

---

## Running

```bash
# Profitability monitor (recommended for buy-and-flip workflows)
python3 nostale_market_bot.py -monitor

# Custom refresh interval (60 seconds)
python3 nostale_market_bot.py -monitor --refresh 60

# Relist loop (default mode)
python3 nostale_market_bot.py
```

On Windows the command is usually `py nostale_market_bot.py -monitor` instead of `python3`.

### Command-line options

| Flag | Default | Description |
|---|---|---|
| `-monitor` | off | Switch to profitability monitor mode. Without this flag the script runs the relist loop. |
| `--refresh N` | `30` | Monitor refresh interval in seconds. Each pass takes ~2.5s × number-of-items, so very low values aren't useful. |
| `-h` / `--help` | — | Print usage. |

### Prerequisites for `-monitor`

- Phoenix bot is running and a NosTale client matching each `character` field in `ITEMS` is attached.
- Your character must eventually be standing next to a **Bibi Basar (NosBazar) NPC**. You can start the script *before* walking there — it'll just sit in waiting state and start querying as soon as you arrive. Same thing if you walk away mid-session: it auto-detects, drops back to waiting state, and resumes when you return. **No restart needed.**

### Prerequisites for relist mode

- Phoenix bot running and character attached.
- The character has the items you want to sell **in inventory** (the script auto-detects the inventory slot per pass).
- You're standing in front of the Bibi Basar NPC with the NosBazar window open client-side (relist mode does NOT auto-open the window — start it after clicking the NPC manually).

---

## Configuration

Everything is driven by **`items.py`** - a separate config file with two top-level values:

- `DEFAULT_CHARACTER` - your in-game character name. Applied to every item that doesn't override it. Change this once at the top of `items.py` and all items follow.
- `ITEMS` - the list of items to track. Each item is a dict.

Editing `items.py` is the only thing you need to do to add/remove items, change costs, or switch characters. The main script `nostale_market_bot.py` doesn't need to be touched for normal config changes.

### Field reference

| Field | Required for | Meaning |
|---|---|---|
| `name` | both | Display label only - **NOT** sent to NosBazar. The actual search uses the vnums inside `search_packet`. Pick whatever name helps you cross-reference your spreadsheet. |
| `character` | optional | Character name passed to `phoenixapi.create_api_from_name()`. **Omit to use `DEFAULT_CHARACTER`.** Set per-item only if you have multiple characters and want this specific item to use a different one. |
| `search_packet` | both | Full `c_blist` packet string. Set to `None` to disable an item entirely (both loops skip it). |
| `vnum` | relist | Item VNUM — used to locate the item in your inventory. |
| `inv_tab` | relist | `0`=Equip, `1`=Main, `2`=Etc — which inventory tab the item is in. |
| `amount` | relist | How many pieces per listing. |
| `unk1` / `unk2` / `durability` / `medal` | relist | Constants for the `c_reg` register packet. Defaults of `9 / 4 / 1 / 2` work for most items in Main/Etc tabs. |
| `min_price` | relist | Floor price — won't undercut below this. Set to a huge number (`9999999999`) for monitor-only items so accidental relisting can't lose money. |
| `nos_cost` | monitor | Cost in **NosMall ND** (premium currency). Fractional allowed (e.g. `0.5`). Used to compute `gold/ND` profitability. |
| `npc_cost` | monitor | Cost in **gold** from an NPC vendor. Used to compute an `Nx` multiplier (NB price ÷ NPC cost). Mutually exclusive with `nos_cost` — if both are set, `nos_cost` wins. |

### Example: monitor-only item (uses DEFAULT_CHARACTER)

```python
{
    "name": "bubbl",
    "vnum": 2174, "inv_tab": 2,
    "search_packet": "c_blist 0 0 0 0 0 0 0 0 4 1261 2174 9480 10029",
    "amount": 5, "nos_cost": 0.5,
    "unk1": 10, "unk2": 3, "durability": 1, "medal": 2,
    "min_price": 43000,
}
```

### Example: NPC item (gold cost, no ND)

```python
{
    "name": "Pet Food (NPC)",
    "vnum": 2077, "inv_tab": None,
    "search_packet": "c_blist 0 0 0 0 0 0 0 0 11 2077 2078 2158 2187 2325 2663 2671 10013 10014 10024 10030",
    "amount": 5,
    "npc_cost": 300,  # gold per piece from NPC vendor
    "unk1": 9, "unk2": 4, "durability": 1, "medal": 2, "min_price": 9999999999,
}
```

### Example: per-item character override (multi-character setup)

```python
{
    "name": "alt-only item",
    "character": "myAltChar",   # overrides DEFAULT_CHARACTER for this entry
    "vnum": 1234, "inv_tab": 1,
    "search_packet": "c_blist 0 0 0 0 0 0 0 0 1 1234",
    ...
}
```

### Capturing a `c_blist` packet for a new item

1. Enable packet logging in Phoenix.
2. In-game, open the NosBazar window and search for the item you want to track.
3. Find the `[SEND] c_blist ...` line in the packet log and copy it verbatim into the `search_packet` field.
4. Format reference:
   ```
   c_blist 0 0 0 0 0 0 0 0 <count> <vnum1> <vnum2> ...
   ```
   The 8 zeros are filter slots (page/type/subtype/etc). `<count>` must equal the number of vnums that follow.

### Adding a new character

For a single-character setup, just change `DEFAULT_CHARACTER` at the top of `items.py`. For multi-character setups, set `"character": "otherChar"` on the items that should use a different character. The script auto-discovers all unique characters in `ITEMS`, opens one connection per character at startup, and routes each item's queries through the right connection.

---

## Example monitor output

```
=== NosBazar Monitor [00:36:41] ===
┌──────────────────┬────────┬────────────┬──────────────┬───────────────┐
│ Item             │   Cost │   NB Price │       Profit │ Seller        │
├──────────────────┼────────┼────────────┼──────────────┼───────────────┤
│ bubbl            │ 0.5 ND │     13,798 │  27,596 g/ND │ †Artemisa†    │
│ stone bles       │   1 ND │     26,999 │  26,999 g/ND │ MeaningLess   │
│ Fairy Experience │ 2.5 ND │     61,000 │  24,400 g/ND │ Lindbloom     │
│ ner skill ticket │  50 ND │  1,119,999 │  22,399 g/ND │ Xianzhou      │
│ Wings of f       │ 0.5 ND │     10,799 │  21,598 g/ND │ MeaningLess   │
│ en specialis     │ 100 ND │  1,948,888 │  19,488 g/ND │ Kaito         │
│ ...                                                                    │
│ Pet Food (NPC)   │  300 g │      1,996 │         6.7x │ DannyL14      │
│ Draco            │      - │    128,900 │            - │ NecroHyper    │
└──────────────────┴────────┴────────────┴──────────────┴───────────────┘

Refreshing in 30s... (Ctrl+C to stop)
```

Items with no listings show `n/a`. Items with no cost (like `Draco` above) sort to the bottom for reference.

---

## Error handling

The script handles common failures gracefully without crashing:

| Situation | Behavior |
|---|---|
| Phoenix bot not running for one character | Yellow warning, that character's items are skipped, script keeps running with the rest. |
| Phoenix bot not running for *any* character | Red error and clean exit. |
| Bibi Basar NPC not nearby at startup | Red error, monitor enters **waiting state**, retries `open_bazaar` every refresh. Script keeps running. |
| All item queries time out mid-session | Red error, monitor drops back into waiting state (no more search packets sent until the bazaar can be re-opened). |
| Some items time out (transient drops) | Yellow warning naming the failed items, retried automatically once per pass. |
| Item with no `search_packet` | Silently skipped (use `None` to disable items without removing them). |

### What "waiting state" means

When the bazaar can't be opened (NPC out of range), the monitor enters waiting state. In this state it sends ONLY the 4-packet `open_bazaar` sequence each refresh:
```
npc_req 2 10188              # request dialog with Bibi Basar
n_run 60 0 2 10188           # click "NosBazar" option
c_blist 0 0 0 0 0 0 0 0 0    # init bazaar listing
c_slist 0 0 0                # init seller list
```
It does NOT send the per-item `c_blist` searches until `open_bazaar` succeeds again. This way moving away from the NPC won't get the character flagged for spam.

---

## Important notes

- **Don't lower the inter-item sleep below 2.5s** in monitor mode. The game silently drops `c_blist` packets sent faster than ~2s apart.
- **`name` field is display-only.** It's not sent to NosBazar — the search is purely by vnum from `search_packet`. Renaming items doesn't affect what gets queried.
- **Verbose mode** (per-item `Sending search packet for ...` lines) is currently enabled in `monitor_items.query()`. Flip the `verbose=True` to `False` in that one call to silence it.
- **The bot only modifies items you explicitly configure** in `ITEMS`. It will never touch other items in your inventory.
- **Always test new items in monitor mode first** before relying on relist behavior.

---

## Troubleshooting

| Symptom | Likely cause |
|---|---|
| `RuntimeError: No bot windows found.` | Phoenix bot isn't running, or no client matches the `character` name. |
| Monitor sits in waiting state forever | Character isn't actually next to a Bibi Basar NPC, or you're on a different map. |
| Specific items always show `n/a` | The market genuinely has no listings for that item right now (try a popular item to confirm), or the captured `search_packet` is wrong. |
| Specific items intermittently time out | Transient packet drops — the retry pass should catch most. If persistent, your inter-item pacing may be too aggressive. |
| `KeyError` on a character name | An item in `ITEMS` references a character that failed to connect — check the connection warnings at startup. |

---

## Files in this repo

| File | What it is |
|---|---|
| `nostale_market_bot.py` | The main bot script (relist + monitor). Doesn't need editing for normal config changes. |
| `items.py` | Item configuration: `DEFAULT_CHARACTER` and the `ITEMS` list. **This is the file you edit to add/remove items or change costs.** |
| `phoenixapi/` | Local copy of the PhoenixAPI Python bindings (for Linux/WSL2 development). On Windows, prefer the upstream PhoenixAPI install. |
| `CLAUDE.md` | Architecture / internals reference for AI coding assistants editing this repo. |
| `README.md` | This file. |
