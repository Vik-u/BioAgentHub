# Protocol H3 (Relaxed Instrumentation)  
**Goal:** Apply full automation to engineer FAST-PETase variants with DuraPETase surface-charge tuning for additive tolerance and immobilization, leveraging the device profile in `Devices/workflow_json/LOR51185-25 Illinois-a4S Sealer.json:3`.

---

## 0. Preparation
1. Run `python scripts/update_pipeline.py --full` to update KG with any new additive/immobilization literature (`README.md:40-137`).  
2. Use the agent CLI to pull solvent-tolerance notes into the ELN.

---

## 1. Library Construction
1. **Plate labeling:** `SciPrintMP2` prints target plates.  
2. **Mutagenesis:**  
   - `ATC A_ATC384` sets up combinatorial PCR for modules (charge vs aromatic).  
   - `ATC A_ATC96_1` performs Gibson assembly.  
3. **Automation flow:** Spinnaker moves plates between devices; ALPS sealer locks plates before thermocycling.

---

## 2. Transformation & Colony Handling
1. Dispense cells with `MultidropCombi`.  
2. Add DNA via ATC 96-channel head; heat shock using automated shuttle to heat block.  
3. Recover in `Cytomat2C4` (37 °C, shaking on).  
4. Plate and incubate at 30 °C in `Cytomat10C`.

---

## 3. Expression
1. Automated colony picking into 24-well plates; grow at 30 °C.  
2. Scale to 1 L cultures; purify (IMAC + SEC).  
3. Record yields and note any solubility issues (surface mutations can affect expression).

---

## 4. Additive Challenge Platform
1. **Plate layout:** Use Spinnaker to stage 384-well plates.  
2. **Dispensing:** `ATC A_ATC384` adds enzyme (1 µM) + buffer (100 mM KH₂PO₄, pH 8.0).  
3. **Additives:** Multidrop dispenses stock solutions:  
   - 0.1 % Tween-20, 0.5 M NaCl, 100 ppm textile dye, 5 % ethylene glycol.  
4. **Incubation:** Seal via ALPS5000 and incubate at 50 °C in `Cytomat2C4`.  
5. **Sampling:** Every 6 h, Spinnaker retrieves plates; `ATC A_ATC96_2` transfers aliquots for UHPLC quantification of TPA/BHET.  
6. **Activity metric:** Calculate % activity relative to additive-free control.

---

## 5. Immobilization Workflow
1. **Bead prep:** Automate EDC/NHS activation using `ATC A_ATC96_1`.  
2. **Coupling:** Mix enzyme with activated magnetic beads on a shaker; monitor conjugation by measuring supernatant protein.  
3. **Packed-bed simulation:** Load beads into column; perfuse PET oligomer solution at 1 mL/min; measure effluent TPA.  
4. **Cycle testing:** Run 10 PET film digestions; after each, wash beads and re-measure activity.

---

## 6. Aggregation & Structural QC
1. DLS on each variant ± additives to detect aggregation.  
2. Analytical SEC to confirm monodispersity.  
3. Document if surface mutations alter oligomeric state.

---

## 7. Reporting
1. Plot % activity retention vs additive condition; highlight ≥80 % performers.  
2. Summarize immobilization cycle data.  
3. Feed findings into KG methodology JSON for future reasoning.
