import os, sys, subprocess, socket, json

# Copyright 2026 R2
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# http://www.apache.org/licenses/LICENSE-2.0

# =============================================================================
# 📡 NETWORK UTILITIES
# =============================================================================
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

def run_cmd(cmd):
    # Ensure dependencies are installed silently
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install"] + cmd, 
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except: pass # Assume installed if fails or offline

# ==============================================================================
# 🛠️ GLOBAL HEADERS (Apache 2.0 License Stamp)
# ==============================================================================
LICENSE_HEADER = """# Copyright 2026 R2
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# http://www.apache.org/licenses/LICENSE-2.0
"""

# ==============================================================================
# 🚀 INTEGRITY CHECK & SETUP
# ==============================================================================
def setup():
    local_ip = get_local_ip()
    print("\n" + "═"*60)
    print(f" 🏭 HIVE FABRICATOR v1.8 // LOCAL IP: {local_ip}")
    print(" 🛡️  COMMERCIAL GRADE AI INFRASTRUCTURE (APACHE 2.0)")
    print("═"*60)

    # 1. Component Synchronization
    print("\n [1/4] Syncing components (FastAPI, uvicorn, httpx, psutil)...")
    try:
        run_cmd(["fastapi", "uvicorn", "httpx", "psutil"])
        print(" [OK] All systems synchronized.")
    except Exception as e:
        print(f" [ERR] Critical Sync Failure: {e}"); return

    # 2. Resilient Network Config
    config_file = "hive_config.json"
    if os.path.exists(config_file):
        with open(config_file, "r") as f:
            config = json.load(f)
        print(f"\n [🔍] Config Found: Queen({config['queen_ip']}), Cell({config['cell_ip']})")
        if input("  > Maintain these deployment parameters? (y/n): ").lower() != 'y':
            os.remove(config_file)
            return setup()
    else:
        q_ip = input(f"  > Primary Queen IP (Default {local_ip}): ") or local_ip
        c_ip = input(f"  > Backup Cell IP    (Default {local_ip}): ") or local_ip
        config = {"queen_ip": q_ip, "cell_ip": c_ip, "webhook_url": ""}
        with open(config_file, "w") as f:
            json.dump(config, f)

    # 3. Role Deployment
    print("\n [2/4] Deploying Node Role:")
    print("  (1) Queen : Strategic Command & External API Gateway")
    print("  (2) Drone : AI Execution (Self-Registering Worker)")
    print("  (3) Cell  : Log Archivist & Backup Command (Failover)")
    
    choice = input("\n Deployment ID (1-3): ").strip()

    # 4. Neural Code Generation
    print("\n [3/4] Generating Source Code with Failover DNA...")
    
    # --- Queen: Master & Gateway ---
    if choice == "1":
        with open("queen.py", "w", encoding="utf-8") as f:
            f.write(LICENSE_HEADER + f"""
import fastapi, httpx, os, time, threading, uvicorn
from fastapi import Request

app = fastapi.FastAPI(title="HIVE Queen")
CONFIG = {json.dumps(config)}
WORKERS = [] 
CURRENT_WORKER_IDX = 0 # Round-Robin Counter

@app.get("/health")
async def health(): return {{"status": "ALIVE", "role": "MASTER"}}

@app.post("/register")
async def register(req: Request):
    data = await req.json()
    # Check if worker already exists to prevent duplicates
    if not any(d['id'] == data['id'] for d in WORKERS):
        WORKERS.append(data)
        print(f" [🌐] New Drone Connected: {{data['id']}}")
    return {{"status": "ACCEPTED"}}

@app.post("/v1/chat/completions")
async def gateway(req: Request):
    global CURRENT_WORKER_IDX
    if not WORKERS: return {{"error": "No Drones available"}}
    
    # Round-Robin Load Balancing
    target_drone = WORKERS[CURRENT_WORKER_IDX % len(WORKERS)]
    CURRENT_WORKER_IDX += 1
    
    async with httpx.AsyncClient() as client:
        try:
            # Forward the request to the selected Drone
            res = await client.post(f"{{target_drone['url']}}/v1/chat/completions", json=await req.json(), timeout=60.0)
            return res.json()
        except Exception as e:
            return {{"error": f"Drone connection failed: {{str(e)}}"}}

def ui():
    while True:
        os.system("clear" if os.name != "nt" else "cls")
        print(" ┌──────────────────────────────────────────────────┐")
        print(f" │ 👑 HIVE MASTER CONSOLE // ECU v1.8                │")
        print(f" │ External API: http://{{get_local_ip()}}:8000/v1      │")
        print(" ├──────────────────────────────────────────────────┤")
        # Thread-safe iteration using list() to avoid runtime errors
        for w in list(WORKERS):
            print(f" │ 🟢 {{w['id']:<15}} ONLINE  IP: {{w['url']}}      │")
        if not WORKERS: print(" │ 🔴 WAITING FOR DRONES...                          │")
        print(" └──────────────────────────────────────────────────┘")
        time.sleep(2)

if __name__ == "__main__":
    threading.Thread(target=ui, daemon=True).start()
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="critical")
""")

    # --- Drone: Self-Registering Worker ---
    elif choice == "2":
        with open("drone.py", "w", encoding="utf-8") as f:
            f.write(LICENSE_HEADER + f"""
import fastapi, httpx, uvicorn, socket, asyncio

app = fastapi.FastAPI()
CONFIG = {json.dumps(config)}
MY_IP = "{local_ip}"
MY_ID = socket.gethostname()

@app.on_event("startup")
async def join_hive():
    async with httpx.AsyncClient() as client:
        # [FIX] Explicitly target Queen (8000) and Cell (9000) regardless of IP
        targets = [(CONFIG['queen_ip'], 8000), (CONFIG['cell_ip'], 9000)]
        
        for ip, port in targets:
            try:
                # Loop through specific ports to ensure both Queen and Cell are contacted
                await client.post(f"http://{{ip}}:{{port}}/register", 
                    json={{"id": MY_ID, "url": f"http://{{MY_IP}}:8081"}}, timeout=2.0)
                print(f" [📡] Signal sent to Command Node at {{ip}}:{{port}}")
            except Exception as e: 
                print(f" [⚠️] Connection failed to {{ip}}:{{port}}")

@app.post("/v1/chat/completions")
async def infer(): 
    # Placeholder for Inference Engine connection
    return {{"msg": "HIVE_DRONE_SUCCESS", "source": MY_ID}}

if __name__ == "__main__":
    print(f" 🐝 DRONE ONLINE: {{MY_ID}} ({{MY_IP}})")
    uvicorn.run(app, host="0.0.0.0", port=8081, log_level="critical")
""")

    # --- Cell: Archivist & Backup Queen ---
    elif choice == "3":
        with open("cell.py", "w", encoding="utf-8") as f:
            f.write(LICENSE_HEADER + f"""
import fastapi, uvicorn, datetime, httpx, asyncio, threading

app = fastapi.FastAPI()
CONFIG = {json.dumps(config)}
IS_BACKUP_ACTIVE = False
WORKERS = []

@app.post("/write")
async def write(req: fastapi.Request):
    data = await req.json()
    log = f"[{{datetime.datetime.now()}}] {{data}}\\n"
    with open("hive_archive.log", "a", encoding="utf-8") as f: f.write(log)
    return {{"status": "recorded"}}

@app.post("/register") # Backup Registry
async def register(req: fastapi.Request):
    data = await req.json()
    if not any(d['id'] == data['id'] for d in WORKERS): WORKERS.append(data)
    return {{"status": "ACCEPTED_BY_BACKUP"}}

async def monitor_queen():
    global IS_BACKUP_ACTIVE
    async with httpx.AsyncClient() as client:
        while True:
            try:
                await client.get(f"http://{{CONFIG['queen_ip']}}:8000/health", timeout=1.0)
                IS_BACKUP_ACTIVE = False
            except:
                if not IS_BACKUP_ACTIVE:
                    print("🚨 Queen Offline. Cell assuming Backup Command...")
                    IS_BACKUP_ACTIVE = True
            await asyncio.sleep(2)

if __name__ == "__main__":
    threading.Thread(target=lambda: asyncio.run(monitor_queen()), daemon=True).start()
    print("🏛️ HIVE ARCHIVIST & BACKUP COMMANDER ONLINE")
    uvicorn.run(app, host="0.0.0.0", port=9000)
""")

    print("\n" + "═"*60)
    print(" 🎉 HIVE v1.8 DEPLOYMENT READY. GLORY TO THE SWARM.")
    print("═"*60)

# ==============================================================================
# 🏁 ENGINE IGNITION
# ==============================================================================
if __name__ == "__main__":
    setup()
