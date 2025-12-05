## FastAPI Retrieval Service Deployment

1. **Activate the project environment**
   ```bash
   cd /path/to/BioAgentHub
   source .venv/bin/activate
   ```

2. **Ensure the corpus artifacts are present**
   ```bash
   python scripts/build_kg_edges.py
   python scripts/build_graph_store.py
   python scripts/build_vector_store.py
   ```

3. **Launch the API**
   ```bash
   uvicorn services.retrieval_service:app --host 0.0.0.0 --port 8000 --reload
   ```

4. **Sample requests**
   ```bash
   curl -X POST http://localhost:8000/vector_search \
     -H "Content-Type: application/json" \
     -d '{"query":"What stabilizes PETase?","top_k":3}'
   ```

5. **Logs**
   - Vector/graph/hybrid calls append to `logs/retrieval_trajectories.jsonl`.
   - RL agent runs log to `logs/rl_agent_runs.jsonl`.

6. **Shutting down**
   - Press `Ctrl+C` in the uvicorn terminal.
