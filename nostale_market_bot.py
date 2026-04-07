from phoenixapi.finder import create_api_from_name
import argparse
import time


def calculate_tax(price, amount=5):
    total_price = price * amount
    total_tax = total_price * 0.0005
    return int(total_tax)


def find_item_slot(api, inv_tab, vnum):
    """Find the slot index of an item by VNUM in the given inventory tab."""
    if inv_tab == 1:
        slots = api.inventory_manager.get_main_tab()
    elif inv_tab == 2:
        slots = api.inventory_manager.get_etc_tab()
    elif inv_tab == 0:
        slots = api.inventory_manager.get_equip_tab()
    else:
        return None, 0

    for slot in slots:
        if slot["vnum"] == vnum and slot.get("quantity", 0) > 0:
            return slot["index"], slot["quantity"]
    return None, 0


def open_bazaar(api, verbose=False):
    """Open the NosBazar window by replaying the in-game NPC interaction.

    Sends:
      npc_req 2 10188              - request dialog with the NosBazar NPC (Bibi Basar)
      n_run 60 0 2 10188           - click the "NosBazar" option in the dialog
      c_blist 0 0 0 0 0 0 0 0 0    - init bazaar listing (no filter)
      c_slist 0 0 0                - init seller list

    Returns True once the server confirms with an rc_blist response.
    Returns False if no rc_blist arrives within 3s - meaning the NPC isn't
    nearby (or the player isn't in the same map).
    """
    # Drain stale packets first so we don't false-positive on a leftover rc_blist
    api.packet_manager.get_pending_recv_packets()

    api.packet_manager.send("npc_req 2 10188")
    time.sleep(0.3)
    api.packet_manager.send("n_run 60 0 2 10188")
    time.sleep(0.3)
    api.packet_manager.send("c_blist 0 0 0 0 0 0 0 0 0")
    api.packet_manager.send("c_slist 0 0 0")

    if verbose:
        print("Opening NosBazar window...")

    timeout = time.time() + 3
    while time.time() < timeout:
        for packet in api.packet_manager.get_pending_recv_packets():
            if packet.startswith("rc_blist"):
                if verbose:
                    print("NosBazar opened.")
                return True
        api.packet_manager.get_pending_send_packets()
        time.sleep(0.1)
    return False


def fetch_cheapest_listing(api, item_config, verbose=True):
    """Send a c_blist search and return (price, seller, status).

    status is one of:
      "ok"      - got a real listing, price/seller filled
      "empty"   - server replied but the bazaar has no listings for this item
      "timeout" - no rc_blist response within the timeout (bazaar likely closed,
                  rate limited, or wrong client state) - price/seller are None
      "bad"     - response came back malformed (price/seller None)

    Caller is responsible for subscribe/unsubscribe of the packet manager.
    """
    item_name = item_config["name"]
    # Drain stale packets so we don't read a leftover rc_blist from a prior call
    api.packet_manager.get_pending_recv_packets()
    api.packet_manager.send(item_config["search_packet"])
    if verbose:
        print(f"Sending search packet for {item_name}")

    seen = []  # capture everything for diagnostics on failure
    timeout = time.time() + 5
    while time.time() < timeout:
        packets = api.packet_manager.get_pending_recv_packets()
        for packet in packets:
            seen.append(packet)
            if not packet.startswith("rc_blist"):
                continue
            parts = packet.split(' ', 2)
            if len(parts) < 3:
                if verbose:
                    print(f"[{item_name}] empty rc_blist: {packet!r}")
                return None, None, "empty"
            items = parts[2].split(' ')
            if not items or not items[0]:
                if verbose:
                    print(f"[{item_name}] no items in rc_blist: {packet!r}")
                return None, None, "empty"
            item_details = items[0].split('|')
            if len(item_details) <= 6:
                if verbose:
                    print(f"[{item_name}] short item entry: {item_details}")
                return None, None, "bad"
            return int(item_details[6]), item_details[2], "ok"
        api.packet_manager.get_pending_send_packets()
        time.sleep(0.1)
    if verbose:
        rc = [p for p in seen if "blist" in p]
        if rc:
            print(f"[{item_name}] timeout - saw blist packets: {rc}")
        else:
            print(f"[{item_name}] timeout - NO rc_blist response (saw {len(seen)} other packets)")
    return None, None, "timeout"


def check_and_update_price(api, item_config):
    item_name = item_config["name"]
    print(f"{item_name}...")

    # Find the item's current slot in inventory
    inv_tab = item_config["inv_tab"]
    vnum = item_config["vnum"]
    slot, qty = find_item_slot(api, inv_tab, vnum)

    if slot is None:
        print(f"Item {item_name} (vnum {vnum}) not found in inventory tab {inv_tab}!")
        return False

    print(f"Found {item_name} at tab {inv_tab}, slot {slot}, qty {qty}")

    # Subscribe to packet monitoring
    api.packet_manager.subscribe()

    try:
        price, seller, _status = fetch_cheapest_listing(api, item_config)
        price_found = price is not None
        if price_found:
            print(f"{item_name} PRICE: {price}")
            print(f"{item_name} SELLER: {seller}")

            if seller != item_config["character"]:
                new_price = price - 1
                print(f"{item_name} CALCULATED NEW PRICE: {new_price}")

                if new_price < item_config["min_price"]:
                    print(f"WARNING: Market price ({new_price}) is below minimum threshold ({item_config['min_price']})")
                    print(f"Not updating price for {item_name} to protect profits")
                else:
                    tax = calculate_tax(new_price)
                    print(f"{item_name} TAX: {tax}")

                    # Build c_reg packet with correct slot
                    # c_reg [type] [inv_tab] [slot] [unk1] [unk2] [durability] [isPackage] [amount] [price] [tax] [medalUsed]
                    amount = item_config.get("amount", 5)
                    medal = item_config.get("medal", 2)
                    reg_packet = f"c_reg 0 {inv_tab} {slot} {item_config.get('unk1', 9)} {item_config.get('unk2', 4)} {item_config.get('durability', 1)} 0 {amount} {new_price} {tax} {medal}"

                    print(f"Sending packet: {reg_packet}")
                    api.packet_manager.send(reg_packet)
                    print(f"{item_name} price updated!")
            else:
                print(f"You are already the lowest seller for {item_name}!")
        else:
            print(f"No price data found for {item_name}")

    finally:
        api.packet_manager.unsubscribe()

    print(f"{item_name} check complete")
    return price_found


# Item configurations
# vnum: item VNUM to find in inventory
# inv_tab: 0=Equip, 1=Main, 2=Etc
# amount: how many to sell per listing
# nos_cost: how many ND (NosDollars) the item costs in NosMall
#           - used by -monitor mode to compute gold/ND profitability
# The slot is auto-detected from inventory!
ITEMS = [
    {
        "name": "Fairy Experience",
        "character": "root2",
        "vnum": 5370,
        "inv_tab": 1,
        "search_packet": "c_blist 0 0 0 0 0 0 0 0 4 5370 9116 13593 13594",
        "amount": 5,
        "nos_cost": 2.5,
        "unk1": 9, "unk2": 4, "durability": 1, "medal": 2,
        "min_price": 200000
    },
    {
        "name": "Lord Dra",
        "character": "root2",
        "vnum": 5500,
        "inv_tab": 1,
        "search_packet": "c_blist 0 0 0 0 0 0 0 0 1 5500",
        "amount": 5,
        "nos_cost": 0,
        "unk1": 9, "unk2": 4, "durability": 1, "medal": 2,
        "min_price": 31000
    },
    {
        "name": "stone bles",
        "character": "root2",
        "vnum": 1362,
        "inv_tab": 1,
        "search_packet": "c_blist 0 0 0 0 0 0 0 0 3 1362 5195 9075",
        "amount": 5,
        "nos_cost": 1,
        "unk1": 9, "unk2": 4, "durability": 1, "medal": 2,
        "min_price": 9999999999
    },
    {
        "name": "bubbl",
        "character": "root2",
        "vnum": 2174,
        "inv_tab": 2,
        "search_packet": "c_blist 0 0 0 0 0 0 0 0 4 1261 2174 9480 10029",
        "amount": 5,
        "nos_cost": 0.5,
        "unk1": 10, "unk2": 3, "durability": 1, "medal": 2,
        "min_price": 43000
    },
    {
        "name": "Wings of f",
        "character": "root2",
        "vnum": 2160,
        "inv_tab": 2,
        "search_packet": "c_blist 0 0 0 0 0 0 0 0 2 2160 10048",
        "amount": 5,
        "nos_cost": 0.5,
        "unk1": 10, "unk2": 3, "durability": 1, "medal": 2,
        "min_price": 7000
    },
    {
        "name": "en specialis",
        "character": "root2", "vnum": 907, "inv_tab": None,
        "search_packet": "c_blist 0 0 0 0 0 0 0 0 2 907 4240",
        "amount": 5, "nos_cost": 100,
        "unk1": 9, "unk2": 4, "durability": 1, "medal": 2, "min_price": 9999999999,
    },
    {
        "name": "ancel",
        "character": "root2", "vnum": 1286, "inv_tab": None,
        "search_packet": "c_blist 0 0 0 0 0 0 0 0 13 1286 1452 4717 5884 5885 5886 5887 5996 9041 9380 9874 13710 13731",
        "amount": 5, "nos_cost": 5,
        "unk1": 9, "unk2": 4, "durability": 1, "medal": 2, "min_price": 9999999999,
    },
    {
        "name": "ner skill ticket",
        "character": "root2", "vnum": 5931, "inv_tab": None,
        "search_packet": "c_blist 0 0 0 0 0 0 0 0 4 5931 5932 9109 9110",
        "amount": 5, "nos_cost": 50,
        "unk1": 9, "unk2": 4, "durability": 1, "medal": 2, "min_price": 9999999999,
    },
    {
        "name": "medicine",
        "character": "root2", "vnum": 1765, "inv_tab": None,
        "search_packet": "c_blist 0 0 0 0 0 0 0 0 5 1765 2159 2313 2390 10049",
        "amount": 5, "nos_cost": 2,
        "unk1": 9, "unk2": 4, "durability": 1, "medal": 2, "min_price": 9999999999,
    },
    {
        "name": "fairy bo",
        "character": "root2", "vnum": 1296, "inv_tab": None,
        "search_packet": "c_blist 0 0 0 0 0 0 0 0 3 1296 5194 9074",
        "amount": 5, "nos_cost": 5,
        "unk1": 9, "unk2": 4, "durability": 1, "medal": 2, "min_price": 9999999999,
    },
    {
        "name": "met pet food",
        "character": "root2", "vnum": 2158, "inv_tab": None,
        "search_packet": "c_blist 0 0 0 0 0 0 0 0 2 2158 10024",
        "amount": 5, "nos_cost": 2,
        "unk1": 9, "unk2": 4, "durability": 1, "medal": 2, "min_price": 9999999999,
    },
    {
        "name": "tarot card g",
        "character": "root2", "vnum": 1904, "inv_tab": None,
        "search_packet": "c_blist 0 0 0 0 0 0 0 0 1 1904",
        "amount": 5, "nos_cost": 10,
        "unk1": 9, "unk2": 4, "durability": 1, "medal": 2, "min_price": 9999999999,
    },
    {
        "name": "ment protec",
        "character": "root2", "vnum": 1218, "inv_tab": None,
        "search_packet": "c_blist 0 0 0 0 0 0 0 0 4 1218 5369 9458 9459",
        "amount": 5, "nos_cost": 20,
        "unk1": 9, "unk2": 4, "durability": 1, "medal": 2, "min_price": 9999999999,
    },
    {
        "name": "sing amulet",
        "character": "root2", "vnum": 282, "inv_tab": None,
        "search_packet": "c_blist 0 0 0 0 0 0 0 0 8 282 498 4262 4264 5735 8541 8543 8544",
        "amount": 5, "nos_cost": 50,
        "unk1": 9, "unk2": 4, "durability": 1, "medal": 2, "min_price": 9999999999,
    },
    {
        "name": "higher SP Pro",
        "character": "root2", "vnum": 1364, "inv_tab": None,
        "search_packet": "c_blist 0 0 0 0 0 0 0 0 4 1364 9464 9498 9925",
        "amount": 5, "nos_cost": 5,
        "unk1": 9, "unk2": 4, "durability": 1, "medal": 2, "min_price": 9999999999,
    },
    {
        "name": "wer SP Pro",
        "character": "root2", "vnum": 1363, "inv_tab": None,
        "search_packet": "c_blist 0 0 0 0 0 0 0 0 4 1363 9463 9497 9924",
        "amount": 5, "nos_cost": 5,
        "unk1": 9, "unk2": 4, "durability": 1, "medal": 2, "min_price": 9999999999,
    },
    {
        "name": "speak",
        "character": "root2", "vnum": 2173, "inv_tab": None,
        "search_packet": "c_blist 0 0 0 0 0 0 0 0 2 2173 10028",
        "amount": 5, "nos_cost": 0.5,
        "unk1": 9, "unk2": 4, "durability": 1, "medal": 2, "min_price": 9999999999,
    },
    {
        "name": "perfum",
        "character": "root2", "vnum": 1156, "inv_tab": None,
        "search_packet": "c_blist 0 0 0 0 0 0 0 0 2 1156 1428",
        "amount": 5, "nos_cost": 0.8,
        "unk1": 9, "unk2": 4, "durability": 1, "medal": 2, "min_price": 9999999999,
    },
    # ---- NPC items (cost in gold, not ND) ----
    {
        "name": "Pet Food (NPC)",
        "character": "root2", "vnum": 2077, "inv_tab": None,
        "search_packet": "c_blist 0 0 0 0 0 0 0 0 11 2077 2078 2158 2187 2325 2663 2671 10013 10014 10024 10030",
        "amount": 5,
        "npc_cost": 300,  # gold per piece from NPC vendor
        "unk1": 9, "unk2": 4, "durability": 1, "medal": 2, "min_price": 9999999999,
    },
]


def monitor_items(apis, items, refresh=30):
    """Continuously poll NosBazar prices and print a sorted profitability table.

    For each item with a configured nos_cost, computes gold-per-ND
    (cheapest NB listing price / NosMall ND cost) and sorts descending so
    the most profitable items to buy from NosMall and resell sit on top.
    """
    YELLOW = "\033[93m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    RESET = "\033[0m"

    active_chars = {it["character"] for it in items}

    def try_open_all():
        """Try open_bazaar for every character. Returns list of failed characters."""
        failed = []
        for ch in active_chars:
            apis[ch].packet_manager.subscribe()
        try:
            for ch in active_chars:
                if not open_bazaar(apis[ch], verbose=True):
                    failed.append(ch)
        finally:
            for ch in active_chars:
                try:
                    apis[ch].packet_manager.unsubscribe()
                except Exception:
                    pass
        return failed

    bazaar_open = False  # state: are we currently able to query?

    while True:
        # ---- Waiting state ----
        # If the bazaar isn't open (startup or after a total failure), only
        # send the lightweight open sequence - never the per-item searches.
        # Keep retrying every refresh until the player walks back to the NPC.
        if not bazaar_open:
            failed = try_open_all()
            if failed:
                print(
                    f"\n{RED}✗ Could not open NosBazar for: {', '.join(failed)}{RESET}\n"
                    f"{RED}  Move next to a Bibi Basar (NosBazar) NPC. "
                    f"Will check again in {refresh}s. (Ctrl+C to stop){RESET}"
                )
                time.sleep(refresh)
                continue
            print(f"{GREEN}✓ NosBazar open - starting queries.{RESET}")
            bazaar_open = True

        # ---- Active state ----

        results = {}  # name -> (item, price, seller, status)
        # Subscribe once per character for the whole pass to avoid subscribe/
        # unsubscribe races that drop in-flight rc_blist responses.
        for ch in active_chars:
            apis[ch].packet_manager.subscribe()
        try:
            def query(item):
                if not item.get("search_packet"):
                    return None, None, "skipped"
                api = apis[item["character"]]
                try:
                    return fetch_cheapest_listing(api, item, verbose=True)
                except Exception as e:
                    print(f"{RED}Error fetching {item['name']}: {e}{RESET}")
                    return None, None, "error"

            # First pass - pace at 2.5s between items to stay under the
            # game's c_blist rate limit (the relist loop uses 2s; we use a bit
            # more since we query everything every refresh).
            for item in items:
                price, seller, status = query(item)
                results[item["name"]] = (item, price, seller, status)
                time.sleep(2.5)

            # Retry pass - transient drops are common, so re-query anything
            # that timed out before giving up for this refresh.
            failed = [
                it for it in items
                if results[it["name"]][3] == "timeout" and it.get("search_packet")
            ]
            if failed:
                print(f"{YELLOW}Retrying {len(failed)} timed-out item(s)...{RESET}")
                time.sleep(2)
                for item in failed:
                    price, seller, status = query(item)
                    # Only overwrite if we got a real result; keep timeout status
                    # if retry also failed so we still warn the user.
                    if status == "ok" or status == "empty":
                        results[item["name"]] = (item, price, seller, status)
                    time.sleep(2.5)
        finally:
            for ch in active_chars:
                try:
                    apis[ch].packet_manager.unsubscribe()
                except Exception:
                    pass

        results_list = [(results[it["name"]][0],
                         results[it["name"]][1],
                         results[it["name"]][2]) for it in items]

        # Count outcomes for end-of-pass warnings
        statuses = [results[it["name"]][3] for it in items if it.get("search_packet")]
        timed_out = [it["name"] for it in items
                     if results[it["name"]][3] == "timeout"]
        all_failed = statuses and all(s == "timeout" for s in statuses)

        def cost_info(item):
            """Return (display_string, raw_cost, unit) where unit is 'ND' or 'g'."""
            nd = item.get("nos_cost")
            npc = item.get("npc_cost")
            if nd:
                return f"{nd} ND", nd, "ND"
            if npc:
                return f"{npc} g", npc, "g"
            return "-", None, None

        def sort_key(row):
            it, pr, _ = row
            _, cost, _ = cost_info(it)
            if pr is None or not cost:
                return -1
            return pr / cost

        results_list.sort(key=sort_key, reverse=True)

        # Build display rows first so we can size columns to actual content
        rows = []
        for it, pr, seller in results_list:
            cost_s, cost, unit = cost_info(it)
            if pr is None:
                price_s = "n/a"
                profit_s = "n/a"
            elif not cost:
                price_s = f"{pr:,}"
                profit_s = "-"
            else:
                price_s = f"{pr:,}"
                ratio = pr / cost
                # ND items: show "12,345 g/ND". NPC items: show "11.7x" multiplier.
                if unit == "ND":
                    profit_s = f"{int(ratio):,} g/ND"
                else:
                    profit_s = f"{ratio:.1f}x"
            rows.append((it["name"], cost_s, price_s, profit_s, seller or ""))

        headers = ("Item", "Cost", "NB Price", "Profit", "Seller")
        widths = [
            max(len(h), max((len(r[i]) for r in rows), default=0))
            for i, h in enumerate(headers)
        ]
        # Minimum widths for readability
        widths = [max(w, m) for w, m in zip(widths, (12, 6, 10, 12, 12))]

        def hline(left, mid, right, fill="─"):
            return left + mid.join(fill * (w + 2) for w in widths) + right

        def row_line(cells, aligns):
            parts = []
            for cell, w, a in zip(cells, widths, aligns):
                if a == "<":
                    parts.append(f" {cell:<{w}} ")
                else:
                    parts.append(f" {cell:>{w}} ")
            return "│" + "│".join(parts) + "│"

        aligns = ("<", ">", ">", ">", "<")

        ts = time.strftime("%H:%M:%S", time.localtime())
        print(f"\n=== NosBazar Monitor [{ts}] ===")
        print(hline("┌", "┬", "┐"))
        print(row_line(headers, aligns))
        print(hline("├", "┼", "┤"))
        for r in rows:
            print(row_line(r, aligns))
        print(hline("└", "┴", "┘"))

        # Warnings - surface timeouts the user couldn't see while logs were silent
        if all_failed:
            print(
                f"\n{RED}✗ ALL items timed out. The bazaar window may have closed "
                f"or the character moved away from the NPC.{RESET}\n"
                f"{RED}  Pausing item queries - will retry opening the bazaar next refresh.{RESET}"
            )
            bazaar_open = False  # drop into waiting state - no more search spam
        elif timed_out:
            print(
                f"\n{YELLOW}⚠  {len(timed_out)} item(s) timed out: "
                f"{', '.join(timed_out)}{RESET}"
            )

        print(f"\nRefreshing in {refresh}s... (Ctrl+C to stop)")
        time.sleep(refresh)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="NosTale market bot")
    parser.add_argument(
        "-monitor",
        action="store_true",
        help="Monitor NosBazar prices and show gold/ND profitability - does not relist anything",
    )
    parser.add_argument(
        "--refresh",
        type=int,
        default=30,
        help="Monitor refresh interval in seconds (default: 30)",
    )
    args = parser.parse_args()

    try:
        print("=== NosTale Market Bot ===")

        # Group items by character and create one API connection per character
        characters = {}
        for item in ITEMS:
            char = item["character"]
            if char not in characters:
                characters[char] = []
            characters[char].append(item)

        # ANSI colors for terminal output
        YELLOW = "\033[93m"
        RED = "\033[91m"
        GREEN = "\033[92m"
        RESET = "\033[0m"

        # Create persistent API connections
        apis = {}
        for char in characters:
            print(f"Connecting to {char}...")
            try:
                apis[char] = create_api_from_name(char)
                print(f"{GREEN}Connected to {char}!{RESET}")
            except Exception as e:
                print(
                    f"{YELLOW}⚠  Could not connect to '{char}': {e}{RESET}\n"
                    f"{YELLOW}   Make sure the Phoenix bot is running and a NosTale client "
                    f"named '{char}' is attached, then restart this script.{RESET}"
                )

        if not apis:
            print(f"{RED}✗ No characters connected. Nothing to do - exiting.{RESET}")
            raise SystemExit(1)

        # Drop items belonging to characters that failed to connect
        active_items = [it for it in ITEMS if it["character"] in apis]
        skipped = len(ITEMS) - len(active_items)
        if skipped:
            print(f"{YELLOW}   Skipping {skipped} item(s) tied to disconnected characters.{RESET}")

        if args.monitor:
            monitor_items(apis, active_items, refresh=args.refresh)

        while True:
            current_time = time.strftime("%H:%M:%S", time.localtime())
            print(f"\n[{current_time}] Starting market price checks...")

            for item in active_items:
                if not item.get("search_packet"):
                    continue  # monitor-only stub, no relist
                print(f"\n----------[ {item['name']} ]----------")
                try:
                    check_and_update_price(
                        api=apis[item['character']],
                        item_config=item
                    )
                except Exception as e:
                    print(f"Error: {e}")
                    # Reconnect on failure
                    try:
                        apis[item['character']] = create_api_from_name(item['character'])
                        print(f"Reconnected to {item['character']}")
                    except Exception:
                        print(f"Failed to reconnect to {item['character']}")
                time.sleep(2)

                print(f"----------[ {item['name']} Complete ]----------")

            print("\nWaiting 15 seconds before next check...")
            time.sleep(15)

    except KeyboardInterrupt:
        print("\nScript terminated by user.")
        print("Exiting...")
