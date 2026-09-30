import os
from flask import Flask, render_template, request, jsonify
import sqlite3

app = Flask(__name__)
DB_PATH = 'dong_database.db'

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS transactions 
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                      description TEXT, 
                      amount REAL, 
                      buyer TEXT, 
                      dong_mahdi REAL, 
                      dong_mehrdad REAL, 
                      dong_mohammad REAL, 
                      dong_ali REAL)''')
        conn.commit()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/transactions', methods=['GET', 'POST'])
def handle_transactions():
    if request.method == 'POST':
        data = request.json
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute('''INSERT INTO transactions 
                         (description, amount, buyer, dong_mahdi, dong_mehrdad, dong_mohammad, dong_ali) 
                         VALUES (?, ?, ?, ?, ?, ?, ?)''', 
                         (data['description'], data['amount'], data['buyer'], 
                          data['dong_mahdi'], data['dong_mehrdad'], data['dong_mohammad'], data['dong_ali']))
            conn.commit()
        return jsonify({"status": "success"})
    
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute('SELECT * FROM transactions ORDER BY id DESC').fetchall()
        return jsonify([dict(row) for row in rows])

@app.route('/api/delete/<int:tid>', methods=['POST'])
def delete_transaction(tid):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute('DELETE FROM transactions WHERE id = ?', (tid,))
        conn.commit()
    return jsonify({"status": "deleted"})

@app.route('/api/summary')
def get_summary():
    names = ['مهدی', 'مهرداد', 'محمد', 'علی']
    paid = {n: 0.0 for n in names}
    consumed = {n: 0.0 for n in names}
    
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute('SELECT * FROM transactions').fetchall()
        for row in rows:
            if row['buyer'] in paid:
                paid[row['buyer']] += row['amount']
            consumed['مهدی'] += row['dong_mahdi']
            consumed['مهرداد'] += row['dong_mehrdad']
            consumed['محمد'] += row['dong_mohammad']
            consumed['علی'] += row['dong_ali']
            
    net = {n: paid[n] - consumed[n] for n in names}
    
    creditors = sorted([(k, v) for k, v in net.items() if v > 0.1], key=lambda x: x[1], reverse=True)
    debtors = sorted([(k, -v) for k, v in net.items() if v < -0.1], key=lambda x: x[1], reverse=True)
    
    settlements = []
    temp_debtors = [list(d) for d in debtors]
    temp_creditors = [list(c) for c in creditors]
    
    i, j = 0, 0
    while i < len(temp_debtors) and j < len(temp_creditors):
        deb_name, deb_amt = temp_debtors[i]
        crd_name, crd_amt = temp_creditors[j]
        amt = min(deb_amt, crd_amt)
        if amt > 0.1:
            settlements.append({"from": deb_name, "to": crd_name, "amount": int(round(amt))})
        temp_debtors[i][1] -= amt
        temp_creditors[j][1] -= amt
        if temp_debtors[i][1] <= 0.1: i += 1
        if temp_creditors[j][1] <= 0.1: j += 1
            
    return jsonify({
        "balances": [{"name": n, "paid": paid[n], "consumed": consumed[n], "net": net[n]} for n in names],
        "settlements": settlements
    })

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)
