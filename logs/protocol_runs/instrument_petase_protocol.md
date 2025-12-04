# PETase Activity & Thermostability Improvement Protocol  
*All steps use only the instruments listed in the brief.*

---

## Experimental Workflow  
*(Reference instrument → action → key parameters → justification)*  

| Step | Action | Key Parameters | Instrument(s) | Why it’s appropriate |
|------|--------|----------------|---------------|----------------------|
| **1. Library Generation** | Error‑prone PCR of PETase gene → Gibson assembly into pET‑28a(+) plasmid | PCR: 1 µM primers, 1 U/µL Taq, 1 min/10 °C ramp | – | Standard bench‑top work; no biofoundry instrument required. |
| **2. Transformation & Plating** | Transform *E. coli* BL21(DE3) → spread on LB‑agar + kanamycin | 50 µg/mL kanamycin, 0.5 % agar | – | Conventional plating. |
| **3. Colony Picking** | Pick ~3 000 colonies into 96‑well plates (LB + 50 µg/mL kan + 0.1 % IPTG) | 96‑well format, 200 µL per well | **Singer Instruments PIXL** | • 3000 colony/h throughput.<br>• Brightfield + fluorescence imaging (use GFP‑fused PETase or a fluorescent reporter).<br>• Directly deposits colonies into 96‑well plates for downstream expression. |
| **4. Expression Incubation** | Grow cultures 16–18 h at 37 °C, 5 % CO₂ (optional) | 37 °C, 50 % RH | **Thermo Scientific Cytomat 10 C450 R3 Lift** | • Stores ~210 plates; lift‑based access for high‑throughput.<br>• Precise temperature & humidity control for optimal protein expression. |
| **5. Activity Assay (Room Temp)** | Transfer 50 µL culture to 96‑well assay plate containing 200 µL of 10 µM fluorescent PETase substrate (e.g., PET‑linked 7‑amino‑coumarin) | 37 °C, 2 h incubation | **QuantStudio 7 Pro** (qPCR machine used as a fluorescence plate reader) | • 384‑well capability; multiplex fluorescence detection (up to 6 dyes).<br>• Excitation/emission matched to substrate (e.g., 405 nm/460 nm).<br>• Provides quantitative activity readout without a dedicated plate reader. |
| **6. Thermostability Screening** | Transfer selected top 5 % variants to new 96‑well plates with substrate; incubate at 45 °C for 2 h | 45 °C, 2 h | **Thermo Scientific Cytomat 2 C450‑Lin B1 ToS** | • Linear access, ideal for medium‑throughput assays.<br>• Precise temperature control (ambient + 10 → 50 °C).<br>• CO₂ optional (not needed for enzyme assay). |
| **7. Plate Sealing** | Seal assay plates to prevent evaporation & cross‑contamination | 80 °C heat‑seal, 0.5 mm foil | **Thermo Scientific ALPS 5000 Plate Sealer** | • Seals 96‑ and 384‑well plates in < 10 s.<br>• Heat‑seal ensures airtight seal for fluorescence stability. |
| **8. Long‑Term Storage** | Store sealed plates at 4 °C (short‑term) or –20 °C (long‑term) | 4 °C or –20 °C, 50 % RH | **Thermo Scientific Cytomat SkyLine** | • High‑density storage (250+ plates).<br>• Random‑access shuttle for easy retrieval of selected variants. |
| **9. Data Acquisition** | Read fluorescence from QuantStudio 7 Pro (post‑incubation) | 384‑well read, 6‑channel multiplex | **QuantStudio 7 Pro** | • Same instrument used for assay; no additional plate reader needed.<br>• Provides raw fluorescence units for downstream analysis. |
| **10. Iteration** | Re‑clone top variants → repeat steps 3–9 for 3–5 rounds | – | – | Directed evolution cycle; each round enriches for higher activity & thermostability. |

---

## Computational Workflow  
*(Data handling, analysis, and design – no additional hardware beyond the instruments above)*  

1. **Data Import**  
   - Load raw fluorescence files (CSV) from QuantStudio 7 Pro into Python/R.  
   - Map plate layout to variant IDs.

2. **Normalization & QC**  
   - Subtract background (blank wells).  
   - Normalize to positive control (wild‑type PETase).  
   - Flag outliers (Z‑score > 3).

3. **Statistical Ranking**  
   - Compute activity scores (ΔF/F₀).  
   - Rank variants; select top 5 % for thermostability assay.

4. **Sequence Alignment**  
   - Retrieve plasmid sequences (Sanger or NGS).  
   - Align to wild‑type PETase using MUSCLE.  
   - Identify mutations in top performers.

5. **Predictive Modeling**  
   - Encode mutations as one‑hot vectors.  
   - Train a Random Forest regressor to predict thermostability (ΔTₘ) from sequence features.  
   - Cross‑validate (k‑fold, k = 5).

6. **Structural Mapping**  
   - Build homology model of PETase (e.g., using SWISS‑Model).  
   - Map beneficial mutations onto 3D structure.  
   - Visualize via PyMOL (offline).

7. **Library Design**  
   - Select positions with highest predictive importance.  
   - Design degenerate codons (NNK) for saturation mutagenesis at those sites.  
   - Generate oligos via automated oligo synthesizer (not listed but assumed available).

8. **Validation Loop**  
   - Use QuantStudio 7 Pro data to confirm predictions.  
   - Iterate until desired activity/thermostability thresholds met.

9. **Documentation & Reporting**  
   - Generate markdown reports summarizing variant performance, mutation hotspots, and next‑generation design.  
   - Store all data in a shared repository (e.g., GitHub) for reproducibility.

---

### Summary  
By leveraging the **Singer PIXL** for high‑throughput colony picking, the **Cytomat** incubators for controlled expression and thermostability assays, the **ALPS 5000** for rapid plate sealing, and the **QuantStudio 7 Pro** as a dual qPCR/fluorescence reader, this protocol maximizes throughput while staying within the instrument constraints. The computational workflow ties raw fluorescence data to sequence‑based predictions, enabling iterative directed evolution of PETase for superior activity and thermostability.