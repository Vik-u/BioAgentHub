# Protocol H2 (Relaxed Instrumentation)  
**Goal:** Engineer FAST variants with ThermoPETase salt-bridge motifs using the full automation stack defined in `Devices/workflow_json/LOR51185-25 Illinois-a4S Sealer.json:3`.

---

## 0. Pre-Run Workflow
1. **KG rebuild** – `python scripts/update_pipeline.py --full` for latest semicrystalline PET insights (`README.md:40-137`).  
2. **MD queue** – Launch in silico constant-pH MD jobs (333 K) to prioritize T140D/N246D/S242T/D246 variants; store results in ELN before cloning.

---

## 1. Automated DNA Construction
1. Label source/destination plates via `SciPrintMP2 A_Labeler`.  
2. Pipetting:  
   - `ATC A_ATC384` prepares PCR mixes for site-saturation at T140/N246 (use 2 µL primer pools, 3 µL template).  
   - `ATC A_ATC96_1` assembles Gibson reactions (5 µL per well).  
3. Sealing with `ALPS5000` (165 °C, 2 s).  
4. Thermocycle on `QuantStudio7Pro`: 98 °C 30 s, 30 cycles (98 °C 10 s, 60 °C 20 s, 72 °C 30 s), 72 °C 5 min.

---

## 2. Automated Transformation
1. Dispense competent BL21(DE3) with `MultidropCombi A_Combi_Shelf` (Valve 1, 40 µL/well).  
2. Add 5 µL DNA via `ATC A_ATC96_2`.  
3. Use `HiG3Centrifuge` for quick spin, then robotic transfer to heat block (Spinnaker).  
4. Recover in SOC within `Cytomat2C4` at 37 °C, shake amplitude 50, frequency 12.  
5. Plate onto LB-kan agar using 96-channel head; incubate at 30 °C in `Cytomat10C`.

---

## 3. Expression & Purification
1. Colony pick with automated picker into 24-deep-well plates.  
2. Grow seeds in `Cytomat2C4` (30 °C, 250 rpm).  
3. Scale to 1 L auto-induction cultures (manual).  
4. Harvest (HiG3Centrifuge) → IMAC/SEC on ÄKTA → buffer exchange to PET assay buffer.

---

## 4. Structural QC
1. nanoDSF + DSC to confirm ΔTm shifts.  
2. SAXS or cryo-EM submission for top clones to verify salt-bridge formation.  
3. Document MD + experimental matches.

---

## 5. Semicrystalline PET Assays
1. **Substrate characterization** – Use DSC to confirm crystallinity (amorphous film vs 30 % pellet vs textile).  
2. **Automated reactor setup** –  
   - `ATC A_ATC96_1` dispenses buffer and enzyme (2 µM).  
   - Insert PET substrate; seal via ALPS5000.  
   - Load into `Cytomat2C4` at 65 °C (update temperature setpoint).  
3. **Sampling** – Every 6 h use Spinnaker to move plates for sampling; analyze by UHPLC for TPA/BHET.  
4. **Fiber rigs** – Mount textile strips in 50 mL baffled tubes, incubate at 70 °C, 250 rpm; collect aliquots for LC-MS.  
5. **Kinetics** – Determine k_cat/K_M on BHET/MHET using plate reader (Abs 240 nm) for correlation.

---

## 6. Data Flow
1. Calculate activity retention ratio (semi-crystalline vs amorphous).  
2. Plot vs ΔTm; identify variants meeting ≥90 % retention at 65 °C for pilot trials.  
3. Feed metrics back into KG (methodology JSON) for future agent runs.
