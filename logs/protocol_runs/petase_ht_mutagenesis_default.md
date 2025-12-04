## Experimental Workflow

**Step 1 – Library Design & Construction**  
Action: Generate a combinatorial PETase library enriched for thermostability and activity.  
Detailed Instructions:  
1. **Template**: Use the PETase gene from *Ideonella sakaiensis* (accession: WP_011398595).  
2. **Mutagenesis Strategy**:  
   - **Error‑prone PCR** (EP-PCR) to introduce random mutations (target 1–3 mutations per gene).  
   - **Site‑saturation mutagenesis** at positions 171, 241, 260, 275, 292 (key residues for stability and activity) using NNK codons.  
3. **PCR Conditions** (EP-PCR):  
   - 1 µL template DNA (10 ng/µL)  
   - 0.2 µM dNTPs (each)  
   - 1 U Taq DNA polymerase (high‑error)  
   - 1 mM MnCl₂, 0.5 mM MgCl₂  
   - 30 cycles: 98 °C 30 s, 55 °C 30 s, 72 °C 1 min/kb.  
4. **Golden Gate Assembly**:  
   - Use BsaI‑cut plasmid backbone pET‑28a(+) with N‑terminal His₆‑tag and C‑terminal Flag‑tag (as in [1]).  
   - Assemble 1 µL of each PCR product with 1 µL of backbone, 1 U BsaI, 1 U T4 DNA ligase, 1× CutSmart buffer, 37 °C 1 h, 80 °C 5 min.  
5. **Transformation**:  
   - Transform 50 µL chemically competent *E. coli* BL21(DE3) via heat shock (42 °C, 45 s).  
   - Plate on LB‑agar + 50 µg/mL kanamycin.  
6. **Library Size**: Aim for ≥10⁶ colonies (≥10⁵ unique variants).  

Rationale: Random mutagenesis coupled with targeted saturation at key residues maximizes exploration of sequence space while focusing on positions known to influence thermostability and catalytic efficiency [1].  
Next Step Trigger: Confirmation of library diversity by colony PCR and sequencing of 96 random clones.

---

**Step 2 – High‑Throughput Expression Screening**  
Action: Express library variants in 96‑well format and assess soluble protein yield.  
Detailed Instructions:  
1. **Inoculation**: Pick 96 colonies into 200 µL LB + 50 µg/mL kanamycin in a deep‑well 96‑plate.  
2. **Growth**: 37 °C, 200 rpm, 4 h.  
3. **Induction**: Add IPTG to 0.8 mM (final) and incubate 18 h at 18 °C (as in [1]).  
4. **Harvest**: Centrifuge 5 min, 4,000 × g, 4 °C.  
5. **Cell Lysis**: Resuspend pellet in 500 µL lysis buffer (50 mM Tris‑HCl pH 8.0, 300 mM NaCl, 10 mM imidazole, 1 mM PMSF).  
6. **Sonication**: 3 × 10 s pulses, 30 % amplitude, ice bath.  
7. **Clarification**: 10 min, 12,000 × g, 4 °C.  
8. **Protein Quantification**: Use Coomassie Bradford assay (1 µL sample, 200 µL dye, 5 min, 595 nm).  

Rationale: Low‑temperature induction enhances proper folding and solubility, while the His₆‑tag allows rapid purification and quantification [1].  
Next Step Trigger: Selection of top 10% soluble expression clones for purification.

---

**Step 3 – Affinity Purification & Tag Removal**  
Action: Purify selected variants via IMAC and remove tags if necessary.  
Detailed Instructions:  
1. **Ni‑NTA Spin Columns** (Qiagen):  
   - Equilibrate with 10 mL wash buffer (50 mM Tris‑HCl pH 8.0, 300 mM NaCl, 10 % glycerol, 20 mM imidazole).  
   - Load 1 mL clarified lysate, wash 3 × 1 mL, elute 3 × 0.5 mL with 250 mM imidazole.  
2. **Tag Cleavage (optional)**:  
   - Add TEV protease (1:50 protease:protein) in cleavage buffer (50 mM Tris‑HCl pH 8.0, 150 mM NaCl, 1 mM DTT).  
   - Incubate 4 h at 4 °C.  
3. **Second IMAC**: Remove His‑tagged TEV and uncleaved protein.  
4. **Buffer Exchange**: Dialyze into assay buffer (50 mM Tris‑HCl pH 8.0, 150 mM NaCl).  

Rationale: IMAC provides high purity and the glycerol in wash buffer stabilizes the enzyme during purification [2].  
Next Step Trigger: Concentration to 1 mg/mL and storage at 4 °C.

---

**Step 4 – Activity Assay (High‑Throughput)**  
Action: Measure PETase activity using p‑NPA chromogenic substrate in 96‑well plates.  
Detailed Instructions:  
1. **Assay Buffer**: 50 mM Tris‑HCl pH 8.0, 150 mM NaCl.  
2. **Reaction Setup** (per well):  
   - 50 µL enzyme (0.1 mg/mL)  
   - 50 µL 100 µM p‑NPA in assay buffer.  
3. **Incubation**: 20 min at 24 °C (unless indicated).  
4. **Readout**: Measure absorbance at 400 nm (plate reader).  
5. **Controls**: Include wild‑type PETase and buffer blank.  

Rationale: p‑NPA hydrolysis provides a rapid, quantitative readout of esterase activity, directly comparable to literature values [1].  
Next Step Trigger: Rank variants by activity; select top 5 for thermostability testing.

---

**Step 5 – Thermostability Assessment (Differential Scanning Fluorimetry)**  
Action: Determine melting temperature (Tm) of selected variants.  
Detailed Instructions:  
1. **Sample Prep**: 10 µL enzyme (0.5 mg/mL) in 96‑well PCR plate.  
2. **Add 0.3 µL 75× SYPRO Orange (final 1×).**  
3. **Thermal Gradient**: 25–95 °C, 0.5 °C/min, 1 s hold per step.  
4. **Data Acquisition**: Fluorescence (excitation 470 nm, emission 570 nm).  
5. **Tm Calculation**: First derivative of fluorescence vs. temperature.  

Rationale: SYPRO Orange DMSO‑free dye provides accurate Tm shifts; the protocol aligns with the method used in [2].  
Next Step Trigger: Identify variants with Tm ≥ 70 °C and activity ≥ 1.5× WT.

---

**Step 6 – PET Degradation Assay**  
Action: Quantify terephthalic acid (TPA) release from PET film.  
Detailed Instructions:  
1. **PET Substrate**: 10 mg amorphous PET film (0.5 mm thick).  
2. **Reaction**: 1 mL enzyme (0.1 mg/mL) in 50 mM Tris‑HCl pH 8.0, 150 mM NaCl, 0.5 M NaCl (to enhance activity per [1]).  
3. **Incubation**: 24 h at 24 °C with gentle shaking (200 rpm).  
4. **Sampling**: 200 µL aliquot, centrifuge 10 min, 12,000 × g.  
5. **TPA Quantification**: HPLC with C18 column, 0.1 M NaOH mobile phase, detection at 240 nm.  
6. **Calibration**: Standard curve 0–1 mM TPA.  

Rationale: Direct measurement of TPA provides a functional readout of PET hydrolysis, correlating with industrial relevance [3].  
Next Step Trigger: Select top 3 variants for scale‑up and detailed kinetic analysis.

---

**Step 7 – Scale‑Up & Kinetic Characterization**  
Action: Produce selected variants in 1 L culture and determine kinetic parameters.  
Detailed Instructions:  
1. **Culture**: 1 L TB medium + 50 µg/mL kanamycin, 0.8 mM IPTG, 18 h at 18 °C.  
2. **Purification**: Same IMAC protocol, final buffer 50 mM Tris‑HCl pH 8.0, 150 mM NaCl.  
3. **Kinetic Assay**:  
   - Substrate: p‑NPA (0.05–5 mM).  
   - Measure initial rates at 24 °C, 400 nm.  
   - Fit to Michaelis–Menten equation to obtain Kₘ and k_cat.  

Rationale: Large‑scale production ensures sufficient material for detailed kinetic studies, enabling comparison with literature values [1].  
Next Step Trigger: Final selection of engineered PETase for industrial application.

---

## Computational Workflow

**Step 1 – Sequence Analysis & Mutation Prioritization**  
Action: Identify conserved residues and potential stabilizing mutations.  
Detailed Instructions:  
1. **Multiple Sequence Alignment**: Use Clustal Omega on 50 PETase homologs.  
2. **Conservation Scoring**: Compute Shannon entropy; flag residues with entropy < 0.5.  
3. **Mutation Library Design**:  
   - For each low‑entropy residue, generate all 19 possible substitutions.  
   - Filter for mutations predicted to increase hydrophobic packing or introduce salt bridges.  

Rationale: Conserved residues are likely critical for structure; targeted mutations at these sites can enhance stability without compromising activity [1].  
Next Step Trigger: Input mutation list into Rosetta design pipeline.

---

**Step 2 – Homology Modeling & Active‑Site Mapping**  
Action: Build 3D models of PETase variants.  
Detailed Instructions:  
1. **Template**: PDB 6N4B (PETase crystal structure).  
2. **Modeling Software**: MODELLER v9.25.  
3. **Parameters**: 10 models per variant, select lowest DOPE score.  
4. **Active‑Site Identification**: Use CASTp to locate catalytic triad (Ser160, His237, Asp206).  

Rationale: Accurate structural models are essential for downstream stability predictions and docking studies [2].  
Next Step Trigger: Submit models to FoldX for ΔΔG calculations.

---

**Step 3 – Stability Prediction (FoldX)**  
Action: Estimate ΔΔG of unfolding for each mutation.  
Detailed Instructions:  
1. **Command**: `foldx --command=RepairPDB --pdb=variant.pdb`  
2. **Mutation Analysis**: `foldx --command=BuildModel --pdb=variant.pdb --mutant-file=individual_list.txt`  
3. **Output**: ΔΔG values; retain mutations with ΔΔG < –1.0 kcal/mol.  

Rationale: FoldX provides rapid, reliable estimates of thermodynamic stability changes, guiding selection of stabilizing mutations [3].  
Next Step Trigger: Combine stabilizing mutations into combinatorial libraries.

---

**Step 4 – Molecular Docking of PET Oligomers**  
Action: Assess binding affinity of PETase variants to PET oligomers.  
Detailed Instructions:  
1. **Ligand Preparation**: Generate PET dimer (PET₂) using Avogadro; optimize geometry with Gaussian 16 (B3LYP/6‑31G*).  
2. **Docking Software**: AutoDock Vina 1.2.3.  
3. **Grid Box**: Center on catalytic serine; size 30 Å³.  
4. **Parameters**: 20 runs per variant, exhaustiveness = 8.  
5. **Scoring**: Record binding energy; select variants with ΔG ≤ –7 kcal/mol.  

Rationale: Docking predicts how mutations affect substrate positioning, correlating with catalytic efficiency [1].  
Next Step Trigger: Integrate docking scores with stability predictions to rank variants.

---

**Step 5 – Molecular Dynamics (MD) Simulation**  
Action: Validate stability of top variants in explicit solvent.  
Detailed Instructions:  
1. **Software**: GROMACS 2024.2.  
2. **Force Field**: AMBER99SB‑ILDN for protein, GAFF for PET₂.  
3. **System Setup**: Solvate in TIP3P water, add 150 mM NaCl.  
4. **Equilibration**: 100 ps NVT, 100 ps NPT.  
5. **Production Run**: 200 ns, 2 fs timestep, PME for long‑range electrostatics.  
6. **Analysis**: RMSD, RMSF, hydrogen bond occupancy, solvent accessible surface area.  

Rationale: MD provides dynamic insight into protein flexibility and substrate interactions, confirming computational predictions [2].  
Next Step Trigger: Select variants with stable RMSD (< 2 Å) and favorable interaction profiles.

---

**Step 6 – In Silico Library Generation for Biofoundry**  
Action: Translate computationally prioritized mutations into a synthetic DNA library.  
Detailed Instructions:  
1. **Codon Optimization**: Use Benchling codon optimizer for *E. coli* BL21(DE3).  
2. **Oligo Design**: For each mutation, design 60‑mer oligos with NNK at target codon.  
3. **Assembly**: Golden Gate with BsaI overhangs; include 5′/3′ homology arms for plasmid backbone.  
4. **Automation**: Program Opentrons OT‑2 to dispense reagents; use 96‑well format.  

Rationale: Golden Gate allows rapid, scarless assembly of large libraries, compatible with high‑throughput screening [3].  
Next Step Trigger: Proceed to experimental workflow Step 1.

---