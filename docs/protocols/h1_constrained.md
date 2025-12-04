# Protocol H1 (Constrained Instrumentation)  
**Goal:** Execute the FAST+HotPETase+DuraPETase design using only the core instruments listed in `Devices/workflow_json/LOR51185-25 Illinois-a4S Sealer.json:3` (ATC 96-channel heads, Cytomats, HiG3 centrifuge, ALPS sealer) plus standard benchtop equipment.

---

## 0. Preparation
1. Refresh KG with `python scripts/update_pipeline.py --full` (`README.md:40-137`).  
2. Export design table (variant IDs, mutations, primer sets).  
3. Reserve instruments: ATC A_ATC96_1, ALPS5000 sealer, Cytomat2C4 incubator, Cytomat10C, HiG3 centrifuge.

---

## 1. DNA Assembly (Semi-manual)
1. **Primer mix** – Use `ATC A_ATC96_1` to dispense 2 µL primers + 3 µL template into 96-well PCR plates.  
2. **Gibson master mix** – Add 5 µL 2× Gibson to each well; vortex manually.  
3. **Seal** – Run `ALPS5000` at 165 °C, SealTime 2 s, SealForce 8.  
4. **Incubate** – Transfer to thermocycler (50 °C 30 min, 72 °C 10 min).

---

## 2. Transformation
1. Chill competent BL21(DE3) aliquots on ice.  
2. Mix 50 µL cells + 5 µL assembly product with `ATC A_ATC96_1`.  
3. Heat shock manually (42 °C, 45 s).  
4. Recover 60 min at 37 °C, 300 rpm inside `Cytomat2C4` (shaking enabled at frequency 12, amplitude 50).  
5. Plate 100 µL on LB-kan agar using multichannel pipette; incubate at 30 °C in `Cytomat10C`.

---

## 3. Expression & Purification
1. Pick single colonies into 5 mL LB-kan tubes; grow overnight at 30 °C, 250 rpm.  
2. Inoculate 250 mL auto-induction media; incubate 18 °C for 20 h.  
3. Harvest at 4,000 g using `HiG3Centrifuge` (Bucket 2).  
4. Lyse (sonication) and purify via Ni-NTA gravity columns; desalt into 100 mM KH₂PO₄-NaOH pH 8.0.

---

## 4. Thermal QC
1. **ThermoFluor** – Mix 5 µM protein + SYPRO Orange; record melt curves on QuantStudio7Pro (if available) or standalone qPCR (Ramp 1 °C/min).  
2. **DSC (shared instrument)** – Submit top 4 variants for VP-DSC runs to confirm ΔTm ≥ +10 °C.

---

## 5. Activity Assays
1. Prepare PET discs (6 mm) and 20 % w/v PET powder stocks.  
2. For each variant:  
   - Combine 2 µM enzyme + disc + 200 µL buffer in PCR tubes.  
   - Seal with ALPS5000; incubate at 50/60/70 °C using dry-block heaters.  
   - At defined intervals (0, 6, 12, 24 h) withdraw 20 µL, quench at 90 °C 5 min, centrifuge 10,000 g 5 min.  
   - Analyze TPA/BHET via HPLC (0.1 % H₃PO₄/MeCN gradient).  
3. Run 50 mL conical reactions with 10 % PET powder at 70 °C on orbital shaker to assess high-load performance.

---

## 6. Documentation
1. Log all setpoints (ALPS, Cytomat, HiG3) referencing device configuration lines for traceability.  
2. Summarize ΔTm vs activity at 70 °C; flag variants reaching ≥80 % FAST activity for downstream immobilization studies.
