# Protocol H1 (Relaxed Instrumentation)  
**Goal:** Execute the FAST+HotPETase+ DuraPETase hypothesis with full automation, using the device roster configured in `Devices/workflow_json/LOR51185-25 Illinois-a4S Sealer.json:3`.

---

## 0. Digital & Knowledge Preparation
1. **Refresh KG:** `python scripts/update_pipeline.py --full` to ingest any new PDFs before planning (`README.md:40-137`).  
2. **Agent query:** Use `python app/cli_chat.py --mode llm` with the hypothesis prompt to pull the freshest KG citations for notebooking.  
3. **Sequence planning:** Generate variant list (FAST core + {N233C, S282C, L117Y, Q119Y, W159H, S214H, G165A}) in Benchling; export as CSV for automation scripts.

---

## 1. DNA Assembly (Automated)
1. **SciPrint labeling** – Print 96-well barcode labels for gene fragments with `SciPrintMP2 A_Labeler` (PlateMoveTo = “Sample Plate”) so Spinnaker can recognize plates (`Devices/workflow_json/LOR51185-25 Illinois-a4S Sealer.json:3`).  
2. **Plate setup** – Load donor DNA into hotel positions A_Hotel_1–4; stage destination plates on `SwapStation AB_SwapStation`.  
3. **Liquid handling** –  
   - Run `ATC A_ATC384` for nanoliter mix of primers + template (50 nL primer, 150 nL template, 225 nL master mix).  
   - Switch to `ATC A_ATC96_1` for Gibson assembly (5 µL total per well). Use `GenericMover A_SpinnakerXT` (velocity 90 %, acceleration 90 %) to shuttle plates.  
4. **Sealing** – Apply film with `ALPS5000 B_ALPS_Sealer` at 165 °C, 2 s seal time, 30 mil seal distance, seal force 8 for uniform heating (`Devices/workflow_json/LOR51185-25 Illinois-a4S Sealer.json:3`).  
5. **Thermocycle** – Place plates into `QuantStudio7Pro A_PCR` for Gibson program (50 °C 30 min, 72 °C 10 min).

---

## 2. Transformation & Colony Generation
1. **Competent cells dispenses** – Use `MultidropCombi A_Combi_Shelf` (Valve 1, prime volume 10 µL) to aliquot 40 µL BL21(DE3) cells into chilled plates on `SwapStation BC_SwapStation`.  
2. **DNA mix-in** – Transfer 5 µL assembly product via `ATC A_ATC96_2`.  
3. **Heat shock** – Move plates to `HiG3Centrifuge B_Centrifuge` buckets for brief spin-down, then to heat block (manual) for 42 °C, 45 s; recover in SOC.  
4. **Incubation** – Load recovery plates into `Cytomat2C4 A_Cytomat2C` set to 37 °C, shaking enabled (frequency 12 Hz, amplitude 50) per device profile for 1 h.  
5. **Plating** – Spot 100 µL onto LB+kan agar plates using `ATC A_ATC384`; incubate overnight in `Cytomat10 B_Cytomat10C` at 30 °C to reduce mutation pressure.

---

## 3. Expression & Purification
1. **Starter cultures** – Pick clones with `GenericMover` + colony picking head (if available) into 24-deep-well plates; incubate in `Cytomat2C4` at 30 °C, 250 rpm.  
2. **Scale-up** – Transfer 1 mL seed into 250 mL baffled flasks (manual) with auto-induction media; grow 18 °C overnight.  
3. **Harvest** – Spin 4,000 g, 20 min using `HiG3Centrifuge` (Bucket 2).  
4. **Purification** –  
   - Load lysate onto automated IMAC with ÄKTA Pure (manual programming).  
   - Desalt into 100 mM KH₂PO₄-NaOH pH 8.0; sterile-filter.  
5. **QC** – Run SDS-PAGE and UPLC-MS; record yields in ELN.

---

## 4. Stability Characterization
1. **nanoDSF** – Use Prometheus NT.48 to record unfolding profiles (25–95 °C, 1 °C/min).  
2. **DSC** – Analyze top variants on MicroCal VP-DSC to confirm ΔTm ≥ +10 °C vs FAST.  
3. **Loop integrity** – For the best hits, run 200 ns MD at 343 K to confirm disulfide integrity and aromatic stacking; archive trajectories.

---

## 5. Activity Assays (Automated)
1. **Substrate prep** – Punch Goodfellow films into 6 mm discs; weigh to ±0.1 mg.  
2. **Reaction setup** –  
   - Use `ATC A_ATC96_1` to dispense 200 µL buffer (100 mM KH₂PO₄-NaOH, pH 8.0).  
   - Add 2 µM enzyme and a PET disc per well.  
   - Seal with `ALPS5000` and place into `Cytomat2C4` at 50, 60, 70, and 75 °C (toggle temperature setpoint before run).  
3. **Sampling** – Every 4 h, `GenericMover` retrieves plates, `ATC A_ATC384` withdraws 20 µL, Spinnaker transfers to analysis plate.  
4. **Analytics** – UHPLC (C18, 0.1 % phosphoric acid / MeCN gradient, 0.5 mL/min) to quantify TPA/BHET; confirm by LC-MS for select samples.  
5. **High-load test** – Charge 1 L jacketed reactor with 20 % w/v PET powder; maintain 70 °C with recirculating bath; add 0.5 µM enzyme, stir 350 rpm, sample hourly to ensure linear kinetics.

---

## 6. Data & Follow-up
1. **Property dashboard** – Plot ΔTm vs activity at 70 °C and PET conversion vs time; highlight variants above target line (≥80 % of FAST activity at 70 °C).  
2. **Immobilization readiness** – Flag top variants for Hypothesis H3 workflows.  
3. **Notebook entries** – Store raw data, automation logs, and MD summaries in ELN with cross-links to KG citations.
