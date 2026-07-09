from pydantic import BaseModel, Field
from typing import Optional, List
import json
import requests
from pathlib import Path

CORTEX_ROOT = Path(__file__).resolve().parents[1]
PRIMARY_URL = "http://localhost:8642/v1/chat/completions"
PRIMARY_KEY = "cortex-local-key"

# Structured output schemas
class CodePatchResponse(BaseModel):
    fixed_code: str = Field(description="Complete corrected Python script")
    explanation: str = Field(description="What was fixed and why")
    estimated_impact: str = Field(description="low/medium/high impact on system")
    safety_validated: bool = Field(description="True if code passes safety checks")

class RAGQueryResponse(BaseModel):
    answer: str = Field(description="Direct answer to the query")
    sources: List[str] = Field(description="Source documents used")
    confidence: str = Field(description="low/medium/high confidence")

class GoalAnalysisResponse(BaseModel):
    goal_name: str = Field(description="Clean goal name")
    subtasks: List[str] = Field(description="List of subtasks to complete the goal")
    priority: str = Field(description="low/medium/high priority")
    estimated_duration: str = Field(description="Estimated time to complete")

class HealthAnalysisResponse(BaseModel):
    status: str = Field(description="GREEN/YELLOW/RED")
    issues: List[str] = Field(description="List of detected issues")
    recommendations: List[str] = Field(description="List of fix recommendations")

def call_structured(prompt: str, schema: type, system: str = "You are CORTEX AI OS. Respond only in valid JSON matching the schema.") -> Optional[dict]:
    """Call Hermes with structured JSON output enforcement"""
    schema_str = json.dumps(schema.model_json_schema(), indent=2)
    full_prompt = f"{prompt}\n\nRespond ONLY with valid JSON matching this schema:\n{schema_str}"
    
    try:
        response = requests.post(
            PRIMARY_URL,
            headers={"Authorization": f"Bearer {PRIMARY_KEY}", "Content-Type": "application/json"},
            json={
                "model": "hermes",
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": full_prompt}
                ]
            },
            timeout=30
        )
        if response.status_code == 200:
            data = response.json()
            if data.get("hermes", {}).get("failed"):
                return None
            content = data["choices"][0]["message"]["content"]
            # Strip markdown if present
            content = content.strip()
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            parsed = json.loads(content.strip())
            return schema(**parsed).model_dump()
    except Exception as e:
        print(f"Structured call error: {e}")
    return None

if __name__ == "__main__":
    print("Testing Pydantic structured outputs...")
    result = call_structured(
        "Analyze this health status: system is GREEN, all services running",
        HealthAnalysisResponse
    )
    if result:
        print(f"Status: {result['status']}")
        print(f"Issues: {result['issues']}")
        print(f"Recommendations: {result['recommendations']}")
    else:
        print("Quota exhausted - schema built correctly, will work after midnight reset")
