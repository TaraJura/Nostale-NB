from phoenixapi import phoenix, finder
import json
import time


def calculate_tax(price, amount=5):
    total_price = price * amount
    total_tax = total_price * 0.0005
    
    return int(total_tax)

def check_and_update_price(character_name, item_type, search_packet, register_packet_template, min_price_threshold, item_name):
    print(f"{item_name}...")
    api = finder.create_api_from_name(character_name)
    
    api.send_packet(search_packet)
    print(f"Sending search packet for {item_name}")

    # Try for up to 3 seconds to get a response
    timeout = time.time() + 3
    price_found = False
    
    while not price_found and time.time() < timeout and api.working():
        if not api.empty():
            msg = api.get_message()
            json_msg = json.loads(msg)
            
            # Check if this is a received packet
            if json_msg["type"] == phoenix.Type.packet_recv.value:
                packet = json_msg["packet"]
                
                # Check if it's the rc_blist response
                if packet.startswith("rc_blist"):
                    print(f"Received response for {item_name}")
                    
                    # Parse the price from the response
                    parts = packet.split(' ', 2)  # Split into ['rc_blist', '0', 'rest of data']
                    if len(parts) >= 3:
                        items = parts[2].split(' ')
                        if not items:
                            print(f"No items found for {item_name}")
                            break
                            
                        first_item = items[0]
                        item_details = first_item.split('|')
                        
                        # The price is the 7th element (index 6) in the item details
                        if len(item_details) > 6:
                            price = item_details[6]
                            print(f"{item_name} PRICE: {price}")

                            name = item_details[2]
                            print(f"{item_name} SELLER: {name}")

                            if name != character_name:
                                new_price = int(price) - 1
                                print(f"{item_name} CALCULATED NEW PRICE: {new_price}")
                                
                                # Check if the new price is below our threshold
                                if new_price < min_price_threshold:
                                    print(f"WARNING: Market price ({new_price}) is below minimum threshold ({min_price_threshold})")
                                    print(f"Not updating price for {item_name} to protect profits")
                                else:
                                    tax = calculate_tax(new_price)
                                    print(f"{item_name} TAX: {tax}")
                                    
                                    # Use the template to create the packet with price and tax
                                    packet_for_uploading = register_packet_template.format(
                                        price=new_price,
                                        tax=tax
                                    )
                                    
                                    print(f"Sending packet: {packet_for_uploading}")
                                    api.send_packet(packet_for_uploading)
                                    print(f"{item_name} price updated!")
                            else:
                                print(f"You are already the lowest seller for {item_name}!")

                            price_found = True
        else:
            time.sleep(0.01)
    
    if not price_found:
        print(f"No price data found for {item_name}")
    
    # Close the connection
    api.close()
    print(f"{item_name} check complete")
    return price_found

# Item configurations
ITEMS = [
    {
        "name": "Fairy",
        "character": "war1",
        "search_packet": "c_blist 0 0 0 0 0 0 0 0 2 5370 9116",
        "register_template": "c_reg 0 1 0 9 4 1 0 5 {price} {tax} 2",
        "min_price": 200000
    },
    {
        "name": "Draco",
        "character": "war1",
        "search_packet": "c_blist 0 0 0 0 0 0 0 0 1 5500",
        "register_template": "c_reg 0 1 1 9 4 1 0 5 {price} {tax} 2",
        "min_price": 20000
    },
    {
        "name": "Job Stone",
        "character": "war1",
        "search_packet": "c_blist 0 0 0 0 0 0 0 0 3 1362 5195 9075",
        "register_template": "c_reg 0 1 2 9 4 1 0 5 {price} {tax} 2",
        "min_price": 80000
    }
]

# Original functionality preserved as separate functions for compatibility
def check_and_update_price_fairy(min_price_threshold=200000):
    return check_and_update_price(
        character_name="war1",
        item_type=0,
        search_packet="c_blist 0 0 0 0 0 0 0 0 2 5370 9116",
        register_packet_template="c_reg 0 1 0 9 4 1 0 5 {price} {tax} 2",
        min_price_threshold=min_price_threshold,
        item_name="Fairy"
    )

def check_and_update_price_draco(min_price_threshold=20000):
    return check_and_update_price(
        character_name="war1",
        item_type=1,
        search_packet="c_blist 0 0 0 0 0 0 0 0 1 5500",
        register_packet_template="c_reg 0 1 1 9 4 1 0 5 {price} {tax} 2",
        min_price_threshold=min_price_threshold,
        item_name="Draco"
    )

def check_and_update_price_job_stone(min_price_threshold=80000, item_name="Job Stone"):
    return check_and_update_price(
        character_name="war1",
        item_type=2,
        search_packet="c_blist 0 0 0 0 0 0 0 0 3 1362 5195 9075",
        register_packet_template="c_reg 0 1 2 9 4 1 0 5 {price} {tax} 2",
        min_price_threshold=min_price_threshold,
        item_name=item_name
    )

if __name__ == "__main__":
    try:
        print("=== NosTale Market Bot ===")

        while True:
            current_time = time.strftime("%H:%M:%S", time.localtime())
            print(f"\n[{current_time}] Starting market price checks...")
            
            # Run each item check one by one
            for item in ITEMS:
                print(f"\n----------[ {item['name']} ]----------")
                check_and_update_price(
                    character_name=item['character'],
                    item_type=int(item['register_template'].split()[2]),  # Extract type from template
                    search_packet=item['search_packet'],
                    register_packet_template=item['register_template'],
                    min_price_threshold=item['min_price'],
                    item_name=item['name']
                )
                print(f"----------[ {item['name']} Complete ]----------")
                
                # Small delay between items
                time.sleep(2)
            
            print("\nWaiting 30 seconds before next check...")
            time.sleep(30)
            
    except KeyboardInterrupt:
        print("\nScript terminated by user.")
        print("Exiting...")
