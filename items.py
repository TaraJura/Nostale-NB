"""Item configuration for the NosTale market bot.

Edit this file to add/remove items, change costs, or change the active character.
The main script (`nostale_market_bot.py`) imports `ITEMS` and `DEFAULT_CHARACTER`
from here, so no changes to the main script are needed when tweaking the list.

See CLAUDE.md / README.md for the full field reference.

Quick reference:
  name           display label only (NOT sent to NosBazar)
  vnum           item VNUM (used by find_item_slot for relisting)
  inv_tab        0=Equip, 1=Main, 2=Etc (None for monitor-only items)
  search_packet  full c_blist packet string (None = disable item)
  nos_cost       cost in NosMall ND (premium currency, fractional allowed)
  npc_cost       cost in gold from an NPC vendor (mutually exclusive with nos_cost)
  amount         pieces per relist listing
  min_price      relist floor price (won't undercut below this)
  unk1/unk2/durability/medal  c_reg packet constants

Per-item character override: any item can specify its own "character": "name"
to use a character different from DEFAULT_CHARACTER.
"""

# ---- Default character ----
# All items below use this character unless they explicitly set their own
# "character" key. Change this string to your in-game character name.
DEFAULT_CHARACTER = "root2"


ITEMS = [
    # ---- Relistable items (have inv_tab + min_price + relist fields) ----
    {
        "name": "Fairy Experience",
        "vnum": 5370,
        "inv_tab": 1,
        "search_packet": "c_blist 0 0 0 0 0 0 0 0 4 5370 9116 13593 13594",
        "amount": 5,
        "nos_cost": 2.5,
        "unk1": 9, "unk2": 4, "durability": 1, "medal": 2,
        "min_price": 200000,
    },
    {
        "name": "Lord Dra",
        "vnum": 5500,
        "inv_tab": 1,
        "search_packet": "c_blist 0 0 0 0 0 0 0 0 1 5500",
        "amount": 5,
        "nos_cost": 0,
        "unk1": 9, "unk2": 4, "durability": 1, "medal": 2,
        "min_price": 31000,
    },
    {
        "name": "stone bles",
        "vnum": 1362,
        "inv_tab": 1,
        "search_packet": "c_blist 0 0 0 0 0 0 0 0 3 1362 5195 9075",
        "amount": 5,
        "nos_cost": 1,
        "unk1": 9, "unk2": 4, "durability": 1, "medal": 2,
        "min_price": 9999999999,
    },
    {
        "name": "bubbl",
        "vnum": 2174,
        "inv_tab": 2,
        "search_packet": "c_blist 0 0 0 0 0 0 0 0 4 1261 2174 9480 10029",
        "amount": 5,
        "nos_cost": 0.5,
        "unk1": 10, "unk2": 3, "durability": 1, "medal": 2,
        "min_price": 43000,
    },
    {
        "name": "Wings of f",
        "vnum": 2160,
        "inv_tab": 2,
        "search_packet": "c_blist 0 0 0 0 0 0 0 0 2 2160 10048",
        "amount": 5,
        "nos_cost": 0.5,
        "unk1": 10, "unk2": 3, "durability": 1, "medal": 2,
        "min_price": 7000,
    },

    # ---- NosMall items from spreadsheet (monitor-only, no inv_tab) ----
    {
        "name": "en specialis",
        "vnum": 907, "inv_tab": None,
        "search_packet": "c_blist 0 0 0 0 0 0 0 0 2 907 4240",
        "amount": 5, "nos_cost": 100,
        "unk1": 9, "unk2": 4, "durability": 1, "medal": 2, "min_price": 9999999999,
    },
    {
        "name": "ancel",
        "vnum": 1286, "inv_tab": None,
        "search_packet": "c_blist 0 0 0 0 0 0 0 0 13 1286 1452 4717 5884 5885 5886 5887 5996 9041 9380 9874 13710 13731",
        "amount": 5, "nos_cost": 5,
        "unk1": 9, "unk2": 4, "durability": 1, "medal": 2, "min_price": 9999999999,
    },
    {
        "name": "ner skill ticket",
        "vnum": 5931, "inv_tab": None,
        "search_packet": "c_blist 0 0 0 0 0 0 0 0 4 5931 5932 9109 9110",
        "amount": 5, "nos_cost": 50,
        "unk1": 9, "unk2": 4, "durability": 1, "medal": 2, "min_price": 9999999999,
    },
    {
        "name": "medicine",
        "vnum": 1765, "inv_tab": None,
        "search_packet": "c_blist 0 0 0 0 0 0 0 0 5 1765 2159 2313 2390 10049",
        "amount": 5, "nos_cost": 2,
        "unk1": 9, "unk2": 4, "durability": 1, "medal": 2, "min_price": 9999999999,
    },
    {
        "name": "fairy bo",
        "vnum": 1296, "inv_tab": None,
        "search_packet": "c_blist 0 0 0 0 0 0 0 0 3 1296 5194 9074",
        "amount": 5, "nos_cost": 5,
        "unk1": 9, "unk2": 4, "durability": 1, "medal": 2, "min_price": 9999999999,
    },
    {
        "name": "met pet food",
        "vnum": 2158, "inv_tab": None,
        "search_packet": "c_blist 0 0 0 0 0 0 0 0 2 2158 10024",
        "amount": 5, "nos_cost": 2,
        "unk1": 9, "unk2": 4, "durability": 1, "medal": 2, "min_price": 9999999999,
    },
    {
        "name": "tarot card g",
        "vnum": 1904, "inv_tab": None,
        "search_packet": "c_blist 0 0 0 0 0 0 0 0 1 1904",
        "amount": 5, "nos_cost": 10,
        "unk1": 9, "unk2": 4, "durability": 1, "medal": 2, "min_price": 9999999999,
    },
    {
        "name": "ment protec",
        "vnum": 1218, "inv_tab": None,
        "search_packet": "c_blist 0 0 0 0 0 0 0 0 4 1218 5369 9458 9459",
        "amount": 5, "nos_cost": 20,
        "unk1": 9, "unk2": 4, "durability": 1, "medal": 2, "min_price": 9999999999,
    },
    {
        "name": "sing amulet",
        "vnum": 282, "inv_tab": None,
        "search_packet": "c_blist 0 0 0 0 0 0 0 0 8 282 498 4262 4264 5735 8541 8543 8544",
        "amount": 5, "nos_cost": 50,
        "unk1": 9, "unk2": 4, "durability": 1, "medal": 2, "min_price": 9999999999,
    },
    {
        "name": "higher SP Pro",
        "vnum": 1364, "inv_tab": None,
        "search_packet": "c_blist 0 0 0 0 0 0 0 0 4 1364 9464 9498 9925",
        "amount": 5, "nos_cost": 5,
        "unk1": 9, "unk2": 4, "durability": 1, "medal": 2, "min_price": 9999999999,
    },
    {
        "name": "wer SP Pro",
        "vnum": 1363, "inv_tab": None,
        "search_packet": "c_blist 0 0 0 0 0 0 0 0 4 1363 9463 9497 9924",
        "amount": 5, "nos_cost": 5,
        "unk1": 9, "unk2": 4, "durability": 1, "medal": 2, "min_price": 9999999999,
    },
    {
        "name": "speak",
        "vnum": 2173, "inv_tab": None,
        "search_packet": "c_blist 0 0 0 0 0 0 0 0 2 2173 10028",
        "amount": 5, "nos_cost": 0.5,
        "unk1": 9, "unk2": 4, "durability": 1, "medal": 2, "min_price": 9999999999,
    },
    {
        "name": "perfum",
        "vnum": 1156, "inv_tab": None,
        "search_packet": "c_blist 0 0 0 0 0 0 0 0 2 1156 1428",
        "amount": 5, "nos_cost": 0.8,
        "unk1": 9, "unk2": 4, "durability": 1, "medal": 2, "min_price": 9999999999,
    },

    # ---- NPC items (cost in gold, not ND) ----
    {
        "name": "Pet Food (NPC)",
        "vnum": 2077, "inv_tab": None,
        "search_packet": "c_blist 0 0 0 0 0 0 0 0 11 2077 2078 2158 2187 2325 2663 2671 10013 10014 10024 10030",
        "amount": 5,
        "npc_cost": 300,  # gold per piece from NPC vendor
        "unk1": 9, "unk2": 4, "durability": 1, "medal": 2, "min_price": 9999999999,
    },
]
