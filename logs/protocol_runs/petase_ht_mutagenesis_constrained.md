# PETase Engineering & Screening Protocol  
**Goal:** Generate a high‑throughput pipeline that produces PETase variants with improved catalytic activity and thermostability, using only the instruments listed below.  

> **Instruments**  
> 1. Applied Biosystems QuantStudio 7 Pro (qPCR/RT‑qPCR)  
> 2. Thermo Scientific ALPS 5000 Plate Sealer  
> 3. Thermo Scientific Cytomat 10 C450 R3 Lift (automated incubator)  
> 4. Thermo Scientific Cytomat 2 C450‑Lin B1 ToS (automated incubator)  
> 5. Thermo Scientific Cytomat SkyLine (storage/temperature‑controlled rack)  

> **Plate formats** – 96‑well (qPCR, expression) and 384‑well (mutagenesis library, activity assay).  
> **Dispensing** – Manual pipetting or a benchtop liquid‑handling robot (not listed, but assumed available in the biofoundry).  

---

## Experimental Workflow  

| Step | Action | Key Parameters | Instrument(s) | Why It’s Appropriate |
|------|--------|----------------|---------------|-----------------------|
| **1. Library Design & Synthesis** | In silico design of a focused mutagenesis library (e.g., error‑prone PCR, saturation mutagenesis at hotspot residues). | Target mutation rate: 1–3 nt per kb; codon‑optimized for *E. coli*. | *Computational* (Rosetta, PyRosetta, or machine‑learning model). | Not an instrument step – sets the foundation for the downstream high‑throughput workflow. |
| **2. Plasmid Construction** | Clone each mutant into a high‑copy vector (pET‑28a) with a His‑tag. | 1 µg plasmid per 96‑well reaction; 2 h ligation at 16 °C. | *Manual* or *robotic* plasmid prep (not listed). | Enables uniform expression across the library. |
| **3. Transformation & Starter Cultures** | Transform *E. coli* BL21(DE3) with each plasmid in 96‑well format. | 200 µL LB + 50 µg/mL kanamycin; 37 °C, 1 h. | **Cytomat 10 C450 R3 Lift** – 37 °C, 1 h incubation. | Rapid, uniform growth; the Cytomat’s fast access (<10 s) keeps the temperature stable for all wells. |
| **4. Expression Induction** | Induce protein expression with IPTG. | 0.5 mM IPTG; 30 °C, 4 h. | **Cytomat 10** – 30 °C, 4 h. | Lower temperature improves folding; Cytomat’s precise temperature control ensures consistent induction across the library. |
| **5. Cell Harvest & Lysis** | Harvest cells by centrifugation (4000 × g, 10 min). Resuspend in lysis buffer (50 mM Tris‑HCl pH 8.0, 300 mM NaCl, 10 mM imidazole). Lyse by sonication or freeze‑thaw. | 1 mL per well. | *Manual* or *robotic* lysis (not listed). | Standard lysis protocol; no instrument restriction. |
| **6. Heat‑Selection for Thermostability** | Incubate lysate at 60 °C for 30 min to denature non‑thermostable variants. | 60 °C, 30 min. | **Cytomat 2 C450‑Lin B1 ToS** – 60 °C, 30 min. | Cytomat 2’s tight temperature control (±0.5 °C) ensures selective survival of thermostable enzymes. |
| **7. Clarification & Storage** | Centrifuge (12,000 × g, 10 min) to remove precipitate. Aliquot supernatant into 384‑well plates. | 200 µL per well. | **Cytomat SkyLine** – 4 °C storage, 48 h. | SkyLine’s low‑temperature, humidity‑controlled environment preserves enzyme activity for downstream assays. |
| **8. PET Substrate Preparation** | Prepare PET film or micro‑crystalline PET (mPET) in 384‑well plates. | 10 µg/mL PET in 50 mM phosphate buffer pH 7.4; 200 µL per well. | *Manual* or *robotic* dispensing (not listed). | Uniform substrate loading is critical for comparative activity assays. |
| **9. Enzyme Activity Assay** | Add 10 µL of clarified lysate to each PET well. Incubate at various temperatures (30, 40, 50, 60 °C). | 30–60 °C, 2 h. | **Cytomat 2** – programmable temperature ramp; 30–60 °C, 2 h. | Cytomat 2’s ability to hold multiple temperature points simultaneously allows high‑throughput thermostability profiling. |
| **10. Reaction Termination & Sealing** | Stop reaction by adding 50 µL of 0.1 M NaOH. Seal plates to prevent evaporation. | 50 µL NaOH; seal at 80 °C for 30 s. | **ALPS 5000 Plate Sealer** – 80 °C, 30 s, 384‑well. | ALPS provides rapid, uniform sealing with minimal contamination risk, essential for downstream qPCR or spectrophotometric readouts. |
| **11. Product Quantification (qPCR‑based)** | Quantify released terephthalic acid (TPA) or mono‑ethylene terephthalate (MET) by derivatization to a DNA‑compatible reporter, then amplify by RT‑qPCR. | 1 µL of derivatized sample per 10 µL qPCR mix; 40 cycles (95 °C 15 s, 60 °C 1 min). | **QuantStudio 7 Pro** – 384‑well qPCR. | qPCR offers nanomolar sensitivity and high throughput; the QuantStudio’s 384‑well format matches the assay plate, enabling simultaneous measurement of all variants. |
| **12. Data Acquisition & Normalization** | Export Ct values; calculate ΔCt relative to a reference (wild‑type PETase). | ΔCt = Ct_variant – Ct_wild‑type. | **QuantStudio software** | Provides automated data export and basic statistical analysis. |
| **13. Hit Selection & Secondary Validation** | Rank variants by ΔCt (lower Ct = higher activity). Select top 10 for secondary assays (e.g., HPLC, mass spectrometry). | Top 10 variants. | *Manual* or *robotic* secondary assays (not listed). | Ensures that hits are reproducible and not artifacts of the qPCR assay. |

---

## Computational Workflow  

| Step | Action | Key Parameters | Tools / Software | Why It’s Appropriate |
|------|--------|----------------|------------------|-----------------------|
| **1. Mutagenesis Library Design** | Use Rosetta or a deep‑learning model (e.g., AlphaFold‑based stability predictor) to generate a focused library. | Target residues: active‑site, surface loops, and known thermostability hotspots. | Rosetta, PyRosetta, or custom Python scripts. | Generates a diverse yet manageable library for high‑throughput screening. |
| **2. In Silico Stability Prediction** | Predict ΔΔG for each mutant at 60 °C. | Cut‑off: ΔΔG < 2 kcal/mol. | FoldX, Rosetta ddG, or machine‑learning model. | Filters out destabilizing mutations before wet‑lab work. |
| **3. qPCR Data Analysis** | Import Ct data into QuantStudio software; perform baseline correction, efficiency calculation, and ΔCt normalization. | Efficiency > 90 %. | QuantStudio Analysis Suite. | Provides reliable quantitative activity metrics. |
| **4. Activity & Thermostability Modeling** | Fit activity vs. temperature data to a Boltzmann or Arrhenius model to extract activation energy and optimum temperature. | Non‑linear regression. | GraphPad Prism or Python (SciPy). | Quantifies thermostability improvements. |
| **5. Machine‑Learning Hit Prioritization** | Train a random‑forest or gradient‑boosting model on the activity data to predict future hits. | Features: ΔΔG, residue identity, solvent accessibility. | scikit‑learn, TensorFlow. | Accelerates library refinement by focusing on promising mutations. |
| **6. Data Integration & Reporting** | Compile all data into a relational database (e.g., SQLite) and generate a dashboard (e.g., Jupyter Notebook). | Tables: plasmid ID, sequence, ΔΔG, ΔCt, kinetic parameters. | Jupyter, Pandas, SQLAlchemy. | Enables rapid decision‑making and reproducibility. |
| **7. Validation Pipeline** | Cross‑validate top hits with in‑silico MD simulations at 60 °C to confirm structural stability. | 100 ns MD, explicit solvent. | GROMACS or AMBER. | Provides mechanistic insight into thermostability. |

---

### Analytical Instruments for Validation (Not Listed but Recommended)

- **Plate Reader (e.g., BioTek Synergy)** – for absorbance or fluorescence readouts of PET degradation products.  
- **HPLC or LC‑MS** – to quantify TPA/MET directly.  
- **Circular Dichroism (CD) Spectrometer** – to assess secondary‑structure stability.  

> **Note:** While these instruments are not part of the mandatory list, they are essential for confirming the biochemical performance of the engineered PETase variants. If unavailable, the qPCR‑based assay described above provides a surrogate activity readout that can be correlated with downstream orthogonal assays.

---

### Summary

This protocol leverages the **QuantStudio 7 Pro** for high‑throughput, sensitive activity measurement; the **ALPS 5000 Plate Sealer** for rapid, contamination‑free sealing of assay plates; the **Cytomat 10** for uniform expression incubation; the **Cytomat 2** for precise thermostability selection and activity assays; and the **Cytomat SkyLine** for long‑term storage of plasmids and enzymes. The computational workflow integrates in‑silico design, data analysis, and machine‑learning‑driven hit prioritization, ensuring a rapid, iterative cycle of PETase optimization.