# Nostale-NB

A single-file Python script (`nostale_market_bot.py`) that talks to a running NosTale game client through the local `phoenixapi` package and automates two flows on the in-game NosBazar (player auction house):

1. **Relisting** (default mode) - for items the user is selling, query the cheapest current listing, undercut by 1 gold, and re-register at the new price (with a `min_price` floor to protect profit margins).
2. **Profitability monitoring** (`-monitor` flag) - for items the user *might* buy from NosMall (premium currency shop) or from NPC vendors and resell on NosBazar, query the cheapest current listing and compute a profitability ratio against the source cost. Sorted descending so the most profitable flips sit at the top.

---

## Game context (what NosTale is and why this bot exists)

**NosTale** is a free-to-play 2.5D anime-style MMORPG developed by Entwell and published by Gameforge. It launched in 2006 and is still actively run. Players pick from five classes (Adventurer, Sorcerer, Archer, Swordsman, Martial Artist), level both a combat level and a job level, and progress through PvE quests, dungeons, and PvP content. ([Class wiki](https://nostale.fandom.com/wiki/Class), [NosTale wiki](https://nostale.fandom.com/wiki/NosTale))

The relevant systems for understanding this bot:

### Two currencies

- **Gold** - the in-game currency. Earned by killing monsters, selling drops, completing quests, running dungeons (e.g. Spacetime Rift), and trading on NosBazar. This is the currency the bot's profit numbers are denominated in. ([Gold farming guide](https://www.mmocs.com/news/nostale-guide-what-you-need-to-know-about-gold-farming.html))
- **NosDollars (ND)** - Gameforge's real-money premium currency. Bought with cash via the Steam top-up flow or the Gameforge shop. ND is **not** earnable through gameplay - it only enters the economy via real-money purchases. ([NosDollars Steam guide](https://steamcommunity.com/sharedfiles/filedetails/?id=1138157981))

### NosMall (the cash shop)

The **NosMall** is the official in-game cash shop where players spend ND on items not obtainable through normal play. ([NosMall wiki](https://nostale.fandom.com/wiki/Nosmall)) Categories of items relevant to this bot:

- **Specialist Card protection scrolls** (`Lower SP Protection`, `Higher SP Protection`, `Dragon Card Protection`) - these protect a Specialist Card from being destroyed during upgrade attempts. Without them, a failed upgrade can wipe out hours/days/weeks of farming. They're a *core* p2w item because the SP system is the main power-progression treadmill. ([Protection scroll announcement](https://store.steampowered.com/news/posts/?feed=steam_community_announcements&appids=550470))
- **Equipment Protection Scrolls** - same idea but for weapon/armor upgrades.
- **Cancel Cards** - remove a stat from an item so it can be re-rolled.
- **Blessed Stones** - upgrade material for SP cards.
- **Inner Skill Tickets, Blessing Amulets, Fairy XP Boosters** - QoL/progression boosters.
- **Pets, partners, costumes, name change tickets** - cosmetic and convenience items.
- **NosMerchant Medal** - a NosMall item that grants vendor perks: no NosBazar sale fee, longer listing duration (longer than the default 30 days), discounted listing fees, and the ability to list up to 100 items at once. ([NosBazar overview](http://gameguide.nostale.co.uk/main/game_trade))

These items are exactly the ones in `ITEMS` with a `nos_cost` field. Their ND values (e.g. `2.5`, `5`, `50`, `100`) come from the user's NosMall price spreadsheet.

### NosBazar (the player auction house)

The **NosBazar** is NosTale's player-to-player auction house, accessed by talking to a Bibi Basar NPC in any major town. ([NosBazar guide](http://gameguide.nostale.co.uk/main/game_trade)) Key mechanics:

- Listings are paid for in **gold**, not ND. So the entire trade flow is "buy in ND, sell in gold."
- Insertion fees and sale fees apply (waived/reduced with the NosMerchant Medal).
- Maximum price per listing is 100,000,000 gold; default listing duration is up to 30 days.
- Listings are filterable by item, but *only* by VNUM (item ID). The display name in the search bar doesn't matter to the server - it filters server-side by VNUM. (This is why the bot's `name` field is purely cosmetic and the real search happens via vnums in `search_packet`.)

### The "buy in ND, sell in gold" flip economy

Because NosMall items can only be bought with ND but NosBazar settles in gold, there's a natural arbitrage market: players who don't want to spend real money buy NosMall items second-hand from players who do, paying gold for them. This creates a stable **gold-per-ND exchange rate** that varies by item:

- High-demand consumables (Bubble of Conservation, Wings of Friendship, Speakers, etc.) trade at the highest g/ND ratios because they're consumed quickly and constantly in demand.
- High-cost progression items (Pen Specialist 100 ND, Inner Skill Ticket 50 ND) trade at lower g/ND but absolute gold values are large.
- The g/ND ratio is essentially the implicit market price of NosTale's premium currency, denominated in farmable gold. Tracking it tells a player which NosMall items convert ND to gold most efficiently.

The reverse flow also exists: items bought cheap from NPC vendors (e.g. Pet Food at ~300g) sometimes resell on NosBazar for several multiples of NPC price, due to convenience or location. This is what the `npc_cost` field tracks. ([Reselling discussion](https://www.mmocs.com/news/nostale-guide-what-you-need-to-know-about-gold-farming.html))

### Why this bot exists

NosTale is widely considered pay-to-win. The game's progression treadmill (Specialist Card upgrades, equipment upgrades) has random failure outcomes that destroy expensive items, and the only reliable insurance is NosMall protection scrolls bought with real money. ([Card upgrading wiki](https://nostale.fandom.com/wiki/Card_Upgrading))

A player who wants to compete *without* spending money has two options:
1. **Farm gold** in-game and **buy NosMall items second-hand** from other players via NosBazar.
2. **Flip items** - buy cheap from NosMall (or NPC), resell on NosBazar at a markup, accumulate gold.

Both strategies require knowing the *current* gold-per-ND exchange rate for each NosMall item, since prices fluctuate constantly with supply/demand. Manually checking 17+ items every few minutes via the in-game NosBazar search is tedious. **This bot does that automatically:**

- `-monitor` mode polls the cheapest current NosBazar listing for every item the user tracks and computes profitability against the source cost (ND for NosMall items, gold for NPC items).
- The result is a live, sorted "best flips right now" table - the user can see at a glance which item is currently the most efficient gold→ND conversion (or NPC→NB flip).
- The relist mode (default) handles the *seller* side of the same trade: keeping the user's own listings competitive (1g cheaper than the cheapest competitor) without manually re-listing every few minutes.

In short: this bot automates the price-discovery and listing-maintenance chores of being a NosBazar trader, so a non-paying player can efficiently farm gold and exchange it for NosMall items at the best available rates.

## Running

```bash
python3 nostale_market_bot.py                       # default = relist loop
python3 nostale_market_bot.py -monitor              # profitability monitor
python3 nostale_market_bot.py -monitor --refresh 60 # custom refresh interval
```

The game client and the script communicate via the `phoenixapi` local package — the user must have a NosTale client + Phoenix bot running before starting the script. Each character is contacted via `create_api_from_name(character)`.

## Prerequisites for `-monitor`

- Phoenix bot is running and a NosTale client matching each `character` field in `ITEMS` is attached.
- The character must eventually be **standing next to a Bibi Basar (NosBazar) NPC**. You can start the script *before* walking there — it'll just sit in waiting state, retry `open_bazaar` every refresh, and start querying as soon as you arrive. Same thing if you walk away mid-session: it auto-detects, drops back to waiting state, and resumes when you return.

## Architecture

Single file: `nostale_market_bot.py`. Key pieces:

### `open_bazaar(api, verbose)`
Replays the in-game NosBazar NPC interaction by sending:
```
npc_req 2 10188              # request dialog with Bibi Basar
n_run 60 0 2 10188           # click "NosBazar" option in dialog
c_blist 0 0 0 0 0 0 0 0 0    # init bazaar listing (no filter)
c_slist 0 0 0                # init seller list
```
Then waits up to 3s for an `rc_blist` response confirming the bazaar window is open. Returns `True` on success, `False` if the NPC isn't nearby. Called by `monitor_items` whenever it's in waiting state — at startup and whenever a query pass detects the bazaar has closed.

### `fetch_cheapest_listing(api, item_config, verbose)`
Sends one `c_blist` search packet, polls `packet_manager.get_pending_recv_packets()` for an `rc_blist` response, parses the first listing's price (`item_details[6]`) and seller (`item_details[2]`). Returns `(price, seller, status)` where `status` is one of:
- `"ok"` — got a real listing
- `"empty"` — server replied but the bazaar has no listings for this item
- `"timeout"` — no `rc_blist` arrived within 5s (bazaar closed, rate-limited, or wrong client state)
- `"bad"` — response came back malformed

Drains stale packets *before* sending so prior responses don't get misattributed. Verbose mode prints diagnostics on every failure mode.

### `check_and_update_price(api, item_config)`
Relist flow. Looks up the item in inventory via `find_item_slot`, calls `fetch_cheapest_listing`, computes `new_price = cheapest - 1`, refuses to undercut below `min_price`, builds a `c_reg` packet, sends it.

### `monitor_items(apis, items, refresh)`
Monitor flow with a two-state machine (`bazaar_open: bool`):

**Waiting state** (initial OR after a total-failure pass):
- Sends ONLY the lightweight `open_bazaar` 4-packet sequence — never per-item search packets.
- On failure → red `✗ Could not open NosBazar... Will check again in Ns.` and sleep until next refresh.
- On success → green `✓ NosBazar open — starting queries.` and transition to active state.
- This is what makes "walk away → walk back" auto-recovery work without spamming search packets while the NPC is unreachable.

**Active state** (per refresh cycle):
1. Subscribes the packet manager **once per character** for the whole pass (not per item — that caused subscribe/unsubscribe races dropping in-flight responses).
2. Queries every item via `fetch_cheapest_listing` with **2.5s pacing** between sends (the game silently drops `c_blist` packets if you spam them — original relist loop used 2s, monitor uses 2.5s for safety).
3. Runs a **retry pass** for any item with status `timeout` (transient drops are common). `empty` results are NOT retried — that's a definitive answer.
4. Renders a sorted box-drawing table with dynamic column widths.
5. Prints warnings: yellow `⚠ N item(s) timed out: name1, name2, ...` for partial failures.
6. **If ALL items timed out** → red error + sets `bazaar_open = False`, dropping back into waiting state on the next iteration. No more search spam until the bazaar can be re-opened.

### `ITEMS` (imported from `items.py`)

The item list lives in a separate module: `items.py`. The main script imports `ITEMS` and `DEFAULT_CHARACTER` from there:

```python
from items import ITEMS, DEFAULT_CHARACTER

for _it in ITEMS:
    _it.setdefault("character", DEFAULT_CHARACTER)
```

`DEFAULT_CHARACTER` is applied via `setdefault` so per-item `"character"` overrides still win. This means:

- **Single-character setup** (the common case): set `DEFAULT_CHARACTER = "yourname"` at the top of `items.py` once. Don't put `"character"` in any item dict.
- **Multi-character setup**: leave `DEFAULT_CHARACTER` as your main one and add `"character": "altname"` only to the items that should run on the alt.

When editing items, work in `items.py` - the main script doesn't need touching.

## Item config fields

| Field | Required for | Meaning |
|---|---|---|
| `name` | both | Display label only — **NOT** sent to NosBazar. Searches are by vnum via `search_packet`. Match the user's spreadsheet names exactly (e.g. `bubbl`, `wer SP Pro`, `tarot card g`) so the table cross-references their notes. |
| `character` | optional | Character name passed to `create_api_from_name`. **Omit to inherit `DEFAULT_CHARACTER` from `items.py`.** Per-item override only needed for multi-character setups. |
| `search_packet` | both | Full `c_blist` packet string (e.g. `c_blist 0 0 0 0 0 0 0 0 4 5370 9116 13593 13594`). `None` = skip this item entirely in both loops. |
| `vnum` | relist | Item VNUM — used by `find_item_slot` to locate the item in inventory for relisting |
| `inv_tab` | relist | `0`=Equip, `1`=Main, `2`=Etc — which inventory tab to scan |
| `amount` | relist | How many pieces per listing |
| `unk1` / `unk2` / `durability` / `medal` | relist | `c_reg` packet fields |
| `min_price` | relist | Floor price — won't undercut below this. Set to a huge number (`9999999999`) for monitor-only items so accidental relisting can't lose money. |
| `nos_cost` | monitor | Cost in **NosMall ND** (premium currency, fractional allowed e.g. `0.5`). Used to compute `gold/ND` profitability. |
| `npc_cost` | monitor | Cost in **gold** from an NPC vendor. Used to compute a `Nx` multiplier (NB price ÷ NPC cost). Mutually exclusive with `nos_cost` — if both are set, `nos_cost` wins (see `cost_info()`). |

## How `-monitor` displays profitability

Two cost units are supported simultaneously:

- **NosMall items** (`nos_cost` set) — profit shown as `g/ND` (e.g. `27,596 g/ND` for `bubbl`: NB price 13,798 ÷ 0.5 ND).
- **NPC items** (`npc_cost` set) — profit shown as `Nx` multiplier (e.g. `6.7x` for `Pet Food (NPC)`: NB price 1,996 ÷ 300 g).
- **Items with neither** (e.g. `Draco`) — show `-` in cost and profit columns; still appear at the bottom of the table for reference.

Sort key is `nb_price / cost` descending across all items regardless of unit. ND items naturally sort to the top because `gold/ND` ratios are large numbers (10⁴–10⁵) while NPC multipliers are small (10⁰–10²); that's expected and acceptable. Items without a cost or with no listing sort to the bottom.

Example output:

```
=== NosBazar Monitor [00:36:41] ===
┌──────────────────┬────────┬────────────┬──────────────┬───────────────┐
│ Item             │   Cost │   NB Price │       Profit │ Seller        │
├──────────────────┼────────┼────────────┼──────────────┼───────────────┤
│ bubbl            │ 0.5 ND │     13,798 │  27,596 g/ND │ †Artemisa†    │
│ stone bles       │   1 ND │     26,999 │  26,999 g/ND │ MeaningLess   │
│ Fairy Experience │ 2.5 ND │     61,000 │  24,400 g/ND │ Lindbloom     │
│ ...                                                                   │
│ Pet Food (NPC)   │  300 g │      1,996 │         6.7x │ DannyL14      │
│ Draco            │      - │    128,900 │            - │ NecroHyper    │
└──────────────────┴────────┴────────────┴──────────────┴───────────────┘
```

## Adding a new item

1. **Capture the `c_blist` packet.** In-game, with packet logging enabled, search for the item in NosBazar. Tail your packet log file and copy the `[SEND] c_blist ...` line. The format is:
   ```
   c_blist 0 0 0 0 0 0 0 0 <count> <vnum1> <vnum2> ...
   ```
   The 8 zeros are filter slots (page, type, subtype, etc.); `<count>` is the number of vnums that follow.
2. **Append a dict to `ITEMS`** with at least `name`, `character`, `search_packet`, and one of `nos_cost` / `npc_cost` (for monitor) or the full relist fields (for relisting).
3. **Run `python3 nostale_market_bot.py -monitor`** to verify it shows up in the table.
4. To **stub** an item without a packet yet, leave `search_packet=None` — both loops skip such items silently, so you can pre-populate names and costs before capturing packets.

## Adding a new character

Just use a different `character` value in any item dict. The script auto-discovers all unique characters in `ITEMS`, opens one `phoenixapi` connection per character at startup, and routes each item's queries through the right connection. If a character connection fails, that character's items are skipped automatically (not a fatal error — the script keeps running with whatever connected).

## Connection error handling

- **Per-character connection failure** → yellow `⚠ Could not connect to '<char>'` warning, script continues with remaining characters.
- **All connections failed** → red `✗ No characters connected. Nothing to do — exiting.` and `SystemExit(1)`.
- **Bazaar open failed** (NPC not nearby) → red `✗ Could not open NosBazar for: <char>` warning, monitor enters waiting state and retries every refresh interval. The script keeps running — no need to restart, just walk to Bibi Basar and the next refresh resumes queries automatically.
- **Errors during a fetch** → red `Error fetching <name>: ...`, monitor pass continues.

ANSI escapes (`\033[91m` red, `\033[93m` yellow, `\033[92m` green) are inline literals — no extra dependency.

## Gotchas

- **`name` field is display-only.** It is NOT sent to NosBazar. The actual search is the vnum list inside `search_packet`. Don't bother "fixing" the name to a more descriptive English string — keep them matching the source spreadsheet for cross-reference. Only `search_packet` affects what the game searches.
- **`c_blist` rate limit.** Sending searches faster than ~2s apart causes silent drops. Don't lower the monitor's inter-item `time.sleep(2.5)` without testing thoroughly.
- **Stale packet contamination.** `fetch_cheapest_listing` drains the recv queue before each send. If you ever remove that drain, expect `rc_blist` responses to get misattributed across items.
- **Subscribe/unsubscribe per item drops responses.** Subscribe **once per character per pass**, not per item — earlier code did per-item subscribe and lost in-flight `rc_blist` packets to the race.
- **Mid-session character movement is auto-handled.** If the player walks away from the NPC the next pass will see all timeouts, drop into waiting state, and retry `open_bazaar` every refresh until the player returns. No restart needed. Critically, while in waiting state the script does NOT send the per-item search packets — only the 4-packet open sequence — so it can't get the character flagged for spam.
- **Whitespace in `c_blist` packets matters loosely.** Some captured packets have double spaces (e.g. `c_blist  0 0 0 ...`) — the game tolerates them but they should be normalized to single spaces for consistency. If a packet stops working after editing, check whitespace.
- **`Job Stone` was actually `stone bles`.** The original packet (`3 1362 5195 9075`) was a Blessed Stone search all along. They were never different items; the entry was renamed to `stone bles` to match the source spreadsheet.
- **Verbose mode** (`fetch_cheapest_listing(..., verbose=True)`) is currently enabled in `monitor_items.query()` for debugging. To silence the per-item `Sending search packet for ...` lines, flip it to `verbose=False` in that one place.
