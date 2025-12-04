# PETase Evolution Campaign – End‑to‑End Biofoundry Protocol

Below is a fully integrated experimental and computational workflow that takes a rationally designed PETase library from in silico design to high‑throughput screening, purification, activity testing, and data‑driven redesign.  Every step explicitly cites the instruments that make the workflow possible, with volumes, temperatures, plate formats, and the rationale for each choice.

---

## Experimental Workflow

1. **In‑silico Library Design & Oligo Synthesis**  
   *Action* – Use Rosetta/AlphaFold to generate 10 000 PETase variants that maximize surface hydrophobicity and thermostability.  
   *Parameters* – 300‑bp synthetic genes, codon‑optimized for *E. coli* BL21(DE3).  
   *Instrument Rationale* – The design is performed on a high‑performance workstation; the resulting oligos are ordered from a commercial provider.  
   *Next Step Trigger* – Receipt of synthetic gene fragments.

2. **Gibson Assembly in 96‑well Format**  
   *Action* – Assemble each gene into a pET‑28a(+) vector in a 96‑well deep‑well plate.  
   *Parameters* – 10 µL reaction per well: 1 µL vector (50 ng/µL), 1 µL insert (50 ng/µL), 8 µL Gibson mix.  
   *Instrument Rationale* – **Agilent BioTek MultiFlo FX** dispenses the precise 10 µL volumes into 96‑well plates (0.2 mL consumables) with 10 % Tween‑20 to reduce surface loss.  
   *Next Step Trigger* – 30 min incubation at 50 °C (MultiFlo FX can hold the plate in a 50 °C block).

3. **Transformation & Colony Picking**  
   *Action* – Transform 5 µL of each assembly into chemically competent BL21(DE3) cells, plate on 1.5 % agar LB + kanamycin.  
   *Parameters* – 200 µL per plate, 30 °C incubation for 16 h.  
   *Instrument Rationale* – **Singer Instruments PIXL** automatically images colonies on 96‑well plates, assigns unique IDs, and records colony size for downstream selection.  
   *Next Step Trigger* – Selection of ~200 colonies per variant for plasmid prep.

4. **High‑throughput Plasmid Purification**  
   *Action* – Isolate plasmids from 96 colonies using a 96‑well miniprep kit.  
   *Parameters* – 50 µL elution per well.  
   *Instrument Rationale* – **KingFisher Presto Purification System** (50 µL protocol) rapidly purifies plasmid DNA from 96 wells in 30 min, yielding 1–2 µg per well.  
   *Next Step Trigger* – Confirmation of insert by qPCR.

5. **qPCR Verification & mRNA Quantification**  
   *Action* – Verify presence of PETase insert and quantify transcription levels after IPTG induction.  
   *Parameters* – 50 µL reaction per well: 25 µL 2× SYBR Master Mix, 1 µL primer pair (10 µM), 1 µL plasmid DNA, 23 µL nuclease‑free water.  
   *Instrument Rationale* – **Applied Biosystems QuantStudio 7 Pro** (96‑well 0.2 mL consumables) runs a 40‑cycle program (95 °C 15 s, 60 °C 30 s). The system’s 0.2 mL format matches the MultiFlo FX‑dispensed volumes, and its 30 °C hold block is ideal for post‑induction cultures.  
   *Next Step Trigger* – Wells with Ct < 25 are carried forward to expression screening.

6. **Automated Expression Screening in 384‑well Plates**  
   *Action* – Grow verified clones in 384‑well deep‑well plates, induce with IPTG, and harvest soluble protein.  
   *Parameters* – 200 µL LB + 0.5 % glucose per well, 0.5 mL culture per well, 0.5 mL final volume after induction.  
   *Instrument Rationale* – **Agilent BioTek MultiFlo FX** dispenses 200 µL media and 5 µL IPTG (1 mM) into each well.  
   *Cytomat Rationale* – **Thermo Scientific Cytomat 10 C450 R3 Lift** incubates the 384‑well plate at 30 °C for 4 h, then at 37 °C for 2 h to allow optimal protein folding.  
   *Next Step Trigger* – Harvest of soluble fraction.

7. **His‑Tag Purification & Buffer Exchange**  
   *Action* – Purify His‑tagged PETase from 96 deep‑well cultures.  
   *Parameters* – 200 µL culture per well, 50 µL elution buffer (50 mM Tris‑HCl pH 8.0, 300 mM NaCl, 10 % glycerol).  
   *Instrument Rationale* – **KingFisher Presto Purification System** (50 µL protocol) pulls down His‑tagged proteins using Ni‑NTA beads in 30 min, while the MultiFlo FX performs a 1:1 buffer exchange into assay buffer (125 mL capacity).  
   *Next Step Trigger* – Protein concentration determination by NanoDrop (not listed but assumed available).

8. **Enzyme Activity Assay (PET Degradation)**  
   *Action* – Measure PET film fragment hydrolysis in 96‑well plates.  
   *Parameters* – 100 µL reaction per well: 50 µL purified enzyme (0.5 µM), 50 µL PET film fragment (10 µg/mL), 200 µL 50 mM phosphate buffer pH 7.5.  
   *Instrument Rationale* – **Agilent BioTek MultiFlo FX** dispenses the 100 µL reaction mix into 96‑well 0.2 mL plates.  
   *Next Step Trigger* – 24 h incubation at 30 °C (Cytomat).

9. **Fluorescence / pH Monitoring**  
   *Action* – Quantify PET degradation by measuring the release of terephthalic acid (TPA) using a fluorogenic probe (p‑nitroaniline derivative).  
   *Parameters* – 50 µL probe per well, excitation 360 nm, emission 460 nm.  
   *Instrument Rationale* – **Applied Biosystems QuantStudio 7 Pro** (96‑well 0.2 mL format) records fluorescence every 10 min over 24 h, providing kinetic curves for each variant.  
   *Next Step Trigger* – Selection of top 10 % performers for mass‑spec confirmation.

10. **Mass‑Spectrometric Confirmation of Degradation Products**  
    *Action* – Analyze reaction supernatants by LC‑MS to confirm TPA, MHET, and BHET formation.  
    *Parameters* – 10 µL injection per sample, 5 µL elution per well.  
    *Instrument Rationale* – **ZenoTOF 7600+ System** delivers high‑resolution MS/MS data (m/z < 1000) with a 10 µL injection volume, enabling precise quantification of PET hydrolysis products.  
    *Next Step Trigger* – Data integration into computational redesign.

---

## Computational Workflow

1. **Variant Modeling & Thermodynamic Scoring**  
   - Input: DNA sequences from the 96‑well plasmid prep.  
   - Software: Rosetta Design, AlphaFold, and a custom Python pipeline that calculates ΔΔG for each mutation.  
   - Data Flow: Sequence files are uploaded to the workstation; the output FASTA is fed into the design pipeline.  

2. **Mass‑Spec Data Processing**  
   - Input: Raw LC‑MS files from the **ZenoTOF 7600+ System**.  
   - Software: Thermo Xcalibur (for peak picking) and Skyline (for quantification).  
   - Data Flow: The processed .mzML files are exported to a shared database; the peak areas for TPA, MHET, and BHET are linked to the corresponding variant IDs recorded by PIXL.  

3. **Activity‑Based QC & Hit Selection**  
   - Input: Fluorescence kinetic curves from **Applied Biosystems QuantStudio 7 Pro** and mass‑spec quantification.  
   - Software: R (ggplot2) and Python (pandas, seaborn) for statistical analysis.  
   - QC Step: Variants with > 30 % PET degradation and ΔΔG < 2 kcal/mol are flagged as “hits.”  

4. **Iterative Redesign**  
   - Input: Hit list, structural models, and degradation product profiles.  
   - Software: Rosetta Design with the “hotspot” protocol to introduce additional stabilizing mutations around the active site.  
   - Data Flow: New designs are automatically added to the in‑silico library, and the cycle restarts from step 2.  

5. **Machine‑Learning Feedback Loop**  
   - Input: Activity data, mass‑spec profiles, and sequence features.  
   - Software: scikit‑learn (Random Forest, XGBoost) to predict activity from sequence descriptors.  
   - QC Step: The model’s feature importance highlights residues that most influence PET hydrolysis, guiding the next round of library generation.  

6. **Final Validation**  
   - Input: Top 10 variants from the last cycle.  
   - Software: Molecular dynamics (GROMACS) to simulate PET‑PETase interactions at 60 °C.  
   - Data Flow: Simulation outputs (binding free energies) are compared against experimental degradation rates to confirm the mechanistic basis of improved activity.  

---

### How Instrument Data Feeds the Computational Loop

- **QuantStudio 7 Pro**: Fluorescence curves are exported as CSV files that are parsed by the Python pipeline to calculate initial velocity (V₀) for each variant.  
- **ZenoTOF 7600+**: MS/MS spectra are exported in .mzML format; Skyline extracts peak areas for TPA, MHET, BHET, which are then matched to variant IDs in the database.  
- **Singer PIXL & Tecan Spark Reader**: Colony images are stored with barcodes; image analysis software (e.g., CellProfiler) extracts colony size and morphology, feeding into the hit‑selection algorithm.  
- **KingFisher Presto**: Plasmid concentration data (ng/µL) are logged automatically and used to normalize qPCR Ct values, ensuring that transcriptional differences are not confounded by plasmid copy number.  

The integrated data flow—sequence → plasmid prep → expression → purification → activity assay → mass‑spec → computational redesign—creates a closed‑loop biofoundry pipeline that can iterate 4–5 times per week, dramatically accelerating PETase evolution.