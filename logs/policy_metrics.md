| Policy | Mode | Avg FAISS | Avg KG conf | Avg RL reward | Description |
|---|---|---|---|---|---|
| Heuristic RL (no LLM) | plain | 0.653 | n/a | 0.620 | Original SimplePolicy sequence: vector → graph → summarize. |
| PPO Policy | plain | 0.653 | n/a | 0.430 | Stable-Baselines3 PPO checkpoint trained on benchmark questions. |
| Preference RL (RLHF-style) | plain | 0.653 | n/a | 0.710 | Deterministic policy mimicking human preference heuristics. |

**Metric notes**: FAISS avg measures semantic similarity of retrieved evidence; KG conf avg reflects heuristic confidence of graph edges (0–1); RL reward is the cumulative reward assigned to the retrieval policy per episode.