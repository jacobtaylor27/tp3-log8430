import os
import sys
import subprocess

ITERATION_COUNT = 1
WORKLOADS_PATH = "workloads"
RESULTS_PATH = "results"
DOCKER_COMPOSE_TEMPLATE_FILENAME = "docker-compose-template.yml"
WORKLOAD_DEFAULT_CONFIG = "workload"
YCSB_BIN_PATH = "ycsb-0.17.0/bin/ycsb.sh"

NODE_COUNT = 0
READ_RATIO = 0
WRITE_RATIO = 0
DB = ""

DOCKER_COMPOSE_PATH = ""
WORKLOAD_PATH = ""

def main():
    if len(sys.argv) < 5:
        print("Usage: python script.py <db> <node_count> <workload-read-ratio> <workload-write-ratio")
        return 1

    global DB, NODE_COUNT, READ_RATIO, WRITE_RATIO
    
    DB = sys.argv[1]
    if DB != "redis" and DB != "mongodb":
        print("Invalid db. Please use either 'redis' or 'mongodb'")
        return 1

    NODE_COUNT = int(sys.argv[2])
    if NODE_COUNT <= 0:
        print("Invalid node count. Please use a positive integer")
        return 1

    READ_RATIO = float(sys.argv[3])
    if READ_RATIO < 0 or READ_RATIO > 1:
        print("Invalid read ratio. Please use a float between 0 and 1")
        return 1

    WRITE_RATIO = float(sys.argv[4])
    if WRITE_RATIO < 0 or WRITE_RATIO > 1:
        print("Invalid write ratio. Please use a float between 0 and 1")
        return 1
    
    generate_docker_compose()
    generate_workload()
    run_docker_compose()
    handle_workload()

    return 0

def generate_docker_compose():
    global DB
    if DB == "redis":
        generate_redis_docker_compose()
    elif DB == "mongodb":
        generate_mongodb_docker_compose()

def generate_redis_docker_compose():
    global DOCKER_COMPOSE_PATH
    redis_yml = None
    with open(f"{DB}/{DOCKER_COMPOSE_TEMPLATE_FILENAME}", "r") as f:
        redis_yml = f.read()
    
    for i in range(1, NODE_COUNT):
        redis_yml += f"""
  redis-replica-{i}:
    image: redis:latest
    networks:
      - redis-net
    command: redis-server --appendonly yes --slaveof redis-master 6379
"""

    redis_yml += f"""
networks:
  redis-net:
    driver: bridge
"""

    DOCKER_COMPOSE_PATH = f"{DB}/docker-compose.yml"
    with open(DOCKER_COMPOSE_PATH, "w") as f:
        f.write(redis_yml)
    
def generate_mongodb_docker_compose():
    with open(f"{DB}/{DOCKER_COMPOSE_TEMPLATE_FILENAME}", "r") as f:
        data = f.read()
    pass

def generate_workload():
    if DB == "redis":
        generate_redis_workload()
    elif DB == "mongodb":
        generate_mongodb_workload()

def generate_redis_workload():
    global WORKLOAD_PATH
    workloadData = None
    with open(f"{WORKLOADS_PATH}/{WORKLOAD_DEFAULT_CONFIG}", "r") as f:
        workloadData = f.read()

    workloadData += f"""
readproportion={READ_RATIO}
updateproportion={WRITE_RATIO}
redis.host=127.0.0.1
redis.port=6379
"""
    WORKLOAD_PATH = f"{WORKLOADS_PATH}/{WORKLOAD_DEFAULT_CONFIG}-{READ_RATIO}-{WRITE_RATIO}"
    with open(WORKLOAD_PATH, "w") as f:
        f.write(workloadData)

def generate_mongodb_workload():
    pass

def run_docker_compose():
    print(DB)
    subprocess.run(["sudo", "docker-compose", "-f", f"{DB}/docker-compose.yml", "up", "-d"])

def handle_workload():
    if DB == "redis":
        handle_redis_workload()
    elif DB == "mongodb":
        handle_mongodb_workload()

def handle_redis_workload():
    for i in range(ITERATION_COUNT):
        ycsb_runner("load", i)
        ycsb_runner("run", i)

def ycsb_runner(command_type: str, iteration: int):
    subprocess.run([
        YCSB_BIN_PATH,
        command_type,
        DB,
        "-s",
        "-P",
        WORKLOAD_PATH,
        ">",
        f"{RESULTS_PATH}/{DB}/{NODE_COUNT}/output-{iteration}-{command_type}-{READ_RATIO}-{WRITE_RATIO}.txt"
    ])

def handle_mongodb_workload():
    pass

if __name__ == '__main__':
    main()