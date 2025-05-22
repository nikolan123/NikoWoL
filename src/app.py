from flask import Flask, render_template, jsonify, request
from werkzeug.exceptions import HTTPException
import json
import re
import aioping
from waitress import serve
from wol import wake_on_lan
import sqlite3
import socket
import os
import sys

data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data')
os.makedirs(data_dir, exist_ok=True)
config_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'config')
os.makedirs(config_dir, exist_ok=True)

static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'static')
templates_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'templates')
CONFIG_PATH = os.path.join(config_dir, 'config.json')
DB_PATH = os.path.join(data_dir, 'devices.db')
app = Flask(__name__, template_folder=templates_dir, static_folder=static_dir)

async def is_pc_up(ip):
    """Perform an asynchronous ping with aioping."""
    try:
        await aioping.ping(ip, timeout=0.5)
        return True
    except TimeoutError:
        return False

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS devices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            ip TEXT NOT NULL,
            mac TEXT NOT NULL,
            "order" INTEGER NOT NULL DEFAULT 0
        )
    ''')
    # Ensure all rows have an order value
    cursor.execute('SELECT id FROM devices WHERE "order" IS NULL')
    rows = cursor.fetchall()
    if rows:
        cursor.execute('SELECT COUNT(*) FROM devices')
        count = cursor.fetchone()[0]
        cursor.execute('UPDATE devices SET "order" = id WHERE "order" IS NULL')
    conn.commit()
    conn.close()

def fetch_devices():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM devices ORDER BY "order" ASC, id ASC')
    rows = cursor.fetchall()
    conn.close()
    return [{"id": row[0], "name": row[1], "ip": row[2], "mac": row[3].split(':'), "order": row[4]} for row in rows]

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

def valid_ipv4(device_ip):
    try:
        socket.inet_aton(device_ip)
        return True
    except (socket.error, ValueError, TypeError):
        return False
    
    
def valid_port(port):
    return isinstance(port, int) and 0 <= port <= 65535
    
def valid_mac(mac_address):
    mac_regex = r'^([0-9A-Fa-f]{2}[-:][0-9A-Fa-f]{2}[-:][0-9A-Fa-f]{2}[-:][0-9A-Fa-f]{2}[-:][0-9A-Fa-f]{2}[-:][0-9A-Fa-f]{2})$'
    return re.match(mac_regex, mac_address)

init_db()

db = fetch_devices()

@app.errorhandler(Exception)
def handle_exception(e):
    if isinstance(e, HTTPException):
        # http errors for flask to handle
        return e

    # handle rest
    response = {
        "error": str(e),
        "type": e.__class__.__name__
    }
    return jsonify(response), 500


@app.route('/')
async def home():
    return render_template("index.html", pcs=db)

@app.route('/edit')
async def edit():
    return render_template("edit.html", pcs=db)

@app.route('/add')
async def add_pc():
    return render_template("add.html")

@app.route('/send_packet', methods=['POST'])
async def send_packet():
    data = request.get_json()
    device_id = data.get("id")

    device = next((item for item in db if item["id"] == device_id), None)

    if device:
        wake_on_lan(device['mac'])
        return jsonify({"message": "Packet sent", "mac": device["mac"]})
    else:
        return jsonify({"error": "Device not found"}), 404
    
@app.route('/check_status')
async def check_status():
    device_id = request.args.get('id')
    if not device_id:
        return jsonify({'error': 'ID is required'}), 400
    try:
        device_id = int(device_id)
    except:
        return jsonify({'error': 'ID must be an integer'}), 400
    
    device = next((item for item in db if item["id"] == device_id), None)

    if device:
        device_ip = device['ip']
        device_status = await is_pc_up(device_ip)
        return jsonify({"status": "up" if device_status is True else "down"})
    else:
        return jsonify({"error": "Device not found"}), 404
    
@app.route('/add_device', methods=['POST'])
async def add_device():
    data = request.get_json()
    pretty_name = data.get("prettyName")
    device_ip = data.get("deviceIP")
    mac_address = data.get("macAddress")

    if not all([pretty_name, device_ip, mac_address]):
        return jsonify({"error": "Missing required fields"}), 400
    
    if not valid_ipv4(device_ip):
        return jsonify({"error": "IP must be a valid IPv4 address."}), 400
    
    if not valid_mac(mac_address):
        return jsonify({"error": "Invalid MAC Address (FF:FF:FF:FF:FF:FF or FF-FF-FF-FF-FF-FF)"}), 400
    
    cleaned_mac = re.sub(r'[-:.]', '', mac_address).upper()
    mac_array = [cleaned_mac[i:i+2] for i in range(0, len(cleaned_mac), 2)]

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # get max order value
    cursor.execute('SELECT MAX("order") FROM devices')
    max_order = cursor.fetchone()[0]
    next_order = (max_order + 1) if max_order is not None else 0
    cursor.execute('''
        INSERT INTO devices (name, ip, mac, "order") VALUES (?, ?, ?, ?)
    ''', (pretty_name, device_ip, ':'.join(mac_array), next_order))
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    db.append({"id": new_id, "name": pretty_name, "ip": device_ip, "mac": mac_array, "order": next_order})
    return jsonify({"success": "true", "id": new_id})

@app.route('/edit/<device_id>', methods=['GET', 'POST'])
def edit_device(device_id):
    if not device_id:
        return jsonify({"error": "ID is required"}), 400
    
    try:
        device_id = int(device_id)
    except:
        return jsonify({"error": "ID must be an integer"}), 400
    
    device = next((item for item in db if item["id"] == device_id), None)

    if not device:
        return jsonify({"error": "ID not found"})
    
    if request.method == "GET":
        pretty_name = device['name']
        device_ip = device['ip']
        mac_address = ":".join(device['mac'])
        return render_template("edit_device.html", pretty_name=pretty_name, device_ip=device_ip, mac_address=mac_address, pcid=device_id)
    else:
        data = request.get_json()
        pretty_name = data.get("prettyName")
        device_ip = data.get("deviceIP")
        mac_address = data.get("macAddress")

        if not all([pretty_name, device_ip, mac_address]):
            return jsonify({"error": "Missing required fields"}), 400
        
        if not valid_ipv4(device_ip):
            return jsonify({"error": "IP must be a valid IPv4 address."}), 400
        
        if not valid_mac(mac_address):
            return jsonify({"error": "Invalid MAC Address (FF:FF:FF:FF:FF:FF or FF-FF-FF-FF-FF-FF)"}), 400
        
        cleaned_mac = re.sub(r'[-:.]', '', mac_address).upper()
        mac_array = [cleaned_mac[i:i+2] for i in range(0, len(cleaned_mac), 2)]

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE devices SET name = ?, ip = ?, mac = ? WHERE id = ?
        ''', (pretty_name, device_ip, ':'.join(mac_array), device_id))
        conn.commit()
        conn.close()
        idx = db.index(device)
        db[idx] = {"id": device_id, "name": pretty_name, "ip": device_ip, "mac": mac_array, "order": device["order"]}
        return jsonify({"success": "true", "id": device_id})

@app.route('/delete_device', methods=['POST'])
def delete_device():
    data = request.get_json()
    device_id = data.get("id")

    if not device_id:
        return jsonify({"error": "ID is required"}), 400
    
    try:
        device_id = int(device_id)
    except:
        return jsonify({"error": "ID must be an integer"}), 400

    device = next((item for item in db if item["id"] == device_id), None)

    if device:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM devices WHERE id = ?', (device_id,))
        conn.commit()
        conn.close()
        db.remove(device)
        # reorder after deletion so its sequential
        reorder_devices()
        return jsonify({"success": "true"})
    else:
        return jsonify({"error": "Device not found"}), 404

def reorder_devices():
    """Ensure device order is sequential after deletion."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM devices ORDER BY "order" ASC, id ASC')
    rows = cursor.fetchall()
    for idx, (device_id,) in enumerate(rows):
        cursor.execute('UPDATE devices SET "order" = ? WHERE id = ?', (idx, device_id))
    conn.commit()
    conn.close()
    global db
    db = fetch_devices()

@app.route('/move_device', methods=['POST'])
def move_device():
    data = request.get_json()
    device_id = data.get("id")
    direction = data.get("direction")

    if not device_id:
        return jsonify({"error": "ID is required"}), 400

    if direction not in ["up", "down"]:
        return jsonify({"error": "Direction must be 'up' or 'down'"}), 400

    try:
        device_id = int(device_id)
    except ValueError:
        return jsonify({"error": "ID must be an integer"}), 400

    device = next((item for item in db if item["id"] == device_id), None)

    if not device:
        return jsonify({"error": "Device not found"}), 404

    index = db.index(device)

    if direction == "up":
        if index == 0:
            return jsonify({"error": "Device is already at the top"}), 400
        other_device = db[index - 1]
    else:  # direction == "down"
        if index == len(db) - 1:
            return jsonify({"error": "Device is already at the bottom"}), 400
        other_device = db[index + 1]

    # swap the order values in the database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('UPDATE devices SET "order" = ? WHERE id = ?', (other_device["order"], device["id"]))
    cursor.execute('UPDATE devices SET "order" = ? WHERE id = ?', (device["order"], other_device["id"]))
    conn.commit()
    conn.close()

    # update cache
    db[index], db[index - 1 if direction == "up" else index + 1] = db[index - 1 if direction == "up" else index + 1], db[index]
    db[index]["order"], db[index - 1 if direction == "up" else index + 1]["order"] = db[index - 1 if direction == "up" else index + 1]["order"], db[index]["order"]

    return jsonify({"success": "true"})


if __name__ == '__main__':
    # check if file exists and load
    if not os.path.exists(CONFIG_PATH):
        sys.exit(f"🛑 Error: Config file '{CONFIG_PATH}' is missing.")

    try:
        with open(CONFIG_PATH, "r") as f:
            config = json.load(f)
    except json.JSONDecodeError as e:
        sys.exit(f"🛑 Error: Failed to parse '{CONFIG_PATH}': {e}")

    # check keys
    if 'host' not in config:
        sys.exit(f"🛑 Error: '{CONFIG_PATH}' is missing the required 'host' field.")
    if 'port' not in config:
        sys.exit(f"🛑 Error: '{CONFIG_PATH}' is missing the required 'port' field.")

    if not valid_ipv4(config['host']):
        sys.exit(f"🛑 Error: Invalid 'host' in '{CONFIG_PATH}'. Must be a valid IPv4 address.")
    if not valid_port(config['port']):
        sys.exit(f"🛑 Error: Invalid 'port' in '{CONFIG_PATH}'. Must be an integer between 1 and 65535.")

    # run
    print(f"Running on http://{get_local_ip()}:{config['port']}/")
    serve(app, host=config['host'], port=config['port'])
