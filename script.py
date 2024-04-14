import os
import sys
import subprocess

ITERATION_COUNT = 50
REDIS_PATH = "redis"
MONGODB_PATH = "mongodb"
WORKLOADS_PATH = "workloads"
RESULTS_PATH = "results"
DOCKER_COMPOSER_TEMPLATE_FILENAME = "docker-compose-template.yml"
WORKLOAD_DEFAULT_CONFIG = "workload"
READ_RATIO_PROPERTY = "readproportion"
WRITE_RATIO_PROPERTY = "updateproportion"

def main():
    if len(sys.argv) < 5:
        print("Usage: python script.py <db> <node_count> <workload-read-ratio> <workload-write-ratio")
        return 1

    db = sys.argv[1]
    if db != "redis" and db != "mongodb":
        print("Invalid db. Please use either 'redis' or 'mongodb'")
        return 1

    node_count = int(sys.argv[2])
    if node_count <= 0:
        print("Invalid node count. Please use a positive integer")
        return 1

    workload_read_ratio = float(sys.argv[3])
    if workload_read_ratio < 0 or workload_read_ratio > 1:
        print("Invalid read ratio. Please use a float between 0 and 1")
        return 1

    workload_write_ratio = float(sys.argv[4])
    if workload_write_ratio < 0 or workload_write_ratio > 1:
        print("Invalid write ratio. Please use a float between 0 and 1")
        return 1

    generate_docker_compose(db, node_count)
    generate_workload(workload_read_ratio, workload_write_ratio)
    run_docker_compose()
    return 0

def generate_docker_compose(db: str, node_count: int):
    if db == "redis":
        generate_redis_docker_compose(node_count)
    elif db == "mongodb":
        generate_mongodb_docker_compose(node_count)

def generate_redis_docker_compose(node_count: int):
    redis_yml = None
    with open(f"{REDIS_PATH}/{DOCKER_COMPOSER_TEMPLATE_FILENAME}", "r") as f:
        redis_yml = f.read()
    
    for i in range(1, node_count):
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

    with open(f"{REDIS_PATH}/docker-compose.yml", "w") as f:
        f.write(redis_yml)

def generate_mongodb_docker_compose(node_count: int):
    with open(f"{MONGODB_PATH}/{DOCKER_COMPOSER_TEMPLATE_FILENAME}", "r") as f:
        data = f.read()
    pass

def generate_workload(read_ratio: float, write_ratio: float):
    workloadData = None
    with open(f"{WORKLOADS_PATH}/{WORKLOAD_DEFAULT_CONFIG}", "r") as f:
        workloadData = f.read()

    workloadData += f"""
readproportion={read_ratio}
updateproportion={write_ratio}
"""

    with open(f"{WORKLOADS_PATH}/{WORKLOAD_DEFAULT_CONFIG}-{read_ratio}-{write_ratio}", "w") as f:
        f.write(workloadData)

def run_docker_compose():
    stop_all_docker_containers()

def stop_all_docker_containers():
    try:
        container_ids = subprocess.check_output(["docker", "ps", "-q"]).decode().split()
    except subprocess.CalledProcessError:
        print("No running containers found.")
        return

    for container_id in container_ids:
        subprocess.run(["docker", "stop", container_id])

if __name__ == '__main__':
    main()