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


def fetch_cheapest_listing(api, item_config, verbose=True):
    """Send a c_blist search and return (price, seller) of the cheapest listing.

    Returns (None, None) on timeout / no results. Caller is responsible for
    subscribe/unsubscribe of the packet manager.
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
                return None, None
            items = parts[2].split(' ')
            if not items or not items[0]:
                if verbose:
                    print(f"[{item_name}] no items in rc_blist: {packet!r}")
                return None, None
            item_details = items[0].split('|')
            if len(item_details) <= 6:
                if verbose:
                    print(f"[{item_name}] short item entry: {item_details}")
                return None, None
            return int(item_details[6]), item_details[2]
        api.packet_manager.get_pending_send_packets()
        time.sleep(0.1)
    if verbose:
        rc = [p for p in seen if "blist" in p]
        if rc:
            print(f"[{item_name}] timeout — saw blist packets: {rc}")
        else:
            print(f"[{item_name}] timeout — NO rc_blist response (saw {len(seen)} other packets)")
    return None, None


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
        price, seller = fetch_cheapest_listing(api, item_config)
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
# nos_cost: how many ND (NosMall diamonds) the item costs in NosMall
#           — used by -monitor mode to compute gold/ND profitability
# The slot is auto-detected from inventory!
ITEMS = [
    {
        "name": "Fairy",
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
        "name": "Draco",
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
        "name": "Job Stone",
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
        "name": "Buble",
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
        "name": "Friend Wing",
        "character": "root2",
        "vnum": 2160,
        "inv_tab": 2,
        "search_packet": "c_blist 0 0 0 0 0 0 0 0 2 2160 10048",
        "amount": 5,
        "nos_cost": 0.5,
        "unk1": 10, "unk2": 3, "durability": 1, "medal": 2,
        "min_price": 7000
    },

    # ---- TODO: NosMall items from spreadsheet ----
    # Fill in vnum, inv_tab, search_packet (and unk1/unk2/durability/medal/min_price if you want to relist).
    # Items with search_packet=None are skipped automatically by both monitor and relist loops.
    {
        "name": "Pen Specialist",  # "en specialis"
        "character": "root2", "vnum": 907, "inv_tab": None,
        "search_packet": "c_blist 0 0 0 0 0 0 0 0 2 907 4240",
        "amount": 5, "nos_cost": 100,
        "unk1": 9, "unk2": 4, "durability": 1, "medal": 2, "min_price": 9999999999,
    },
    {
        "name": "Cancel Card",  # "ancel"
        "character": "root2", "vnum": 1286, "inv_tab": None,
        "search_packet": "c_blist 0 0 0 0 0 0 0 0 13 1286 1452 4717 5884 5885 5886 5887 5996 9041 9380 9874 13710 13731",
        "amount": 5, "nos_cost": 5,
        "unk1": 9, "unk2": 4, "durability": 1, "medal": 2, "min_price": 9999999999,
    },
    {
        "name": "Blessed Stone",  # "stone bles"
        "character": "root2", "vnum": 1362, "inv_tab": None,
        "search_packet": "c_blist 0 0 0 0 0 0 0 0 3 1362 5195 9075",
        "amount": 5, "nos_cost": 1,
        "unk1": 9, "unk2": 4, "durability": 1, "medal": 2, "min_price": 9999999999,
    },
    {
        "name": "Inner Skill Ticket",  # "ner skill ticket"
        "character": "root2", "vnum": 5931, "inv_tab": None,
        "search_packet": "c_blist 0 0 0 0 0 0 0 0 4 5931 5932 9109 9110",
        "amount": 5, "nos_cost": 50,
        "unk1": 9, "unk2": 4, "durability": 1, "medal": 2, "min_price": 9999999999,
    },
    {
        "name": "Medicine",
        "character": "root2", "vnum": 1765, "inv_tab": None,
        "search_packet": "c_blist 0 0 0 0 0 0 0 0 5 1765 2159 2313 2390 10049",
        "amount": 5, "nos_cost": 2,
        "unk1": 9, "unk2": 4, "durability": 1, "medal": 2, "min_price": 9999999999,
    },
    {
        "name": "Fairy Booster",  # "fairy bo"
        "character": "root2", "vnum": 1296, "inv_tab": None,
        "search_packet": "c_blist 0 0 0 0 0 0 0 0 3 1296 5194 9074",
        "amount": 5, "nos_cost": 5,
        "unk1": 9, "unk2": 4, "durability": 1, "medal": 2, "min_price": 9999999999,
    },
    {
        "name": "Pet Food",  # "met pet food"
        "character": "root2", "vnum": 2158, "inv_tab": None,
        "search_packet": "c_blist 0 0 0 0 0 0 0 0 2 2158 10024",
        "amount": 5, "nos_cost": 2,
        "unk1": 9, "unk2": 4, "durability": 1, "medal": 2, "min_price": 9999999999,
    },
    {
        "name": "Tarot Card G",  # "tarot card g"
        "character": "root2", "vnum": 1904, "inv_tab": None,
        "search_packet": "c_blist 0 0 0 0 0 0 0 0 1 1904",
        "amount": 5, "nos_cost": 10,
        "unk1": 9, "unk2": 4, "durability": 1, "medal": 2, "min_price": 9999999999,
    },
    {
        "name": "Equipment Protection",  # "ment protec"
        "character": "root2", "vnum": 1218, "inv_tab": None,
        "search_packet": "c_blist 0 0 0 0 0 0 0 0 4 1218 5369 9458 9459",
        "amount": 5, "nos_cost": 20,
        "unk1": 9, "unk2": 4, "durability": 1, "medal": 2, "min_price": 9999999999,
    },
    {
        "name": "Blessing Amulet",  # "sing amulet"
        "character": "root2", "vnum": 282, "inv_tab": None,
        "search_packet": "c_blist 0 0 0 0 0 0 0 0 8 282 498 4262 4264 5735 8541 8543 8544",
        "amount": 5, "nos_cost": 50,
        "unk1": 9, "unk2": 4, "durability": 1, "medal": 2, "min_price": 9999999999,
    },
    {
        "name": "Higher SP Protection",  # "higher SP Pro"
        "character": "root2", "vnum": 1364, "inv_tab": None,
        "search_packet": "c_blist 0 0 0 0 0 0 0 0 4 1364 9464 9498 9925",
        "amount": 5, "nos_cost": 5,
        "unk1": 9, "unk2": 4, "durability": 1, "medal": 2, "min_price": 9999999999,
    },
    {
        "name": "Lower SP Protection",  # "wer SP Pro"
        "character": "root2", "vnum": 1363, "inv_tab": None,
        "search_packet": "c_blist 0 0 0 0 0 0 0 0 4 1363 9463 9497 9924",
        "amount": 5, "nos_cost": 5,
        "unk1": 9, "unk2": 4, "durability": 1, "medal": 2, "min_price": 9999999999,
    },
    {
        "name": "Speaker",  # "speak"
        "character": "root2", "vnum": 2173, "inv_tab": None,
        "search_packet": "c_blist 0 0 0 0 0 0 0 0 2 2173 10028",
        "amount": 5, "nos_cost": 0.5,
        "unk1": 9, "unk2": 4, "durability": 1, "medal": 2, "min_price": 9999999999,
    },
    {
        "name": "Perfume",  # "perfum"
        "character": "root2", "vnum": 1156, "inv_tab": None,
        "search_packet": "c_blist 0 0 0 0 0 0 0 0 2 1156 1428",
        "amount": 5, "nos_cost": 0.8,
        "unk1": 9, "unk2": 4, "durability": 1, "medal": 2, "min_price": 9999999999,
    },
]


def monitor_items(apis, items, refresh=30):
    """Continuously poll NosBazar prices and print a sorted profitability table.

    For each item with a configured nos_cost, computes gold-per-ND
    (cheapest NB listing price / NosMall ND cost) and sorts descending so
    the most profitable items to buy from NosMall and resell sit on top.
    """
    while True:
        results = {}  # name -> (item, price, seller)
        # Subscribe once per character for the whole pass to avoid subscribe/
        # unsubscribe races that drop in-flight rc_blist responses.
        active_chars = {it["character"] for it in items}
        for ch in active_chars:
            apis[ch].packet_manager.subscribe()
        try:
            def query(item):
                if not item.get("search_packet"):
                    return None, None  # not configured yet — skip silently
                api = apis[item["character"]]
                try:
                    return fetch_cheapest_listing(api, item, verbose=False)
                except Exception as e:
                    print(f"Error fetching {item['name']}: {e}")
                    return None, None

            # First pass — pace at 2.5s between items to stay under the
            # game's c_blist rate limit (the relist loop uses 2s; we use a bit
            # more since we query everything every refresh).
            for item in items:
                price, seller = query(item)
                results[item["name"]] = (item, price, seller)
                time.sleep(2.5)

            # Retry pass — transient drops are common, so re-query anything
            # that came back empty before giving up for this refresh.
            failed = [it for it in items if results[it["name"]][1] is None and it.get("search_packet")]
            if failed:
                print(f"\nRetrying {len(failed)} failed item(s)...")
                time.sleep(2)
                for item in failed:
                    price, seller = query(item)
                    if price is not None:
                        results[item["name"]] = (item, price, seller)
                    time.sleep(2.5)
        finally:
            for ch in active_chars:
                try:
                    apis[ch].packet_manager.unsubscribe()
                except Exception:
                    pass

        results_list = [results[it["name"]] for it in items]

        def sort_key(row):
            it, pr, _ = row
            cost = it.get("nos_cost")
            if pr is None or not cost:
                return -1
            return pr / cost

        results_list.sort(key=sort_key, reverse=True)

        # Build display rows first so we can size columns to actual content
        rows = []
        for it, pr, seller in results_list:
            cost = it.get("nos_cost")
            cost_s = f"{cost}" if cost else "-"
            if pr is None:
                price_s = "n/a"
                ratio_s = "n/a"
            elif not cost:
                price_s = f"{pr:,}"
                ratio_s = "-"
            else:
                price_s = f"{pr:,}"
                ratio_s = f"{int(pr / cost):,}"
            rows.append((it["name"], cost_s, price_s, ratio_s, seller or ""))

        headers = ("Item", "ND", "NB Price", "Gold/ND", "Seller")
        widths = [
            max(len(h), max((len(r[i]) for r in rows), default=0))
            for i, h in enumerate(headers)
        ]
        # Minimum widths for readability
        widths = [max(w, m) for w, m in zip(widths, (12, 4, 10, 9, 12))]

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

        print(f"\nRefreshing in {refresh}s... (Ctrl+C to stop)")
        time.sleep(refresh)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="NosTale market bot")
    parser.add_argument(
        "-monitor",
        action="store_true",
        help="Monitor NosBazar prices and show gold/ND profitability — does not relist anything",
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

        # Create persistent API connections
        apis = {}
        for char in characters:
            print(f"Connecting to {char}...")
            apis[char] = create_api_from_name(char)
            print(f"Connected to {char}!")

        if args.monitor:
            monitor_items(apis, ITEMS, refresh=args.refresh)

        while True:
            current_time = time.strftime("%H:%M:%S", time.localtime())
            print(f"\n[{current_time}] Starting market price checks...")

            for item in ITEMS:
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
