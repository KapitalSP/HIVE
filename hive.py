# Copyright 2026 KapitalSP
# Licensed under the Apache License, Version 2.0 (the "License");

import os, sys, subprocess, socket, json, time

# =============================================================================
# 🧬 KAPITAL SENTINEL DNA [CODE INJECTION PAYLOAD]
# =============================================================================
SENTINEL_CODE = """
import os, sys, platform, zlib, struct, time
try: import psutil; HAS_DEPS=True
except: HAS_DEPS=False

class KapitalSentinel:
    def __init__(self, role="worker"):
        self.ignite(role)
    def ignite(self, role):
        if not HAS_DEPS: return
        try:
            p = psutil.Process(os.getpid())
            if platform.system() == "Windows": p.nice(psutil.HIGH_PRIORITY_CLASS)
            else: 
                try: p.nice(-10)
                except: pass
            cores = psutil.cpu_count(logical=True)
            if role == "worker" and cores > 2:
                try: p.cpu_affinity(list(range(cores - 1)))
                except: pass
            elif role == "server" and cores >= 2:
                try: p.cpu_affinity([0, 1])
                except: pass
        except: pass
    def pack(self, d):
        if isinstance(d, str): d = d.encode()
        return zlib.compress(d, 1) + struct.pack('I', zlib.crc32(d) & 0xffffffff)
    def unpack(self, d):
        try:
            data = d[:-4]; checksum = struct.unpack('I', d[-4:])[0]
            if (zlib.crc32(zlib.decompress(data)) & 0xffffffff) != checksum: return None
            return zlib.decompress(data).decode()
        except: return None
sentinel = KapitalSentinel("worker")
"""

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try: s.connect(('8.8.8.8', 1)); ip = s.getsockname()[0]
    except: ip = '127.0.0.1'
    finally: s.close()
    return ip

class HiveBuilder:
    def deploy(self):
        print(f" 🏗️  HIVE FABRICATOR v3.1 // IP: {get_local_ip()}")
        print(" ------------------------------------------")
        print(" [1] Queen (Command Node)")
        print(" [2] Drone (Computing Node)")
        print(" ------------------------------------------")
        choice = input(" Select Role > ").strip()

        if choice == "1":
            with open("queen.py", "w") as f:
                f.write(f"import fastapi, uvicorn, httpx\nfrom fastapi import Request\n{SENTINEL_CODE.replace('worker', 'server')}\n")
                f.write("\napp = fastapi.FastAPI()\n@app.post('/register')\nasync def reg(req: Request):\n    data = sentinel.unpack(await req.body())\n    if data: print(f' [👑] Drone Active: {data}')\n    return {'status': 'OK'}\n\nif __name__ == '__main__': uvicorn.run(app, host='0.0.0.0', port=8000)")
            print(" [✅] Queen Deployment Script Generated.")

        elif choice == "2":
            q_ip = input(" Enter Queen IP Address: ")
            with open("drone.py", "w") as f:
                f.write(f"import fastapi, uvicorn, httpx, socket, asyncio, json\n{SENTINEL_CODE}\n")
                f.write(f"\napp = fastapi.FastAPI()\n@app.on_event('startup')\nasync def join():\n    async with httpx.AsyncClient() as c:\n        msg = json.dumps({{'id': socket.gethostname()}})\n        await c.post('http://{q_ip}:8000/register', content=sentinel.pack(msg))\n\nif __name__ == '__main__': uvicorn.run(app, host='0.0.0.0', port=8081)")
            print(" [✅] Drone Deployment Script Generated.")

if __name__ == "__main__":
    HiveBuilder().deploy()
