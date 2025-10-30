import json
import pandas as pd
from pathlib import Path
from abc import ABC, abstractmethod
# from google import genai
from openai import OpenAI
import time
import random
import os
import concurrent.futures
from dotenv import load_dotenv

load_dotenv()

# ---------------------- API KEYS ----------------------
OPENROUTE_API_KEY = os.environ.get("OPENROUTE_API_KEY")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# Check if the required key is present
if not OPENROUTE_API_KEY:
    raise ValueError("OPENROUTE_API_KEY not found in .env file. Please add it.")


Evaluator_client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTE_API_KEY,
)


# gemini_client = genai.Client(api_key=keys['gemini'])

# ---------------------- FILE UTILS ----------------------
queries_path = "queries.json"

def detect_file_type(file_path: str) -> str:
    ext = Path(file_path).suffix.lower()
    if ext == '.json':
        try:
            with open(file_path, 'r') as f:
                json.load(f)
                return 'json'
        except:
            pass
    elif ext == '.csv':
        try:
            pd.read_csv(file_path, nrows=1)
            return 'csv'
        except:
            pass
    raise ValueError(f"File {file_path} is neither valid JSON nor CSV")

def read_queries(file_path: str) -> list:
    file_type = detect_file_type(file_path)
    if file_type == 'json':
        with open(file_path, 'r') as f:
            data = json.load(f)
            if isinstance(data, dict):
                data = [data]
            for item in data:
                if not all(k in item for k in ['query', 'ground_truth']):
                    raise ValueError(f"JSON item missing fields: {item}")
            return data
    elif file_type == 'csv':
        df = pd.read_csv(file_path)
        required_cols = [ 'query', 'ground_truth']
        if not all(col in df.columns for col in required_cols):
            raise ValueError(f"CSV missing required columns: {required_cols}")
        return df[required_cols].to_dict('records')

def Save_Responses(responses: list, output_path: str):
    with open(output_path, 'w') as f:
        json.dump(responses, f, indent=4)

# ---------------------- LLM INTERFACE ----------------------
class LLMClient(ABC):
    @abstractmethod
    def chat(self, query: str) -> str:
        pass

class OpenAICompatibleClient(LLMClient):
    def __init__(self, client, model):
        self.client = client
        self.model = model

    def chat(self, query: str, max_retries=5) -> str:
        prompt = (
            "You are a factual QA assistant answering questions based on Indian data. "
            "If the question involves money, assume it refers to Indian Rupees (₹), "
            "Make the response concise and short with no explanation or formatting.\n\n"
            f"Question: {query}"
        )

        if "gpt" in self.model.lower():
            prompt += (
                "Use whatever latest data you have and choose your dataset you think is most prefarable. "
                "I am using you for Benchmarking purpose.So dont reply with questions. Just give the best possible short answer"
            )

        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.0,
                )
                ans = response.choices[0].message.content.strip()
                if ans:
                    return ans

            except Exception as e:
                if any(x in str(e) for x in ["429", "Rate limit", "503", "UNAVAILABLE"]):
                    wait = 2 ** attempt + random.uniform(0, 2)
                    print(f"⚠️ Rate limited or busy ({self.model}). Retrying in {wait:.1f}s...")
                    time.sleep(wait)
                    continue
                raise e

        raise RuntimeError(f"Max retries reached for {self.model} (query: {query})")


class GeminiAdapter(LLMClient):
    def __init__(self, client, model):
        self.client = client
        self.model = model

    def chat(self, query: str, max_retries=5) -> str:
        prompt = (
            "You are a factual QA assistant answering questions based on Indian statistical datasets. "
            "If the question involves money, assume it refers to Indian Rupees (₹), "
            "Make response concise and short with no explanation or formatting."
            f"Question: {query}"
        )

        # For PLFS
        
        print(prompt)


        for attempt in range(max_retries):
            try:
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=prompt,
                )
                answer = response.text.strip()
                
                return answer
            except Exception as e:
                if "429" in str(e) or "UNAVAILABLE" in str(e):
                    wait_time = 5 + random.uniform(0, 3)
                    print(f"⚠️ Rate limited ({self.model}). Retrying in {wait_time:.1f}s...")
                    time.sleep(wait_time)
                    continue
                raise e
        raise RuntimeError(f"Max retries reached for {self.model}")


# ---------------------- INITIALIZE MODEL CLIENTS ----------------------
model_clients = {
    # "claude": OpenAICompatibleClient(openroute_client, "anthropic/claude-haiku-4.5"),
    # "gemini" : OpenAICompatibleClient(openroute_client, "google/gemini-2.5-flash"),
    # "qwen" : OpenAICompatibleClient(openroute_client, "qwen/qwen3-32b"),
    # "llamma": OpenAICompatibleClient(openroute_client, "meta-llama/llama-4-maverick"),
    "gpt" : OpenAICompatibleClient(openroute_client, "openai/gpt-5-mini"),
}

# ---------------------- BENCHMARK LOOP ----------------------
def benchmark(model_clients, queries):
    def run_model(name, client):
        print(f"Running {name}...")
        model_responses = []
        safe_name = name.replace("-", "_")
        output_file = f"./responses/{safe_name}.json"

        for i, q in enumerate(queries):
            if i % 10 == 0:
                print(i)
                # break
            try:
                ans = client.chat(q["query"])
            except Exception as e:
                print(f"❌ Error in {name} for query {i+1}/{len(queries)}: {e}")
                ans = "Error"
                
                Save_Responses(model_responses, output_file)
                print(f"💾 Saved partial responses after error for{name}")
                break

            model_responses.append({
                "query": q["query"],
                "response": ans,
                "ground_truth": q["ground_truth"],
            })

            
            time.sleep(random.uniform(2.0, 4.0))

        Save_Responses(model_responses, output_file)
        print(f"✅ Completed {name}. Final saved to {output_file}")

    # Run models concurrently
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(model_clients)) as executor:
        futures = {executor.submit(run_model, name, client): name for name, client in model_clients.items()}
        for future in concurrent.futures.as_completed(futures):
            name = futures[future]
            try:
                future.result()
            except Exception as e:
                print(f"❌ Uncaught error in {name}: {e}")

    print("🏁 All models done.")


# ---------------------- MAIN ----------------------
if __name__ == "__main__":
    try:
        queries = read_queries(queries_path)
        os.makedirs("responses", exist_ok=True)
        benchmark(model_clients, queries)
    except Exception as e:
        print(f"Error: {e}")
