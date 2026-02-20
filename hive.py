import os
import sys
import subprocess
import time

# =============================================================================
# 🐝 HIVE INSTALLER & LAUNCHER (v12.0 - English & GC Restored Edition)
# =============================================================================

def check_dependencies():
    try: import fastapi, uvicorn, httpx
    except ImportError:
        print("\n [❌] Missing required dependencies.")
        print(" [!] Run: pip install fastapi uvicorn httpx\n")
        sys.exit(1)

def setup_environment():
    os.makedirs("core", exist_ok=True)
    os.makedirs("nodes", exist_ok=True)
    open("core/__init__.py", "a").close()
    open("nodes/__init__.py", "a").close()

    def write_file_safe(path, content):
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
            f.flush()
            os.fsync(f.fileno())

    write_file_safe("core/config.py", '''\
class SystemConfig:
    PORTS = {"queen": 8000, "princess": 8001, "cell": 8082, "sentinel": 8083}
    PHEROMONE_PORT = 9999
    HEARTBEAT_TIMEOUT = 10.0
config = SystemConfig()
''')

def install_and_run_node(role_num):
    nodes = {
        "1": ("queen", "Queen (Master Router & Memory Sync)"),
        "2": ("princess", "Princess (Standby Failover & Memory Receiver)"),
        "3": ("drone", "Drone (AI Inference Worker Node)"),
        "4": ("cell", "Cell (Telemetry & Archive Storage)"),
        "5": ("sentinel", "Sentinel (Split-Brain Judge & Radar)")
    }

    if role_num not in nodes:
        print(" [❌] Invalid selection. Please enter a valid number.")
        return

    role, description = nodes[role_num]
    node_file = f"nodes/{role}.py"
    print(f" [📦] Initializing {description} module...")
    
    path_injector = "import sys, os\\nsys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))"
    
    # ==========================================
    # 👑 1. Queen
    # ==========================================
    if role == "queen":
        template_code = f'''\
{path_injector}
import uvicorn, asyncio, socket, time, httpx
from fastapi import FastAPI, Request
from contextlib import asynccontextmanager
from core.config import config

active_drones = {{}}
princess_url = None

async def emit_pheromone():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    while True:
        try: sock.sendto(f"I_AM_QUEEN:{{config.PORTS['queen']}}".encode(), ('255.255.255.255', config.PHEROMONE_PORT))
        except: pass 
        await asyncio.sleep(2)

async def udp_radar():
    """Scans for Princess to synchronize state"""
    global princess_url
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    if hasattr(socket, "SO_REUSEPORT"):
        try: sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        except AttributeError: pass
    sock.bind(('', config.PHEROMONE_PORT))
    sock.setblocking(False)

    while True:
        try:
            data, addr = sock.recvfrom(1024)
            msg = data.decode()
            if msg.startswith("I_AM_PRINCESS"):
                port = msg.split(':')[1]
                found_url = f"http://{{addr[0]}}:{{port}}"
                if princess_url != found_url:
                    princess_url = found_url
                    print(f" [👑] Backup Princess acquired: {{princess_url}}")
        except BlockingIOError: pass
        await asyncio.sleep(1)

async def sync_to_princess():
    """Replicates active drone registry to Princess"""
    async with httpx.AsyncClient() as client:
        while True:
            if princess_url and active_drones:
                try:
                    await client.post(f"{{princess_url}}/sync", json={{"active_drones": active_drones}}, timeout=1.0)
                except: pass
            await asyncio.sleep(2)

async def prune_dead_drones():
    """Garbage Collector: Removes drones that fail to send heartbeats"""
    while True:
        now = time.time()
        dead = [ip for ip, last_seen in active_drones.items() if now - last_seen > config.HEARTBEAT_TIMEOUT]
        for ip in dead:
            del active_drones[ip]
            print(f" [🗑️] GC: Pruned unresponsive drone ({{ip}})")
        await asyncio.sleep(5)

@asynccontextmanager
async def lifespan(app: FastAPI):
    asyncio.create_task(emit_pheromone())
    asyncio.create_task(udp_radar())
    asyncio.create_task(sync_to_princess())
    asyncio.create_task(prune_dead_drones())
    yield

app = FastAPI(lifespan=lifespan)

@app.get("/status")
def status(): return {{"status": "ALIVE", "role": "QUEEN", "drones": len(active_drones)}}

@app.post("/register")
async def register(req: Request):
    data = await req.json()
    active_drones[data['ip']] = time.time()
    print(f" [👑] New Drone registered: {{data['ip']}} (Total: {{len(active_drones)}})")
    return {{"status": "OK"}}

@app.post("/heartbeat")
async def heartbeat(req: Request):
    data = await req.json()
    active_drones[data['ip']] = time.time()
    return {{"status": "ALIVE"}}

def run_queen():
    print(" [👑] Queen is online. (Awaiting Princess for memory sync)")
    uvicorn.run(app, host="0.0.0.0", port=config.PORTS["queen"], log_level="warning")

if __name__ == "__main__": run_queen()
'''

    # ==========================================
    # 👸 2. Princess 
    # ==========================================
    elif role == "princess":
        template_code = f'''\
{path_injector}
import uvicorn, asyncio, socket, time
from fastapi import FastAPI, Request
from contextlib import asynccontextmanager
from core.config import config

is_promoted = False
active_drones = {{}}

async def emit_pheromone():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    while True:
        try:
            msg_prefix = "I_AM_QUEEN" if is_promoted else "I_AM_PRINCESS"
            msg = f"{{msg_prefix}}:{{config.PORTS['princess']}}".encode()
            sock.sendto(msg, ('255.255.255.255', config.PHEROMONE_PORT))
        except: pass 
        await asyncio.sleep(2)

async def prune_dead_drones():
    """Activates GC only after being promoted to Queen"""
    while True:
        if is_promoted:
            now = time.time()
            dead = [ip for ip, last_seen in active_drones.items() if now - last_seen > config.HEARTBEAT_TIMEOUT]
            for ip in dead:
                del active_drones[ip]
                print(f" [🗑️] GC: Pruned unresponsive drone ({{ip}})")
        await asyncio.sleep(5)

@asynccontextmanager
async def lifespan(app: FastAPI):
    asyncio.create_task(emit_pheromone())
    asyncio.create_task(prune_dead_drones())
    yield

app = FastAPI(lifespan=lifespan)

@app.get("/status")
def status(): return {{"status": "ALIVE", "role": "QUEEN" if is_promoted else "PRINCESS", "drones": len(active_drones)}}

@app.post("/sync")
async def sync_state(req: Request):
    """Receives memory replication from the active Queen"""
    global active_drones
    if is_promoted: return {{"status": "IGNORED"}}
    data = await req.json()
    active_drones = data.get("active_drones", {{}})
    return {{"status": "OK"}}

@app.post("/promote")
def promote():
    global is_promoted
    is_promoted = True
    print(f"\\n [👑] !!! PROMOTION SECURED !!! Assuming command over {{len(active_drones)}} existing Drones.\\n")
    return {{"status": "PROMOTED"}}

@app.post("/register")
async def register(req: Request):
    if not is_promoted: return {{"status": "DENIED"}}
    data = await req.json()
    active_drones[data['ip']] = time.time()
    print(f" [👸->👑] New Drone joined the promoted Queen: {{data['ip']}}")
    return {{"status": "OK"}}

@app.post("/heartbeat")
async def heartbeat(req: Request):
    if not is_promoted: return {{"status": "DENIED"}}
    data = await req.json()
    active_drones[data['ip']] = time.time()
    return {{"status": "ALIVE"}}

def run_princess():
    print(" [👸] Princess is online. Standby mode active. Awaiting memory sync.")
    uvicorn.run(app, host="0.0.0.0", port=config.PORTS["princess"], log_level="warning")

if __name__ == "__main__": run_princess()
'''

    # ==========================================
    # 🐝 3. Drone
    # ==========================================
    elif role == "drone":
        template_code = f'''\
{path_injector}
import socket, time, httpx, asyncio, uvicorn
from fastapi import FastAPI
from contextlib import asynccontextmanager
from core.config import config

def get_ephemeral_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        return s.getsockname()[1]

async def drone_lifecycle(my_port):
    my_ip = "127.0.0.1"
    my_address = f"{{my_ip}}:{{my_port}}"
    
    while True:
        print("\\n [🐝] Scanning network for Queen's pheromone...")
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        if hasattr(socket, "SO_REUSEPORT"):
            try: sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
            except AttributeError: pass
        sock.bind(('', config.PHEROMONE_PORT))
        sock.setblocking(False) 
        
        queen_url = None
        while not queen_url:
            try:
                data, addr = sock.recvfrom(1024)
                msg = data.decode()
                if msg.startswith("I_AM_QUEEN"):
                    queen_url = f"http://{{addr[0]}}:{{msg.split(':')[1]}}"
                    try: 
                        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                        s.connect((addr[0], 80))
                        my_ip = s.getsockname()[0]
                        my_address = f"{{my_ip}}:{{my_port}}"
                        s.close()
                    except: pass
            except BlockingIOError: pass
            await asyncio.sleep(1) 
        sock.close()

        print(f" [🐝] Queen acquired: {{queen_url}}")
        
        registered = False
        async with httpx.AsyncClient() as client:
            while not registered:
                try:
                    resp = await client.post(f"{{queen_url}}/register", json={{"ip": my_address}}, timeout=3.0)
                    if resp.status_code == 200:
                        print(" [🐝] Registration successful. Initiating heartbeat sequence.")
                        registered = True
                except: pass
                await asyncio.sleep(1)

        failed_pings = 0
        async with httpx.AsyncClient() as client:
            while failed_pings < 3:
                try:
                    await client.post(f"{{queen_url}}/heartbeat", json={{"ip": my_address}}, timeout=2.0)
                    failed_pings = 0
                except:
                    failed_pings += 1
                    print(f" [⚠️] Queen unresponsive (Warning: {{failed_pings}}/3)")
                await asyncio.sleep(3)
                
        print(" [🚨] Queen KIA detected. Abandoning hive to search for new Queen!")

@asynccontextmanager
async def lifespan(app: FastAPI):
    my_port = app.state.port
    asyncio.create_task(drone_lifecycle(my_port))
    yield

app = FastAPI(lifespan=lifespan)

def run_drone():
    my_port = get_ephemeral_port()
    app.state.port = my_port
    uvicorn.run(app, host="0.0.0.0", port=my_port, log_level="warning")

if __name__ == "__main__": run_drone()
'''

    # ==========================================
    # 🛡️ 5. Sentinel 
    # ==========================================
    elif role == "sentinel":
        template_code = f'''\
{path_injector}
import socket, time, httpx, asyncio
from core.config import config

queen_url = None
princess_url = None

async def udp_radar():
    global queen_url, princess_url
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    if hasattr(socket, "SO_REUSEPORT"):
        try: sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        except AttributeError: pass
    sock.bind(('', config.PHEROMONE_PORT))
    sock.setblocking(False)

    print(" [📡] Sentinel Radar online. Scanning for HIVE command nodes...")
    while True:
        try:
            data, addr = sock.recvfrom(1024)
            msg = data.decode()
            ip = addr[0]
            if msg.startswith("I_AM_QUEEN"):
                port = msg.split(':')[1]
                if queen_url != f"http://{{ip}}:{{port}}":
                    queen_url = f"http://{{ip}}:{{port}}"
                    print(f" [📡] Target locked: Queen ({{queen_url}})")
            elif msg.startswith("I_AM_PRINCESS"):
                port = msg.split(':')[1]
                if princess_url != f"http://{{ip}}:{{port}}":
                    princess_url = f"http://{{ip}}:{{port}}"
                    print(f" [📡] Target locked: Princess ({{princess_url}})")
        except BlockingIOError: pass
        await asyncio.sleep(0.5)

async def monitor_network():
    global queen_url, princess_url
    print(" [🛡️] Sentinel health-check loop standing by...")
    while not queen_url: await asyncio.sleep(1)
        
    strikes = 0
    async with httpx.AsyncClient() as client:
        while True:
            current_target = queen_url
            try:
                resp = await client.get(f"{{current_target}}/status", timeout=2.0)
                if resp.status_code == 200:
                    strikes = 0
            except Exception:
                strikes += 1
                print(f" [🛡️] ⚠️ Queen ping failed! (Strike {{strikes}}/3)")
                
                if strikes >= 3:
                    print("\\n [🛡️] 🚨 Queen declared DEAD! Initiating failover protocol!")
                    if not princess_url:
                        print(" [🛡️] ❌ CRITICAL: No Standby Princess available on network!")
                        strikes = 0
                        continue
                    try:
                        resp = await client.post(f"{{princess_url}}/promote", timeout=5.0)
                        if resp.status_code == 200:
                            print(" [🛡️] ✅ Princess successfully promoted. Command transferred.")
                            queen_url = None 
                            strikes = 0
                    except Exception as e: print(f" [🛡️] ❌ Failover command failed: {{e}}")
            await asyncio.sleep(2)

async def main_sentinel():
    asyncio.create_task(udp_radar())
    await monitor_network()

def run_sentinel():
    try: asyncio.run(main_sentinel())
    except KeyboardInterrupt: print("\\n [🛡️] Sentinel shutting down.")

if __name__ == "__main__": run_sentinel()
'''

    else:
        template_code = f'''\
{path_injector}
import time
def run_{role}():
    print(" [🚀] Starting {description}...")
    try:
        while True: time.sleep(1)
    except KeyboardInterrupt: pass
if __name__ == "__main__": run_{role}()
'''

    with open(node_file, "w", encoding="utf-8") as f:
        f.write(template_code)
        f.flush()
        os.fsync(f.fileno())

    print(f" [*] Spawning OS subprocess for {role.upper()}...\n")
    try:
        process = subprocess.Popen([sys.executable, node_file])
        process.wait()
    except KeyboardInterrupt:
        pass

def main():
    check_dependencies()
    setup_environment()
    print("\n" + "="*60)
    print(" 🐝 HIVE Enterprise Builder v12.0 (English & GC Edition)")
    print("="*60)
    print(" [1] Deploy Queen    (Master Router & Memory Transmitter)")
    print(" [2] Deploy Princess (Standby Failover & Memory Receiver)")
    print(" [3] Deploy Drone    (AI Inference Worker Node)")
    print(" [4] Deploy Cell     (Telemetry Archive Storage)")
    print(" [5] Deploy Sentinel (Radar & Split-Brain Judge)")
    print("="*60)
    choice = input(" Select a node to deploy > ").strip()
    install_and_run_node(choice)

if __name__ == "__main__":
    try: main()
    except KeyboardInterrupt: sys.exit(0)
