import os
import subprocess
import uuid
import shutil

IMAGES = {
    "python": "coderank-python",
    "java": "coderank-java",
    "cpp": "coderank-cpp",
    "node": "coderank-node",
}

FILES = {
    "python": "Main.py",
    "java": "Main.java",
    "cpp": "Main.cpp",
    "node": "Main.js",
}

RUN = {
    "python": ["python3", "/code/Main.py"],
    "java": ["bash", "-c", "javac /code/Main.java && java -cp /code Main"],
    "cpp": ["bash", "-c", "g++ /code/Main.cpp -o /code/a.out && /code/a.out"],
    "node": ["node", "/code/Main.js"],
}

# Inside the worker container, we write code here:
CONTAINER_CODE_BASE = "/code/runner"

# On macOS, docker-in-docker mounts must use a HOST path that Docker Desktop can access
HOST_CODE_DIR = os.getenv("HOST_CODE_DIR")
if not HOST_CODE_DIR:
    raise RuntimeError("HOST_CODE_DIR env var is required (macOS Docker mounts).")

# On the host, we will mount: {HOST_CODE_DIR}/runner/<job_id> -> /code
HOST_RUNNER_BASE = os.path.join(HOST_CODE_DIR, "runner")
os.makedirs(HOST_RUNNER_BASE, exist_ok=True)


def execute_code(language: str, source: str, input_data: str):
    if language not in IMAGES:
        return {"stdout": "", "stderr": f"Unsupported language: {language}", "exit": -1}

    job_id = str(uuid.uuid4())

    # Write files inside the worker container (same repo bind mount)
    container_job_dir = os.path.join(CONTAINER_CODE_BASE, job_id)
    os.makedirs(container_job_dir, exist_ok=True)

    file_path = os.path.join(container_job_dir, FILES[language])
    with open(file_path, "w") as f:
        f.write(source)

    # But mount using HOST path (because docker CLI talks to host daemon)
    host_job_dir = os.path.join(HOST_RUNNER_BASE, job_id)

    # Ensure host path exists (it will, because /code is bind mounted from host)
    # Still, make sure:
    os.makedirs(host_job_dir, exist_ok=True)

    cmd = [
        "docker", "run", "--rm",
        "-v", f"{host_job_dir}:/code",
        IMAGES[language],
        *RUN[language],
    ]

    try:
        proc = subprocess.run(
            cmd,
            input=(input_data or "").encode(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=5,
        )
        out = {
            "stdout": proc.stdout.decode(errors="replace"),
            "stderr": proc.stderr.decode(errors="replace"),
            "exit": proc.returncode,
        }
        return out
    finally:
        # Cleanup (inside container path; host path is same via bind mount)
        shutil.rmtree(container_job_dir, ignore_errors=True)
