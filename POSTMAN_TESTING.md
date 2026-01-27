# Testing Different Models in Postman

This guide explains how to test **Claude, LLaMA, Ministral, and Titan** with the Bedrock LLM API using the Postman collection.

---

## 1. What You Need First

1. **API running**
   - Local: `docker-compose up api` or `uvicorn app.main:app --host 0.0.0.0 --port 8000`
   - Base URL: `http://localhost:8000` (or your deployed URL)

2. **AWS credentials**
   - Local: set in `.env` or in Postman/Environment:
     - `AWS_ACCESS_KEY_ID`
     - `AWS_SECRET_ACCESS_KEY`
     - `AWS_REGION` (e.g. `us-east-1`)
   - Production: IAM role on EKS/ECS/EC2 — no keys in Postman.

3. **Postman collection**
   - Import `AI_Review_API_Collection.json`.

---

## 2. Two Ways to Choose the Model

### A) Server default (from .env)

- **LLM_FAMILY** + **LLM_MODEL** in `.env` (or env vars) define the default.
- If the request **does not** send `model`, the server uses this default.

**In Postman:**

- Use requests under **“Chat – Default (uses .env LLM_FAMILY/LLM_MODEL)”**.
- Do **not** put a `model` field in the body.
- To change the default: edit `.env` → set `LLM_FAMILY` and optionally `LLM_MODEL` → restart the API.

### B) Per-request override (best for testing)

- Send **`model`** in the JSON body with a **Bedrock model ID**.
- This overrides the .env default for that request only.

**In Postman:**

- Use the requests under **“Chat – Claude”**, **“Chat – LLaMA”**, **“Chat – Ministral (Mistral)”**, **“Chat – Titan”**.
- They already send `"model": "{{modelClaude}}"`, etc., or an explicit model ID.
- You can change the body’s `model` to any of the IDs below.

---

## 3. Collection Variables (Model IDs)

The collection defines variables you can edit in **Collection → Variables**:

| Variable      | Default value                               | Use for     |
|---------------|---------------------------------------------|------------|
| `baseUrl`     | `http://localhost:8000`                     | API root   |
| `modelClaude` | `anthropic.claude-3-5-sonnet-20241022-v2:0`  | Claude     |
| `modelLlama`  | `meta.llama3-8b-instruct-v1:0`              | LLaMA      |
| `modelMinistral` | `mistral.mistral-small-2402-v1:0`        | Ministral  |
| `modelTitan`  | `amazon.titan-text-express-v1`              | Titan      |

How to test different models in Postman:

1. **Use the pre-built requests**  
   - “Claude – default (Sonnet)”, “LLaMA 8B”, “Ministral Small”, “Titan Express”, etc.  
   - They use `{{modelClaude}}`, `{{modelLlama}}`, etc.

2. **Change the collection variables**  
   - Collection → Variables → edit **Current Value** for `modelClaude`, `modelLlama`, etc.  
   - Example: set `modelClaude` to `anthropic.claude-3-5-haiku-20241022-v1:0` to test Haiku.

3. **Override in the body**  
   - Open a request → Body → raw JSON.  
   - Set `"model": "anthropic.claude-3-5-haiku-20241022-v1:0"` (or any ID from the table below).  
   - Send the request.

---

## 4. Valid Model IDs (for the `model` field)

Use these as values for the `model` key in the request body (or in collection variables).

**Claude**

- `anthropic.claude-3-5-sonnet-20241022-v2:0`
- `anthropic.claude-3-5-haiku-20241022-v1:0`
- `anthropic.claude-3-opus-20240229-v1:0`
- `anthropic.claude-3-sonnet-20240229-v1:0`
- `anthropic.claude-3-haiku-20240307-v1:0`

**LLaMA**

- `meta.llama3-8b-instruct-v1:0`
- `meta.llama3-70b-instruct-v1:0`
- `meta.llama3-1-8b-instruct-v1:0`
- `meta.llama3-1-70b-instruct-v1:0`

**Ministral / Mistral**

- `mistral.mistral-small-2402-v1:0`
- `mistral.mistral-large-2402-v1:0`
- `mistral.mixtral-8x7b-instruct-v0:1`
- `mistral.mistral-7b-instruct-v0:2`

**Titan**

- `amazon.titan-text-express-v1`
- `amazon.titan-text-lite-v1`
- `amazon.titan-text-premier-v1:0`

---

## 5. Step-by-Step: Test a Different Model in Postman

**Option 1 – Change collection variable**

1. Open the collection **AI Review API (Bedrock)**.
2. Right‑click → **Edit** → **Variables**.
3. Set **Current Value** for e.g. `modelClaude` to `anthropic.claude-3-5-haiku-20241022-v1:0`.
4. Save.
5. Run **“Claude – default (Sonnet)”** (or any request that uses `{{modelClaude}}`).  
   It will now call Haiku.

**Option 2 – Edit the request body**

1. Open e.g. **“Claude – default (Sonnet)”**.
2. Go to **Body** → **raw** → **JSON**.
3. Change `"model": "{{modelClaude}}"` to  
   `"model": "anthropic.claude-3-5-haiku-20241022-v1:0"`.
4. Send.  
   That request uses Haiku regardless of variables.

**Option 3 – Use a model from another family**

1. Open any **Chat – …** request.
2. In the body, set `"model": "meta.llama3-70b-instruct-v1:0"` (or another ID from the list).
3. Send.  
   The API uses that Bedrock model for that call only.

---

## 6. Checklist Before Sending

- [ ] API is running (`http://localhost:8000` or your base URL).
- [ ] `baseUrl` in the collection (or environment) matches the API.
- [ ] AWS credentials are available to the server (env vars for local, IAM for prod).
- [ ] For “default” requests: `.env` has `LLM_FAMILY` (and optionally `LLM_MODEL`) set as desired.
- [ ] For “Claude/LLaMA/Ministral/Titan” requests: body includes `"model": "<model-id>"` or uses `{{modelClaude}}` etc. correctly.

---

## 7. Quick Reference

| Goal                         | What to do                                                                 |
|-----------------------------|----------------------------------------------------------------------------|
| Use server default          | Omit `model` in body, or use **“Chat – Default”** requests.                |
| Test another Claude model   | Set `"model": "anthropic.claude-3-5-haiku-20241022-v1:0"` (or edit variable). |
| Test LLaMA                  | Use **“Chat – LLaMA”** requests or set `"model": "meta.llama3-8b-instruct-v1:0"`. |
| Test Ministral/Mistral      | Use **“Chat – Ministral”** or set `"model": "mistral.mixtral-8x7b-instruct-v0:1"`. |
| Test Titan                  | Use **“Chat – Titan”** or set `"model": "amazon.titan-text-express-v1"`.   |
| Switch default for all calls| Change `LLM_FAMILY` / `LLM_MODEL` in `.env` and restart the API.           |
