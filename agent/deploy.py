"""Package agent/ for AgentCore Runtime (arm64 zip via uv), upload to S3 and update the runtime; waits until READY.

Run from the repo root: AWS_PROFILE=<profile> .venv/bin/python agent/deploy.py
Needs: uv, the runtime `skillup_coach_agent`, role `skillup-coach-agentcore-runtime`, memory `skillup_coach_memory-*`.
"""
import shutil
import subprocess
import time
from pathlib import Path

import boto3

REGION, NAME = "ap-south-1", "skillup_coach_agent"
HERE = Path(__file__).resolve().parent
PKG, ZIP = HERE / "build" / "deployment_package", HERE / "build" / "deployment_package.zip"


def package():
    subprocess.run(["uv", "pip", "install", "-q", "--python-platform", "aarch64-manylinux2014", "--python-version", "3.13",
                    f"--target={PKG}", "--only-binary=:all:", "-r", str(HERE / "requirements.txt")], check=True)
    shutil.rmtree(PKG / "packs", ignore_errors=True)
    shutil.copytree(HERE.parent / "packs", PKG / "packs")
    shutil.copy(HERE / "main.py", PKG / "main.py")
    for d in list(PKG.rglob("__pycache__")):
        shutil.rmtree(d, ignore_errors=True)
    for p in PKG.rglob("*"):
        p.chmod(0o755 if p.is_dir() or p.parent.name == "bin" else 0o644)
    ZIP.unlink(missing_ok=True)
    shutil.make_archive(str(ZIP.with_suffix("")), "zip", PKG)


def deploy():
    s = boto3.Session(region_name=REGION)
    acct = s.client("sts").get_caller_identity()["Account"]
    bucket, key = f"bedrock-agentcore-code-{acct}-{REGION}", f"{NAME}/deployment_package.zip"
    s.client("s3").upload_file(str(ZIP), bucket, key, ExtraArgs={"ExpectedBucketOwner": acct})
    c = s.client("bedrock-agentcore-control")
    rt = next(r for r in c.list_agent_runtimes()["agentRuntimes"] if r["agentRuntimeName"] == NAME)
    mem = next(m["id"] for m in c.list_memories()["memories"] if m["id"].startswith("skillup_coach_memory-"))
    c.update_agent_runtime(
        agentRuntimeId=rt["agentRuntimeId"],
        agentRuntimeArtifact={"codeConfiguration": {"code": {"s3": {"bucket": bucket, "prefix": key}},
                                                    "runtime": "PYTHON_3_13",
                                                    "entryPoint": ["opentelemetry-instrument", "main.py"]}},
        networkConfiguration={"networkMode": "PUBLIC"},
        roleArn=f"arn:aws:iam::{acct}:role/skillup-coach-agentcore-runtime",
        lifecycleConfiguration={"idleRuntimeSessionTimeout": 300, "maxLifetime": 1800},
        environmentVariables={"BEDROCK_MODEL_ID": "apac.amazon.nova-lite-v1:0", "MEMORY_ID": mem,
                              "AGENT_OBSERVABILITY_ENABLED": "true"},
    )
    while (st := c.get_agent_runtime(agentRuntimeId=rt["agentRuntimeId"]))["status"] == "UPDATING":
        time.sleep(10)
    print(st["status"], "version", st.get("agentRuntimeVersion"), st.get("failureReason", ""))


if __name__ == "__main__":
    package()
    deploy()
