"""SkillUp Coach agent on Amazon Bedrock AgentCore Runtime (go/no-go spike: hello world).

Strands agent on Amazon Nova Lite; the AgentCore SDK serves /invocations and /ping.
"""
import os

from bedrock_agentcore.runtime import BedrockAgentCoreApp
from strands import Agent
from strands.models import BedrockModel

app = BedrockAgentCoreApp()
model = BedrockModel(model_id=os.environ.get("BEDROCK_MODEL_ID", "apac.amazon.nova-lite-v1:0"),
                     region_name=os.environ.get("AWS_REGION", "ap-south-1"))
agent = Agent(model=model, system_prompt="You are SkillUp Coach, a friendly voice coach for junior IT engineers. "
              "Answer in at most two short spoken sentences.")


@app.entrypoint
def invoke(payload):
    result = agent(payload.get("prompt", "Say hello."))
    return {"result": str(result)}


if __name__ == "__main__":
    app.run()
