from phoenixapi import phoenix, finder
import json
import time

def calculate_tax(price, amount=5):
    # Calculate total price
    total_price = price * amount

    total_tax = total_price * 0.0005
    
    return int(total_tax)

def check_and_update_price_fairy(min_price_threshold=200000):
    print("Fairy Check...")
    api = finder.create_api_from_name("war1")
    
    # Send the packet
    packet_content = "c_blist 0 0 0 0 0 0 0 0 2 5370 9116"
    print(f"Sending packet: {packet_content}")
    api.send_packet(packet_content)

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
                    print(f"Received response: {packet}")
                    
                    # Parse the price from the response
                    parts = packet.split(' ', 2)  # Split into ['rc_blist', '0', 'rest of data']
                    if len(parts) >= 3:
                        items = parts[2].split(' ')
                        first_item = items[0]
                        item_details = first_item.split('|')
                        
                        # The price is the 7th element (index 6) in the item details
                        if len(item_details) > 6:
                            price = item_details[6]
                            print(f"Fairy PRICE: {price}")

                            name = item_details[2]
                            print(f"Fairy SELLER: {name}")

                            if name != "war1":
                                new_price = int(price) - 1
                                print(f"Fairy CALCULATED NEW PRICE: {new_price}")
                                
                                # Check if the new price is below our threshold
                                if new_price < min_price_threshold:
                                    print(f"WARNING: Market price ({new_price}) is below minimum threshold ({min_price_threshold})")
                                    print("Not updating price to protect your profits")
                                else:
                                    tax = calculate_tax(new_price)
                                    print(f"Fairy TAX: {tax}")
                                    packet_for_uploading_item_to_nb = f"c_reg 0 1 0 9 4 1 0 5 {new_price} {tax} 2"
                                    print(f"Sending packet: {packet_for_uploading_item_to_nb}")
                                    api.send_packet(packet_for_uploading_item_to_nb)
                                    print("Price updated!")
                            else:
                                print("You are already the lowest seller!")

                            price_found = True
        else:
            time.sleep(0.01)
    
    # Close the connection
    api.close()
    print("Done!")
    return price_found

def check_and_update_price_draco(min_price_threshold=20000):
    print("Draco Check...")
    api = finder.create_api_from_name("war1")
    
    # Send the packet
    packet_content = "c_blist 0 0 0 0 0 0 0 0 1 5500"
    print(f"Sending packet: {packet_content}")
    api.send_packet(packet_content)
    
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
                    print(f"Draco Received response: {packet}")
                    
                    # Parse the price from the response
                    parts = packet.split(' ', 2)  # Split into ['rc_blist', '0', 'rest of data']
                    if len(parts) >= 3:
                        items = parts[2].split(' ')
                        first_item = items[0]
                        item_details = first_item.split('|')
                        
                        # The price is the 7th element (index 6) in the item details
                        if len(item_details) > 6:
                            price = item_details[6]
                            print(f"Draco PRICE: {price}")

                            name = item_details[2]
                            print(f"Draco SELLER: {name}")

                            if name != "war1":
                                new_price = int(price) - 1
                                print(f"Draco CALCULATED NEW PRICE: {new_price}")
                                
                                # Check if the new price is below our threshold
                                if new_price < min_price_threshold:
                                    print(f"WARNING: Market price ({new_price}) is below minimum threshold ({min_price_threshold})")
                                    print("Not updating price to protect your profits")
                                else:
                                    tax = calculate_tax(new_price)
                                    print(f"Draco TAX: {tax}")
                                    packet_for_uploading_item_to_nb = f"c_reg 0 1 1 9 4 1 0 5 {new_price} {tax} 2"
                                    print(f"Sending packet: {packet_for_uploading_item_to_nb}")
                                    api.send_packet(packet_for_uploading_item_to_nb)
                                    print("Price updated!")
                            else:
                                print("You are already the lowest seller!")

                            price_found = True
        else:
            time.sleep(0.01)
    
    # Close the connection
    api.close()
    print("Done!")
    return price_found

if __name__ == "__main__":
    try:
        while True:
            current_time = time.strftime("%H:%M:%S", time.localtime())
            print(f"\n[{current_time}] Checking current market prices...")
            
            print("\n------------------")
            print("\nStarting Fairy...")
            check_and_update_price_fairy()
            print("\n------------------")

            time.sleep(2)

            print("\n------------------")
            print("\nStarting Draco...")
            check_and_update_price_draco()
            print("\n------------------")
            
            print("\nWaiting 30 seconds before next check...")
            time.sleep(30)
            
    except KeyboardInterrupt:
        print("\nScript terminated by user.")
        print("Exiting...")

