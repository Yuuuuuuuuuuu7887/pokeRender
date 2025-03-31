from flask import Flask, render_template, request
import re
import os

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def process_pbn(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()

    boards = []
    card_positions = []
    all_card_tracking = {}  # ✅ รวมตำแหน่งไพ่จากทุกบอร์ด

    dealer_order = {
        'N': ['N', 'E', 'S', 'W'],
        'E': ['E', 'S', 'W', 'N'],
        'S': ['S', 'W', 'N', 'E'],
        'W': ['W', 'N', 'E', 'S']
    }

    board_matches = re.findall(r'\[Board "(\d+)"\](.*?)\[OptimumResultTable', content, re.DOTALL)

    for match in board_matches:
        board_number = int(match[0])
        board_data = match[1]

        dealer_match = re.search(r'\[Dealer "(.*?)"\]', board_data)
        deal_match = re.search(r'\[Deal "(.*?)"\]', board_data)

        if not dealer_match or not deal_match:
            continue

        dealer = dealer_match.group(1)
        deal = deal_match.group(1)

        order = dealer_order[dealer]
        
        # ✅ ลบ "N:" "E:" "S:" "W:" ออกจาก Deal
        raw_deal = re.sub(r'[NESW]:', '', deal).split()
        ordered_deal = {order[i]: raw_deal[i] for i in range(4)}

        suits = {'C': 'Clubs', 'D': 'Diamonds', 'H': 'Hearts', 'S': 'Spades'}
        parsed_hands = {d: {s: [] for s in suits} for d in order}

        for direction in order:
            hand = ordered_deal[direction]
            suit_cards = hand.split('.')
            for suit, cards in zip(suits.keys(), suit_cards):
                parsed_hands[direction][suit] = list(cards.strip())  # ✅ ลบช่องว่าง
                for rank in cards.strip():
                    card_key = f"{suit}{rank}"  # เช่น "C1", "D10"
                    if card_key not in all_card_tracking:
                        all_card_tracking[card_key] = ""  # ✅ ถ้ายังไม่มี ให้สร้าง
                    all_card_tracking[card_key] += direction  # ✅ ต่อข้อมูลทิศทางเข้าไป

        boards.append({
            'board_number': board_number,
            'dealer': dealer,
            'hands': parsed_hands
        })

    return boards, all_card_tracking

@app.route('/', methods=['GET', 'POST'])
def index():
    boards = None
    all_card_tracking = None

    if request.method == 'POST':
        if 'file' not in request.files:
            return 'No file part'
        file = request.files['file']
        if file.filename == '':
            return 'No selected file'
        
        if file and file.filename.endswith('.pbn'):
            filename = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(filename)
            
            boards, all_card_tracking = process_pbn(filename)
            return render_template('index.html', boards=boards, all_card_tracking=all_card_tracking)

    return render_template('index.html', boards=None, all_card_tracking=None)

if __name__ == '__main__':
    app.run(debug=True)
