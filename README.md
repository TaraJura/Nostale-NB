NB Monitor:

<img width="801" height="490" alt="image" src="https://github.com/user-attachments/assets/8f4da6e7-8b16-44f0-89e3-a6ebe1eeb73d" />


 
 # NosTale Market Bot

This bot automatically monitors NosTale's NosBazar market prices and updates your listings to keep them competitive.

## Features

- Automatically monitors market prices for your items
- Undercuts competitors by 1 gold
- Sets minimum price thresholds to protect your profits
- Works with multiple items simultaneously
- Calculates taxes correctly for all price ranges

## Setup Guide

### Prerequisites

1. **Install Python**:
   - Download Python from [python.org](https://www.python.org/downloads/)
   - During installation, make sure to check "Add Python to PATH"
   - Click "Install Now" and wait for the installation to complete

2. **Install PyWin32**:
   - Open Command Prompt (search for "cmd" in Windows search)
   - Type the following command and press Enter:
     ```
     pip install pywin32
     ```

3. **Download PhoenixAPI**:
   - Download from [github.com/hatz2/PhoenixAPI](https://github.com/hatz2/PhoenixAPI)
   - Save and extract the files to a folder (e.g., `C:\NosTale\PhoenixAPI`)

### Setup Instructions

1. **Prepare the Bot**:
   - Copy the `nostale_market_bot.py` file to `C:\NosTale\PhoenixAPI\python`
   
2. **Configure the Bot**:
   - Open `nostale_market_bot.py` in a text editor (like Notepad)
   - Find the `ITEMS` section and edit it to match your items (explained below)
   - Save the file

## Configuration Guide

The bot is configured through the `ITEMS` list in the script. Here's what each setting means:

```python
ITEMS = [
    {
        "name": "Fairy",           # Display name for the item
        "character": "war1",       # Your character name
        "search_packet": "c_blist 0 0 0 0 0 0 0 0 2 5370 9116",  # Search packet
        "register_template": "c_reg 0 1 0 9 4 1 0 5 {price} {tax} 2",  # Register packet
        "min_price": 200000        # Minimum price (won't go below this)
    },
    # Add more items here
]
```

### How to Configure Your Items

1. **Character Name**:
   - Change `"character": "war1"` to your character's name

2. **Item Configuration**:
   - For each item you want to monitor and sell, you need:
     - `name`: A name to identify the item in logs
     - `search_packet`: The packet to search for the item in NosBazar
     - `register_template`: The packet to register your item
     - `min_price`: Minimum price threshold (won't sell below this)

3. **Finding the Correct Packets**:
   - You can find the correct packets by manually putting an item in NosBazar and 
     watching what packets are sent in the logs
   - **DO NOT CHANGE THE FORMAT** of packets - only change the item IDs and values

### Example Item Configuration

Here's an example for selling Gold Stones with a minimum price of 200,000:

```python
{
    "name": "Gold Stone",
    "character": "YourCharName",
    "search_packet": "c_blist 0 0 0 0 0 0 0 0 2 5370 9116",
    "register_template": "c_reg 0 1 0 9 4 1 0 5 {price} {tax} 2",
    "min_price": 200000
}
```

## Running the Bot

1. **Start Phoenix Bot**:
   - Launch NosTale and the Phoenix Bot
   - Log in with your character

2. **Run the Market Bot**:
   - Open Command Prompt (search for "cmd" in Windows search)
   - Navigate to the bot directory by typing:
     ```
     cd C:\NosTale\PhoenixAPI\python
     ```
   - Run the bot with:
     ```
     py nostale_market_bot.py
     ```

3. **Using the Bot**:
   - The bot will check prices every 30 seconds
   - It automatically updates your prices to be 1 gold cheaper than competitors
   - It will never go below your minimum price threshold
   - To stop the bot, press Ctrl+C in the Command Prompt window

## Troubleshooting

- **Bot can't connect**: Make sure Phoenix Bot is running and you're logged in
- **Wrong items being updated**: Double-check your packet configurations
- **Errors when running**: Make sure you have Python and PyWin32 installed correctly

## Safety Notes

- The bot only updates prices for items you specifically configure
- It will never sell below the minimum price you set
- Always monitor the bot initially to ensure it's working correctly

## Additional Help

If you need more help, please check the PhoenixAPI documentation or seek help in NosTale forums or Discord groups.
