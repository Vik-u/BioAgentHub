## Experimental Workflow

**Step 1 – Library Construction**  
Action: Generate a diverse mutant library of the PETase gene using error‑prone PCR (EP-PCR) and site‑saturation mutagenesis at positions predicted to influence thermostability.  
Detailed Instructions:  
- **Template**: 1 µg of plasmid pET‑PETase (His‑tagged, C‑terminal).  
- **EP‑PCR**: 30 cycles, 98 °C 10 s, 55 °C 30 s, 72 °C 30 s; use 1 µM dNTPs, 0.5 U Taq, 1 mM MgCl₂, 0.1 % DMSO, 0.5 mM MnCl₂ to increase mutation rate (~1–2 % per kb).  
- **Site‑saturation**: Target 10 residues (e.g., positions 30, 45, 78, 112, 145, 167, 189, 210, 234, 260) with NNK codons using PCR primers (25 µM each).  
- **PCR product purification**: 1 % agarose gel, excise 1 kb band, extract with QIAquick Gel Extraction Kit.  
- **Assembly**: Gibson Assembly (NEBuilder HiFi DNA Assembly Master Mix) with linearized pET vector (cut with NdeI/XhoI). 1 µL of insert, 2 µL of vector, 1 µL of Gibson mix, 37 °C 1 h.  
- **Transformation**: 50 µL chemically competent *E. coli* BL21(DE3), 30 min on ice, 42 °C 45 s, 4 °C 2 min, recover 1 h in LB + 50 µg/mL kanamycin.  
Rationale: EP-PCR introduces random mutations that can enhance stability, while site‑saturation focuses on residues likely to affect folding or core packing [1].  
Next Step Trigger: Colony screening for growth at 37 °C and preliminary activity assay.

---

**Step 2 – High‑Throughput Expression & Purification**  
Action: Express and purify mutant PETase variants in 96‑well format for rapid activity screening.  
Detailed Instructions:  
- **Culture**: Inoculate 200 µL LB + 50 µg/mL kanamycin per well, 37 °C, 200 rpm, 4 h.  
- **Induction**: Add IPTG to 0.5 mM, 18 °C, 16 h (to favor proper folding).  
- **Harvest**: Centrifuge 5,000 × g, 5 min, 4 °C, discard supernatant.  
- **Lysis**: Resuspend pellet in 500 µL binding buffer (50 mM Tris‑HCl pH 8.0, 300 mM NaCl, 10 mM imidazole). Lyse with 0.1 mm glass beads, 3 × 30 s vortex, 4 °C.  
- **Clarify**: 10,000 × g, 10 min, 4 °C.  
- **Affinity Capture**: Load 200 µL clarified lysate onto 50 µL Ni‑NTA magnetic beads (pre‑equilibrated). Incubate 30 min, 4 °C, gentle rotation.  
- **Wash**: 3 × 200 µL wash buffer (50 mM Tris‑HCl pH 8.0, 300 mM NaCl, 20 mM imidazole).  
- **Elution**: 200 µL elution buffer (50 mM Tris‑HCl pH 8.0, 300 mM NaCl, 250 mM imidazole).  
- **Buffer Exchange**: Desalt into assay buffer (50 mM Tris‑HCl pH 8.0, 0.5 M NaCl) using Zeba Spin Desalting Columns (7 kDa MWCO).  
Rationale: The His‑tag purification protocol is adapted from the stableIsPETase study [1] and yields sufficient enzyme for activity assays.  
Next Step Trigger: Activity screening using p‑NPA assay.

---

**Step 3 – Thermostability‑Assisted Activity Screening**  
Action: Screen purified variants for PETase activity at elevated temperatures (50–60 °C) using a chromogenic p‑NPA assay.  
Detailed Instructions:  
- **Assay Setup**: In a 96‑well plate, add 50 µL of enzyme (final concentration 0.05 mg/mL) to 50 µL of 100 µM p‑NPA in 50 mM Tris‑HCl pH 8.0, 0.5 M NaCl.  
- **Incubation**: 50 °C, 20 min, 200 rpm.  
- **Stop Reaction**: Add 50 µL of 10 % (w/v) Na₂CO₃.  
- **Readout**: Measure absorbance at 400 nm (A₄₀₀) on a plate reader.  
- **Controls**: Include wild‑type PETase, buffer only, and heat‑denatured enzyme.  
- **Data Analysis**: Calculate relative activity (A₄₀₀ of variant / A₄₀₀ of WT).  
Rationale: The p‑NPA assay provides a rapid, quantitative measure of esterase activity and is compatible with high‑temperature conditions, as demonstrated in the salt‑leveraged PETase study [2].  
Next Step Trigger: Select top 10% performers for sequencing and further rounds.

---

**Step 4 – Sequencing & Hit Confirmation**  
Action: Sequence plasmids from top performers and confirm mutations.  
Detailed Instructions:  
- **Plasmid Prep**: Miniprep (Qiagen QIAprep) from 1 mL overnight culture.  
- **PCR Amplification**: 1 µL plasmid, 10 µL 2× Phusion Master Mix, 0.5 µM primers flanking PETase, 30 cycles.  
- **Sanger Sequencing**: Send PCR product to core facility.  
- **Analysis**: Align sequences to WT, identify mutations.  
Rationale: Confirming mutations ensures that observed activity changes are due to engineered variants, not plasmid contamination.  
Next Step Trigger: Design next‑generation library incorporating beneficial mutations.

---

**Step 5 – Iterative Directed Evolution**  
Action: Combine beneficial mutations into a new library (e.g., combinatorial saturation at 3–5 positions) and repeat Steps 1–4.  
Detailed Instructions:  
- **Library Design**: Use degenerate codons (NNK) at selected positions, generate 10⁴–10⁵ variants.  
- **Transformation & Screening**: Follow Steps 1–4.  
- **Convergence**: After 3–4 rounds, select variants with >5‑fold activity at 55 °C and >10‑fold thermostability (half‑life > 4 h).  
Rationale: Iterative rounds of mutation and selection are standard for evolving enzymes with enhanced thermostability [3].  
Next Step Trigger: Final characterization of lead variant.

---

**Step 6 – Scale‑Up & PET Degradation Assay**  
Action: Produce lead variant at gram scale and test PET film degradation.  
Detailed Instructions:  
- **Expression**: 1 L LB + 50 µg/mL kanamycin, 18 °C, 16 h, IPTG 0.5 mM, 18 °C, 16 h.  
- **Purification**: Large‑scale Ni‑NTA chromatography (HisTrap HP, GE).  
- **PET Film**: 0.5 mm PET film, 1 cm², pre‑washed with ethanol, dried.  
- **Incubation**: 50 °C, 0.1 mg/mL enzyme, 50 mM Tris‑HCl pH 8.0, 0.5 M NaCl, 24 h, 200 rpm.  
- **Analysis**: Measure released terephthalic acid (TPA) by HPLC (C18 column, 0.1 % TFA in water/ACN).  
Rationale: Demonstrates practical PET degradation capability of evolved PETase under thermostable conditions [3].  
Next Step Trigger: Publication and potential industrial application.

---

## Computational Workflow

**Step 1 – Structural Modeling & Validation**  
Action: Generate a high‑confidence 3D model of the PETase scaffold for in silico mutagenesis.  
Detailed Instructions:  
- **Software**: AlphaFold2 (ColabFold) with default parameters.  
- **Input**: PETase amino‑acid sequence (WT).  
- **Output**: PDB file, pLDDT scores.  
- **Validation**: Use MolProbity to assess Ramachandran statistics; ensure core residues are well‑packed.  
Hardware: GPU (NVIDIA RTX 3090) or Google Colab Pro.  
Rationale: Accurate structural models are essential for predicting stabilizing mutations [1].  
Next Step Trigger: Identification of mutation hotspots.

---

**Step 2 – Thermostability Prediction**  
Action: Predict the effect of point mutations on ΔΔG of unfolding.  
Detailed Instructions:  
- **Software**: FoldX 5.0 (BuildModel command).  
- **Parameters**: `--pdb <model.pdb> --mutant-file <mutations.txt> --command BuildModel --iterations 5`.  
- **Mutation Library**: Generate all single‑site mutations at 20 surface residues (Ala→all 20).  
- **Output**: ΔΔG values; rank mutations with ΔΔG < –1 kcal/mol (stabilizing).  
Hardware: 8‑core CPU, 32 GB RAM.  
Rationale: FoldX provides rapid ΔΔG estimates correlating with experimental thermostability [2].  
Next Step Trigger: Selection of top 10 stabilizing mutations.

---

**Step 3 – Combinatorial Library Design**  
Action: Design a focused combinatorial library incorporating the most stabilizing mutations.  
Detailed Instructions:  
- **Software**: Rosetta Design (ddG_monomer).  
- **Parameters**: `-ddg:scorefile beta_nov16 -ddg:iterations 2000 -ddg:output_prefix design`.  
- **Constraints**: Limit to 3–5 positions, use NNK codons.  
- **Output**: List of combinatorial variants with predicted ΔΔG.  
Hardware: 16‑core CPU, 64 GB RAM.  
Rationale: Rosetta’s ddG calculations capture cooperative effects among multiple mutations [3].  
Next Step Trigger: Prioritization of variants for experimental synthesis.

---

**Step 4 – In Silico Screening for Substrate Binding**  
Action: Evaluate binding affinity of selected variants to PET oligomer (BHET).  
Detailed Instructions:  
- **Software**: AutoDock Vina.  
- **Preparation**: Generate receptor PDBQT from Rosetta models; ligand BHET (download from PubChem).  
- **Docking**: `vina --receptor PETase.pdbqt --ligand BHET.pdbqt --center_x 0 --center_y 0 --center_z 0 --size_x 20 --size_y 20 --size_z 20 --out out.pdbqt`.  
- **Analysis**: Rank by binding energy; select variants with ΔG < –7 kcal/mol.  
Hardware: 4‑core CPU, 8 GB RAM.  
Rationale: Stronger substrate binding often correlates with higher catalytic efficiency [2].  
Next Step Trigger: Synthesis of top 5 variants.

---

**Step 5 – Molecular Dynamics (MD) Stability Assessment**  
Action: Perform 100 ns MD simulations of top variants at 350 K to assess structural integrity.  
Detailed Instructions:  
- **Software**: GROMACS 2024.  
- **Force Field**: AMBER99SB‑ILDN.  
- **Solvent**: TIP3P water, 150 mM NaCl.  
- **Protocol**: Energy minimization → 100 ps NVT → 100 ps NPT → 100 ns production.  
- **Analysis**: RMSD, RMSF, secondary‑structure content.  
Hardware: GPU (NVIDIA RTX 3090) or HPC cluster.  
Rationale: MD provides dynamic insight into thermostability beyond static ΔΔG predictions [3].  
Next Step Trigger: Selection of variants for experimental validation.

---

**Step 6 – Primer Design & Gene Synthesis**  
Action: Design primers for site‑saturation mutagenesis or order synthetic genes for selected variants.  
Detailed Instructions:  
- **Software**: PrimerX or SnapGene.  
- **Parameters**: 20–25 nt primers, Tm ≈ 60 °C, GC ≈ 50 %.  
- **Order**: Use IDT or Twist Bioscience for gene synthesis (codon‑optimized for *E. coli*).  
Rationale: Accurate primer design ensures efficient cloning and expression of engineered PETase variants [1].  
Next Step Trigger: Commence experimental workflow (Step 1).