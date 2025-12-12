import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core.scryfall import fetch_cards

# Define expected behavior
# True = Always Tapped (or highly likely to be)
# False = Can enter Untapped (Conditionals)

LAND_DATA = {
    # Guildgates (Always Tapped)
    "Azorius Guildgate": True, "Boros Guildgate": True, "Dimir Guildgate": True, 
    "Golgari Guildgate": True, "Gruul Guildgate": True, "Izzet Guildgate": True, 
    "Orzhov Guildgate": True, "Rakdos Guildgate": True, "Selesnya Guildgate": True, 
    "Simic Guildgate": True,

    # Bouncelands (Always Tapped)
    "Azorius Chancery": True, "Boros Garrison": True, "Dimir Aqueduct": True, 
    "Golgari Rot Farm": True, "Gruul Turf": True, "Izzet Boilerworks": True, 
    "Orzhov Basilica": True, "Rakdos Carnarium": True, "Selesnya Sanctuary": True, 
    "Simic Growth Chamber": True,

    # Shocklands (Pay 2 life -> Untapped)
    "Hallowed Fountain": False, "Watery Grave": False, "Blood Crypt": False, 
    "Stomping Ground": False, "Temple Garden": False, "Godless Shrine": False, 
    "Steam Vents": False, "Overgrown Tomb": False, "Sacred Foundry": False, 
    "Breeding Pool": False,

    # Checklands (Unless control Type -> Untapped)
    "Glacial Fortress": False, "Drowned Catacomb": False, "Dragonskull Summit": False, 
    "Rootbound Crag": False, "Sunpetal Grove": False, "Isolated Chapel": False, 
    "Sulfur Falls": False, "Woodland Cemetery": False, "Clifftop Retreat": False, 
    "Hinterland Harbor": False,

    # Fastlands (Unless control 2 or fewer -> Untapped)
    "Seachrome Coast": False, "Darkslick Shores": False, "Blackcleave Cliffs": False, 
    "Copperline Gorge": False, "Razorverge Thicket": False, "Concealed Courtyard": False, 
    "Spirebluff Canal": False, "Blooming Marsh": False, "Inspiring Vantage": False, 
    "Botanical Sanctum": False,

    # Temples (Always Tapped)
    "Temple of Enlightenment": True, "Temple of Deceit": True, "Temple of Malice": True, 
    "Temple of Abandon": True, "Temple of Plenty": True, "Temple of Silence": True, 
    "Temple of Epiphany": True, "Temple of Malady": True, "Temple of Triumph": True, 
    "Temple of Mystery": True,

    # Triomes (Always Tapped)
    "Indatha Triome": True, "Ketria Triome": True, "Raugrin Triome": True, 
    "Savai Triome": True, "Zagoth Triome": True, 
    
    # New Capenna Tri-Cycle Lands (Always Tapped)
    "Jetmir's Garden": True, "Raffine's Tower": True, "Spara's Headquarters": True, 
    "Xander's Lounge": True, "Ziatora's Proving Ground": True,

    # Manlands (Always Tapped)
    "Celestial Colonnade": True, "Creeping Tar Pit": True, "Lavaclaw Reaches": True, 
    "Raging Ravine": True, "Stirring Wildwood": True, "Shambling Vent": True, 
    "Wandering Fumarole": True, "Hissing Quagmire": True, "Needle Spires": True, 
    "Lumbering Falls": True,

    # Gainlands (Always Tapped)
    "Tranquil Cove": True, "Scoured Barrens": True, "Dismal Backwater": True, 
    "Bloodfell Caves": True, "Jungle Hollow": True, "Rugged Highlands": True, 
    "Blossom Sands": True, "Wind-Scarred Crag": True, "Thornwood Falls": True, 
    "Swiftwater Cliffs": True,

    # Snow Duals (Always Tapped)
    "Alpine Meadow": True, "Arctic Treeline": True, "Glacial Floodplain": True, 
    "Highland Forest": True, "Ice Tunnel": True, "Rimewood Falls": True, 
    "Snowfield Sinkhole": True, "Sulfurous Mire": True, "Volatile Fjord": True, 
    "Woodland Chasm": True,
}

async def run_test():
    print(f"🔄 Fetching {len(LAND_DATA)} lands...")
    cards = await fetch_cards(list(LAND_DATA.keys()), use_cache=True)
    card_map = {c.name: c for c in cards}

    correct_count = 0
    errors = []

    print("\n📊 Results:")
    print(f"{'Name':<30} {'Exp':<10} {'Act':<10} {'Status':<5}")
    print("-" * 60)

    for name, expected_tapped in LAND_DATA.items():
        if name not in card_map:
            print(f"⚠️  Missing: {name}")
            continue

        card = card_map[name]
        actual_tapped = "TAPPED_ENTRY" in card.tags
        
        status = "✅" if expected_tapped == actual_tapped else "❌"
        
        if expected_tapped == actual_tapped:
            correct_count += 1
        else:
            errors.append({
                "name": name,
                "oracle": card.oracle_text,
                "expected": "TAPPED" if expected_tapped else "UNTAPPED",
                "actual": "TAPPED" if actual_tapped else "UNTAPPED"
            })

        exp_str = "TAPPED" if expected_tapped else "UNTAP"
        act_str = "TAPPED" if actual_tapped else "UNTAP"
        print(f"{name:<30} {exp_str:<10} {act_str:<10} {status}")

    print("-" * 60)
    print(f"Total: {len(LAND_DATA)}")
    print(f"Correct: {correct_count}")
    print(f"Errors: {len(errors)}")

    if errors:
        print("\n🚨 DETAILED ERRORS:")
        for err in errors:
            print(f"\n❌ {err['name']}")
            print(f"   Expected: {err['expected']}")
            print(f"   Actual:   {err['actual']}")
            print(f"   Oracle:   {err['oracle']}")

if __name__ == "__main__":
    asyncio.run(run_test())
