# SkillUp Coach MCP server for AWS App Runner (Bedrock mode on; offline fallback if Bedrock fails).
FROM python:3.12-slim
RUN pip install --no-cache-dir "boto3>=1.35"
WORKDIR /app
COPY src/ src/
COPY demo/ demo/
ENV PYTHONPATH=/app/src PYTHONUNBUFFERED=1 SKILLUP_LLM=1 AWS_REGION=ap-south-1
EXPOSE 8080
USER nobody
CMD ["python", "-m", "skillup_mcp.server", "--host", "0.0.0.0", "--port", "8080"]
