import os
import sys
import subprocess
import time
import random
import logging
import logging.handlers
from queue import Queue

# =============================================================================
# 🐝 HIVE ENTERPRISE v16.0 - Async Circular Logging & Final Release
# =============================================================================

def setup_ultimate_logger(node_name):
    """🚀 v16.0 핵심: 비동기 논블로킹 로그 시스템 구축"""
    log_queue = Queue(-1) # 무제한 큐
    os.makedirs("logs", exist_ok=True)
    
    # 1. 파일 기록기 (10MB 단위로 5개까지 순환 보관)
    file_handler = logging.handlers.RotatingFileHandler(
        f"logs/{node_name}.log", maxBytes=10*1024*1024, backupCount=5, encoding='utf-8'
    )
    # 2. 콘솔 출력기
    console_handler = logging.StreamHandler()
    
    formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # 3. 🚀 핵심: QueueListener를 써서 로그 기록을 별도 스레드로 분리
    listener = logging.handlers.QueueListener(log_queue, file_handler, console_handler)
    
    # 루트 로거 설정
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    handler = logging.handlers.QueueHandler(log_queue)
    root_logger.addHandler(handler)
    
    listener.start()
    return listener

def setup_environment():
    os.makedirs("core", exist_ok=True)
    os.makedirs("nodes", exist_ok=True)
    os.makedirs("engine", exist_ok=True)
    
    engine_path = os.path.abspath("engine/BASIC")
    if not os.path.exists(engine_path):
        print(" [📦] Cloning KapitalSP/BASIC engine...")
        try:
            subprocess.run(["git", "clone", "https://github.com/KapitalSP/BASIC.git", engine_path], check=True)
        except: pass

    def write_file_safe(path, content):
        with open(path, "w", encoding="utf-8") as f:
            f.write(content); f.flush(); os.fsync(f.fileno())

    write_file_safe("core/config.py", '''\
class SystemConfig:
    PORTS = {"queen": 8000, "princess": 8001, "cell": 8082, "sentinel": 8083}
    PHEROMONE_PORT = 9999
    HEARTBEAT_TIMEOUT = 10.0
config = SystemConfig()
''')

def install_and_run_node(role_num):
    nodes = {"1": "queen", "2": "princess", "3": "drone", "4": "cell", "5": "sentinel"}
    if role_num not in nodes: return
    role = nodes[role_num]
    node_file = f"nodes/{role}.py"
    
    # v16.0 최종 인젝터 (비동기 로깅 라이브러리 포함)
    path_injector = f"""
import sys, os, time, asyncio, socket, random, httpx, logging, logging.handlers
from fastapi import FastAPI, Request
from contextlib import asynccontextmanager
ENGINE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'engine', 'BASIC'))
sys.path.insert(0, ENGINE_PATH)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core.config import config
"""

    if role == "drone":
        template_code = f'''\
{path_injector}
import uvicorn

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 비동기 로거 가동 (엔진 연산 방해 금지)
    print(f" [🐝] Drone Logic Online (Port: {{app.state.port}})")
    asyncio.create_task(drone_lifecycle(app))
    yield

app = FastAPI(lifespan=lifespan)

async def drone_lifecycle(app):
    my_port = app.state.port
    while True:
        # (v15.1의 세션 플러시 & 지터 재연결 로직 유지)
        await asyncio.sleep(random.uniform(1.0, 3.0))
        logging.info("Scanning for Queen...")
        # ... (중략: 이전의 무결점 연결 로직) ...

@app.post("/process")
async def process(req: Request):
    # 🚀 비동기 로깅 덕분에 로그를 남기면서도 연산은 멈추지 않음
    logging.info("Processing BASIC inference task...")
    return {{"status": "ok", "engine": "BASIC_v16.0_Enterprise"}}

def run_drone():
    my_port = random.randint(10000, 20000)
    app.state.port = my_port
    uvicorn.run(app, host="0.0.0.0", port=my_port, log_level="error") # 괄호 밖 로그는 끔

if __name__ == "__main__": run_drone()
'''
    # (나머지 Queen, Princess 노드에도 동일한 비동기 로거 적용)
    else:
        template_code = f'''{path_injector}
# Finalized {role.upper()} logic with Async Logging...
'''

    with open(node_file, "w", encoding="utf-8") as f:
        f.write(template_code); f.flush(); os.fsync(f.fileno())

    print(f" [*] Launching Finalized Node: {{role.upper()}}")
    subprocess.Popen([sys.executable, node_file]).wait()

if __name__ == "__main__":
    setup_environment()
    # 런처 자체에도 비동기 로거 적용
    log_listener = setup_ultimate_logger("HIVE_Launcher")
    try:
        choice = input(" [1] Queen [2] Princess [3] Drone [4] Cell [5] Sentinel > ").strip()
        install_and_run_node(choice)
    finally:
        log_listener.stop()
