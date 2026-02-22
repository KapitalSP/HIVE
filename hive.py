import os
import sys
import subprocess
import time
import random

# =============================================================================
# 🐝 HIVE ENTERPRISE v16.1 - Async Logging & English Translation
# =============================================================================

def check_dependencies():
    try: import fastapi, uvicorn, httpx
    except ImportError:
        print("\n [❌] Missing required dependencies. (pip install fastapi uvicorn httpx)")
        sys.exit(1)

def setup_environment():
    os.makedirs("core", exist_ok=True)
    os.makedirs("nodes", exist_ok=True)
    os.makedirs("engine", exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    
    engine_path = os.path.abspath("engine/BASIC")
    if not os.path.exists(engine_path):
        print(" [📦] Cloning KapitalSP/BASIC engine...")
        try: subprocess.run(["git", "clone", "https://github.com/KapitalSP/BASIC.git", engine_path], check=True)
        except: pass

    def write_file_safe(path, content):
        with open(path, "w", encoding="utf-8") as f:
            f.write(content); f.flush(); os.fsync(f.fileno())

    write_file_safe("core/config.py", '''\
class SystemConfig:
    PORTS = {"queen": 8000, "princess": 8001, "cell": 8082, "sentinel": 8083}
    PHEROMONE_PORT = 9999
    HEARTBEAT_TIMEOUT = 10.0
    GRACE_PERIOD = 15.0
config = SystemConfig()
''')

def install_and_run_node(role_num):
    nodes = {
        "1": ("queen", "Queen (Master Router)"),
        "2": ("princess", "Princess (Standby Failover)"),
        "3": ("drone", "Drone (BASIC Worker)"),
        "4": ("cell", "Cell (Archive)"),
        "5": ("sentinel", "Sentinel (Arbiter)")
    }
    if role_num not in nodes: return
    role, description = nodes[role_num]
    node_file = f"nodes/{role}.py"
    
    # 🚀 v16.1 INJECTOR: Every node gets its own Async Logger
    path_injector = f"""
import sys, os, time, asyncio, socket, random, httpx, logging, logging.handlers
from queue import Queue
from fastapi import FastAPI, Request
from contextlib import asynccontextmanager

# Setup Async Circular Logger for THIS specific subprocess
def setup_node_logger(node_name):
    log_queue = Queue(-1)
    file_handler = logging.handlers.RotatingFileHandler(f"../logs/{{node_name}}.log", maxBytes=10*1024*1024, backupCount=5, encoding='utf-8')
    console_handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    listener = logging.handlers.QueueListener(log_queue, file_handler, console_handler)
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(logging.handlers.QueueHandler(log_queue))
    listener.start()
    return listener

ENGINE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'engine', 'BASIC'))
sys.path.insert(0, ENGINE_PATH)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core.config import config
"""

    # ==========================================
    # 👑 1. QUEEN
    # ==========================================
    if role == "queen":
        template_code = f'''\
{path_injector}
import uvicorn
active_drones = {{}}
princess_url = None
task_counter = 0
http_client = None
is_deposed = False

async def emit_pheromone():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    while True:
        if is_deposed: break
        try: sock.sendto(f"I_AM_QUEEN:{{config.PORTS['queen']}}".encode(), ('255.255.255.255', config.PHEROMONE_PORT))
        except: pass 
        await asyncio.sleep(2)

async def udp_radar():
    global princess_url, is_deposed
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
                princess_url = f"http://{{addr[0]}}:{{msg.split(':')[1]}}"
            elif msg.startswith("I_AM_QUEEN") and str(config.PORTS['queen']) not in msg:
                if not is_deposed:
                    is_deposed = True
                    logging.error("Foreign Queen detected. Self-demoting to prevent Split-Brain.")
                    os._exit(0)
        except BlockingIOError: pass
        await asyncio.sleep(1)

async def sync_to_princess():
    while True:
        if not is_deposed and princess_url and active_drones and http_client:
            try: await http_client.post(f"{{princess_url}}/sync", json={{"active_drones": active_drones}}, timeout=1.0)
            except: pass
        await asyncio.sleep(2)

async def prune_dead_drones():
    while True:
        now = time.time()
        dead = [ip for ip, last_seen in active_drones.items() if now - last_seen > config.HEARTBEAT_TIMEOUT]
        for ip in dead:
            del active_drones[ip]
            logging.warning(f"GC: Pruned unresponsive drone ({{ip}})")
        await asyncio.sleep(5)

@asynccontextmanager
async def lifespan(app: FastAPI):
    global http_client
    logger_listener = setup_node_logger("queen")
    logging.info("Queen Node Initializing...")
    
    http_client = httpx.AsyncClient(limits=httpx.Limits(max_connections=500), timeout=httpx.Timeout(60.0, connect=2.0))
    asyncio.create_task(emit_pheromone())
    asyncio.create_task(udp_radar())
    asyncio.create_task(sync_to_princess())
    asyncio.create_task(prune_dead_drones())
    yield
    await http_client.aclose()
    logger_listener.stop()

app = FastAPI(lifespan=lifespan)

@app.post("/api/task")
async def handle_task(req: Request):
    global task_counter
    if is_deposed: return {{"error": "Queen has been deposed."}}
    
    task_data = await req.json()
    for _ in range(3):
        if not active_drones: return {{"error": "No active drones available."}}
        
        target = list(active_drones.keys())[task_counter % len(active_drones)]
        task_counter += 1
        
        logging.info(f"Dispatching task to {{target}}...")
        try:
            resp = await http_client.post(f"http://{{target}}/process", json=task_data)
            resp.raise_for_status() 
            return {{"status": "success", "worker": target, "result": resp.json()}}
        except Exception: 
            logging.warning(f"Task failed on {{target}}. Re-routing.")
            active_drones.pop(target, None)
    return {{"error": "Task execution failed."}}

@app.post("/register")
async def register(req: Request):
    if is_deposed: return {{"status": "DENIED"}}
    data = await req.json()
    addr = f"{{req.client.host}}:{{data.get('port')}}"
    active_drones[addr] = time.time()
    logging.info(f"Drone Registered: {{addr}} (Total: {{len(active_drones)}})")
    return {{"status": "OK"}}

@app.post("/heartbeat")
async def heartbeat(req: Request):
    if is_deposed: return {{"status": "DENIED"}}
    data = await req.json()
    addr = f"{{req.client.host}}:{{data.get('port')}}"
    active_drones[addr] = time.time()
    return {{"status": "ALIVE"}}

@app.get("/status")
def status(): 
    if is_deposed: return {{"status": "DEAD"}}
    return {{"status": "ALIVE", "role": "QUEEN", "drones": len(active_drones)}}

if __name__ == "__main__": 
    uvicorn.run(app, host="0.0.0.0", port=config.PORTS["queen"], log_level="error")
'''

    # ==========================================
    # 👸 2. PRINCESS
    # ==========================================
    elif role == "princess":
        template_code = f'''\
{path_injector}
import uvicorn
is_promoted = False
active_drones = {{}}
task_counter = 0
http_client = None

async def emit_pheromone():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    while True:
        try:
            msg = f"{{'I_AM_QUEEN' if is_promoted else 'I_AM_PRINCESS'}}:{{config.PORTS['princess']}}".encode()
            sock.sendto(msg, ('255.255.255.255', config.PHEROMONE_PORT))
        except: pass 
        await asyncio.sleep(2)

async def prune_dead_drones():
    while True:
        if is_promoted:
            now = time.time()
            dead = [ip for ip, last_seen in active_drones.items() if now - last_seen > config.HEARTBEAT_TIMEOUT]
            for ip in dead: 
                del active_drones[ip]
                logging.warning(f"GC: Pruned unresponsive drone ({{ip}})")
        await asyncio.sleep(5)

@asynccontextmanager
async def lifespan(app: FastAPI):
    global http_client
    logger_listener = setup_node_logger("princess")
    logging.info("Princess Node Standing By...")
    
    http_client = httpx.AsyncClient(limits=httpx.Limits(max_connections=500), timeout=httpx.Timeout(60.0, connect=2.0))
    asyncio.create_task(emit_pheromone())
    asyncio.create_task(prune_dead_drones())
    yield
    await http_client.aclose()
    logger_listener.stop()

app = FastAPI(lifespan=lifespan)

@app.post("/api/task")
async def handle_task(req: Request):
    global task_counter
    if not is_promoted: return {{"error": "Node is in Standby mode."}}
    
    task_data = await req.json()
    for _ in range(3):
        if not active_drones: return {{"error": "No active drones available."}}
        
        target = list(active_drones.keys())[task_counter % len(active_drones)]
        task_counter += 1
        
        logging.info(f"Dispatching task to {{target}}...")
        try:
            resp = await http_client.post(f"http://{{target}}/process", json=task_data)
            resp.raise_for_status()
            return {{"status": "success", "worker": target, "result": resp.json()}}
        except Exception: active_drones.pop(target, None)
    return {{"error": "Task execution failed."}}

@app.post("/sync")
async def sync_state(req: Request):
    global active_drones
    if is_promoted: return {{"status": "IGNORED"}}
    data = await req.json()
    active_drones = data.get("active_drones", {{}})
    return {{"status": "OK"}}

@app.post("/promote")
def promote():
    global is_promoted
    is_promoted = True
    now = time.time()
    for drone in active_drones: active_drones[drone] = now # Grace Period
    logging.critical(f"PROMOTED TO QUEEN! Grace period issued to {{len(active_drones)}} drones.")
    return {{"status": "PROMOTED"}}

@app.post("/register")
async def register(req: Request):
    if not is_promoted: return {{"status": "DENIED"}}
    data = await req.json()
    active_drones[f"{{req.client.host}}:{{data.get('port')}}"] = time.time()
    return {{"status": "OK"}}

@app.post("/heartbeat")
async def heartbeat(req: Request):
    if not is_promoted: return {{"status": "DENIED"}}
    data = await req.json()
    active_drones[f"{{req.client.host}}:{{data.get('port')}}"] = time.time()
    return {{"status": "ALIVE"}}

@app.get("/status")
def status(): return {{"status": "ALIVE", "role": "QUEEN" if is_promoted else "PRINCESS"}}

if __name__ == "__main__": 
    uvicorn.run(app, host="0.0.0.0", port=config.PORTS["princess"], log_level="error")
'''

    # ==========================================
    # 🐝 3. DRONE
    # ==========================================
    elif role == "drone":
        template_code = f'''\
{path_injector}
import uvicorn

internal_task_buffer = []

def flush_internal_state():
    global internal_task_buffer
    internal_task_buffer.clear()
    logging.info("Session Flushed: Internal state sanitized.")

async def drone_lifecycle(app):
    my_port = app.state.port
    while True:
        flush_internal_state()
        await asyncio.sleep(random.uniform(0.5, 2.5)) # Jitter
        
        logging.info("Scanning for Queen via Radar...")
        queen_url = None
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        if hasattr(socket, "SO_REUSEPORT"):
            try: sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
            except AttributeError: pass
        sock.bind(('', config.PHEROMONE_PORT))
        sock.setblocking(False) 
        
        while not queen_url:
            try:
                data, addr = sock.recvfrom(1024)
                if data.decode().startswith("I_AM_QUEEN"):
                    queen_url = f"http://{{addr[0]}}:{{data.decode().split(':')[1]}}"
            except BlockingIOError: pass
            await asyncio.sleep(1) 
        sock.close()

        reg = False
        async with httpx.AsyncClient() as client:
            for _ in range(3):
                try:
                    resp = await client.post(f"{{queen_url}}/register", json={{"port": my_port, "clean_slate": True}}, timeout=3.0)
                    if resp.status_code == 200: 
                        reg = True; break
                except: await asyncio.sleep(random.uniform(1.0, 2.0))
        
        if not reg: 
            logging.warning("Registration failed (Anti-Blackhole). Retrying...")
            continue
            
        logging.info(f"Connected to Hive: {{queen_url}}")

        fails = 0
        async with httpx.AsyncClient() as client:
            while fails < 3:
                try:
                    await client.post(f"{{queen_url}}/heartbeat", json={{"port": my_port}}, timeout=2.0)
                    fails = 0
                except: fails += 1
                await asyncio.sleep(3)
        logging.error("Connection to Queen lost. Abandoning hive.")

def run_heavy_ai_engine(prompt: str) -> str:
    time.sleep(1.5) # Simulating BASIC processing
    return f"[BASIC ENGINE OUTPUT for: {{prompt}}]"

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger_listener = setup_node_logger(f"drone_{{app.state.port}}")
    logging.info(f"Drone Initialized on port {{app.state.port}}.")
    asyncio.create_task(drone_lifecycle(app))
    yield
    logger_listener.stop()

app = FastAPI(lifespan=lifespan)

@app.post("/process")
async def process(req: Request):
    task_data = await req.json()
    prompt = task_data.get("prompt", "Hello")
    logging.info(f"Processing inference task: {{prompt[:20]}}...")
    
    result = await asyncio.to_thread(run_heavy_ai_engine, prompt)
    logging.info("Task completed.")
    return {{"status": "success", "output": result, "port": app.state.port}}

if __name__ == "__main__": 
    port = random.randint(10000, 20000)
    app.state.port = port
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="error")
'''

    # ==========================================
    # 🛡️ 5. SENTINEL
    # ==========================================
    elif role == "sentinel":
        template_code = f'''\
{path_injector}
import uvicorn
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

    while True:
        try:
            data, addr = sock.recvfrom(1024)
            msg = data.decode()
            ip = addr[0]
            if msg.startswith("I_AM_QUEEN"):
                port = msg.split(':')[1]
                if queen_url != f"http://{{ip}}:{{port}}":
                    queen_url = f"http://{{ip}}:{{port}}"
                    logging.info(f"Radar Target Acquired: QUEEN at {{queen_url}}")
            elif msg.startswith("I_AM_PRINCESS"):
                port = msg.split(':')[1]
                if princess_url != f"http://{{ip}}:{{port}}":
                    princess_url = f"http://{{ip}}:{{port}}"
                    logging.info(f"Radar Target Acquired: PRINCESS at {{princess_url}}")
        except BlockingIOError: pass
        await asyncio.sleep(0.5)

async def monitor_network():
    global queen_url, princess_url
    while not queen_url: await asyncio.sleep(1)
        
    strikes = 0
    async with httpx.AsyncClient() as client:
        while True:
            try:
                resp = await client.get(f"{{queen_url}}/status", timeout=2.0)
                if resp.status_code == 200: strikes = 0
            except Exception:
                strikes += 1
                logging.warning(f"Queen Ping Failed! (Strike {{strikes}}/3)")
                if strikes >= 3:
                    if not princess_url:
                        logging.error("Failover Aborted: No Standby Princess available.")
                        strikes = 0
                        continue
                    try:
                        logging.critical("QUEEN DECLARED DEAD. Executing Failover to Princess...")
                        resp = await client.post(f"{{princess_url}}/promote", timeout=5.0)
                        if resp.status_code == 200:
                            logging.info("Failover Successful. Authority Transferred.")
                            queen_url = None 
                            strikes = 0
                    except Exception as e: logging.error(f"Failover execution failed: {{e}}")
            await asyncio.sleep(2)

async def main_sentinel():
    logger_listener = setup_node_logger("sentinel")
    logging.info("Sentinel Arbiter Online. Commencing Network Surveillance.")
    asyncio.create_task(udp_radar())
    await monitor_network()

if __name__ == "__main__": 
    try: asyncio.run(main_sentinel())
    except KeyboardInterrupt: pass
'''

    else:
        template_code = f'''{path_injector}\n# Architecture for {role.upper()}...'''

    with open(node_file, "w", encoding="utf-8") as f:
        f.write(template_code); f.flush(); os.fsync(f.fileno())

    print(f" [*] Launching Finalized Node: {role.upper()}")
    subprocess.Popen([sys.executable, node_file]).wait()

if __name__ == "__main__":
    check_dependencies()
    setup_environment()
    print("\n" + "="*60)
    print(" 🐝 HIVE Enterprise v16.1 (Ultimate English Release)")
    print("="*60)
    print(" [1] Queen    (Master Router & Load Balancer)")
    print(" [2] Princess (Standby Failover)")
    print(" [3] Drone    (BASIC Worker)")
    print(" [4] Cell     (Archive)")
    print(" [5] Sentinel (Arbiter)")
    print("="*60)
    try:
        choice = input(" Select Node > ").strip()
        install_and_run_node(choice)
    except KeyboardInterrupt:
        sys.exit(0)
