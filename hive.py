import sys
import os
import json
import time
import socket
import subprocess

# Copyright 2026 KapitalSP
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# http://www.apache.org/licenses/LICENSE-2.0

# ==============================================================================
# 📜 LICENSE & BLUEPRINTS (EMBEDDED ASSETS)
# ==============================================================================

# [LEGAL] All generated files will carry the KapitalSP signature.
LICENSE_HEADER = """# Copyright 2026 KapitalSP
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# http://www.apache.org/licenses/LICENSE-2.0
"""

# [BLUEPRINT: QUEEN] - Central Command Node
CODE_QUEEN = LICENSE_HEADER + r"""
import socket
import threading
import json
import os
import time
from datetime import datetime

class HiveQueen:
    def __init__(self, port=9999):
        self.port = port
        self.hq_path = "hive_hq"
        self.registry_path = os.path.join(self.hq_path, "registry", "swarm.json")
        self.log_path = os.path.join(self.hq_path, "logs")
        
        # 🏗️ SELF-INSTALLATION PROTOCOL
        self.initialize_infrastructure()

    def initialize_infrastructure(self):
        print(f" [👑] INITIALIZING INFRASTRUCTURE (KapitalSP Engine)...")
        dirs = [
            self.hq_path,
            os.path.join(self.hq_path, "registry"),
            self.log_path,
            os.path.join(self.hq_path, "plugins")
        ]
        for d in dirs:
            if not os.path.exists(d):
                os.makedirs(d)
                print(f"     [+] Created Sector: {d}")
        
        if not os.path.exists(self.registry_path):
            with open(self.registry_path, 'w') as f:
                json.dump({"drones": [], "created_at": str(datetime.now())}, f)
            print(f"     [+] Registry Initialized.")

    def log(self, message):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = f"[{timestamp}] {message}"
        print(entry)
        with open(os.path.join(self.log_path, "system.log"), "a") as f:
            f.write(entry + "\n")

    def handle_client(self, client_socket, addr):
        try:
            # Simple handshake
            client_socket.send(b"HIVE_QUEEN_V1_READY")
            data = client_socket.recv(1024).decode()
            if data:
                self.log(f"[Network] Signal received from {addr}: {data}")
        except Exception as e:
            self.log(f"[Error] Connection error: {e}")
        finally:
            client_socket.close()

    def start(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind(('0.0.0.0', self.port))
        server.listen(5)
        self.log(f"[System] QUEEN ONLINE. LISTENING ON PORT {self.port}")
        self.log(f"[System] HQ LOCATED AT: {os.path.abspath(self.hq_path)}")
        
        while True:
            client, addr = server.accept()
            threading.Thread(target=self.handle_client, args=(client, addr)).start()

if __name__ == "__main__":
    try:
        print(" [👑] HIVE QUEEN (c) 2026 KapitalSP")
        queen = HiveQueen(9999)
        queen.start()
    except KeyboardInterrupt:
        print("\n [!] SYSTEM HALTED BY USER.")
"""

# [BLUEPRINT: DRONE] - Worker Node
CODE_DRONE = LICENSE_HEADER + r"""
import socket
import time
import json
import os
import sys

class HiveDrone:
    def __init__(self):
        self.workspace = "drone_workspace"
        self.config_file = "config.json"
        
        # 🏗️ SELF-INSTALLATION PROTOCOL
        self.initialize_workspace()
        self.config = self.load_config()

    def initialize_workspace(self):
        print(f" [🐝] DEPLOYING WORKSPACE (KapitalSP Engine)...")
        dirs = [
            self.workspace,
            os.path.join(self.workspace, "temp"),
            os.path.join(self.workspace, "logs"),
            os.path.join(self.workspace, "cache")
        ]
        for d in dirs:
            if not os.path.exists(d):
                os.makedirs(d)
                print(f"     [+] Deployed Sector: {d}")

    def load_config(self):
        if not os.path.exists(self.config_file):
            print(" [❌] CRITICAL ERROR: 'config.json' MISSING.")
            print("      Please run the FABRICATOR to generate configuration.")
            sys.exit(1)
        
        with open(self.config_file, 'r') as f:
            return json.load(f)

    def connect_to_queen(self):
        host = self.config['queen_ip']
        port = self.config['queen_port']
        drone_id = self.config['drone_id']
        
        print(f" [🐝] DRONE [{drone_id}] SEEKING QUEEN AT {host}:{port}...")
        
        while True:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(5)
                s.connect((host, port))
                
                # Handshake
                banner = s.recv(1024).decode()
                if "HIVE_QUEEN" in banner:
                    print(f" [✅] CONNECTION ESTABLISHED: {banner}")
                    s.send(f"REPORTING_IN::{drone_id}".encode())
                    s.close()
                    break
            except socket.error:
                print(f" [⏳] Connection refused. Retrying in 3s...")
                time.sleep(3)
            except Exception as e:
                print(f" [⚠️] Error: {e}")
                time.sleep(3)
                
        print(" [🐝] ENTERING STANDBY MODE. AWAITING INSTRUCTIONS.")

if __name__ == "__main__":
    try:
        print(" [🐝] HIVE DRONE (c) 2026 KapitalSP")
        drone = HiveDrone()
        drone.connect_to_queen()
    except KeyboardInterrupt:
        print("\n [!] DRONE DISENGAGED.")
"""

# ==============================================================================
# 🛠️ UTILITIES
# ==============================================================================

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")

# ==============================================================================
# 🚀 DEPLOYMENT LOGIC
# ==============================================================================

def deploy_queen():
    print("\n" + "═"*60)
    print(" 👑 INITIATING QUEEN PROTOCOL (MASTER NODE)")
    print("═"*60)
    
    target_file = "queen.py"
    
    if os.path.exists(target_file):
        print(f" [!] WARNING: '{target_file}' already exists.")
        if input("     Overwrite? (y/n): ").lower() != 'y':
            print(" [🚫] Aborted.")
            return

    with open(target_file, "w", encoding="utf-8") as f:
        f.write(CODE_QUEEN)
        
    print(f" [✅] FILE GENERATED: {target_file}")
    print(f" [ℹ️] INSTRUCTION: Run 'python queen.py' to initialize HQ.")

def deploy_drone():
    print("\n" + "═"*60)
    print(" 🐝 INITIATING DRONE PROTOCOL (WORKER NODE)")
    print("═"*60)
    
    target_file = "drone.py"
    config_file = "config.json"
    
    # 1. Generate Code
    with open(target_file, "w", encoding="utf-8") as f:
        f.write(CODE_DRONE)
    print(f" [✅] FILE GENERATED: {target_file}")

    # 2. Configuration Wizard
    print("\n [📡] NETWORK CONFIGURATION WIZARD")
    local_ip = get_local_ip()
    print(f"      Current Host IP: {local_ip}")
    
    queen_ip = input(f"      Enter QUEEN IP Address (Default {local_ip}): ").strip()
    if not queen_ip: queen_ip = local_ip
    
    drone_id = f"DRONE_{socket.gethostname()}_{int(time.time())}"
    
    config_data = {
        "queen_ip": queen_ip,
        "queen_port": 9999,
        "drone_id": drone_id,
        "vendor": "KapitalSP",
        "deployment_date": str(time.strftime("%Y-%m-%d"))
    }
    
    with open(config_file, "w", encoding="utf-8") as f:
        json.dump(config_data, f, indent=4)
        
    print(f" [✅] CONFIGURATION SAVED: {config_file}")
    print(f"      -> Target Queen: {queen_ip}:9999")
    print(f" [ℹ️] INSTRUCTION: Run 'python drone.py' to engage.")

# ==============================================================================
# 🏁 MAIN INTERFACE
# ==============================================================================

def main():
    clear_screen()
    print("\n" + "═"*60)
    print(" 🏭 HIVE FABRICATOR v2.2 // KAPITAL SP EDITION")
    print(" 🛡️  LICENSED UNDER APACHE 2.0")
    print("═"*60)
    print(" [SYSTEM STATUS] READY")
    print(" [VENDOR]        KapitalSP")
    print(" [LOCAL IP]      " + get_local_ip())
    print("\n SELECT DEPLOYMENT VECTOR:")
    print("  [1] QUEEN CLASS (Command & Control Node)")
    print("  [2] DRONE CLASS (Distributed Worker Node)")
    print("  [0] TERMINATE SESSION")
    
    choice = input("\n > AWAITING INPUT: ").strip()
    
    if choice == '1':
        deploy_queen()
    elif choice == '2':
        deploy_drone()
    elif choice == '0':
        print("\n [👋] SYSTEM SHUTDOWN.")
        sys.exit()
    else:
        print("\n [❌] INVALID INPUT.")
        time.sleep(1)
        main()

if __name__ == "__main__":
    main()
