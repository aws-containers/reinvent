from .test_mcp_gateway import run_agent

from fastapi import FastAPI

app = FastAPI()

@app.post("/prompt")
async def handle_prompt(request: dict) -> dict:
    result = run_agent(request["text"])
    return {"text": f"{result}"}

def run_server():
    print("starting agent on endpoint /prompt, send a http post with json field text that includes input prompt")
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3000)
# This is how you call the server using curl
# curl -s -X POST http://localhost:3000/prompt -H "Content-Type: application/json" -d '{"text":"Hi, can you list all tools available to you"}' | jq -r .text

if __name__ == "__main__":
    run_server()
