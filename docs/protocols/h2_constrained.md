# Protocol H2 (Constrained Instrumentation)  
**Goal:** Deploy the FAST+ThermoPETase salt-bridge design using only essential devices (ATC 96-channel head, ALPS sealer, Cytomat incubators, HiG3 centrifuge) plus benchtop tools.

---

## 0. Planning
1. Update KG (`python scripts/update_pipeline.py --full`) (`README.md:40-137`).  
2. Prioritize mutation combinations from MD outputs (stored separately).

---

## 1. Mutagenesis
1. Prepare PCR mixes manually or with `ATC A_ATC96_1` (10 µL reactions).  
2. DpnI digest 37 °C 1 h.  
3. Purify using spin columns.  
4. Seal plates using `ALPS5000` (165 °C, 2 s) for storage before transformation.

---

## 2. Transformation & Plating
1. Mix 50 µL BL21(DE3) + 5 µL PCR product.  
2. Heat shock 42 °C 45 s; recover 60 min in `Cytomat2C4` (37 °C shake).  
3. Plate on LB-kan; incubate 30 °C in `Cytomat10C`.

---

## 3. Expression/Purification
1. Grow 500 mL auto-induction cultures.  
2. Harvest using `HiG3Centrifuge`.  
3. Purify via Ni-NTA gravity + desalting.

---

## 4. Thermal & Structural Checks
1. ThermoFluor melts (SYPRO Orange).  
2. Submit select variants for DSC and small-angle X-ray (optional).

---

## 5. Semicrystalline Assays
1. **Substrate prep:** Grind bottle-grade PET to powder; confirm crystallinity via DSC.  
2. **Batch reactions:**  
   - 2 µM enzyme, 200 µL buffer, PET disc/powder in PCR tubes.  
   - Seal (ALPS5000) and incubate 65 °C (dry block).  
   - Sample at 0/6/24 h; quantify via HPLC.  
3. **Textile assay:** Place textile strips in 50 mL tubes with 5 mL enzyme solution; incubate 70 °C on orbital shaker.  
4. **Data:** Compute conversion per g PET and retention ratio vs amorphous control.

---

## 6. Reporting
1. Summarize ΔTm vs crystallinity retention; identify variants for scale-up.  
2. Archive raw HPLC traces and DSC files for agent retraining.
