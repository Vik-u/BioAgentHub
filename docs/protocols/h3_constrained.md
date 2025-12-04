# Protocol H3 (Constrained Instrumentation)  
**Goal:** Evaluate FAST+DuraPETase surface mutations with only core devices (ATC 96-channel head, ALPS sealer, Cytomats, HiG3 centrifuge) and standard benchtop tools.

---

## 0. Preparation
1. Refresh KG ( `python scripts/update_pipeline.py --full` ) to capture new additive/immobilization findings (`README.md:40-137`).  
2. Create design sheet mapping variants to additives.

---

## 1. Library Assembly & Expression
1. Perform sequential site-directed mutagenesis with `ATC A_ATC96_1` (10 µL reactions).  
2. Seal reaction plates with `ALPS5000`.  
3. Transform BL21(DE3), recover in `Cytomat2C4`, plate at 30 °C in `Cytomat10C`.  
4. Express 500 mL auto-induction cultures; purify via Ni-NTA + desalting; record solubility.

---

## 2. Baseline Activity
1. Set up PET disc reactions (2 µM enzyme, 200 µL buffer) in PCR tubes.  
2. Incubate at 50 °C; sample at 0/6/24 h; measure TPA/BHET via HPLC to establish additive-free baseline.

---

## 3. Additive Challenge (Manual)
1. Prepare additive stocks:  
   - Dye cocktail (100 ppm).  
   - 0.1 % Tween-20.  
   - 0.5 M NaCl.  
   - 5 % ethylene glycol.  
2. For each variant/condition:  
   - Combine enzyme + buffer + PET disc + additive in sealed PCR tubes (ALPS5000).  
   - Incubate at 50 °C for 24 h; sample at 0/6/24 h.  
   - Measure product release via HPLC; compute % activity vs control.

---

## 4. Aggregation Monitoring
1. After 24 h exposure, collect 50 µL sample and run DLS (shared instrument).  
2. Optionally run analytical SEC to detect oligomerization.

---

## 5. Immobilization & Reuse
1. Activate silica beads with EDC/NHS (bench-top).  
2. Couple enzyme, wash, and load into 10 mL column.  
3. Circulate PET oligomer solution (1 mL/min) for 2 h; quantify effluent TPA.  
4. Repeat for three cycles, regenerating with buffer between runs.

---

## 6. Reporting
1. Tabulate % activity retained per additive; highlight ≥80 % performers.  
2. Plot immobilized activity vs cycle number to identify stable variants.  
3. Store raw chromatograms and DLS data in ELN with references to device configs.
