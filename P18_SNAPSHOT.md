# P18 snapshot -- BioAgentHub_iBF, 2026-11-18

Made by the P18 storage clean-up so that nothing that exists only on NCSA Delta is lost.
Nothing on Delta was changed to make it; the source stays where it is.

- source: `/taiga/illinois/eng/chbe/zhao5/vikas/iBF/Hmmm/BioAgentHub_iBF`
- in this commit: 454 files, 13.4 MB (code, configs, docs and small results; <= 10 MB per file)
- tracked files deleted in the working tree: 4071
- left out, still on Delta: 28237 files, 1.44 GB

| reason | files | GB |
|---|---:|---:|
| excluded folder | 28233 | 1.43 |
| tracked change, over 10 MB | 1 | 0.02 |
| tracked change, excluded type | 3 | 0.00 |

The 15 largest files left out:

- `.venv_local/lib/python3.9/site-packages/torch/lib/libtorch_cpu.so` (488.9 MB): excluded folder: .venv_local
- `.venv_local/lib/python3.9/site-packages/faiss/_swigfaiss.cpython-39-x86_64-linux-gnu.so` (37.7 MB): excluded folder: .venv_local
- `.venv_local/lib/python3.9/site-packages/faiss/_swigfaiss_avx512.cpython-39-x86_64-linux-gnu.so` (37.0 MB): excluded folder: .venv_local
- `.venv_local/lib/python3.9/site-packages/faiss/_swigfaiss_avx2.cpython-39-x86_64-linux-gnu.so` (36.8 MB): excluded folder: .venv_local
- `.venv_local/lib/python3.9/site-packages/scipy.libs/libopenblasp-r0-23e5df77.3.21.dev.so` (33.0 MB): excluded folder: .venv_local
- `.venv_local/lib/python3.9/site-packages/numpy.libs/libopenblas64_p-r0-15028c96.3.21.so` (33.0 MB): excluded folder: .venv_local
- `.venv_local/lib/python3.9/site-packages/torch/lib/libtorch_python.so` (25.5 MB): excluded folder: .venv_local
- `.venv_local/lib/python3.9/site-packages/tokenizers/tokenizers.cpython-39-x86_64-linux-gnu.so` (17.9 MB): excluded folder: .venv_local
- `.venv_local/lib/python3.9/site-packages/gradio/templates/frontend/assets/Index-33450137.js.map` (16.6 MB): excluded folder: .venv_local
- `workspaces/petase/vector_store/metadata.jsonl` (15.8 MB): tracked change, over 10 MB
- `.venv_local/lib/python3.9/site-packages/torch/bin/test_api` (14.9 MB): excluded folder: .venv_local
- `.venv_local/lib/python3.9/site-packages/cryptography/hazmat/bindings/_rust.abi3.so` (12.8 MB): excluded folder: .venv_local
- `.venv_local/lib/python3.9/site-packages/gradio/node/dev/node_modules/esbuild-wasm/esbuild.wasm` (11.2 MB): excluded folder: .venv_local
- `.venv_local/lib/python3.9/site-packages/torch/bin/test_tensorexpr` (9.0 MB): excluded folder: .venv_local
- `.venv_local/lib/python3.9/site-packages/gradio/templates/frontend/assets/Index-3ddfa2bc.js.map` (8.7 MB): excluded folder: .venv_local
