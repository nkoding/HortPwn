# add_recipient.py

import json
import sys
import os

def add_recipient(recipient_id: str, recipient_type: str):
    if recipient_type not in ["individual", "group"]:
        print("Empfängertyp muss entweder 'individual' oder 'group' sein.")
        return

    if os.path.exists("chat_ids.json"):
        with open("chat_ids.json", "r") as f:
            chat_ids = json.load(f)
    else:
        chat_ids = []

    # Überprüfen, ob der Empfänger bereits vorhanden ist
    for chat in chat_ids:
        if chat["id"] == recipient_id:
            print("Empfänger bereits vorhanden.")
            return

    # Empfänger hinzufügen
    chat_ids.append({
        "type": recipient_type,
        "id": recipient_id
    })

    with open("chat_ids.json", "w") as f:
        json.dump(chat_ids, f, indent=4)
    print(f"Empfänger {recipient_id} als {recipient_type} hinzugefügt.")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python add_recipient.py <RECIPIENT_ID> <TYPE>")
        print("TYPE kann entweder 'individual' oder 'group' sein.")
    else:
        add_recipient(sys.argv[1], sys.argv[2])
