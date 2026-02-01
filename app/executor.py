import subprocess
import uuid
import os
import shutil

IMAGES = {
    "python": "coderank-python",
    "java": "coderank-java",
    "cpp": "coderank-cpp",
    "node": "coderank-node"
}

FILES = {
    "python": "Main.py",
    "java": "Main.java",
    "cpp": "Main.cpp",
    "node": "Main.js"
}

RUN = {
    "python": ["python3", "/code/Main.py"],
    "java": ["bash", "-c", "javac /code/Main.java && java -cp /code Main"],
    "cpp": ["bash", "-c", "g++ /code/Main.cpp -o /code/a.out && /code/a.out"],
    "node": ["node", "/code/Main.js"]
}

BASE = "/runner"

def execute_code(language, source, input_data):
    job_id = str(uuid.uuid4())
    job_dir = os.path.join(BASE, job_id)
    os.makedirs(job_dir, exist_ok=True)

    file_path = os.path.join(job_dir, FILES[language])
    with open(file_path, "w") as f:
        f.write(source)

    cmd = [
        "docker", "run", "--rm",
        "-v", f"{job_dir}:/code",
        IMAGES[language],
        *RUN[language]
    ]

    proc = subprocess.run(
        cmd,
        input=input_data.encode(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=5
    )

    shutil.rmtree(job_dir, ignore_errors=True)

    return {
        "stdout": proc.stdout.decode(),
        "stderr": proc.stderr.decode(),
        "exit": proc.returncode
    }
