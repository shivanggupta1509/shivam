# -*- coding: utf-8 -*-
import asyncio
import random
import re
from telethon.sync import TelegramClient, events

api_id = '25633812'
api_hash = '14f0e5b97bc539c21d2ae05a6d72fffd'
phone_number = '+917039128567'
file_path = 'data.txt'
group_usernames = ['alterchkbot']
approved_messages = {}
client = TelegramClient('session_name', api_id, api_hash)
cmd_file = 'cmds.txt'

# Flags to control sending
send_cards_flag = True

def read_commands():
        with open(cmd_file, 'r') as file:
            lines = file.readlines()
            for line in lines:
                cmd_val = lines[0].split('=')[1].strip()
        return cmd_val

# Function to update the command in the text file
async def update_cmd(cmd_val):
    data = f"cmd = {cmd_val}"
    with open(cmd_file, 'w') as file:
        file.write(data)

# ... (other functions and event handlers)

@client.on(events.NewMessage(pattern=r'/cmk'))
async def handle_cmd_update(event):
    try:
        message = event.message.text
        parts = message.split()
        if len(parts) == 2 and parts[0] == '/cmk':
            new_cmd = parts[1]
            await update_cmd(new_cmd)
            await event.respond('Command updated successfully!')
        else:
            await event.respond('Invalid command format. Use "/cmk {new_command}"')
    except ValueError:
        await event.respond('Invalid command format. Use "/cmk {new_command}"')


# Function to read data from the text file
def read_data():
    with open(file_path, 'r') as file:
        data = file.readlines()
        # Extracting BIN, expiry month, and expiry year from the file
        bin_val = data[0].split('=')[1].strip()
        exp_m_val = data[1].split('=')[1].strip()
        exp_y_val = data[2].split('=')[1].strip()
    return bin_val, exp_m_val, exp_y_val

# Function to update data in the text file
async def update_data(bin_val, exp_m_val, exp_y_val):
    data = f"bin = {bin_val}\nexpm = {exp_m_val}\nexpy = {exp_y_val}"
    with open(file_path, 'w') as file:
        file.write(data)
async def update_cmd(cmd_val):
    data = f"cmd = {cmd_val}"
    with open(cmd_file, 'w') as file:
        file.write(data)
# Function to generate a card with provided BIN, expiry month, and expiry year, and random CVV
# Adjust the gen_card function to accept cmd as an argument:
def gen_card(cmd, bin_val, exp_m_val, exp_y_val):
    cvv = str(random.randint(0, 999)).zfill(3)
    card_number = bin_val
    for _ in range(15 - len(bin_val)):
        digit = random.randint(0, 9)
        card_number += str(digit)
    digits = [int(x) for x in card_number]
    for i in range(0, 16, 2):
        digits[i] *= 2
        if digits[i] > 9:
            digits[i] -= 9
    total = sum(digits)
    check_digit = (10 - (total % 10)) % 10
    card_number += str(check_digit)

    return f".{cmd} {card_number}|{exp_m_val}|{exp_y_val}|{cvv}"

async def send_message(client, group_username, card_info):
    await client.send_message(group_username, card_info)

async def send_cards():
    global send_cards_flag
    while True:
        if send_cards_flag:
            bin_val, exp_m_val, exp_y_val = read_data()
            cmd = read_commands()  # Retrieve the cmd value
            card_info = gen_card(cmd, bin_val, exp_m_val, exp_y_val)  # Pass cmd to gen_card
            for group_username in group_usernames:
                await send_message(client, group_username, card_info)
        await asyncio.sleep(37)
@client.on(events.NewMessage(pattern=r'/u'))
async def handle_update(event):
    try:
        message = event.message.text
        if '|' in message:
            pattern = re.compile(r'/u (\d{16})\|(\d{2})\|(\d{4})')
            match = pattern.match(message)
            if match:
                cc_number, exp_m_val, exp_y_val = match.groups()
                bin_val = cc_number[:12]  # Extract first 12 digits as BIN
                await update_data(bin_val, exp_m_val, exp_y_val)
                await event.respond('Data updated successfully!')

            else:
                await event.respond('Invalid command format. Use "/u {cc}|{expm}|{expy}|{cvv}"')
        else:
            parts = message.split()
            if len(parts) >= 4 and parts[0] == '/u':
                bin_val, exp_m_val, exp_y_val = parts[1], parts[2], parts[3]
                cvv_val = ""  # Assuming CVV is not provided in the old format
                await update_data(bin_val, exp_m_val, exp_y_val)
                await event.respond('Data updated successfully!')
            else:
                await event.respond('Invalid command format. Use "/update {cc}|{expm}|{expy}|{cvv}"')
    except ValueError:
        await event.respond('Invalid command format. Use "/update {cc}|{expm}|{expy}|{cvv}"')


@client.on(events.NewMessage(pattern=r'/start(\s+\d+)?'))
async def handle_start(event):
    global send_cards_flag

    # Extract the argument after /start (if any)
    argument = event.pattern_match.group(1)

    # If no argument is provided, or if it's just /start without a number
    if argument is None:
        send_cards_flag = True  # Continue sending CC details indefinitely

    else:
        # Extract the number from the argument
        try:
            repeat_count = int(argument.strip())
            # Set send_cards_flag to True for the specified number of times
            for _ in range(repeat_count):
                bin_val, exp_m_val, exp_y_val = read_data()
                card_info = gen_card(bin_val, exp_m_val, exp_y_val)
                for group_username in group_usernames:
                    await send_message(client, group_username, card_info)
                await asyncio.sleep(45)
            send_cards_flag = False  # Stop sending after the specified count
        except ValueError:
            await event.respond('Invalid argument format. Use "/start" or "/start <number>"')

    await event.respond('Sending cc!')


@client.on(events.NewMessage(pattern=r'/stop'))
async def handle_stop(event):
    global send_cards_flag
    send_cards_flag = False
    await event.respond('Stopped!')

approved_messages = set()  # Initialize an empty set to store approved messages

@client.on(events.MessageEdited(incoming=True))
async def forward_approved_messages(event):
    sender = await event.get_sender()

    if sender.username == 'alterchkbot' and event.is_private:
        if 'APPROVED' in event.message.text:
            if event.id not in approved_messages:  # Check if the message has not been forwarded before
                print("Message contains 'approved'. Forwarding...")
                target_username = 'Bruto1onlyfans'
                target_entity = await client.get_entity(target_username)
                await client.forward_messages(target_entity, event.message)
                approved_messages.add(event.id)  # Add the message ID to the set to mark it as forwarded
            else:
                print("Message already forwarded. Not forwarding again.")
        else:
            print("Message does not contain 'APPROVED'. Not forwarding.")


# Start the client and tasks
client.start()
client.loop.create_task(send_cards())
client.run_until_disconnected()
