Start input

Workspace: /taiga/illinois/eng/chbe/zhao5/vikas/iBF/BioAgentHub_iBF/workspaces/petase
Config:
{
  "topics": [
    "petase"
  ],
  "use_kg": true,
  "include_instruments": false,
  "kg_top_k": 5,
  "assay_enabled": true,
  "llm_rationale": true
}

Output
{
  "topics": [
    "petase"
  ],
  "cases": [
    {
      "case_study_title": "petase (E.coli + EchoMS)",
      "topic": "petase",
      "organism": "E.coli",
      "readout": "EchoMS",
      "template": "E.coli_EchoMS_protocol.md",
      "ordered_modules": [
        "module_1",
        "module_2",
        "module_3",
        "module_4",
        "module_5",
        "module_6",
        "module_8"
      ],
      "selection_evidence": {
        "organism": {
          "E.coli": {
            "score": 0.6228218923012415,
            "sources": [
              "New Labeled PET Analogues Enable the Functional Screening and",
              "Mechanoenzymatic reactions for the hydrolysis of",
              "2025 \uf0efVol. 35",
              "Functional and Structural Characterization of PETase SM14 from"
            ]
          },
          "Yeast": {
            "score": 0.6202215055624644,
            "sources": [
              "Article https://doi.org/10.1038/s41467-022-34908-z",
              "Academic Editor:",
              "New Labeled PET Analogues Enable the Functional Screening and",
              "Received:6 April 2025.Revised:2 June 2025.Accepted:10 June 2025"
            ]
          }
        },
        "readout": {
          "PlateReader": {
            "score": 0.5101024707158407,
            "sources": [
              "Academic Editor:",
              "Received:16August2021 Revised:18September2021 Accepted:22September2021",
              "www.chembiochem.org",
              "Thermostability and Activity Improvements of PETase from"
            ]
          },
          "EchoMS": {
            "score": 0.5456932683785757,
            "sources": [
              "Academic Editor:",
              "www.chembiochem.org",
              "New Labeled PET Analogues Enable the Functional Screening and",
              "Single Distal Mutation Enhances Activity of known PETases via"
            ]
          }
        }
      }
    }
  ],
  "outputs": [
    {
      "case": {
        "case_study_title": "petase (E.coli + EchoMS)",
        "topic": "petase",
        "organism": "E.coli",
        "readout": "EchoMS",
        "template": "E.coli_EchoMS_protocol.md",
        "ordered_modules": [
          "module_1",
          "module_2",
          "module_3",
          "module_4",
          "module_5",
          "module_6",
          "module_8"
        ],
        "selection_evidence": {
          "organism": {
            "E.coli": {
              "score": 0.6228218923012415,
              "sources": [
                "New Labeled PET Analogues Enable the Functional Screening and",
                "Mechanoenzymatic reactions for the hydrolysis of",
                "2025 \uf0efVol. 35",
                "Functional and Structural Characterization of PETase SM14 from"
              ]
            },
            "Yeast": {
              "score": 0.6202215055624644,
              "sources": [
                "Article https://doi.org/10.1038/s41467-022-34908-z",
                "Academic Editor:",
                "New Labeled PET Analogues Enable the Functional Screening and",
                "Received:6 April 2025.Revised:2 June 2025.Accepted:10 June 2025"
              ]
            }
          },
          "readout": {
            "PlateReader": {
              "score": 0.5101024707158407,
              "sources": [
                "Academic Editor:",
                "Received:16August2021 Revised:18September2021 Accepted:22September2021",
                "www.chembiochem.org",
                "Thermostability and Activity Improvements of PETase from"
              ]
            },
            "EchoMS": {
              "score": 0.5456932683785757,
              "sources": [
                "Academic Editor:",
                "www.chembiochem.org",
                "New Labeled PET Analogues Enable the Functional Screening and",
                "Single Distal Mutation Enhances Activity of known PETases via"
              ]
            }
          }
        }
      },
      "protocol_path": "/taiga/illinois/eng/chbe/zhao5/vikas/iBF/BioAgentHub_iBF/outputs/biofoundry_output/runs/20260210_212149/case_studies/petase_(e.coli_plus_echoms).md",
      "plan_path": "/taiga/illinois/eng/chbe/zhao5/vikas/iBF/BioAgentHub_iBF/outputs/biofoundry_output/runs/20260210_212149/case_studies/petase_(e.coli_plus_echoms)_plan.json",
      "protocol": "<!-- generated: 2026-02-10T21:21:49Z UTC -->\n# petase (E.coli + EchoMS)\nClosest template used: ModuleTemplate/E.coli_EchoMS_protocol.md\n\n1. [module_1] Mutagenesis PCR & DpnI Treatment\n   - Purpose: Introduce defined point mutations into enzyme ORFs; Provide amplified fragment for HiFi assembly\n   - Subprocess: Mutagenesis PCR Setup\n     * Objective: Introduce defined point mutations into enzyme ORFs; Provide amplified fragment for HiFi assembly\n     * Description: Forward and reverse mutagenic PCRs performed in 96-well format\n     * Actions: Dispense linearized plasmid templates and primers via worklists; Execute PCR amplification protocol\n     * Labware: 96-well PCR plates with forward primers, 96-well PCR plates with reverse primers\n     * Instruments: Tecan Fluent liquid handler, Themocycler\n     * Inputs/Materials: plasmid DNA, Mutagenic primers (96-well format), Q5 DNA polymerase\n     * Parameters: Reaction volume: 50 \u00b5L, PCR cycles: 18, Annealing temperature: 65 \u00b0C\n   - Subprocess: PCR Quality Control\n     * Objective: Confirm successful amplification prior to assembly\n     * Description: EvaGreen fluorescence assay on PCR products\n     * Actions: Mix PCR aliquot with EvaGreen dye; Measure fluorescence\n     * Labware: 96-well assay plates\n     * Instruments: Tecan Fluent liquid handler, Tecan Infinite plate reader\n     * Inputs/Materials: EvaGreen dye\n     * Parameters: Excitation: 498 nm, Emission: 535 nm\n   - Subprocess: DpnI Digestion\n     * Objective: Remove methylated parental plasmid DNA\n     * Description: Enzymatic digestion of PCR products\n     * Actions: Add DpnI; Incubate digestion reaction\n     * Labware: PCR plates\n     * Instruments: Thermocycler\n     * Inputs/Materials: DpnI restriction enzyme\n     * Parameters: 37 \u00b0C, ~4 h incubation\n   - Metadata to provide: Plasmid template ID/backbone, Target gene and variant list, Forward/reverse primer IDs and sequences, PCR product concentration (ng/\u00b5L) after DpnI\n   - Expected output: DpnI-treated mutagenesis PCR amplicons with QC (ng/\u00b5L, melt curve).\n   - Open item: Provide plasmid/backbone identifiers, target variants, and mutagenic primer sequences.\n   - Open item: Record DpnI digest QC (concentration, melt curve) for each well.\n2. [module_2] HiFi Assembly & DH5\u03b1 Transformation\n   - Purpose: Reconstruct full plasmids containing desired mutations\n   - Subprocess: HiFi DNA Assembly\n     * Objective: Reconstruct full plasmids containing desired mutations\n     * Description: Three-fragment HiFi assembly (forward fragment, reverse fragment, backbone)\n     * Actions: Dispense fragments into assembly reactions using Echo worklists; Incubate assembly reaction\n     * Labware: 384-well source plate, 96-well destination plate\n     * Instruments: Echo liquid handler, Thermocycler\n     * Inputs/Materials: HiFi DNA Assembly Master Mix\n     * Parameters: 50 \u00b0C, 30 min incubation\n   - Subprocess: DH5\u03b1 Heat-Shock Transformation\n     * Objective: Clone assembled plasmids into propagation host\n     * Description: Automated heat-shock transformation in 96-well format\n     * Actions: Mix assembly product with competent cells; Heat shock and recovery\n     * Labware: 96-well plates\n     * Instruments: Tecan Fluent (onboard heating/cooling block)\n     * Inputs/Materials: DH5\u03b1 competent cells\n     * Parameters: Heat shock: ~42 \u00b0C, ~30 s\n   - Subprocess: Plating & Incubation\n     * Objective: Obtain clonal transformant colonies\n     * Description: Automated spreading on 8-well agar omnitray plates; Overnight growth fo plated transformant\n     * Actions: Plate transformed cells; Incubate overnight\n     * Labware: 8-well omnitray agar plates, 96-well transformant plates\n     * Instruments: Tecan Fluent liquid handler, Cytomat automated incubator\n     * Inputs/Materials: LB agar + kanamycin\n     * Parameters: 37 \u00b0C, overnight\n   - Metadata to provide: Assembly fragments/backbone IDs and antibiotic marker, Insert/backbone molar ratios and total assembly volume, Transformation strain and heat-shock parameters per plate layout\n   - Expected output: Assembled plasmids and DH5\u03b1 transformant plates with colony counts.\n   - Open item: List assembly fragment IDs, antibiotic markers, and expected colony counts per construct.\n3. [module_3] DH5\u03b1 Colony Picking & Culture\n   - Purpose: Establish 96-well plasmid cultures\n   - Subprocess: Colony Picking\n     * Objective: Establish 96-well plasmid cultures\n     * Description: Automated colony picking while preserving plate mapping\n     * Actions: Pick colonies from omnitrays; Inoculate deepwell cultures\n     * Labware: 96-deepwell plates, 8-well omnitray agar plates\n     * Instruments: Pickolo colony picker integrated with Tecan Fluent\n     * Inputs/Materials: Terrific Broth (TB) + kanamycin\n     * Parameters: Culture volume: 1 mL\n   - Subprocess: Overnight Culture\n     * Objective: Amplify plasmid DNA\n     * Description: Shaking incubation of bacterial cultures\n     * Actions: Incubate cultures overnight\n     * Labware: 96-deepwell plates\n     * Instruments: Cytomat shaking incubator\n     * Parameters: 37 \u00b0C, 900 rpm\n   - Metadata to provide: Plate/colony map (source omnitray to destination deepwell), Pick criteria (colony size/fluorescence) and expected culture OD range\n   - Expected output: Overnight DH5\u03b1 cultures in deepwell plates, OD600 ranges recorded.\n   - Open item: Define colony picking criteria and barcode map from omnitray to deepwell plate.\n4. [module_4] Miniprep & BL21 Transformation\n   - Purpose: Purify plasmids for expression host transformation\n   - Subprocess: Plasmid Miniprep\n     * Objective: Purify plasmids for expression host transformation\n     * Description: Automated vacuum-based 96-well plasmid purification\n     * Actions: Execute miniprep protocol\n     * Labware: 96-well miniprep plates\n     * Instruments: Tecan Fluent (vacuum module)\n     * Inputs/Materials: PureLink Pro Quick96 Plasmid Kit\n     * Parameters: miniprep protocol\n   - Subprocess: BL21 Transformation\n     * Objective: Generate protein expression strains\n     * Description: Heat-shock transformation into BL21 cells\n     * Actions: Transform purified plasmids; Plate and incubate\n     * Labware: 96-well plates, 8-well omnitrays\n     * Instruments: Tecan Fluent, Cytomat incubator\n     * Inputs/Materials: BL21 competent cells, LB agar + kanamycin\n     * Parameters: Heat shock: ~42 \u00b0C, ~30 s\n   - Metadata to provide: Miniprep yield target (ng/\u00b5L) and QC (A260/280), Expression strain antibiotic selection and plate format\n   - Expected output: Purified plasmid DNA with concentration/A260/280; plated BL21 transformants.\n   - Open item: Specify antibiotics for BL21 transformation and miniprep yield/QC targets.\n5. [module_5] BL21 Colony Picking & Preculture\n   - Purpose: Establish expression precultures\n   - Subprocess: BL21 Colony Picking\n     * Objective: Establish expression precultures\n     * Description: Automated picking of BL21 colonies\n     * Actions: Pick colonies; Inoculate LB precultures\n     * Labware: 96-deepwell plates, 8-well omnitrays\n     * Instruments: Pickolo colony picker\n     * Inputs/Materials: LB + kanamycin\n     * Parameters: Overnight incubation\n   - Metadata to provide: Number of colonies per construct to pick; mapping to preculture wells, Preculture media/antibiotic volumes and incubation duration\n   - Expected output: BL21 precultures ready for induction; plate IDs and colony source recorded.\n   - Open item: Set colonies-per-construct and preculture volume/timing; map source colonies to wells.\n6. [module_6] Protein Expression Induction\n   - Purpose: Express enzyme variants in BL21\n   - Subprocess: Expression Induction\n     * Objective: Express enzyme variants in BL21\n     * Description: IPTG-induced or autoinduction expression\n     * Actions: Inoculate expression cultures; Induce protein expression\n     * Labware: 96-deepwell plates\n     * Instruments: Tecan Fluent, Cytomat incubator\n     * Inputs/Materials: IPTG or autoinduction media\n     * Parameters: 30\u201337 \u00b0C, Overnight expression\n   - Metadata to provide: Induction mode (IPTG vs autoinduction), concentration, temperature, duration, Culture volume per well and shaking RPM/oxygenation constraints\n   - Expected output: Induced expression cultures with induction timestamps and temperatures logged.\n   - Open item: Choose induction mode (IPTG vs autoinduction) with temperature, concentration, and duration.\n7. [module_8] E.coli screening - EchoMS\n   - Purpose: Release enzyme into crude lysate\n   - Subprocess: Cell Lysis\n     * Objective: Release enzyme into crude lysate\n     * Description: Chemical lysis followed by clarification\n     * Actions: Lyse cells; Centrifuge to remove debris\n     * Labware: 96-deepwell plates\n     * Instruments: Automated centrifuge, Tecan Fluent\n     * Inputs/Materials: lysis buffer\n     * Parameters: 30\u201337 \u00b0C, 1\u20131.5 h, 300 \u03bcL of lysis buffer, 20 min at 2900xg centrifugation\n   - Subprocess: Functional Enzyme Assay\n     * Objective: Quantify enzyme fitness in high throughput\n     * Description: EchoMS-based Mass spectrometry quantification\n     * Actions: Dispense substrates and reagents; Quantify taraget molecule\n     * Labware: 96-well plates, 384-well plates\n     * Instruments: SCIEX Echo MS System, Tecan Fluent\n     * Inputs/Materials: cell lysate\n     * Parameters: volume: 60 \u03bcL, Mass spectrometry method\n   - Metadata to provide: Target analytes for Echo-MS, internal standards, calibration levels, Sample prep volumes, carrier solvent, plate/barcode mapping\n   - Expected output: Echo-MS MRM results with calibration curves and QC sample performance.\n   - Open item: Provide Echo-MS MRM panel for TPA/MHET/BHET with internal standard (e.g., d4-TPA) and calibration range.\n   - Open item: Upload worklists for Echo transfers (sample volume 60 \u00b5L split, carrier solvent, plate barcodes).\n   - Open item: Define MS method (MRM transitions, internal standards, calibration curve, blanks/QCs).\n\nNote: All content is directly sourced from ModuleTemplate/Modules_library.md. Missing items are flagged as TODOs.\n## KG Evidence (per module)\n- module_2:\n  * [K1] performed_at_temperature: The reaction mixture was incubated at room temperature for 10 min before being directly used in the transformation.\n  * [K2] performed_at_temperature: The peptide solutions were incubated at room temperature for 24 h for self-assembly.\n  * [K3] performed_at_temperature: This is unexpected, given the increase in reaction temperature.\n  * [K4] performed_at_temperature: It works by turning raw materials into syngas a mix of gases like carbon dioxide, water vapor, and methane through reactions with oxygen at high temperatures.\n  * [K5] mixed_with: Gibson assembly was performed using reagents from NEB Gibson Assembly Cloning Kit.\n  Sources: [K1] polymers; [K2] fmicb-16-1599470 June 28, 2025 Time: 19:3 # 1; [K3] Comparative Performance of PETase as a Function of; [K4] Advanced technologies for plastic waste recycling:; [K5] Citation: Edwards, S.; Le\u00f3n-Zayas,\n- module_3:\n  * [K1] volume: 2 mL\n  * [K2] volume: 2 mL\n  * [K2] concentration: 2.0%\n  * [K4] volume: 2 mL\n  * [K5] pH: pH 6\n  Sources: [K1] Hu\u00a0and Chen  Bioresources and Bioprocessing           (2023) 10:91; [K2] Machine Learning-Guided Identification of PET Hydrolases from; [K4] Brandenberg\u00a0et\u00a0al. Microbial Cell Factories          (2022) 21:119; [K5] Article https://doi.org/10.1038/s41467-023-40233-w\n- module_4:\n  * [K1] performed_at_temperature: A The relative enzyme activity of FAST-PETase  surface-displayed BL21 at different temperature.\n  Sources: [K1] Journal of Hazardous Materials 461 (2024) 132632\n- module_5:\n  * [K1] volume: 2 mL\n  * [K2] volume: 2 mL\n  * [K3] volume: 1 ml\n  * [K3] duration: 5 min\n  * [K5] concentration: 1.6 %\n  Sources: [K1] Hu\u00a0and Chen  Bioresources and Bioprocessing           (2023) 10:91; [K2] Citation: Qu, Z.; Zhang, L.; Sun, Y.; [K3] Frontiers in Microbiology 01 frontiersin.org; [K5] Comparative Performance of PETase as a Function of\n- module_6:\n  * [K1] performed_at_temperature: coli using  autoinduction media  (Autoinductionsupplemented) in a stirred-tank  reactor at an expression temperature of 30 \u00b0C and lactose feeding.\n  * [K2] performed_at_temperature: [17] Rather, there is a large variation in conv K m across enzymes and temperatures.\n  * [K3] performed_at_temperature: Samples were shaken (200 rpm) at various temperatures in a shaking incubator (IKA KS 3000i) (Staufen, Germany).\n  Sources: [K1] Fritzsche\u00a0et\u00a0al. Microbial Cell Factories          (2024) 23:274; [K2] Comparative Performance of PETase as a Function of; [K3] polymers\n- module_8:\n  * [K1] performed_at_temperature: [17] Rather, there is a large variation in conv K m across enzymes and temperatures.\n  Sources: [K1] Comparative Performance of PETase as a Function of\n\n## Assay Evidence (per module)\n- module_8:\n  * [S1] volume: 6 ml\n  * [S2] volume: 10 ml\n  * [S1] volume: 100 ml\n  * [S4] volume: 12.5 \u03bcL\n  * [S5] labeled_with: 47 In this context, we also assessed the ability of the labeled substrates to differentiate between FAEs/MHETases and PETases.\n  * [S5] labeled_with: Particularly, these labeled substrates are well- suited for screening mutant libraries or characterizing engineered PETases, providing valuable insights into enzyme performance as they can promptly ev\n  * [S7] performed_at_temperature: The steady-state kinetic parameters derived from the convMM and invMM models suggest there is an important temperature-dependent change in affinity between the enzyme and the substrate at 40 \u00b0 C, perh\n  * [S8] mixed_with: Although WED208_00500 and  WED208_02014 were annotated as esterase and PETase and linked to  PET degradation, no degradation products were observed in cultures  containing 1% PET powder, suggesting th\n  Sources: [S1] 2025 \uf0efVol. 35; [S2] fmicb-16-1599470 June 28, 2025 Time: 19:3 # 1; [S4] MethodsX 11 (2023) 102434; [S5] New Labeled PET Analogues Enable the Functional Screening and; [S7] Comparative Performance of PETase as a Function of; [S8] Frontiers in Microbiology 01 frontiersin.org\n\n## Module Decisions\n- module_1: ambiguous (score 0.45) contradiction_ambiguous. Evidence for Mutagenesis PCR & DpnI Treatment is conflicting; marked ambiguous at score 0.45.[12][13] [12][13][14][15][16][17][18][19][20][21][22][23][24][25][26][27][28][29][30][31][32][33][34][35][36][37][38][39][40]\n- module_2: optional (score 0.37) . HiFi Assembly & DH5\u03b1 Transformation optional with evidence score 0.37.[41][42] [41][42][43][44][45][46][47][48][49][50][51][52][53][54][55][56][57][58][59][60][61][62][63][64]\n- module_3: ambiguous (score 0.34) contradiction_ambiguous. Evidence for DH5\u03b1 Colony Picking & Culture is conflicting; marked ambiguous at score 0.34.[65][66] [65][66][67]\n- module_4: optional (score 0.43) . Miniprep & BL21 Transformation optional with evidence score 0.43.[68][69] [68][69][70][71][72][73][74][75][76][77][78][79][80][13][81][82][83][84][85][86][87]\n- module_5: ambiguous (score 0.38) contradiction_ambiguous. Evidence for BL21 Colony Picking & Preculture is conflicting; marked ambiguous at score 0.38.[88][89] [88][89][90][91]\n- module_6: ambiguous (score 0.42) contradiction_ambiguous. Evidence for Protein Expression Induction is conflicting; marked ambiguous at score 0.42.[32][92] [32][92][93][94][95][96][97][98][99][100][101][102][103][104][105][106][107][64][108][109][110][63]\n- module_7: excluded (score 0.00) readout_mismatch. E.coli screening - Plate reader excluded due to readout_mismatch. \n- module_8: include (score 0.50) . E.coli screening - EchoMS supported by evidence score 0.50.[111][112] [111][112][113][114][115][116][117][118][119][120][121][122][123][124][125][126][127][128][129][130][131][132][133][134][135][136][137][138][139][140][141][142][143][144][107]\n- module_9: excluded (score 0.00) organism_mismatch. Yeast transformation and plating excluded due to organism_mismatch. \n- module_10: excluded (score 0.00) organism_mismatch. Yeast colony picking and fermentation excluded due to organism_mismatch. \n- module_11: excluded (score 0.00) readout_mismatch. Yeast Screening - plate reader excluded due to readout_mismatch. \n- module_12: excluded (score 0.00) template_not_selected. Yeast Screening - EchoMS excluded due to template_not_selected. \n\n## Citations\n[1] New Labeled PET Analogues Enable the Functional Screening and\n[2] Mechanoenzymatic reactions for the hydrolysis of\n[3] 2025 \uf0efVol. 35\n[4] Functional and Structural Characterization of PETase SM14 from\n[5] Article https://doi.org/10.1038/s41467-022-34908-z\n[6] Academic Editor:\n[7] Received:6 April 2025.Revised:2 June 2025.Accepted:10 June 2025\n[8] Received:16August2021 Revised:18September2021 Accepted:22September2021\n[9] www.chembiochem.org\n[10] Thermostability and Activity Improvements of PETase from\n[11] Single Distal Mutation Enhances Activity of known PETases via\n[12] Balance-directed protein engineering of IsPETase enhances both PET hydrolysis activity\n[13] 1\n[14] Analysis of Poly(ethylene terephthalate) degradation kinetics\n[15] Mechanoenzymatic reactions for the hydrolysis of\n[16] Academic Editor:\n[17] Computational and Structural Biotechnology Journal 27 (2025) 969\u2013977\n[18] ARTICLE\n[19] Received:6 April 2025.Revised:2 June 2025.Accepted:10 June 2025\n[20] Precise redesign for improving enzyme robustness\n[21] International Journal of\n[22] RESEARCH ARTICLE\n[23] Computational Insights into the Catalytic Mechanism of\n[24] Cao\u00a0et\u00a0al. Bioresources and Bioprocessing           (2023) 10:94\n[25] 1\n[26] Analysis of Poly(ethylene terephthalate) degradation kinetics\n[27] Towards site-specific information\n[28] Computational design of a cutinase for plastic biodegradation by mining\n[29] Towards site-specific information\n[30] Carter\u00a0et\u00a0al. Microbial Cell Factories          (2024) 23:319\n[31] Cinematic\n[32] ARTICLE\n[33] Enhancing PET Degrading Enzymes: A Combinatory\n[34] Insights into the Enhancement of the Poly(ethylene terephthalate)\n[35] Characterization and engineering of a\n[36] New Insights into the Function and Global Distribution of\n[37] 80\n[38] Citation: Sales, J.C.S.; de Castro,\n[39] Activity of an anaerobic\n[40] Article https://doi.org/10.1038/s41467-024-45662-9\n[41] Article https://doi.org/10.1038/s41467-022-34908-z\n[42] Article https://doi.org/10.1038/s41467-022-35237-x\n[43] Engineering surface electrostatics affords control over morphological 1\n[44] QM/MM Study of the Enzymatic Biodegradation Mechanism of\n[45] Unraveling the Interplay between Stability and Flexibility in the\n[46] Received:6 December 2024.Revised:25 March 2025.Accepted:8 April 2025\n[47] Accelerated Polyethylene Terephthalate (PET) Enzymatic\n[48] Recyclable Enzymatic Hydrolysis with Metal\u2212Organic Framework\n[49] Functional and Structural Characterization of PETase SM14 from\n[50] 1\n[51] fbioe-09-656465 May 21, 2021 Time: 17:53 # 1\n[52] Computational design of a cutinase for plastic biodegradation by mining\n[53] fmicb-11-571265 November 5, 2020 Time: 14:17 # 1\n[54] Insights into the Enhancement of the Poly(ethylene terephthalate)\n[55] communicationschemistry Article\n[56] Kim\u00a0et\u00a0al. Microb Cell Fact           (2020) 19:97\n[57] Received:6 April 2025.Revised:2 June 2025.Accepted:10 June 2025\n[58] Article https://doi.org/10.1038/s41467-024-45523-5\n[59] Article https://doi.org/10.1038/s41467-024-45523-5\n[60] Citation: Edwards, S.; Le\u00f3n-Zayas,\n[61] Advanced technologies for plastic waste recycling:\n[62] fmicb-16-1599470 June 28, 2025 Time: 19:3 # 1\n[63] polymers\n[64] 1\n[65] 662 | Nature | Vol 604 | 28 April 2022\n[66] 1\n[67] Moog\u00a0et\u00a0al. Microb Cell Fact          (2019) 18:171\n[68] communicationsbiology Article\n[69] communicationsbiology Article\n[70] Conformational Selection of a Tryptophan Side Chain Drives the\n[71] Carter\u00a0et\u00a0al. Microbial Cell Factories          (2024) 23:319\n[72] fmicb-16-1599470 June 28, 2025 Time: 19:3 # 1\n[73] Structural Insights into (Tere)phthalate-Ester Hydrolysis by a\n[74] Catalytic Features and Thermal\n[75] Analysis of Poly(ethylene terephthalate) degradation kinetics\n[76] Kim\u00a0et\u00a0al. Microb Cell Fact           (2020) 19:97\n[77] Carter\u00a0et\u00a0al. Microbial Cell Factories          (2024) 23:319\n[78] Characterization and engineering of a two-enzyme\n[79] 1\n[80] 2025 \uf0efVol. 35\n[81] communicationsbiology Article\n[82] | Bacteriology | Announcement\n[83] 1\n[84] fmicb-13-888343 April 6, 2022 Time: 16:36 # 1\n[85] Academic Editor: Arnaud Chatonnet\n[86] Journal of Hazardous Materials 461 (2024) 132632\n[87] ARTICLE\n[88] fmicb-16-1599470 June 28, 2025 Time: 19:3 # 1\n[89] fmicb-12-778828 December 17, 2021 Time: 14:33 # 1\n[90] RESEARCH Open Access\n[91] 2025 \uf0efVol. 35\n[92] 1\n[93] Enhancing PET Degrading Enzymes: A Combinatory\n[94] 1\n[95] Li\u00a0et\u00a0al. Bioresources and Bioprocessing           (2023) 10:26\n[96] Computational Insights into the Catalytic Mechanism of\n[97] MethodsX 9 (2022) 101815\n[98] Characterization and engineering\n[99] 1\n[100] 1\n[101] Machine Learning-Guided Identification of PET Hydrolases from\n[102] Unraveling the Interplay between Stability and Flexibility in the\n[103] Computational and Structural Biotechnology Journal 27 (2025) 969\u2013977\n[104] Molecular Details of Polyester Decrystallization via Molecular\n[105] September 2024 \uf0efVol. 34 \uf0efNo. 9\n[106] Single Distal Mutation Enhances Activity of known PETases via\n[107] New Labeled PET Analogues Enable the Functional Screening and\n[108] Fritzsche\u00a0et\u00a0al. Microbial Cell Factories          (2024) 23:274\n[109] Fritzsche\u00a0et\u00a0al. Microbial Cell Factories          (2024) 23:274\n[110] | Environmental Microbiology | Research Article\n[111] New Labeled PET Analogues Enable the Functional Screening and\n[112] RESEARCH ARTICLE\n[113] | Editor\u2019s Pick | Environmental Microbiology | Research Article\n[114] Journal of Basic Microbiology\n[115] Article https://doi.org/10.1038/s41467-025-61599-z\n[116] Received:6 April 2025.Revised:2 June 2025.Accepted:10 June 2025\n[117] Journal of Hazardous Materials 455 (2023) 131574\n[118] Title: Identification of Prospective PETases Across Prokaryotes Using an in silico Approach\n[119] Machine Learning-Guided Identification of PET Hydrolases from\n[120] Development of a highly active engineered PETase enzyme\n[121] Article https://doi.org/10.1038/s41467-022-35237-x\n[122] Journal of Hazardous Materials 455 (2023) 131574\n[123] Journal of Hazardous Materials 455 (2023) 131574\n[124] 1\n[125] 662 | Nature | Vol 604 | 28 April 2022\n[126] RESEARCH ARTICLE\n[127] An Ultra-SensitiveComamonas thiooxidansBiosensor for the\n[128] Computational and Structural Biotechnology Journal 27 (2025) 969\u2013977\n[129] Efficient secretion of a plastic\n[130] Article https://doi.org/10.1038/s41467-023-39201-1\n[131] Characterization and engineering of a two-enzyme\n[132] Article https://doi.org/10.1038/s41467-023-39201-1\n[133] Vol.:(0123456789)\n[134] Frontiers in Microbiology 01 frontiersin.org\n[135] International Journal of\n[136] An Ultra-SensitiveComamonas thiooxidansBiosensor for the\n[137] Vol.:(0123456789)\n[138] Fine tuning enzyme activity assays\n[139] Screening putative polyester polyurethane degrading\n[140] Moog\u00a0et\u00a0al. Microb Cell Fact          (2019) 18:171\n[141] Kawai\u00a0et\u00a0al. AMB Express          (2022) 12:134\n[142] Vol.:(0123456789)\n[143] MethodsX 9 (2022) 101815\n[144] Functional and Structural Characterization of PETase SM14 from\n\n## Template Selection Rationale (KG-grounded)\nThe chosen organism, E. coli, has a score of 0.6228, which is slightly higher than the alternative yeast option at 0.6202, indicating a marginal preference for E. coli based on the sources provided, including \"New Labeled PET Analogues Enable the Functional Screening and.\" The selected readout, EchoMS, scores 0.5457, outperforming the PlateReader option at 0.5101, further supporting its suitability for this application. While the scores are close, they provide a clear rationale for the E. coli and EchoMS combination. It is important to note that the module order is locked to the chosen template, E.coli_EchoMS_protocol.md, and no new steps will be added.\n",
      "plan": {
        "case_study_title": "petase (E.coli + EchoMS)",
        "organism": "E.coli",
        "readout": "EchoMS",
        "closest_template_used": "ModuleTemplate/E.coli_EchoMS_protocol.md",
        "ordered_modules": [
          "module_1",
          "module_2",
          "module_3",
          "module_4",
          "module_5",
          "module_6",
          "module_8"
        ],
        "parameters_needed": [
          "Assay substrates/readout settings (substrate, wavelength or MRM, standards, controls).",
          "Assembly fragment IDs, molar ratios, antibiotic markers for transformation.",
          "Induction mode (IPTG vs autoinduction), concentration, temperature, duration.",
          "Plasmid template/backbone IDs, target variants, mutagenic primer sequences."
        ],
        "TODOs": [
          "Choose induction mode (IPTG vs autoinduction) with temperature, concentration, and duration.",
          "Define MS method (MRM transitions, internal standards, calibration curve, blanks/QCs).",
          "Define colony picking criteria and barcode map from omnitray to deepwell plate.",
          "List assembly fragment IDs, antibiotic markers, and expected colony counts per construct.",
          "Provide Echo-MS MRM panel for TPA/MHET/BHET with internal standard (e.g., d4-TPA) and calibration range.",
          "Provide plasmid/backbone identifiers, target variants, and mutagenic primer sequences.",
          "Record DpnI digest QC (concentration, melt curve) for each well.",
          "Set colonies-per-construct and preculture volume/timing; map source colonies to wells.",
          "Specify antibiotics for BL21 transformation and miniprep yield/QC targets.",
          "Upload worklists for Echo transfers (sample volume 60 \u00b5L split, carrier solvent, plate barcodes)."
        ],
        "assumptions": [
          "Module order follows template; no reordering applied.",
          "Organism/readout chosen via methodology KG evidence (vector search scores)."
        ],
        "selection_evidence": {
          "organism": {
            "E.coli": {
              "score": 0.6228218923012415,
              "sources": [
                "New Labeled PET Analogues Enable the Functional Screening and",
                "Mechanoenzymatic reactions for the hydrolysis of",
                "2025 \uf0efVol. 35",
                "Functional and Structural Characterization of PETase SM14 from"
              ]
            },
            "Yeast": {
              "score": 0.6202215055624644,
              "sources": [
                "Article https://doi.org/10.1038/s41467-022-34908-z",
                "Academic Editor:",
                "New Labeled PET Analogues Enable the Functional Screening and",
                "Received:6 April 2025.Revised:2 June 2025.Accepted:10 June 2025"
              ]
            }
          },
          "readout": {
            "PlateReader": {
              "score": 0.5101024707158407,
              "sources": [
                "Academic Editor:",
                "Received:16August2021 Revised:18September2021 Accepted:22September2021",
                "www.chembiochem.org",
                "Thermostability and Activity Improvements of PETase from"
              ]
            },
            "EchoMS": {
              "score": 0.5456932683785757,
              "sources": [
                "Academic Editor:",
                "www.chembiochem.org",
                "New Labeled PET Analogues Enable the Functional Screening and",
                "Single Distal Mutation Enhances Activity of known PETases via"
              ]
            }
          }
        },
        "evidence": {
          "module_1": [],
          "module_2": [
            {
              "module_id": "module_2",
              "type": "methodology_edge",
              "relation": "performed_at_temperature",
              "value": "The reaction mixture was incubated at room temperature for 10 min before being directly used in the transformation.",
              "source": "polymers"
            },
            {
              "module_id": "module_2",
              "type": "methodology_edge",
              "relation": "performed_at_temperature",
              "value": "The peptide solutions were incubated at room temperature for 24 h for self-assembly.",
              "source": "fmicb-16-1599470 June 28, 2025 Time: 19:3 # 1"
            },
            {
              "module_id": "module_2",
              "type": "methodology_edge",
              "relation": "performed_at_temperature",
              "value": "This is unexpected, given the increase in reaction temperature.",
              "source": "Comparative Performance of PETase as a Function of"
            },
            {
              "module_id": "module_2",
              "type": "methodology_edge",
              "relation": "performed_at_temperature",
              "value": "It works by turning raw materials into syngas a mix of gases like carbon dioxide, water vapor, and methane through reactions with oxygen at high temperatures.",
              "source": "Advanced technologies for plastic waste recycling:"
            },
            {
              "module_id": "module_2",
              "type": "methodology_edge",
              "relation": "mixed_with",
              "value": "Gibson assembly was performed using reagents from NEB Gibson Assembly Cloning Kit.",
              "source": "Citation: Edwards, S.; Le\u00f3n-Zayas,"
            }
          ],
          "module_3": [
            {
              "module_id": "module_3",
              "type": "methodology_edge",
              "relation": "volume",
              "value": "2 mL",
              "source": "Hu\u00a0and Chen  Bioresources and Bioprocessing           (2023) 10:91"
            },
            {
              "module_id": "module_3",
              "type": "methodology_edge",
              "relation": "volume",
              "value": "2 mL",
              "source": "Machine Learning-Guided Identification of PET Hydrolases from"
            },
            {
              "module_id": "module_3",
              "type": "methodology_edge",
              "relation": "concentration",
              "value": "2.0%",
              "source": "Machine Learning-Guided Identification of PET Hydrolases from"
            },
            {
              "module_id": "module_3",
              "type": "methodology_edge",
              "relation": "volume",
              "value": "2 mL",
              "source": "Brandenberg\u00a0et\u00a0al. Microbial Cell Factories          (2022) 21:119"
            },
            {
              "module_id": "module_3",
              "type": "methodology_edge",
              "relation": "pH",
              "value": "pH 6",
              "source": "Article https://doi.org/10.1038/s41467-023-40233-w"
            },
            {
              "module_id": "module_3",
              "type": "methodology_edge",
              "relation": "pH",
              "value": "pH 7",
              "source": "Article https://doi.org/10.1038/s41467-023-40233-w"
            },
            {
              "module_id": "module_3",
              "type": "methodology_edge",
              "relation": "concentration",
              "value": "5 nM",
              "source": "Single Distal Mutation Enhances Activity of known PETases via"
            },
            {
              "module_id": "module_3",
              "type": "methodology_edge",
              "relation": "temperature",
              "value": "50 \u00b0C",
              "source": "Frontiers in Microbiology 01 frontiersin.org"
            },
            {
              "module_id": "module_3",
              "type": "methodology_edge",
              "relation": "concentration",
              "value": "86.9%",
              "source": "Single Distal Mutation Enhances Activity of known PETases via"
            },
            {
              "module_id": "module_3",
              "type": "methodology_edge",
              "relation": "concentration",
              "value": "5.5 %",
              "source": "Comparative Performance of PETase as a Function of"
            }
          ],
          "module_4": [
            {
              "module_id": "module_4",
              "type": "methodology_edge",
              "relation": "performed_at_temperature",
              "value": "A The relative enzyme activity of FAST-PETase  surface-displayed BL21 at different temperature.",
              "source": "Journal of Hazardous Materials 461 (2024) 132632"
            }
          ],
          "module_5": [
            {
              "module_id": "module_5",
              "type": "methodology_edge",
              "relation": "volume",
              "value": "2 mL",
              "source": "Hu\u00a0and Chen  Bioresources and Bioprocessing           (2023) 10:91"
            },
            {
              "module_id": "module_5",
              "type": "methodology_edge",
              "relation": "volume",
              "value": "2 mL",
              "source": "Citation: Qu, Z.; Zhang, L.; Sun, Y."
            },
            {
              "module_id": "module_5",
              "type": "methodology_edge",
              "relation": "volume",
              "value": "1 ml",
              "source": "Frontiers in Microbiology 01 frontiersin.org"
            },
            {
              "module_id": "module_5",
              "type": "methodology_edge",
              "relation": "duration",
              "value": "5 min",
              "source": "Frontiers in Microbiology 01 frontiersin.org"
            },
            {
              "module_id": "module_5",
              "type": "methodology_edge",
              "relation": "concentration",
              "value": "1.6 %",
              "source": "Comparative Performance of PETase as a Function of"
            },
            {
              "module_id": "module_5",
              "type": "methodology_edge",
              "relation": "concentration",
              "value": "5.5 %",
              "source": "Comparative Performance of PETase as a Function of"
            },
            {
              "module_id": "module_5",
              "type": "methodology_edge",
              "relation": "volume",
              "value": "10 ml",
              "source": "Special issue article"
            },
            {
              "module_id": "module_5",
              "type": "methodology_edge",
              "relation": "duration",
              "value": "2 sec",
              "source": "Article https://doi.org/10.1038/s41467-022-34908-z"
            },
            {
              "module_id": "module_5",
              "type": "methodology_edge",
              "relation": "volume",
              "value": "10 mL",
              "source": "www.chembiochem.org"
            },
            {
              "module_id": "module_5",
              "type": "methodology_edge",
              "relation": "volume",
              "value": "50 ml",
              "source": "Frontiers in Microbiology 01 frontiersin.org"
            }
          ],
          "module_6": [
            {
              "module_id": "module_6",
              "type": "methodology_edge",
              "relation": "performed_at_temperature",
              "value": "coli using  autoinduction media  (Autoinductionsupplemented) in a stirred-tank  reactor at an expression temperature of 30 \u00b0C and lactose feeding.",
              "source": "Fritzsche\u00a0et\u00a0al. Microbial Cell Factories          (2024) 23:274"
            },
            {
              "module_id": "module_6",
              "type": "methodology_edge",
              "relation": "performed_at_temperature",
              "value": "[17] Rather, there is a large variation in conv K m across enzymes and temperatures.",
              "source": "Comparative Performance of PETase as a Function of"
            },
            {
              "module_id": "module_6",
              "type": "methodology_edge",
              "relation": "performed_at_temperature",
              "value": "Samples were shaken (200 rpm) at various temperatures in a shaking incubator (IKA KS 3000i) (Staufen, Germany).",
              "source": "polymers"
            }
          ],
          "module_8": [
            {
              "module_id": "module_8",
              "type": "methodology_edge",
              "relation": "performed_at_temperature",
              "value": "[17] Rather, there is a large variation in conv K m across enzymes and temperatures.",
              "source": "Comparative Performance of PETase as a Function of"
            }
          ]
        },
        "assay_evidence": {
          "module_1": [],
          "module_2": [],
          "module_3": [],
          "module_4": [],
          "module_5": [],
          "module_6": [],
          "module_8": [
            {
              "relation": "volume",
              "value": "6 ml",
              "source": "2025 \uf0efVol. 35"
            },
            {
              "relation": "volume",
              "value": "10 ml",
              "source": "fmicb-16-1599470 June 28, 2025 Time: 19:3 # 1"
            },
            {
              "relation": "volume",
              "value": "100 ml",
              "source": "2025 \uf0efVol. 35"
            },
            {
              "relation": "volume",
              "value": "12.5 \u03bcL",
              "source": "MethodsX 11 (2023) 102434"
            },
            {
              "relation": "labeled_with",
              "value": "47 In this context, we also assessed the ability of the labeled substrates to differentiate between FAEs/MHETases and PETases.",
              "source": "New Labeled PET Analogues Enable the Functional Screening and"
            },
            {
              "relation": "labeled_with",
              "value": "Particularly, these labeled substrates are well- suited for screening mutant libraries or characterizing engineered PETases, providing valuable insights into enzyme performance as they can promptly ev",
              "source": "New Labeled PET Analogues Enable the Functional Screening and"
            },
            {
              "relation": "performed_at_temperature",
              "value": "The steady-state kinetic parameters derived from the convMM and invMM models suggest there is an important temperature-dependent change in affinity between the enzyme and the substrate at 40 \u00b0 C, perh",
              "source": "Comparative Performance of PETase as a Function of"
            },
            {
              "relation": "mixed_with",
              "value": "Although WED208_00500 and  WED208_02014 were annotated as esterase and PETase and linked to  PET degradation, no degradation products were observed in cultures  containing 1% PET powder, suggesting th",
              "source": "Frontiers in Microbiology 01 frontiersin.org"
            }
          ]
        },
        "module_decisions": [
          {
            "module_id": "module_1",
            "module_name": "Mutagenesis PCR & DpnI Treatment",
            "module_status": "ambiguous",
            "score": 0.4523,
            "exclusion_reason": "contradiction_ambiguous",
            "required_instruments": [
              "Tecan Fluent liquid handler",
              "Themocycler",
              "Tecan Infinite plate reader",
              "Thermocycler"
            ],
            "evidence_sources": [
              {
                "id": 12,
                "source_id": "text:balancedirectedproteinengineeringofispetaseenhan",
                "source": "Balance-directed protein engineering of IsPETase enhances both PET hydrolysis activity",
                "title": "",
                "section": "Methods"
              },
              {
                "id": 13,
                "source_id": "text:1",
                "source": "1",
                "title": "",
                "section": "Methods"
              },
              {
                "id": 14,
                "source_id": "text:analysisofpolyethyleneterephthalatedegradationki",
                "source": "Analysis of Poly(ethylene terephthalate) degradation kinetics",
                "title": "",
                "section": "In silicomutant libraries of TS-PETase were synthesized by"
              },
              {
                "id": 15,
                "source_id": "text:mechanoenzymaticreactionsforthehydrolysisof",
                "source": "Mechanoenzymatic reactions for the hydrolysis of",
                "title": "",
                "section": "Results and discussion"
              },
              {
                "id": 16,
                "source_id": "text:academiceditor",
                "source": "Academic Editor:",
                "title": "",
                "section": "Researchers typically combine in silico approaches with PET-degrading activity assays"
              },
              {
                "id": 17,
                "source_id": "text:computationalandstructuralbiotechnologyjournal27",
                "source": "Computational and Structural Biotechnology Journal 27 (2025) 969\u2013977",
                "title": "",
                "section": "Computational and Structural Biotechnology Journal"
              },
              {
                "id": 18,
                "source_id": "text:article",
                "source": "ARTICLE",
                "title": "",
                "section": "Methods"
              },
              {
                "id": 19,
                "source_id": "text:received6april2025revised2june2025accepted10june",
                "source": "Received:6 April 2025.Revised:2 June 2025.Accepted:10 June 2025",
                "title": "",
                "section": "Efficiency scoring and homology modeling"
              },
              {
                "id": 20,
                "source_id": "text:preciseredesignforimprovingenzymerobustness",
                "source": "Precise redesign for improving enzyme robustness",
                "title": "",
                "section": "Experimental validation of the sheer number of possible"
              },
              {
                "id": 21,
                "source_id": "text:internationaljournalof",
                "source": "International Journal of",
                "title": "",
                "section": "Some\u00a0of\u00a0the\u00a0most\u00a0employed\u00a0genetic\u00a0engineering\u00a0methods\u00a0are\u00a0directed\u00a0evolution,"
              },
              {
                "id": 22,
                "source_id": "text:researcharticle",
                "source": "RESEARCH ARTICLE",
                "title": "",
                "section": "Theseresultsdemonstratedthefeasibilityofthebiosensor-based"
              },
              {
                "id": 23,
                "source_id": "text:computationalinsightsintothecatalyticmechanismof",
                "source": "Computational Insights into the Catalytic Mechanism of",
                "title": "",
                "section": "Because of the potentially different experimental conditions"
              },
              {
                "id": 24,
                "source_id": "text:caoetalbioresourcesandbioprocessing20231094",
                "source": "Cao\u00a0et\u00a0al. Bioresources and Bioprocessing           (2023) 10:94",
                "title": "",
                "section": "Overall, these results indicated that DuraPETase exhib -"
              },
              {
                "id": 25,
                "source_id": "text:1",
                "source": "1",
                "title": "",
                "section": "Plausibly, the void space observed in the film using X-ray CT is not due to an experimental artifact 269"
              },
              {
                "id": 26,
                "source_id": "text:analysisofpolyethyleneterephthalatedegradationki",
                "source": "Analysis of Poly(ethylene terephthalate) degradation kinetics",
                "title": "",
                "section": "Experimental methods"
              },
              {
                "id": 27,
                "source_id": "text:towardssitespecificinformation",
                "source": "Towards site-specific information",
                "title": "",
                "section": "Materials and methods"
              },
              {
                "id": 28,
                "source_id": "text:computationaldesignofacutinaseforplasticbiodegra",
                "source": "Computational design of a cutinase for plastic biodegradation by mining",
                "title": "",
                "section": "RF model outperformed the other two ML methods, the optimal"
              },
              {
                "id": 29,
                "source_id": "text:towardssitespecificinformation",
                "source": "Towards site-specific information",
                "title": "",
                "section": "To evaluate experimentally the influence of temperature on the spectral quality of our PETase, we recorded"
              },
              {
                "id": 30,
                "source_id": "text:carteretalmicrobialcellfactories202423319",
                "source": "Carter\u00a0et\u00a0al. Microbial Cell Factories          (2024) 23:319",
                "title": "",
                "section": "Conclusions"
              },
              {
                "id": 31,
                "source_id": "text:cinematic",
                "source": "Cinematic",
                "title": "",
                "section": "Simulation of Substrate-to-Product"
              },
              {
                "id": 32,
                "source_id": "text:article",
                "source": "ARTICLE",
                "title": "",
                "section": "Results"
              },
              {
                "id": 33,
                "source_id": "text:enhancingpetdegradingenzymesacombinatory",
                "source": "Enhancing PET Degrading Enzymes: A Combinatory",
                "title": "",
                "section": "Machine learning and deep learning methods have been"
              },
              {
                "id": 34,
                "source_id": "text:insightsintotheenhancementofthepolyethyleneterep",
                "source": "Insights into the Enhancement of the Poly(ethylene terephthalate)",
                "title": "",
                "section": "COMPUTATIONAL METHODS"
              },
              {
                "id": 35,
                "source_id": "text:characterizationandengineeringofa",
                "source": "Characterization and engineering of a",
                "title": "",
                "section": "Both the IFD results and MD simulations independently in-"
              },
              {
                "id": 36,
                "source_id": "text:newinsightsintothefunctionandglobaldistributiono",
                "source": "New Insights into the Function and Global Distribution of",
                "title": "",
                "section": "MATERIALS AND METHODS"
              },
              {
                "id": 37,
                "source_id": "text:80",
                "source": "80",
                "title": "",
                "section": "Computational redesign of a hydrolase for nearly complete PET depolymerization at"
              },
              {
                "id": 38,
                "source_id": "text:citationsalesjcsdecastro",
                "source": "Citation: Sales, J.C.S.; de Castro,",
                "title": "",
                "section": "To evaluate the biodepolymerization process and consolidate the results obtained by"
              },
              {
                "id": 39,
                "source_id": "text:activityofananaerobic",
                "source": "Activity of an anaerobic",
                "title": "",
                "section": "3.3 Modeling Thb and HiC"
              },
              {
                "id": 40,
                "source_id": "doi:10.1038/s41467-024-45662-9",
                "source": "Article https://doi.org/10.1038/s41467-024-45662-9",
                "title": "",
                "section": "Results"
              }
            ],
            "top_evidence_sets": [
              {
                "type": "methodology_section",
                "score": 0.6219,
                "summary": "Methods: Cloning. The PETase fromIdeonella sakaiensis (GenBank accession number: GAP38373.1) without the N-terminal 29 amino acid",
                "citation_ids": [
                  18
                ]
              },
              {
                "type": "methodology_section",
                "score": 0.6106,
                "summary": "Methods: Site-directed mutagenesis   The template used to create all variants is shown in the Supplementary Table. 2.22 The  vari",
                "citation_ids": [
                  12
                ]
              }
            ],
            "rationale": "Evidence for Mutagenesis PCR & DpnI Treatment is conflicting; marked ambiguous at score 0.45.[12][13]"
          },
          {
            "module_id": "module_2",
            "module_name": "HiFi Assembly & DH5\u03b1 Transformation",
            "module_status": "optional",
            "score": 0.3708,
            "exclusion_reason": "",
            "required_instruments": [
              "Echo liquid handler",
              "Thermocycler",
              "Tecan Fluent (onboard heating/cooling block)",
              "Tecan Fluent liquid handler",
              "Cytomat automated incubator"
            ],
            "evidence_sources": [
              {
                "id": 41,
                "source_id": "doi:10.1038/s41467-022-34908-z",
                "source": "Article https://doi.org/10.1038/s41467-022-34908-z",
                "title": "",
                "section": "Results and discussion"
              },
              {
                "id": 42,
                "source_id": "doi:10.1038/s41467-022-35237-x",
                "source": "Article https://doi.org/10.1038/s41467-022-35237-x",
                "title": "",
                "section": "Docking simulations with a PET trimer reveal the potential for binding"
              },
              {
                "id": 43,
                "source_id": "text:engineeringsurfaceelectrostaticsaffordscontrolov",
                "source": "Engineering surface electrostatics affords control over morphological 1",
                "title": "",
                "section": "Materials and Methods 272"
              },
              {
                "id": 44,
                "source_id": "text:qmmmstudyoftheenzymaticbiodegradationmechanismof",
                "source": "QM/MM Study of the Enzymatic Biodegradation Mechanism of",
                "title": "",
                "section": "\u25a0 RESULTS AND DISCUSSION"
              },
              {
                "id": 45,
                "source_id": "text:unravelingtheinterplaybetweenstabilityandflexibi",
                "source": "Unraveling the Interplay between Stability and Flexibility in the",
                "title": "",
                "section": "Further projections of simulation trajectories onto the PCs"
              },
              {
                "id": 46,
                "source_id": "text:received6december2024revised25march2025accepted8",
                "source": "Received:6 December 2024.Revised:25 March 2025.Accepted:8 April 2025",
                "title": "",
                "section": "Materials and methods"
              },
              {
                "id": 47,
                "source_id": "text:acceleratedpolyethyleneterephthalatepetenzymatic",
                "source": "Accelerated Polyethylene Terephthalate (PET) Enzymatic",
                "title": "",
                "section": "Results and Discussion"
              },
              {
                "id": 48,
                "source_id": "text:recyclableenzymatichydrolysiswithmetalorganicfra",
                "source": "Recyclable Enzymatic Hydrolysis with Metal\u2212Organic Framework",
                "title": "",
                "section": "RESULTS AND DISCUSSION"
              },
              {
                "id": 49,
                "source_id": "text:functionalandstructuralcharacterizationofpetases",
                "source": "Functional and Structural Characterization of PETase SM14 from",
                "title": "",
                "section": "MATERIALS AND METHODS"
              },
              {
                "id": 50,
                "source_id": "text:1",
                "source": "1",
                "title": "",
                "section": "Experimental procedures"
              },
              {
                "id": 51,
                "source_id": "text:fbioe09656465may212021time17531",
                "source": "fbioe-09-656465 May 21, 2021 Time: 17:53 # 1",
                "title": "",
                "section": "The conventional culture-dependent methods, cutting-edge"
              },
              {
                "id": 52,
                "source_id": "text:computationaldesignofacutinaseforplasticbiodegra",
                "source": "Computational design of a cutinase for plastic biodegradation by mining",
                "title": "",
                "section": "As one of the state-of-the-art statistical methods, the logistic"
              },
              {
                "id": 53,
                "source_id": "text:fmicb11571265november52020time14171",
                "source": "fmicb-11-571265 November 5, 2020 Time: 14:17 # 1",
                "title": "",
                "section": "In a study that employed anin silico-based screening approach"
              },
              {
                "id": 54,
                "source_id": "text:insightsintotheenhancementofthepolyethyleneterep",
                "source": "Insights into the Enhancement of the Poly(ethylene terephthalate)",
                "title": "",
                "section": "Classical molecular dynamics (MD) simulations for the mutant"
              },
              {
                "id": 55,
                "source_id": "text:communicationschemistryarticle",
                "source": "communicationschemistry Article",
                "title": "",
                "section": "analysis simulations as the plateau value of the function:"
              },
              {
                "id": 56,
                "source_id": "text:kimetalmicrobcellfact20201997",
                "source": "Kim\u00a0et\u00a0al. Microb Cell Fact           (2020) 19:97",
                "title": "",
                "section": "Results"
              },
              {
                "id": 57,
                "source_id": "text:received6april2025revised2june2025accepted10june",
                "source": "Received:6 April 2025.Revised:2 June 2025.Accepted:10 June 2025",
                "title": "",
                "section": "Discussion"
              },
              {
                "id": 58,
                "source_id": "doi:10.1038/s41467-024-45523-5",
                "source": "Article https://doi.org/10.1038/s41467-024-45523-5",
                "title": "",
                "section": "Methods"
              },
              {
                "id": 59,
                "source_id": "doi:10.1038/s41467-024-45523-5",
                "source": "Article https://doi.org/10.1038/s41467-024-45523-5",
                "title": "",
                "section": "Taken together, these results suggest that the reaction plateau for"
              },
              {
                "id": 60,
                "source_id": "text:citationedwardsslenzayas",
                "source": "Citation: Edwards, S.; Le\u00f3n-Zayas,",
                "title": "",
                "section": "mixed_with"
              },
              {
                "id": 61,
                "source_id": "text:advancedtechnologiesforplasticwasterecycling",
                "source": "Advanced technologies for plastic waste recycling:",
                "title": "",
                "section": "performed_at_temperature"
              },
              {
                "id": 62,
                "source_id": "text:fmicb161599470june282025time1931",
                "source": "fmicb-16-1599470 June 28, 2025 Time: 19:3 # 1",
                "title": "",
                "section": "performed_at_temperature"
              },
              {
                "id": 63,
                "source_id": "text:polymers",
                "source": "polymers",
                "title": "",
                "section": "performed_at_temperature"
              },
              {
                "id": 64,
                "source_id": "text:1",
                "source": "1",
                "title": "",
                "section": "performed_at_temperature"
              }
            ],
            "top_evidence_sets": [
              {
                "type": "methodology_section",
                "score": 0.6059,
                "summary": "Classical molecular dynamics (MD) simulations for the mutant: FAST-PETase and the wild-type PETase enzymes and their respective enzyme:PET complexes were first performed to gain insi",
                "citation_ids": [
                  54
                ]
              },
              {
                "type": "methodology_section",
                "score": 0.5499,
                "summary": "Results and discussion: HFBI and PETase were functionally codisplayed on the surface of yeast cells In our codisplay system, hydrophobin HFBI an",
                "citation_ids": [
                  41
                ]
              }
            ],
            "rationale": "HiFi Assembly & DH5\u03b1 Transformation optional with evidence score 0.37.[41][42]"
          },
          {
            "module_id": "module_3",
            "module_name": "DH5\u03b1 Colony Picking & Culture",
            "module_status": "ambiguous",
            "score": 0.3367,
            "exclusion_reason": "contradiction_ambiguous",
            "required_instruments": [
              "Pickolo colony picker integrated with Tecan Fluent",
              "Cytomat shaking incubator"
            ],
            "evidence_sources": [
              {
                "id": 65,
                "source_id": "text:662naturevol60428april2022",
                "source": "662 | Nature | Vol 604 | 28 April 2022",
                "title": "",
                "section": "Methods"
              },
              {
                "id": 66,
                "source_id": "text:1",
                "source": "1",
                "title": "",
                "section": "Supplementary Methods 1: Description of methods 368"
              },
              {
                "id": 67,
                "source_id": "text:moogetalmicrobcellfact201918171",
                "source": "Moog\u00a0et\u00a0al. Microb Cell Fact          (2019) 18:171",
                "title": "",
                "section": "Results: Using the photosynthetic microalga Phaeodactylum tricornutum as a chassis we generated a microbial cell"
              }
            ],
            "top_evidence_sets": [
              {
                "type": "methodology_section",
                "score": 0.4527,
                "summary": "Results: Using the photosynthetic microalga Phaeodactylum tricornutum as a chassis we generated a microbial cell: factory capable of producing and secreting an engineered version of PETase into the surrounding culture medium.  Initial",
                "citation_ids": [
                  67
                ]
              },
              {
                "type": "methodology_section",
                "score": 0.2557,
                "summary": "Methods: CNN model MutCompute24 is a three-dimensional CNN (3DCNN) model in which  the architecture consists of nine layers divid",
                "citation_ids": [
                  65
                ]
              }
            ],
            "rationale": "Evidence for DH5\u03b1 Colony Picking & Culture is conflicting; marked ambiguous at score 0.34.[65][66]"
          },
          {
            "module_id": "module_4",
            "module_name": "Miniprep & BL21 Transformation",
            "module_status": "optional",
            "score": 0.4255,
            "exclusion_reason": "",
            "required_instruments": [
              "Tecan Fluent (vacuum module)",
              "Tecan Fluent",
              "Cytomat incubator"
            ],
            "evidence_sources": [
              {
                "id": 68,
                "source_id": "text:communicationsbiologyarticle",
                "source": "communicationsbiology Article",
                "title": "",
                "section": "Here, we developed a computational design approach based on the struc-"
              },
              {
                "id": 69,
                "source_id": "text:communicationsbiologyarticle",
                "source": "communicationsbiology Article",
                "title": "",
                "section": "Computational enzyme design"
              },
              {
                "id": 70,
                "source_id": "text:conformationalselectionofatryptophansidechaindri",
                "source": "Conformational Selection of a Tryptophan Side Chain Drives the",
                "title": "",
                "section": "In this work, we employ molecular dynamics (MD) and"
              },
              {
                "id": 71,
                "source_id": "text:carteretalmicrobialcellfactories202423319",
                "source": "Carter\u00a0et\u00a0al. Microbial Cell Factories          (2024) 23:319",
                "title": "",
                "section": "Results We found expression in SHuffle T7 Express results in higher active expression of IsPETase compared"
              },
              {
                "id": 72,
                "source_id": "text:fmicb161599470june282025time1931",
                "source": "fmicb-16-1599470 June 28, 2025 Time: 19:3 # 1",
                "title": "",
                "section": "To address the limitations of existing methods in developing"
              },
              {
                "id": 73,
                "source_id": "text:structuralinsightsintoterephthalateesterhydrolys",
                "source": "Structural Insights into (Tere)phthalate-Ester Hydrolysis by a",
                "title": "",
                "section": "Methods for mitigating the product inhibition during"
              },
              {
                "id": 74,
                "source_id": "text:catalyticfeaturesandthermal",
                "source": "Catalytic Features and Thermal",
                "title": "",
                "section": "Molecular Dynamics Simulations"
              },
              {
                "id": 75,
                "source_id": "text:analysisofpolyethyleneterephthalatedegradationki",
                "source": "Analysis of Poly(ethylene terephthalate) degradation kinetics",
                "title": "",
                "section": "Optimization and simulation were performed using Math-"
              },
              {
                "id": 76,
                "source_id": "text:kimetalmicrobcellfact20201997",
                "source": "Kim\u00a0et\u00a0al. Microb Cell Fact           (2020) 19:97",
                "title": "",
                "section": "Methods"
              },
              {
                "id": 77,
                "source_id": "text:carteretalmicrobialcellfactories202423319",
                "source": "Carter\u00a0et\u00a0al. Microbial Cell Factories          (2024) 23:319",
                "title": "",
                "section": "Methods"
              },
              {
                "id": 78,
                "source_id": "text:characterizationandengineeringofatwoenzyme",
                "source": "Characterization and engineering of a two-enzyme",
                "title": "",
                "section": "Methods"
              },
              {
                "id": 79,
                "source_id": "text:1",
                "source": "1",
                "title": "",
                "section": "Materials and methods 253"
              },
              {
                "id": 80,
                "source_id": "text:2025vol35",
                "source": "2025 \uf0efVol. 35",
                "title": "",
                "section": "Materials and Methods"
              },
              {
                "id": 13,
                "source_id": "text:1",
                "source": "1",
                "title": "",
                "section": "Methods"
              },
              {
                "id": 81,
                "source_id": "text:communicationsbiologyarticle",
                "source": "communicationsbiology Article",
                "title": "",
                "section": "Loop remodeling"
              },
              {
                "id": 82,
                "source_id": "text:bacteriologyannouncement",
                "source": "| Bacteriology | Announcement",
                "title": "",
                "section": "Conceptualization, Funding acquisition, Methodology, Project administration, Resources,"
              },
              {
                "id": 83,
                "source_id": "text:1",
                "source": "1",
                "title": "",
                "section": "Methodology: RMD, ES, EA 642"
              },
              {
                "id": 84,
                "source_id": "text:fmicb13888343april62022time16361",
                "source": "fmicb-13-888343 April 6, 2022 Time: 16:36 # 1",
                "title": "",
                "section": "Met177, results from the same study also indicated Gly105,"
              },
              {
                "id": 85,
                "source_id": "text:academiceditorarnaudchatonnet",
                "source": "Academic Editor: Arnaud Chatonnet",
                "title": "",
                "section": "The results of the colorimetric quantitative detection indicate that Gs no longer exhibits"
              },
              {
                "id": 86,
                "source_id": "text:journalofhazardousmaterials4612024132632",
                "source": "Journal of Hazardous Materials 461 (2024) 132632",
                "title": "",
                "section": "performed_at_temperature"
              },
              {
                "id": 87,
                "source_id": "text:article",
                "source": "ARTICLE",
                "title": "",
                "section": "mixed_with"
              }
            ],
            "top_evidence_sets": [
              {
                "type": "methodology_section",
                "score": 0.5977,
                "summary": "Methods: Plasmid construction, strains, and\u00a0cell cultivation All plasmids, oligonucleotide primers, and strains used in  this stu",
                "citation_ids": [
                  76
                ]
              },
              {
                "type": "methodology_section",
                "score": 0.5798,
                "summary": "Methods: Plasmid construction and\u00a0strains The gene encoding PETase from Ideonella sakaiensis  (IsPETase) was codon optimized for",
                "citation_ids": [
                  77
                ]
              }
            ],
            "rationale": "Miniprep & BL21 Transformation optional with evidence score 0.43.[68][69]"
          },
          {
            "module_id": "module_5",
            "module_name": "BL21 Colony Picking & Preculture",
            "module_status": "ambiguous",
            "score": 0.3764,
            "exclusion_reason": "contradiction_ambiguous",
            "required_instruments": [
              "Pickolo colony picker"
            ],
            "evidence_sources": [
              {
                "id": 88,
                "source_id": "text:fmicb161599470june282025time1931",
                "source": "fmicb-16-1599470 June 28, 2025 Time: 19:3 # 1",
                "title": "",
                "section": "4 Discussion and conclusion"
              },
              {
                "id": 89,
                "source_id": "text:fmicb12778828december172021time14331",
                "source": "fmicb-12-778828 December 17, 2021 Time: 14:33 # 1",
                "title": "",
                "section": "These results established a theoretical basis for the design of"
              },
              {
                "id": 90,
                "source_id": "text:researchopenaccess",
                "source": "RESEARCH Open Access",
                "title": "",
                "section": "Results"
              },
              {
                "id": 91,
                "source_id": "text:2025vol35",
                "source": "2025 \uf0efVol. 35",
                "title": "",
                "section": "Results and Discussion"
              }
            ],
            "top_evidence_sets": [
              {
                "type": "methodology_section",
                "score": 0.5053,
                "summary": "These results established a theoretical basis for the design of: PET biodegradation systems. Most studies focused on the initial degradation step. Hydrophobin has been used to convert P",
                "citation_ids": [
                  89
                ]
              },
              {
                "type": "methodology_section",
                "score": 0.3846,
                "summary": "4 Discussion and conclusion: The rapid accumulation of PET waste poses a global environmental crisis, necessitating innovative and sustainable soluti",
                "citation_ids": [
                  88
                ]
              }
            ],
            "rationale": "Evidence for BL21 Colony Picking & Preculture is conflicting; marked ambiguous at score 0.38.[88][89]"
          },
          {
            "module_id": "module_6",
            "module_name": "Protein Expression Induction",
            "module_status": "ambiguous",
            "score": 0.4199,
            "exclusion_reason": "contradiction_ambiguous",
            "required_instruments": [
              "Tecan Fluent",
              "Cytomat incubator"
            ],
            "evidence_sources": [
              {
                "id": 32,
                "source_id": "text:article",
                "source": "ARTICLE",
                "title": "",
                "section": "Results"
              },
              {
                "id": 92,
                "source_id": "text:1",
                "source": "1",
                "title": "",
                "section": "Directed Evolution Results"
              },
              {
                "id": 93,
                "source_id": "text:enhancingpetdegradingenzymesacombinatory",
                "source": "Enhancing PET Degrading Enzymes: A Combinatory",
                "title": "",
                "section": "Conclusions"
              },
              {
                "id": 94,
                "source_id": "text:1",
                "source": "1",
                "title": "",
                "section": "Results"
              },
              {
                "id": 95,
                "source_id": "text:lietalbioresourcesandbioprocessing20231026",
                "source": "Li\u00a0et\u00a0al. Bioresources and Bioprocessing           (2023) 10:26",
                "title": "",
                "section": "Results and\u00a0discussion"
              },
              {
                "id": 96,
                "source_id": "text:computationalinsightsintothecatalyticmechanismof",
                "source": "Computational Insights into the Catalytic Mechanism of",
                "title": "",
                "section": "Computational Insights into the Catalytic Mechanism of"
              },
              {
                "id": 97,
                "source_id": "text:methodsx92022101815",
                "source": "MethodsX 9 (2022) 101815",
                "title": "",
                "section": "MethodsX"
              },
              {
                "id": 98,
                "source_id": "text:characterizationandengineering",
                "source": "Characterization and engineering",
                "title": "",
                "section": "2 Materials and methods"
              },
              {
                "id": 99,
                "source_id": "text:1",
                "source": "1",
                "title": "",
                "section": "Materials and Methods"
              },
              {
                "id": 100,
                "source_id": "text:1",
                "source": "1",
                "title": "",
                "section": "Performing directed evolution using machine learning on the computer is known as in silico"
              },
              {
                "id": 101,
                "source_id": "text:machinelearningguidedidentificationofpethydrolas",
                "source": "Machine Learning-Guided Identification of PET Hydrolases from",
                "title": "",
                "section": "Identified Using Bioinformatics and Iterative Machine"
              },
              {
                "id": 102,
                "source_id": "text:unravelingtheinterplaybetweenstabilityandflexibi",
                "source": "Unraveling the Interplay between Stability and Flexibility in the",
                "title": "",
                "section": "Our results align with these findings, showing that Thermo-"
              },
              {
                "id": 103,
                "source_id": "text:computationalandstructuralbiotechnologyjournal27",
                "source": "Computational and Structural Biotechnology Journal 27 (2025) 969\u2013977",
                "title": "",
                "section": "C simulations are"
              },
              {
                "id": 104,
                "source_id": "text:moleculardetailsofpolyesterdecrystallizationviam",
                "source": "Molecular Details of Polyester Decrystallization via Molecular",
                "title": "",
                "section": "Pressure Molecular Dynamics Simulation: The Langevin Piston"
              },
              {
                "id": 105,
                "source_id": "text:september2024vol34no9",
                "source": "September 2024 \uf0efVol. 34 \uf0efNo. 9",
                "title": "",
                "section": "44. Parrinello M, Rahman A. 1981. Polymorphic transiti ons in single crystals: a new molecular dynamics method. J. Appl. Phys. 52:"
              },
              {
                "id": 106,
                "source_id": "text:singledistalmutationenhancesactivityofknownpetas",
                "source": "Single Distal Mutation Enhances Activity of known PETases via",
                "title": "",
                "section": "All productionsimulationswereconductedunder theisothermal,isobaricconditions(NPT) with"
              },
              {
                "id": 107,
                "source_id": "text:newlabeledpetanaloguesenablethefunctionalscreeni",
                "source": "New Labeled PET Analogues Enable the Functional Screening and",
                "title": "",
                "section": "labeled_with"
              },
              {
                "id": 64,
                "source_id": "text:1",
                "source": "1",
                "title": "",
                "section": "performed_at_temperature"
              },
              {
                "id": 108,
                "source_id": "text:fritzscheetalmicrobialcellfactories202423274",
                "source": "Fritzsche\u00a0et\u00a0al. Microbial Cell Factories          (2024) 23:274",
                "title": "",
                "section": "mixed_with"
              },
              {
                "id": 109,
                "source_id": "text:fritzscheetalmicrobialcellfactories202423274",
                "source": "Fritzsche\u00a0et\u00a0al. Microbial Cell Factories          (2024) 23:274",
                "title": "",
                "section": "performed_at_temperature"
              },
              {
                "id": 110,
                "source_id": "text:environmentalmicrobiologyresearcharticle",
                "source": "| Environmental Microbiology | Research Article",
                "title": "",
                "section": "induced_with"
              },
              {
                "id": 63,
                "source_id": "text:polymers",
                "source": "polymers",
                "title": "",
                "section": "performed_at_temperature"
              }
            ],
            "top_evidence_sets": [
              {
                "type": "methodology_edge",
                "score": 0.6088,
                "summary": "labeled_with: Particularly, these labeled substrates are well-\nsuited for screening mutant libraries or characterizing\nengineered PETases, providing valuable insights into enzyme\nperformance as they can promptly ev",
                "citation_ids": [
                  107
                ]
              },
              {
                "type": "methodology_section",
                "score": 0.5919,
                "summary": "Results: Overall structures of PETase. The recombinant protein of wild- type PETase without signal peptide was expressed and crys",
                "citation_ids": [
                  32
                ]
              }
            ],
            "rationale": "Evidence for Protein Expression Induction is conflicting; marked ambiguous at score 0.42.[32][92]"
          },
          {
            "module_id": "module_7",
            "module_name": "E.coli screening - Plate reader",
            "module_status": "excluded",
            "score": 0.0,
            "exclusion_reason": "readout_mismatch",
            "required_instruments": [
              "Automated centrifuge",
              "Tecan Fluent",
              "Tecan Infinite plate reader"
            ],
            "evidence_sources": [],
            "top_evidence_sets": [],
            "rationale": "E.coli screening - Plate reader excluded due to readout_mismatch."
          },
          {
            "module_id": "module_8",
            "module_name": "E.coli screening - EchoMS",
            "module_status": "include",
            "score": 0.4978,
            "exclusion_reason": "",
            "required_instruments": [
              "Automated centrifuge",
              "Tecan Fluent",
              "SCIEX Echo MS System"
            ],
            "evidence_sources": [
              {
                "id": 111,
                "source_id": "text:newlabeledpetanaloguesenablethefunctionalscreeni",
                "source": "New Labeled PET Analogues Enable the Functional Screening and",
                "title": "",
                "section": "Taking all of the results and limitations into account, it is"
              },
              {
                "id": 112,
                "source_id": "text:researcharticle",
                "source": "RESEARCH ARTICLE",
                "title": "",
                "section": "2 | RESULTS AND DISCUSSION"
              },
              {
                "id": 113,
                "source_id": "text:editorspickenvironmentalmicrobiologyresearcharti",
                "source": "| Editor\u2019s Pick | Environmental Microbiology | Research Article",
                "title": "",
                "section": "Methodology, Project administration, Resources, Software, Validation, Visualization,"
              },
              {
                "id": 114,
                "source_id": "text:journalofbasicmicrobiology",
                "source": "Journal of Basic Microbiology",
                "title": "",
                "section": "Seong Hyeon Lee: conceptualization, methodology, investigation,"
              },
              {
                "id": 115,
                "source_id": "doi:10.1038/s41467-025-61599-z",
                "source": "Article https://doi.org/10.1038/s41467-025-61599-z",
                "title": "",
                "section": "Program of China (2024YFA0917603), the Computational Biology Key"
              },
              {
                "id": 116,
                "source_id": "text:received6april2025revised2june2025accepted10june",
                "source": "Received:6 April 2025.Revised:2 June 2025.Accepted:10 June 2025",
                "title": "",
                "section": "Lab (IAC) at KAUST for providing the computational and exper-"
              },
              {
                "id": 117,
                "source_id": "text:journalofhazardousmaterials4552023131574",
                "source": "Journal of Hazardous Materials 455 (2023) 131574",
                "title": "",
                "section": "Christina Gkountela : Methodology, Validation, Formal analysis,"
              },
              {
                "id": 118,
                "source_id": "text:titleidentificationofprospectivepetasesacrosspro",
                "source": "Title: Identification of Prospective PETases Across Prokaryotes Using an in silico Approach",
                "title": "",
                "section": "Availability of data and materials: The data supporting the results are provided with the"
              },
              {
                "id": 119,
                "source_id": "text:machinelearningguidedidentificationofpethydrolas",
                "source": "Machine Learning-Guided Identification of PET Hydrolases from",
                "title": "",
                "section": "METHODS"
              },
              {
                "id": 120,
                "source_id": "text:developmentofahighlyactiveengineeredpetaseenzyme",
                "source": "Development of a highly active engineered PETase enzyme",
                "title": "",
                "section": "SB, RC contributed to methodology, investigation,"
              },
              {
                "id": 121,
                "source_id": "doi:10.1038/s41467-022-35237-x",
                "source": "Article https://doi.org/10.1038/s41467-022-35237-x",
                "title": "",
                "section": "Results"
              },
              {
                "id": 122,
                "source_id": "text:journalofhazardousmaterials4552023131574",
                "source": "Journal of Hazardous Materials 455 (2023) 131574",
                "title": "",
                "section": "The results demonstrate that Dm PETase was able to degrade all"
              },
              {
                "id": 123,
                "source_id": "text:journalofhazardousmaterials4552023131574",
                "source": "Journal of Hazardous Materials 455 (2023) 131574",
                "title": "",
                "section": "The results of the degradation study on PCL powder showed that"
              },
              {
                "id": 124,
                "source_id": "text:1",
                "source": "1",
                "title": "",
                "section": "The 29 candidate enzyme variants originating from the different screening methods were then subject to"
              },
              {
                "id": 125,
                "source_id": "text:662naturevol60428april2022",
                "source": "662 | Nature | Vol 604 | 28 April 2022",
                "title": "",
                "section": "The authors declare that all data supporting the findings of this study"
              },
              {
                "id": 126,
                "source_id": "text:researcharticle",
                "source": "RESEARCH ARTICLE",
                "title": "",
                "section": "Initially, we started the MD simulation assuming the PET L-shape"
              },
              {
                "id": 127,
                "source_id": "text:anultrasensitivecomamonasthiooxidansbiosensorfor",
                "source": "An Ultra-SensitiveComamonas thiooxidansBiosensor for the",
                "title": "",
                "section": "Table 3Current methods used to assay PET degradation mainly monitoring hydrolytic TPA release"
              },
              {
                "id": 128,
                "source_id": "text:computationalandstructuralbiotechnologyjournal27",
                "source": "Computational and Structural Biotechnology Journal 27 (2025) 969\u2013977",
                "title": "",
                "section": "Molecular simulations, modelling, and analysis were performed by"
              },
              {
                "id": 129,
                "source_id": "text:efficientsecretionofaplastic",
                "source": "Efficient secretion of a plastic",
                "title": "",
                "section": "ing\u2014original draft, Writing\u2014review & editing BS: Investigation, Methodology, Writing\u2014review & editing KK:"
              },
              {
                "id": 130,
                "source_id": "doi:10.1038/s41467-023-39201-1",
                "source": "Article https://doi.org/10.1038/s41467-023-39201-1",
                "title": "",
                "section": "Results"
              },
              {
                "id": 131,
                "source_id": "text:characterizationandengineeringofatwoenzyme",
                "source": "Characterization and engineering of a two-enzyme",
                "title": "",
                "section": "Discussion"
              },
              {
                "id": 132,
                "source_id": "doi:10.1038/s41467-023-39201-1",
                "source": "Article https://doi.org/10.1038/s41467-023-39201-1",
                "title": "",
                "section": "Discussion"
              },
              {
                "id": 133,
                "source_id": "text:vol0123456789",
                "source": "Vol.:(0123456789)",
                "title": "",
                "section": "Different pH values, drying methods and solutions were"
              },
              {
                "id": 134,
                "source_id": "text:frontiersinmicrobiology01frontiersinorg",
                "source": "Frontiers in Microbiology 01 frontiersin.org",
                "title": "",
                "section": "Based on the findings of the double mutation (DM) strategy"
              },
              {
                "id": 135,
                "source_id": "text:internationaljournalof",
                "source": "International Journal of",
                "title": "",
                "section": "II, the already described ester bond breakage results in the production of a MHET monomer"
              },
              {
                "id": 136,
                "source_id": "text:anultrasensitivecomamonasthiooxidansbiosensorfor",
                "source": "An Ultra-SensitiveComamonas thiooxidansBiosensor for the",
                "title": "",
                "section": "RESULTS"
              },
              {
                "id": 137,
                "source_id": "text:vol0123456789",
                "source": "Vol.:(0123456789)",
                "title": "",
                "section": "The absorption measurement also provided the best results"
              },
              {
                "id": 138,
                "source_id": "text:finetuningenzymeactivityassays",
                "source": "Fine tuning enzyme activity assays",
                "title": "",
                "section": "Results and discussion"
              },
              {
                "id": 139,
                "source_id": "text:screeningputativepolyesterpolyurethanedegrading",
                "source": "Screening putative polyester polyurethane degrading",
                "title": "",
                "section": "F-test on the results also shows that the automated addition with"
              },
              {
                "id": 140,
                "source_id": "text:moogetalmicrobcellfact201918171",
                "source": "Moog\u00a0et\u00a0al. Microb Cell Fact          (2019) 18:171",
                "title": "",
                "section": "Essen for helpful discussions and valuable technical advices supporting the"
              },
              {
                "id": 141,
                "source_id": "text:kawaietalambexpress202212134",
                "source": "Kawai\u00a0et\u00a0al. AMB Express          (2022) 12:134",
                "title": "",
                "section": "Results"
              },
              {
                "id": 142,
                "source_id": "text:vol0123456789",
                "source": "Vol.:(0123456789)",
                "title": "",
                "section": "Results"
              },
              {
                "id": 143,
                "source_id": "text:methodsx92022101815",
                "source": "MethodsX 9 (2022) 101815",
                "title": "",
                "section": "As a validation of the methodology the effect of the X C , on the product release rate of the gold"
              },
              {
                "id": 144,
                "source_id": "text:functionalandstructuralcharacterizationofpetases",
                "source": "Functional and Structural Characterization of PETase SM14 from",
                "title": "",
                "section": "concentration"
              },
              {
                "id": 107,
                "source_id": "text:newlabeledpetanaloguesenablethefunctionalscreeni",
                "source": "New Labeled PET Analogues Enable the Functional Screening and",
                "title": "",
                "section": "labeled_with"
              }
            ],
            "top_evidence_sets": [
              {
                "type": "methodology_section",
                "score": 0.6361,
                "summary": "Essen for helpful discussions and valuable technical advices supporting the: progress of the project. Moreover, we are grateful to ALPLA\u2011Werke Lehner  GmbH & Co KG (Gem\u00fcnden, Germany) for providing",
                "citation_ids": [
                  140
                ]
              },
              {
                "type": "methodology_section",
                "score": 0.6225,
                "summary": "Results: Mechanism of\u00a0PET degradation The hydrolysis of PET is considered to proceed at ran - dom via endo-type degradation (Eber",
                "citation_ids": [
                  141
                ]
              }
            ],
            "rationale": "E.coli screening - EchoMS supported by evidence score 0.50.[111][112]"
          },
          {
            "module_id": "module_9",
            "module_name": "Yeast transformation and plating",
            "module_status": "excluded",
            "score": 0.0,
            "exclusion_reason": "organism_mismatch",
            "required_instruments": [
              "Tecan Fluent",
              "Cytomat",
              "Centrifuge",
              "Echo650"
            ],
            "evidence_sources": [],
            "top_evidence_sets": [],
            "rationale": "Yeast transformation and plating excluded due to organism_mismatch."
          },
          {
            "module_id": "module_10",
            "module_name": "Yeast colony picking and fermentation",
            "module_status": "excluded",
            "score": 0.0,
            "exclusion_reason": "organism_mismatch",
            "required_instruments": [
              "Tecan Fluent",
              "PIXL"
            ],
            "evidence_sources": [],
            "top_evidence_sets": [],
            "rationale": "Yeast colony picking and fermentation excluded due to organism_mismatch."
          },
          {
            "module_id": "module_11",
            "module_name": "Yeast Screening - plate reader",
            "module_status": "excluded",
            "score": 0.0,
            "exclusion_reason": "readout_mismatch",
            "required_instruments": [
              "Tecan Infinite plate reader",
              "Tecan Fluent"
            ],
            "evidence_sources": [],
            "top_evidence_sets": [],
            "rationale": "Yeast Screening - plate reader excluded due to readout_mismatch."
          },
          {
            "module_id": "module_12",
            "module_name": "Yeast Screening - EchoMS",
            "module_status": "excluded",
            "score": 0.0,
            "exclusion_reason": "template_not_selected",
            "required_instruments": [
              "SCIEX Echo MS System",
              "Tecan Fluent",
              "Centrifuge"
            ],
            "evidence_sources": [],
            "top_evidence_sets": [],
            "rationale": "Yeast Screening - EchoMS excluded due to template_not_selected."
          }
        ],
        "citations": [
          {
            "id": 1,
            "source_id": "text:newlabeledpetanaloguesenablethefunctionalscreeni",
            "source": "New Labeled PET Analogues Enable the Functional Screening and",
            "title": "",
            "section": "selection_evidence"
          },
          {
            "id": 2,
            "source_id": "text:mechanoenzymaticreactionsforthehydrolysisof",
            "source": "Mechanoenzymatic reactions for the hydrolysis of",
            "title": "",
            "section": "selection_evidence"
          },
          {
            "id": 3,
            "source_id": "text:2025vol35",
            "source": "2025 \uf0efVol. 35",
            "title": "",
            "section": "selection_evidence"
          },
          {
            "id": 4,
            "source_id": "text:functionalandstructuralcharacterizationofpetases",
            "source": "Functional and Structural Characterization of PETase SM14 from",
            "title": "",
            "section": "selection_evidence"
          },
          {
            "id": 5,
            "source_id": "doi:10.1038/s41467-022-34908-z",
            "source": "Article https://doi.org/10.1038/s41467-022-34908-z",
            "title": "",
            "section": "selection_evidence"
          },
          {
            "id": 6,
            "source_id": "text:academiceditor",
            "source": "Academic Editor:",
            "title": "",
            "section": "selection_evidence"
          },
          {
            "id": 7,
            "source_id": "text:received6april2025revised2june2025accepted10june",
            "source": "Received:6 April 2025.Revised:2 June 2025.Accepted:10 June 2025",
            "title": "",
            "section": "selection_evidence"
          },
          {
            "id": 8,
            "source_id": "text:received16august2021revised18september2021accept",
            "source": "Received:16August2021 Revised:18September2021 Accepted:22September2021",
            "title": "",
            "section": "selection_evidence"
          },
          {
            "id": 9,
            "source_id": "text:wwwchembiochemorg",
            "source": "www.chembiochem.org",
            "title": "",
            "section": "selection_evidence"
          },
          {
            "id": 10,
            "source_id": "text:thermostabilityandactivityimprovementsofpetasefr",
            "source": "Thermostability and Activity Improvements of PETase from",
            "title": "",
            "section": "selection_evidence"
          },
          {
            "id": 11,
            "source_id": "text:singledistalmutationenhancesactivityofknownpetas",
            "source": "Single Distal Mutation Enhances Activity of known PETases via",
            "title": "",
            "section": "selection_evidence"
          },
          {
            "id": 12,
            "source_id": "text:balancedirectedproteinengineeringofispetaseenhan",
            "source": "Balance-directed protein engineering of IsPETase enhances both PET hydrolysis activity",
            "title": "",
            "section": "Methods"
          },
          {
            "id": 13,
            "source_id": "text:1",
            "source": "1",
            "title": "",
            "section": "Methods"
          },
          {
            "id": 14,
            "source_id": "text:analysisofpolyethyleneterephthalatedegradationki",
            "source": "Analysis of Poly(ethylene terephthalate) degradation kinetics",
            "title": "",
            "section": "In silicomutant libraries of TS-PETase were synthesized by"
          },
          {
            "id": 15,
            "source_id": "text:mechanoenzymaticreactionsforthehydrolysisof",
            "source": "Mechanoenzymatic reactions for the hydrolysis of",
            "title": "",
            "section": "Results and discussion"
          },
          {
            "id": 16,
            "source_id": "text:academiceditor",
            "source": "Academic Editor:",
            "title": "",
            "section": "Researchers typically combine in silico approaches with PET-degrading activity assays"
          },
          {
            "id": 17,
            "source_id": "text:computationalandstructuralbiotechnologyjournal27",
            "source": "Computational and Structural Biotechnology Journal 27 (2025) 969\u2013977",
            "title": "",
            "section": "Computational and Structural Biotechnology Journal"
          },
          {
            "id": 18,
            "source_id": "text:article",
            "source": "ARTICLE",
            "title": "",
            "section": "Methods"
          },
          {
            "id": 19,
            "source_id": "text:received6april2025revised2june2025accepted10june",
            "source": "Received:6 April 2025.Revised:2 June 2025.Accepted:10 June 2025",
            "title": "",
            "section": "Efficiency scoring and homology modeling"
          },
          {
            "id": 20,
            "source_id": "text:preciseredesignforimprovingenzymerobustness",
            "source": "Precise redesign for improving enzyme robustness",
            "title": "",
            "section": "Experimental validation of the sheer number of possible"
          },
          {
            "id": 21,
            "source_id": "text:internationaljournalof",
            "source": "International Journal of",
            "title": "",
            "section": "Some\u00a0of\u00a0the\u00a0most\u00a0employed\u00a0genetic\u00a0engineering\u00a0methods\u00a0are\u00a0directed\u00a0evolution,"
          },
          {
            "id": 22,
            "source_id": "text:researcharticle",
            "source": "RESEARCH ARTICLE",
            "title": "",
            "section": "Theseresultsdemonstratedthefeasibilityofthebiosensor-based"
          },
          {
            "id": 23,
            "source_id": "text:computationalinsightsintothecatalyticmechanismof",
            "source": "Computational Insights into the Catalytic Mechanism of",
            "title": "",
            "section": "Because of the potentially different experimental conditions"
          },
          {
            "id": 24,
            "source_id": "text:caoetalbioresourcesandbioprocessing20231094",
            "source": "Cao\u00a0et\u00a0al. Bioresources and Bioprocessing           (2023) 10:94",
            "title": "",
            "section": "Overall, these results indicated that DuraPETase exhib -"
          },
          {
            "id": 25,
            "source_id": "text:1",
            "source": "1",
            "title": "",
            "section": "Plausibly, the void space observed in the film using X-ray CT is not due to an experimental artifact 269"
          },
          {
            "id": 26,
            "source_id": "text:analysisofpolyethyleneterephthalatedegradationki",
            "source": "Analysis of Poly(ethylene terephthalate) degradation kinetics",
            "title": "",
            "section": "Experimental methods"
          },
          {
            "id": 27,
            "source_id": "text:towardssitespecificinformation",
            "source": "Towards site-specific information",
            "title": "",
            "section": "Materials and methods"
          },
          {
            "id": 28,
            "source_id": "text:computationaldesignofacutinaseforplasticbiodegra",
            "source": "Computational design of a cutinase for plastic biodegradation by mining",
            "title": "",
            "section": "RF model outperformed the other two ML methods, the optimal"
          },
          {
            "id": 29,
            "source_id": "text:towardssitespecificinformation",
            "source": "Towards site-specific information",
            "title": "",
            "section": "To evaluate experimentally the influence of temperature on the spectral quality of our PETase, we recorded"
          },
          {
            "id": 30,
            "source_id": "text:carteretalmicrobialcellfactories202423319",
            "source": "Carter\u00a0et\u00a0al. Microbial Cell Factories          (2024) 23:319",
            "title": "",
            "section": "Conclusions"
          },
          {
            "id": 31,
            "source_id": "text:cinematic",
            "source": "Cinematic",
            "title": "",
            "section": "Simulation of Substrate-to-Product"
          },
          {
            "id": 32,
            "source_id": "text:article",
            "source": "ARTICLE",
            "title": "",
            "section": "Results"
          },
          {
            "id": 33,
            "source_id": "text:enhancingpetdegradingenzymesacombinatory",
            "source": "Enhancing PET Degrading Enzymes: A Combinatory",
            "title": "",
            "section": "Machine learning and deep learning methods have been"
          },
          {
            "id": 34,
            "source_id": "text:insightsintotheenhancementofthepolyethyleneterep",
            "source": "Insights into the Enhancement of the Poly(ethylene terephthalate)",
            "title": "",
            "section": "COMPUTATIONAL METHODS"
          },
          {
            "id": 35,
            "source_id": "text:characterizationandengineeringofa",
            "source": "Characterization and engineering of a",
            "title": "",
            "section": "Both the IFD results and MD simulations independently in-"
          },
          {
            "id": 36,
            "source_id": "text:newinsightsintothefunctionandglobaldistributiono",
            "source": "New Insights into the Function and Global Distribution of",
            "title": "",
            "section": "MATERIALS AND METHODS"
          },
          {
            "id": 37,
            "source_id": "text:80",
            "source": "80",
            "title": "",
            "section": "Computational redesign of a hydrolase for nearly complete PET depolymerization at"
          },
          {
            "id": 38,
            "source_id": "text:citationsalesjcsdecastro",
            "source": "Citation: Sales, J.C.S.; de Castro,",
            "title": "",
            "section": "To evaluate the biodepolymerization process and consolidate the results obtained by"
          },
          {
            "id": 39,
            "source_id": "text:activityofananaerobic",
            "source": "Activity of an anaerobic",
            "title": "",
            "section": "3.3 Modeling Thb and HiC"
          },
          {
            "id": 40,
            "source_id": "doi:10.1038/s41467-024-45662-9",
            "source": "Article https://doi.org/10.1038/s41467-024-45662-9",
            "title": "",
            "section": "Results"
          },
          {
            "id": 41,
            "source_id": "doi:10.1038/s41467-022-34908-z",
            "source": "Article https://doi.org/10.1038/s41467-022-34908-z",
            "title": "",
            "section": "Results and discussion"
          },
          {
            "id": 42,
            "source_id": "doi:10.1038/s41467-022-35237-x",
            "source": "Article https://doi.org/10.1038/s41467-022-35237-x",
            "title": "",
            "section": "Docking simulations with a PET trimer reveal the potential for binding"
          },
          {
            "id": 43,
            "source_id": "text:engineeringsurfaceelectrostaticsaffordscontrolov",
            "source": "Engineering surface electrostatics affords control over morphological 1",
            "title": "",
            "section": "Materials and Methods 272"
          },
          {
            "id": 44,
            "source_id": "text:qmmmstudyoftheenzymaticbiodegradationmechanismof",
            "source": "QM/MM Study of the Enzymatic Biodegradation Mechanism of",
            "title": "",
            "section": "\u25a0 RESULTS AND DISCUSSION"
          },
          {
            "id": 45,
            "source_id": "text:unravelingtheinterplaybetweenstabilityandflexibi",
            "source": "Unraveling the Interplay between Stability and Flexibility in the",
            "title": "",
            "section": "Further projections of simulation trajectories onto the PCs"
          },
          {
            "id": 46,
            "source_id": "text:received6december2024revised25march2025accepted8",
            "source": "Received:6 December 2024.Revised:25 March 2025.Accepted:8 April 2025",
            "title": "",
            "section": "Materials and methods"
          },
          {
            "id": 47,
            "source_id": "text:acceleratedpolyethyleneterephthalatepetenzymatic",
            "source": "Accelerated Polyethylene Terephthalate (PET) Enzymatic",
            "title": "",
            "section": "Results and Discussion"
          },
          {
            "id": 48,
            "source_id": "text:recyclableenzymatichydrolysiswithmetalorganicfra",
            "source": "Recyclable Enzymatic Hydrolysis with Metal\u2212Organic Framework",
            "title": "",
            "section": "RESULTS AND DISCUSSION"
          },
          {
            "id": 49,
            "source_id": "text:functionalandstructuralcharacterizationofpetases",
            "source": "Functional and Structural Characterization of PETase SM14 from",
            "title": "",
            "section": "MATERIALS AND METHODS"
          },
          {
            "id": 50,
            "source_id": "text:1",
            "source": "1",
            "title": "",
            "section": "Experimental procedures"
          },
          {
            "id": 51,
            "source_id": "text:fbioe09656465may212021time17531",
            "source": "fbioe-09-656465 May 21, 2021 Time: 17:53 # 1",
            "title": "",
            "section": "The conventional culture-dependent methods, cutting-edge"
          },
          {
            "id": 52,
            "source_id": "text:computationaldesignofacutinaseforplasticbiodegra",
            "source": "Computational design of a cutinase for plastic biodegradation by mining",
            "title": "",
            "section": "As one of the state-of-the-art statistical methods, the logistic"
          },
          {
            "id": 53,
            "source_id": "text:fmicb11571265november52020time14171",
            "source": "fmicb-11-571265 November 5, 2020 Time: 14:17 # 1",
            "title": "",
            "section": "In a study that employed anin silico-based screening approach"
          },
          {
            "id": 54,
            "source_id": "text:insightsintotheenhancementofthepolyethyleneterep",
            "source": "Insights into the Enhancement of the Poly(ethylene terephthalate)",
            "title": "",
            "section": "Classical molecular dynamics (MD) simulations for the mutant"
          },
          {
            "id": 55,
            "source_id": "text:communicationschemistryarticle",
            "source": "communicationschemistry Article",
            "title": "",
            "section": "analysis simulations as the plateau value of the function:"
          },
          {
            "id": 56,
            "source_id": "text:kimetalmicrobcellfact20201997",
            "source": "Kim\u00a0et\u00a0al. Microb Cell Fact           (2020) 19:97",
            "title": "",
            "section": "Results"
          },
          {
            "id": 57,
            "source_id": "text:received6april2025revised2june2025accepted10june",
            "source": "Received:6 April 2025.Revised:2 June 2025.Accepted:10 June 2025",
            "title": "",
            "section": "Discussion"
          },
          {
            "id": 58,
            "source_id": "doi:10.1038/s41467-024-45523-5",
            "source": "Article https://doi.org/10.1038/s41467-024-45523-5",
            "title": "",
            "section": "Methods"
          },
          {
            "id": 59,
            "source_id": "doi:10.1038/s41467-024-45523-5",
            "source": "Article https://doi.org/10.1038/s41467-024-45523-5",
            "title": "",
            "section": "Taken together, these results suggest that the reaction plateau for"
          },
          {
            "id": 60,
            "source_id": "text:citationedwardsslenzayas",
            "source": "Citation: Edwards, S.; Le\u00f3n-Zayas,",
            "title": "",
            "section": "mixed_with"
          },
          {
            "id": 61,
            "source_id": "text:advancedtechnologiesforplasticwasterecycling",
            "source": "Advanced technologies for plastic waste recycling:",
            "title": "",
            "section": "performed_at_temperature"
          },
          {
            "id": 62,
            "source_id": "text:fmicb161599470june282025time1931",
            "source": "fmicb-16-1599470 June 28, 2025 Time: 19:3 # 1",
            "title": "",
            "section": "performed_at_temperature"
          },
          {
            "id": 63,
            "source_id": "text:polymers",
            "source": "polymers",
            "title": "",
            "section": "performed_at_temperature"
          },
          {
            "id": 64,
            "source_id": "text:1",
            "source": "1",
            "title": "",
            "section": "performed_at_temperature"
          },
          {
            "id": 65,
            "source_id": "text:662naturevol60428april2022",
            "source": "662 | Nature | Vol 604 | 28 April 2022",
            "title": "",
            "section": "Methods"
          },
          {
            "id": 66,
            "source_id": "text:1",
            "source": "1",
            "title": "",
            "section": "Supplementary Methods 1: Description of methods 368"
          },
          {
            "id": 67,
            "source_id": "text:moogetalmicrobcellfact201918171",
            "source": "Moog\u00a0et\u00a0al. Microb Cell Fact          (2019) 18:171",
            "title": "",
            "section": "Results: Using the photosynthetic microalga Phaeodactylum tricornutum as a chassis we generated a microbial cell"
          },
          {
            "id": 68,
            "source_id": "text:communicationsbiologyarticle",
            "source": "communicationsbiology Article",
            "title": "",
            "section": "Here, we developed a computational design approach based on the struc-"
          },
          {
            "id": 69,
            "source_id": "text:communicationsbiologyarticle",
            "source": "communicationsbiology Article",
            "title": "",
            "section": "Computational enzyme design"
          },
          {
            "id": 70,
            "source_id": "text:conformationalselectionofatryptophansidechaindri",
            "source": "Conformational Selection of a Tryptophan Side Chain Drives the",
            "title": "",
            "section": "In this work, we employ molecular dynamics (MD) and"
          },
          {
            "id": 71,
            "source_id": "text:carteretalmicrobialcellfactories202423319",
            "source": "Carter\u00a0et\u00a0al. Microbial Cell Factories          (2024) 23:319",
            "title": "",
            "section": "Results We found expression in SHuffle T7 Express results in higher active expression of IsPETase compared"
          },
          {
            "id": 72,
            "source_id": "text:fmicb161599470june282025time1931",
            "source": "fmicb-16-1599470 June 28, 2025 Time: 19:3 # 1",
            "title": "",
            "section": "To address the limitations of existing methods in developing"
          },
          {
            "id": 73,
            "source_id": "text:structuralinsightsintoterephthalateesterhydrolys",
            "source": "Structural Insights into (Tere)phthalate-Ester Hydrolysis by a",
            "title": "",
            "section": "Methods for mitigating the product inhibition during"
          },
          {
            "id": 74,
            "source_id": "text:catalyticfeaturesandthermal",
            "source": "Catalytic Features and Thermal",
            "title": "",
            "section": "Molecular Dynamics Simulations"
          },
          {
            "id": 75,
            "source_id": "text:analysisofpolyethyleneterephthalatedegradationki",
            "source": "Analysis of Poly(ethylene terephthalate) degradation kinetics",
            "title": "",
            "section": "Optimization and simulation were performed using Math-"
          },
          {
            "id": 76,
            "source_id": "text:kimetalmicrobcellfact20201997",
            "source": "Kim\u00a0et\u00a0al. Microb Cell Fact           (2020) 19:97",
            "title": "",
            "section": "Methods"
          },
          {
            "id": 77,
            "source_id": "text:carteretalmicrobialcellfactories202423319",
            "source": "Carter\u00a0et\u00a0al. Microbial Cell Factories          (2024) 23:319",
            "title": "",
            "section": "Methods"
          },
          {
            "id": 78,
            "source_id": "text:characterizationandengineeringofatwoenzyme",
            "source": "Characterization and engineering of a two-enzyme",
            "title": "",
            "section": "Methods"
          },
          {
            "id": 79,
            "source_id": "text:1",
            "source": "1",
            "title": "",
            "section": "Materials and methods 253"
          },
          {
            "id": 80,
            "source_id": "text:2025vol35",
            "source": "2025 \uf0efVol. 35",
            "title": "",
            "section": "Materials and Methods"
          },
          {
            "id": 81,
            "source_id": "text:communicationsbiologyarticle",
            "source": "communicationsbiology Article",
            "title": "",
            "section": "Loop remodeling"
          },
          {
            "id": 82,
            "source_id": "text:bacteriologyannouncement",
            "source": "| Bacteriology | Announcement",
            "title": "",
            "section": "Conceptualization, Funding acquisition, Methodology, Project administration, Resources,"
          },
          {
            "id": 83,
            "source_id": "text:1",
            "source": "1",
            "title": "",
            "section": "Methodology: RMD, ES, EA 642"
          },
          {
            "id": 84,
            "source_id": "text:fmicb13888343april62022time16361",
            "source": "fmicb-13-888343 April 6, 2022 Time: 16:36 # 1",
            "title": "",
            "section": "Met177, results from the same study also indicated Gly105,"
          },
          {
            "id": 85,
            "source_id": "text:academiceditorarnaudchatonnet",
            "source": "Academic Editor: Arnaud Chatonnet",
            "title": "",
            "section": "The results of the colorimetric quantitative detection indicate that Gs no longer exhibits"
          },
          {
            "id": 86,
            "source_id": "text:journalofhazardousmaterials4612024132632",
            "source": "Journal of Hazardous Materials 461 (2024) 132632",
            "title": "",
            "section": "performed_at_temperature"
          },
          {
            "id": 87,
            "source_id": "text:article",
            "source": "ARTICLE",
            "title": "",
            "section": "mixed_with"
          },
          {
            "id": 88,
            "source_id": "text:fmicb161599470june282025time1931",
            "source": "fmicb-16-1599470 June 28, 2025 Time: 19:3 # 1",
            "title": "",
            "section": "4 Discussion and conclusion"
          },
          {
            "id": 89,
            "source_id": "text:fmicb12778828december172021time14331",
            "source": "fmicb-12-778828 December 17, 2021 Time: 14:33 # 1",
            "title": "",
            "section": "These results established a theoretical basis for the design of"
          },
          {
            "id": 90,
            "source_id": "text:researchopenaccess",
            "source": "RESEARCH Open Access",
            "title": "",
            "section": "Results"
          },
          {
            "id": 91,
            "source_id": "text:2025vol35",
            "source": "2025 \uf0efVol. 35",
            "title": "",
            "section": "Results and Discussion"
          },
          {
            "id": 92,
            "source_id": "text:1",
            "source": "1",
            "title": "",
            "section": "Directed Evolution Results"
          },
          {
            "id": 93,
            "source_id": "text:enhancingpetdegradingenzymesacombinatory",
            "source": "Enhancing PET Degrading Enzymes: A Combinatory",
            "title": "",
            "section": "Conclusions"
          },
          {
            "id": 94,
            "source_id": "text:1",
            "source": "1",
            "title": "",
            "section": "Results"
          },
          {
            "id": 95,
            "source_id": "text:lietalbioresourcesandbioprocessing20231026",
            "source": "Li\u00a0et\u00a0al. Bioresources and Bioprocessing           (2023) 10:26",
            "title": "",
            "section": "Results and\u00a0discussion"
          },
          {
            "id": 96,
            "source_id": "text:computationalinsightsintothecatalyticmechanismof",
            "source": "Computational Insights into the Catalytic Mechanism of",
            "title": "",
            "section": "Computational Insights into the Catalytic Mechanism of"
          },
          {
            "id": 97,
            "source_id": "text:methodsx92022101815",
            "source": "MethodsX 9 (2022) 101815",
            "title": "",
            "section": "MethodsX"
          },
          {
            "id": 98,
            "source_id": "text:characterizationandengineering",
            "source": "Characterization and engineering",
            "title": "",
            "section": "2 Materials and methods"
          },
          {
            "id": 99,
            "source_id": "text:1",
            "source": "1",
            "title": "",
            "section": "Materials and Methods"
          },
          {
            "id": 100,
            "source_id": "text:1",
            "source": "1",
            "title": "",
            "section": "Performing directed evolution using machine learning on the computer is known as in silico"
          },
          {
            "id": 101,
            "source_id": "text:machinelearningguidedidentificationofpethydrolas",
            "source": "Machine Learning-Guided Identification of PET Hydrolases from",
            "title": "",
            "section": "Identified Using Bioinformatics and Iterative Machine"
          },
          {
            "id": 102,
            "source_id": "text:unravelingtheinterplaybetweenstabilityandflexibi",
            "source": "Unraveling the Interplay between Stability and Flexibility in the",
            "title": "",
            "section": "Our results align with these findings, showing that Thermo-"
          },
          {
            "id": 103,
            "source_id": "text:computationalandstructuralbiotechnologyjournal27",
            "source": "Computational and Structural Biotechnology Journal 27 (2025) 969\u2013977",
            "title": "",
            "section": "C simulations are"
          },
          {
            "id": 104,
            "source_id": "text:moleculardetailsofpolyesterdecrystallizationviam",
            "source": "Molecular Details of Polyester Decrystallization via Molecular",
            "title": "",
            "section": "Pressure Molecular Dynamics Simulation: The Langevin Piston"
          },
          {
            "id": 105,
            "source_id": "text:september2024vol34no9",
            "source": "September 2024 \uf0efVol. 34 \uf0efNo. 9",
            "title": "",
            "section": "44. Parrinello M, Rahman A. 1981. Polymorphic transiti ons in single crystals: a new molecular dynamics method. J. Appl. Phys. 52:"
          },
          {
            "id": 106,
            "source_id": "text:singledistalmutationenhancesactivityofknownpetas",
            "source": "Single Distal Mutation Enhances Activity of known PETases via",
            "title": "",
            "section": "All productionsimulationswereconductedunder theisothermal,isobaricconditions(NPT) with"
          },
          {
            "id": 107,
            "source_id": "text:newlabeledpetanaloguesenablethefunctionalscreeni",
            "source": "New Labeled PET Analogues Enable the Functional Screening and",
            "title": "",
            "section": "labeled_with"
          },
          {
            "id": 108,
            "source_id": "text:fritzscheetalmicrobialcellfactories202423274",
            "source": "Fritzsche\u00a0et\u00a0al. Microbial Cell Factories          (2024) 23:274",
            "title": "",
            "section": "mixed_with"
          },
          {
            "id": 109,
            "source_id": "text:fritzscheetalmicrobialcellfactories202423274",
            "source": "Fritzsche\u00a0et\u00a0al. Microbial Cell Factories          (2024) 23:274",
            "title": "",
            "section": "performed_at_temperature"
          },
          {
            "id": 110,
            "source_id": "text:environmentalmicrobiologyresearcharticle",
            "source": "| Environmental Microbiology | Research Article",
            "title": "",
            "section": "induced_with"
          },
          {
            "id": 111,
            "source_id": "text:newlabeledpetanaloguesenablethefunctionalscreeni",
            "source": "New Labeled PET Analogues Enable the Functional Screening and",
            "title": "",
            "section": "Taking all of the results and limitations into account, it is"
          },
          {
            "id": 112,
            "source_id": "text:researcharticle",
            "source": "RESEARCH ARTICLE",
            "title": "",
            "section": "2 | RESULTS AND DISCUSSION"
          },
          {
            "id": 113,
            "source_id": "text:editorspickenvironmentalmicrobiologyresearcharti",
            "source": "| Editor\u2019s Pick | Environmental Microbiology | Research Article",
            "title": "",
            "section": "Methodology, Project administration, Resources, Software, Validation, Visualization,"
          },
          {
            "id": 114,
            "source_id": "text:journalofbasicmicrobiology",
            "source": "Journal of Basic Microbiology",
            "title": "",
            "section": "Seong Hyeon Lee: conceptualization, methodology, investigation,"
          },
          {
            "id": 115,
            "source_id": "doi:10.1038/s41467-025-61599-z",
            "source": "Article https://doi.org/10.1038/s41467-025-61599-z",
            "title": "",
            "section": "Program of China (2024YFA0917603), the Computational Biology Key"
          },
          {
            "id": 116,
            "source_id": "text:received6april2025revised2june2025accepted10june",
            "source": "Received:6 April 2025.Revised:2 June 2025.Accepted:10 June 2025",
            "title": "",
            "section": "Lab (IAC) at KAUST for providing the computational and exper-"
          },
          {
            "id": 117,
            "source_id": "text:journalofhazardousmaterials4552023131574",
            "source": "Journal of Hazardous Materials 455 (2023) 131574",
            "title": "",
            "section": "Christina Gkountela : Methodology, Validation, Formal analysis,"
          },
          {
            "id": 118,
            "source_id": "text:titleidentificationofprospectivepetasesacrosspro",
            "source": "Title: Identification of Prospective PETases Across Prokaryotes Using an in silico Approach",
            "title": "",
            "section": "Availability of data and materials: The data supporting the results are provided with the"
          },
          {
            "id": 119,
            "source_id": "text:machinelearningguidedidentificationofpethydrolas",
            "source": "Machine Learning-Guided Identification of PET Hydrolases from",
            "title": "",
            "section": "METHODS"
          },
          {
            "id": 120,
            "source_id": "text:developmentofahighlyactiveengineeredpetaseenzyme",
            "source": "Development of a highly active engineered PETase enzyme",
            "title": "",
            "section": "SB, RC contributed to methodology, investigation,"
          },
          {
            "id": 121,
            "source_id": "doi:10.1038/s41467-022-35237-x",
            "source": "Article https://doi.org/10.1038/s41467-022-35237-x",
            "title": "",
            "section": "Results"
          },
          {
            "id": 122,
            "source_id": "text:journalofhazardousmaterials4552023131574",
            "source": "Journal of Hazardous Materials 455 (2023) 131574",
            "title": "",
            "section": "The results demonstrate that Dm PETase was able to degrade all"
          },
          {
            "id": 123,
            "source_id": "text:journalofhazardousmaterials4552023131574",
            "source": "Journal of Hazardous Materials 455 (2023) 131574",
            "title": "",
            "section": "The results of the degradation study on PCL powder showed that"
          },
          {
            "id": 124,
            "source_id": "text:1",
            "source": "1",
            "title": "",
            "section": "The 29 candidate enzyme variants originating from the different screening methods were then subject to"
          },
          {
            "id": 125,
            "source_id": "text:662naturevol60428april2022",
            "source": "662 | Nature | Vol 604 | 28 April 2022",
            "title": "",
            "section": "The authors declare that all data supporting the findings of this study"
          },
          {
            "id": 126,
            "source_id": "text:researcharticle",
            "source": "RESEARCH ARTICLE",
            "title": "",
            "section": "Initially, we started the MD simulation assuming the PET L-shape"
          },
          {
            "id": 127,
            "source_id": "text:anultrasensitivecomamonasthiooxidansbiosensorfor",
            "source": "An Ultra-SensitiveComamonas thiooxidansBiosensor for the",
            "title": "",
            "section": "Table 3Current methods used to assay PET degradation mainly monitoring hydrolytic TPA release"
          },
          {
            "id": 128,
            "source_id": "text:computationalandstructuralbiotechnologyjournal27",
            "source": "Computational and Structural Biotechnology Journal 27 (2025) 969\u2013977",
            "title": "",
            "section": "Molecular simulations, modelling, and analysis were performed by"
          },
          {
            "id": 129,
            "source_id": "text:efficientsecretionofaplastic",
            "source": "Efficient secretion of a plastic",
            "title": "",
            "section": "ing\u2014original draft, Writing\u2014review & editing BS: Investigation, Methodology, Writing\u2014review & editing KK:"
          },
          {
            "id": 130,
            "source_id": "doi:10.1038/s41467-023-39201-1",
            "source": "Article https://doi.org/10.1038/s41467-023-39201-1",
            "title": "",
            "section": "Results"
          },
          {
            "id": 131,
            "source_id": "text:characterizationandengineeringofatwoenzyme",
            "source": "Characterization and engineering of a two-enzyme",
            "title": "",
            "section": "Discussion"
          },
          {
            "id": 132,
            "source_id": "doi:10.1038/s41467-023-39201-1",
            "source": "Article https://doi.org/10.1038/s41467-023-39201-1",
            "title": "",
            "section": "Discussion"
          },
          {
            "id": 133,
            "source_id": "text:vol0123456789",
            "source": "Vol.:(0123456789)",
            "title": "",
            "section": "Different pH values, drying methods and solutions were"
          },
          {
            "id": 134,
            "source_id": "text:frontiersinmicrobiology01frontiersinorg",
            "source": "Frontiers in Microbiology 01 frontiersin.org",
            "title": "",
            "section": "Based on the findings of the double mutation (DM) strategy"
          },
          {
            "id": 135,
            "source_id": "text:internationaljournalof",
            "source": "International Journal of",
            "title": "",
            "section": "II, the already described ester bond breakage results in the production of a MHET monomer"
          },
          {
            "id": 136,
            "source_id": "text:anultrasensitivecomamonasthiooxidansbiosensorfor",
            "source": "An Ultra-SensitiveComamonas thiooxidansBiosensor for the",
            "title": "",
            "section": "RESULTS"
          },
          {
            "id": 137,
            "source_id": "text:vol0123456789",
            "source": "Vol.:(0123456789)",
            "title": "",
            "section": "The absorption measurement also provided the best results"
          },
          {
            "id": 138,
            "source_id": "text:finetuningenzymeactivityassays",
            "source": "Fine tuning enzyme activity assays",
            "title": "",
            "section": "Results and discussion"
          },
          {
            "id": 139,
            "source_id": "text:screeningputativepolyesterpolyurethanedegrading",
            "source": "Screening putative polyester polyurethane degrading",
            "title": "",
            "section": "F-test on the results also shows that the automated addition with"
          },
          {
            "id": 140,
            "source_id": "text:moogetalmicrobcellfact201918171",
            "source": "Moog\u00a0et\u00a0al. Microb Cell Fact          (2019) 18:171",
            "title": "",
            "section": "Essen for helpful discussions and valuable technical advices supporting the"
          },
          {
            "id": 141,
            "source_id": "text:kawaietalambexpress202212134",
            "source": "Kawai\u00a0et\u00a0al. AMB Express          (2022) 12:134",
            "title": "",
            "section": "Results"
          },
          {
            "id": 142,
            "source_id": "text:vol0123456789",
            "source": "Vol.:(0123456789)",
            "title": "",
            "section": "Results"
          },
          {
            "id": 143,
            "source_id": "text:methodsx92022101815",
            "source": "MethodsX 9 (2022) 101815",
            "title": "",
            "section": "As a validation of the methodology the effect of the X C , on the product release rate of the gold"
          },
          {
            "id": 144,
            "source_id": "text:functionalandstructuralcharacterizationofpetases",
            "source": "Functional and Structural Characterization of PETase SM14 from",
            "title": "",
            "section": "concentration"
          }
        ],
        "decision_evidence": {
          "module_1": {
            "sections": [
              {
                "type": "methodology_section",
                "score": 0.6105992197990417,
                "heading": "Methods",
                "text": "Site-directed mutagenesis \n The template used to create all variants is shown in the Supplementary Table. 2.22 The \nvariant IsPETaseS121E/D186H/S242T/N246D was subcloned into a pET-15b expression vector at the \nNdeI and XhoI restriction sites. The forward and reverse primers used are detailed in \nSupplementary Table. 1",
                "source": "Balance-directed protein engineering of IsPETase enhances both PET hydrolysis activity",
                "title": ""
              },
              {
                "type": "methodology_section",
                "score": 0.5928301215171814,
                "heading": "Methods",
                "text": "Chemicals, Reagents and Polymers.  All chemicals and reagents used in this work were of analytical \ngrade. Buffer components, para-nitrophenyl butyrate (p-NPB), bovine serum albumin (BSA) and HPLC-grade \nmethanol were purchased from Sigma-Aldrich (USA). Films of polyethylene terephthalate (PET), with a thick-\nness of 0",
                "source": "1",
                "title": ""
              },
              {
                "type": "methodology_section",
                "score": 0.5709640979766846,
                "heading": "In silicomutant libraries of TS-PETase were synthesized by",
                "text": "Twist Biosciences and cloned into the pET21a+ plasmid.\nRound one\u2013 directed evolution library was generated using\nWT IsPETase as template and the following PCR conditions\nfor a\ufb01nal reaction of 50\u03bcl: 2\u03bcl of 10 mM dGTP/dATP, 10\u03bcl\nof 10 mM dCTP/dTTP, 10 \u03bcl 55 mM MgCl\n2,5 \u03bcl1m M\nMnCl2,3 \u03bclo f1 0 \u03bcM IsPETase mut F/R, 2 fmol ",
                "source": "Analysis of Poly(ethylene terephthalate) degradation kinetics",
                "title": ""
              },
              {
                "type": "methodology_section",
                "score": 0.5384008288383484,
                "heading": "Results and discussion",
                "text": "Enzyme selection\nInitially six PETases with potentially interesting properties in\nthis system were selected (Table 1). These were,Is-PETase, Pol-\nyangium brachysporum PETase (Pb-PETase), Acidovorax dela-\n\ue103eldii PETase (Ad-PETase), Burkholderiales bacterium PETase\n(Bb-PETase), and PET2 from an uncultured organism.25,28 ",
                "source": "Mechanoenzymatic reactions for the hydrolysis of",
                "title": ""
              },
              {
                "type": "methodology_section",
                "score": 0.5372629165649414,
                "heading": "Researchers typically combine in silico approaches with PET-degrading activity assays",
                "text": "to screen novel PETases. This dual approach allows them to identify enzymes that are\nstructurally similar to IsPETases and capable of degrading PET. The most commonly used\nassays for measuring PET-degrading activity are depicted in Figure 2. These screening\ntechniques vary in scale from low to ultra-high throughput, de",
                "source": "Academic Editor:",
                "title": ""
              },
              {
                "type": "methodology_section",
                "score": 0.5564756393432617,
                "heading": "Computational and Structural Biotechnology Journal",
                "text": "journal homepag e: www.else vier.com/loc ate/csbj\nhttps://doi.org/10.1016/j.csbj.2025.03.006\nReceived 7 January 2025; Received in revised form 3 March 2025; Accepted 4 March 2025  \nComputational and Structural Biotechnology Journal 27 (2025) 969\u2013977\n970\nfurther optimized by harnessing a structure-based machine learning",
                "source": "Computational and Structural Biotechnology Journal 27 (2025) 969\u2013977",
                "title": ""
              },
              {
                "type": "methodology_section",
                "score": 0.6218725442886353,
                "heading": "Methods",
                "text": "Cloning. The PETase fromIdeonella sakaiensis (GenBank accession number:\nGAP38373.1) without the N-terminal 29 amino acids was chemically synthesized\n(GENE ray Biotech Co., Shanghai, China), ligated into the pET32a vector, and\nexpressed in Escherichia coli.\nSite-directed mutagenesis. Variants were constructed by using a",
                "source": "ARTICLE",
                "title": ""
              },
              {
                "type": "methodology_section",
                "score": 0.605584979057312,
                "heading": "Efficiency scoring and homology modeling",
                "text": "A scoring system was developed to rank the candidate PETases, \neight known PET hydrolases, and 12 seed sequences containing \nthe DLH domain. This scoring was made by comparison to the \nPETase sequence from IsPETase, considering some of the key \nresidues that are known to contribute to the activity and sta-\nbility ofIsP",
                "source": "Received:6 April 2025.Revised:2 June 2025.Accepted:10 June 2025",
                "title": ""
              },
              {
                "type": "methodology_section",
                "score": 0.42654043436050415,
                "heading": "Experimental validation of the sheer number of possible",
                "text": "combinations resulting from saturated combinatorial muta-\ntions on 20 coevolving residue pairs, 7980 in total, would be\nprohibitive. Because screening potential stability-enhancing\nmutations based on a single indicator has limitations, we\ncombined a static indicator (DDG) with dynamic indicators\n(RMSD, R\ng, and total H",
                "source": "Precise redesign for improving enzyme robustness",
                "title": ""
              },
              {
                "type": "methodology_section",
                "score": 0.41045188903808594,
                "heading": "Some\u00a0of\u00a0the\u00a0most\u00a0employed\u00a0genetic\u00a0engineering\u00a0methods\u00a0are\u00a0directed\u00a0evolution,",
                "text": "DNA\u00a0shuffling,\u00a0saturation\u00a0mutagenesis,\u00a0fusion,\u00a0site\u2010directed\u00a0mutagenesis,\u00a0and\u00a0truncation\u00a0\n[61].\u00a0In\u00a0directed\u00a0evolution,\u00a0no\u00a0data\u00a0on\u00a0the\u00a0protein\u00a0structure\u00a0and\u00a0function\u00a0are\u00a0required,\u00a0and\u00a0\nFigure 1. Scheme of the PET repeating unit, a molecule of 2PET, and the main PET degradation\nproducts.\nThe growing usage of enzymes in b",
                "source": "International Journal of",
                "title": ""
              },
              {
                "type": "methodology_section",
                "score": 0.40271681547164917,
                "heading": "Theseresultsdemonstratedthefeasibilityofthebiosensor-based",
                "text": "HTS system for MHETase. We anticipated that the activity of\nMHETase could be further enhanced by several rounds of iter-\nativeevolutionfacilitatedbyour\ufb02uorescentHTStool.\nSubsequently,single-pointmutationswereconstructedforthe\n23 mutated residues in MHETase mutants to analyze the con-\ntribution of each mutation to the d",
                "source": "RESEARCH ARTICLE",
                "title": ""
              },
              {
                "type": "methodology_section",
                "score": 0.39276209473609924,
                "heading": "Because of the potentially different experimental conditions",
                "text": "and the uncertainties in our calculated numbers mentioned\nabove, direct comparison of computed and observed kinetic\nquantities is difficult. It has also been suggested that as the\nsubstrate of this reaction is non-aqueous, classical Michaelis\u2013\nMenten kinetics cannot be used to relate reaction rates to\ncalculated energy",
                "source": "Computational Insights into the Catalytic Mechanism of",
                "title": ""
              },
              {
                "type": "methodology_section",
                "score": 0.45249563455581665,
                "heading": "Overall, these results indicated that DuraPETase exhib -",
                "text": "ited the highest catalytic activity at 30\u00a0\u00b0C, and is a suitable \nenzyme for subsequent heterologous expression in C. tes-\ntosteroni CNB-1.\nFunctional expression of\u00a0DuraPETase enabled PET \ndegradation by\u00a0C. testosteroni CNB\u20111\nTo efficiently degrade PET, the secretion of DuraPETase \nis crucial, as PET is a high molecular",
                "source": "Cao\u00a0et\u00a0al. Bioresources and Bioprocessing           (2023) 10:94",
                "title": ""
              },
              {
                "type": "methodology_section",
                "score": 0.41441982984542847,
                "heading": "Plausibly, the void space observed in the film using X-ray CT is not due to an experimental artifact 269",
                "text": ".CC-BY-NC-ND 4.0 International licensemade available under a\n(which was not certified by peer review) is the author/funder, who has granted bioRxiv a license to display the preprint in perpetuity. It is \nThe copyright holder for this preprintthis version posted March 27, 2025. ; https://doi.org/10.1101/2025.03.24.64513",
                "source": "1",
                "title": ""
              },
              {
                "type": "methodology_section",
                "score": 0.394125759601593,
                "heading": "Experimental methods",
                "text": "Cloning and plasmid constructs\nAll plasmids used in this study were generated using the\npET21a+ backbone (2). Brie\ufb02y, IsPETase (residues 28\u2013 290) was\ncodon optimized for expression in E. coli and cloned into\npET21a+ with a C-terminal His-tag using PCR with Phusion\npolymerase (New England BioLabs) and primers listed in\n",
                "source": "Analysis of Poly(ethylene terephthalate) degradation kinetics",
                "title": ""
              },
              {
                "type": "methodology_section",
                "score": 0.266981840133667,
                "heading": "Materials and methods",
                "text": "Protein expression and purification\nLCCICCG-S165A and its active variant were expressed and purified according to previous studies36,40.\nNMR spectroscopy\nLCCICCG-S165A\nAll experiments recorded for backbone assignment at 50\u00b0C were acquired on a 800 MHz spectrometer equipped \nwith a 5-mm cryoprobe with pulsed field z-gra",
                "source": "Towards site-specific information",
                "title": ""
              },
              {
                "type": "methodology_section",
                "score": 0.25327831506729126,
                "heading": "RF model outperformed the other two ML methods, the optimal",
                "text": "PCC value for RF method was 0.716.\n3.3. Blind test and comparison with four traditional thermostability\nprediction methods\nA blind test was used to evaluate the generalization of the MDL\napproach. The dataset M1293 were divided into two datasets: 1000\nsingle-point variants (M1000), which were used for the 10-fold\ncross",
                "source": "Computational design of a cutinase for plastic biodegradation by mining",
                "title": ""
              },
              {
                "type": "methodology_section",
                "score": 0.23786388337612152,
                "heading": "To evaluate experimentally the influence of temperature on the spectral quality of our PETase, we recorded",
                "text": "on the same sample at 30\u00b0C and 50\u00b0C both the 1H-15N HSQC and 1H-15N TROSY correlation spectra using \nstandard Bruker pulse programs (hsqcf3gpph19 and trosyf3gpph19). Already at 30\u00b0C, signal intensity improved \nTime domain data size (points) Spectral width/carrier frequency (ppm)\nt1 t2 t3 F1 (1H) F2(15N) F3\n1H,15N HSQC ",
                "source": "Towards site-specific information",
                "title": ""
              },
              {
                "type": "methodology_section",
                "score": 0.3548228442668915,
                "heading": "Conclusions",
                "text": "Through this work we have shown that wild-type \nIsPETase is better produced in the cytoplasm of E. coli \nusing a disulfide bond forming host with disulfide bond \nisomerase. Production was increased by 13-fold over \noften used BL21(DE3) and purity was enhanced due to \noverexpression. IsPETase was purified from SHuffle T",
                "source": "Carter\u00a0et\u00a0al. Microbial Cell Factories          (2024) 23:319",
                "title": ""
              },
              {
                "type": "methodology_section",
                "score": 0.20152150094509125,
                "heading": "Simulation of Substrate-to-Product",
                "text": "Chemical Reactions with Chemical Accuracy\nUsing QuantaMind MD\nSong Xia and Deqiang Zhang\u2217\nMoleculeMind\nE-mail: deqiangzhang@moleculemind.com\nAbstract\nPolyethylene terephthalate hydrolases (PETases) are enzymes that catalyze the\nbreakdown of PET plastic. Previous studies have employed classical molecular dy-\nnamics (MD)",
                "source": "Cinematic",
                "title": ""
              },
              {
                "type": "methodology_section",
                "score": 0.18173913657665253,
                "heading": "Results",
                "text": "Isolation and identi \ufb01cation of a PET-degrading marine\nstrain P23. Several marine strains were screened from deep-sea\nsediment enrichment culture with PET powder as the sole carbon\nand energy source for growth. Among these PET-degrading\nstrains, a gram-positive strain termed P23 (Supplementary Fig. 1)\nwas selected for ",
                "source": "ARTICLE",
                "title": ""
              },
              {
                "type": "methodology_section",
                "score": 0.18133898079395294,
                "heading": "Machine learning and deep learning methods have been",
                "text": "applied to develop both novel plastic degrading enzymes as\nwell as PET hydrolase variants. Although this is an emerging\nstrategy with only a limited number of examples, a few\nremarkable studies have demonstrated the synergistic effect of\ncombining ML/AI and rational design methods. For instance,\nFAST-PETase is a varian",
                "source": "Enhancing PET Degrading Enzymes: A Combinatory",
                "title": ""
              },
              {
                "type": "methodology_section",
                "score": 0.43215855956077576,
                "heading": "COMPUTATIONAL METHODS",
                "text": "Building of (FAST-)PETase:PET Systems. The initial coordi-\nnates of the PETase enzyme were taken from the highest-resolved X-\nray crystal structure (0.92 \u00c5) of the apoenzyme available in the\nProtein Data Bank, with code 6EQE.\n25\nFor the FAST-PETase mutant,\nthe structure available with code 7SH6 was selected.\n16\nTo calc",
                "source": "Insights into the Enhancement of the Poly(ethylene terephthalate)",
                "title": ""
              },
              {
                "type": "methodology_section",
                "score": 0.41477370262145996,
                "heading": "Both the IFD results and MD simulations independently in-",
                "text": "dicate the PETase binding site is characterized by highly flexible,\nlarge aromatic side chains, such as Trp185, Tyr87, and Trp159,\nand Phe238 in the PETase double mutant. Binding of PET and\nPEF induces conformational changes in these residues relative to\nthe crystal structure; thus, modeling protein flexibility in re-\n",
                "source": "Characterization and engineering of a",
                "title": ""
              },
              {
                "type": "methodology_section",
                "score": 0.22036212682724,
                "heading": "MATERIALS AND METHODS",
                "text": "Bacterial strains, plasmids, and primers.Bacterial strains, plasmids, and primers used in this study\nare listed inTables 3and4. If not otherwise mentioned,Escherichia coliclones were grown in LB medium\n(1% tryptone/peptone, 0.5% yeast extract, and 1% NaCl) supplemented with appropriate antibiotics (25\n/H9262g/ml kanamy",
                "source": "New Insights into the Function and Global Distribution of",
                "title": ""
              },
              {
                "type": "methodology_section",
                "score": 0.19384853541851044,
                "heading": "Computational redesign of a hydrolase for nearly complete PET depolymerization at",
                "text": "industrially relevant high-solids loading. Nature Communications, 15(1). \nhttps://doi.org/10.1038/s41467-024-45662-9\n \n18. Shi, L., Liu, P., Tan, Z., Zhao, W., Gao, J., Gu, Q., Ma, H., Liu, H., & Zhu, L. (2023). \nComplete Depolymerization of PET Wastes by an Evolved PET Hydrolase from \n.CC-BY-NC-ND 4.0 International li",
                "source": "80",
                "title": ""
              },
              {
                "type": "methodology_section",
                "score": 0.19119375944137573,
                "heading": "To evaluate the biodepolymerization process and consolidate the results obtained by",
                "text": "HPLC, other analyses were performed on the material after the biological treatment, such\nas ATR-FTIR. Figure 12 presents the results obtained by this technique.\nFrom the ATR-FTIR analysis shown in Figure 12, it is observed, as in the tests in\nthe \ufb02asks, that the same pro\ufb01le of bands are characteristic of PET (close to ",
                "source": "Citation: Sales, J.C.S.; de Castro,",
                "title": ""
              },
              {
                "type": "methodology_section",
                "score": 0.1897507905960083,
                "heading": "3.3 Modeling Thb and HiC",
                "text": "The overlay of the HiC structure with the one from Thb\ndisplayed signi \ufb01cant differences between the two enzymes,\noffering a structural interpretation of their different speci\ufb01city on\naromatic and aliphatic polyesters. Strikingly, the HiC catalytic triad\n(Ser105, Asp160, and His173) aligned almost perfectly with that\nf",
                "source": "Activity of an anaerobic",
                "title": ""
              },
              {
                "type": "methodology_section",
                "score": 0.18921874463558197,
                "heading": "Results",
                "text": "Computational redesign of an ef\ufb01cient PET hydrolase\nPET hydrolases belong to serine-hydrolase family, a widely distributed\ngroup known for their relatively low substrate speci\ufb01city. The degra-\ndation function of PET hydrolases is thought to preexist as a pro-\nmiscuous function, which then evolves into a primary functio",
                "source": "Article https://doi.org/10.1038/s41467-024-45662-9",
                "title": ""
              }
            ],
            "edges": [],
            "assays": [],
            "queries": [
              "petase Mutagenesis PCR & DpnI Treatment",
              "petase Mutagenesis PCR & DpnI Treatment protocol",
              "petase mutagenesis",
              "mutagenesis",
              "petase pcr",
              "pcr",
              "petase dpni",
              "dpni",
              "petase primer",
              "primer"
            ]
          },
          "module_2": {
            "sections": [
              {
                "type": "methodology_section",
                "score": 0.5499393939971924,
                "heading": "Results and discussion",
                "text": "HFBI and PETase were functionally codisplayed on the surface of\nyeast cells\nIn our codisplay system, hydrophobin HFBI and PETase should play\ndifferent roles based on their unique protein structures. HFBI is\nthought to regulate the adsorption of yeast cells on the substrate PET.\nPETase is responsible for degrading the s",
                "source": "Article https://doi.org/10.1038/s41467-022-34908-z",
                "title": ""
              },
              {
                "type": "methodology_section",
                "score": 0.5329413414001465,
                "heading": "Docking simulations with a PET trimer reveal the potential for binding",
                "text": "within a large open cleft, as compared to the relatively narrow groove\nof the LCC active site (Fig.5C).\nEnzyme 305 also displays a major deletion, but more surprisingly\nin the opposite half of the core compared to 307. The missing\u03b1-helical\nregion would normally contribute half of the active site cavity and the\nHis resi",
                "source": "Article https://doi.org/10.1038/s41467-022-35237-x",
                "title": ""
              },
              {
                "type": "methodology_section",
                "score": 0.47703278064727783,
                "heading": "Materials and Methods 272",
                "text": "Amorphous PET film (ES30-FM-000145) and semi-crystalline PET powder (ES30-PD-006031) were purchased 273 \nfrom Goodfellow. Post-consumer plastic waste was obtained from PET sandwich packaging. All reagents for 274 \nmolecular biology and strains were purchased from New England Biolabs. All other reagents and buffer 275 \n",
                "source": "Engineering surface electrostatics affords control over morphological 1",
                "title": ""
              },
              {
                "type": "methodology_section",
                "score": 0.47501543164253235,
                "heading": "\u25a0 RESULTS AND DISCUSSION",
                "text": "Mechanism of PETase/MHET2. Our \ufb01rst goal was to\ndescribe the mechanism of hydrolysis of PET catalyzed by\nPETase. For this purpose, a model of this system was prepared\nwith a dimer (MHET\n2) manually docked in the active site of\nthe enzyme, as described in the Computational Methods\nsection. The substrate is broken symmet",
                "source": "QM/MM Study of the Enzymatic Biodegradation Mechanism of",
                "title": ""
              },
              {
                "type": "methodology_section",
                "score": 0.4699895977973938,
                "heading": "Further projections of simulation trajectories onto the PCs",
                "text": "with structural illustrations showcase the key motions in\nPETase (Figure 2E\u2212H). We observed that the most dominant\nstructural dynamics in these two PETases at both temperatures\nare related to the collective motions led by the PET-binding\nsite and catalytic site. Specifically, at 298 K, the D-loop exhibits\na twisting mo",
                "source": "Unraveling the Interplay between Stability and Flexibility in the",
                "title": ""
              },
              {
                "type": "methodology_section",
                "score": 0.23535579442977905,
                "heading": "Materials and methods",
                "text": "Metagenomic sequencing, assembly, and binning\nSequencing through de novo binning has been previously \ndescribed in detail for these samples [\n16]. Briefly , GB sediment \npush cores were collected by the human-operated vessel Alvin \nand research vessel Atlantis in November 2018 (AT42-05). \nOnshore, we extracted DNA for ",
                "source": "Received:6 December 2024.Revised:25 March 2025.Accepted:8 April 2025",
                "title": ""
              },
              {
                "type": "methodology_section",
                "score": 0.34440088272094727,
                "heading": "Results and Discussion",
                "text": "We base our study on the well-known PETase from Ideonella\nsakaiensis enzymatic activity.\n[18,19]\nPETase can follow different\npathways to produce TPA and monohydroxyethyl terephthalate\n(MHET) and ethylene Glycol (EG)\n[19\u201321]\n(Figure 1A). Here, we\ncompare the activity of this enzyme on untreated highly\ncrystalline (~ 35 ",
                "source": "Accelerated Polyethylene Terephthalate (PET) Enzymatic",
                "title": ""
              },
              {
                "type": "methodology_section",
                "score": 0.2220962941646576,
                "heading": "RESULTS AND DISCUSSION",
                "text": "Developing HiC Encapsulation and EGDB Hydrolysis\nConditions. NU-1000 was synthesized based on a reported\nprocedure (Figure S1).\n27\nEncapsulation conditions such as salt\nconcentration and pH of the solution have been shown to be\nhighly influential to the kinetics of protein intraparticle\ndiffusion and its encapsulation ",
                "source": "Recyclable Enzymatic Hydrolysis with Metal\u2212Organic Framework",
                "title": ""
              },
              {
                "type": "methodology_section",
                "score": 0.30925941467285156,
                "heading": "MATERIALS AND METHODS",
                "text": "PETase SM14 Sequence Analysis. The target protein (PETase)\nwas identified in the PAZy database (https://www.pazy.eu/doku.php)\namong the 119 sequences recognized as acting on PET. The protein\nsequence spanning residues 25\u2212284, classified by InterPro automatic\nannotation as a cutinase, is provided in the Supporting Infor",
                "source": "Functional and Structural Characterization of PETase SM14 from",
                "title": ""
              },
              {
                "type": "methodology_section",
                "score": 0.29734838008880615,
                "heading": "Experimental procedures",
                "text": "Expression and puri\ufb01ca?on of PETase enzymes \nDNA plasmids for wild -type PETase (PETase, I. sakaiensis , accession number: A0A0K8P6T7, \nAddgene number: #112202), hyperacNve mutant (Addgene number: #112203) and the impaired \nmutant (Addgene number: #112204) were purchased from Addgene.  Plasmids were transformed \ninto E",
                "source": "1",
                "title": ""
              },
              {
                "type": "methodology_section",
                "score": 0.2957752048969269,
                "heading": "The conventional culture-dependent methods, cutting-edge",
                "text": "multi-omics-based systems biology approaches, and molecular\nbiology techniques enable researchers to identify novel PET-\nhydrolyzing enzymes from the plastisphere to cleave ester bonds\nof PET ( Supplementary Table 1 ). Also, computational and\nmachine learning approaches enable the researcher to discover\nnovel potent PE",
                "source": "fbioe-09-656465 May 21, 2021 Time: 17:53 # 1",
                "title": ""
              },
              {
                "type": "methodology_section",
                "score": 0.18675188720226288,
                "heading": "As one of the state-of-the-art statistical methods, the logistic",
                "text": "regression (LR) model was used for calculation of the classi\ufb01cation\nand regression models. In this study, the R package glmnet was\nused as the LR machine learning package[44]. To obtain the opti-\nmal lambda parameter, the prediction effect was tested by iterat-\ning the lambda values. Finally, the optimal lambda value w",
                "source": "Computational design of a cutinase for plastic biodegradation by mining",
                "title": ""
              },
              {
                "type": "methodology_section",
                "score": 0.15985308587551117,
                "heading": "In a study that employed anin silico-based screening approach",
                "text": "to interrogate 52 genomes from the Streptomyces genus, a\npotential PETase-like gene was identi\ufb01ed in Streptomyces sp.\nSM14 (Almeida et al., 2019). Heterologous expression of the gene\nin Escherichia coli resulted in the extracellular production of an\nenzyme, SM14est, that was shown to have polyesterase activity\non polyc",
                "source": "fmicb-11-571265 November 5, 2020 Time: 14:17 # 1",
                "title": ""
              },
              {
                "type": "methodology_section",
                "score": 0.605884850025177,
                "heading": "Classical molecular dynamics (MD) simulations for the mutant",
                "text": "FAST-PETase and the wild-type PETase enzymes and their\nrespective enzyme:PET complexes were first performed to gain\ninsight into the structural changes induced by the mutations in\nthe FAST-PETase scaffold that might be important for the\nPET depolymerization. In a second step, multiscale QM/MM\nsimulations were employed ",
                "source": "Insights into the Enhancement of the Poly(ethylene terephthalate)",
                "title": ""
              },
              {
                "type": "methodology_section",
                "score": 0.15902355313301086,
                "heading": "analysis simulations as the plateau value of the function:",
                "text": "\u03ba\u00f0t\u00de\u00bc _q0 /C3 \u03b8 qt\u00f0\u00de\n/C0/C1/C10/C11\n1\n2 _q0\n/C12/C12/C12/C12/C10/C11\nwhere t is the timestep of the simulation,qt\u00f0\u00de is the value of the reaction\ncoordinate at timestept, _q0 is the initial rate of change of the reaction\ncoordinate for a given simulation,\u03b8\u00f0\u00de is the Heaviside step function, and\nangle brackets indicate th",
                "source": "communicationschemistry Article",
                "title": ""
              },
              {
                "type": "methodology_section",
                "score": 0.14491957426071167,
                "heading": "Results",
                "text": "Transformation of\u00a0microalgae\nChlamydomonas reinhardtii CC-124 (mt\u2212 [137c]) is \na common laboratory wild-type strain, which carries \nthe nit1 and nit2 mutations and is usually used for gene \ntransformation. C. reinhardtii CC-503 (cw92 mt+) is a \ncell wall-less mutant of CC-125 developed for efficient \ntransformation. In",
                "source": "Kim\u00a0et\u00a0al. Microb Cell Fact           (2020) 19:97",
                "title": ""
              },
              {
                "type": "methodology_section",
                "score": 0.4347204864025116,
                "heading": "Discussion",
                "text": "In this study , we developed a motif-based classification system \nto distinguish functional PETases from non\u2212/pre-functional vari-\nants or pseudo-PETases that utilize different substrates. The iden-\ntified PETase-defining M5 motif incorporates structural elements \nessential for efficient substrate recognition and catal",
                "source": "Received:6 April 2025.Revised:2 June 2025.Accepted:10 June 2025",
                "title": ""
              },
              {
                "type": "methodology_section",
                "score": 0.2526078224182129,
                "heading": "Methods",
                "text": "Materials\nPA6 \ufb01lm (0.2 mm thickness, 13.2% crystallinity by DSC, full material\ncharacterization available in Supplementary Table 1, Supplementary\nFig. 3, product ID: AM30-FM-000200), PA6 powder (particle size:\n5\u201350 \u00b5m, 47.6% crystallinity by DSC, full material characterization\navailable in Supplementary Table 3, produc",
                "source": "Article https://doi.org/10.1038/s41467-024-45523-5",
                "title": ""
              },
              {
                "type": "methodology_section",
                "score": 0.20102638006210327,
                "heading": "Taken together, these results suggest that the reaction plateau for",
                "text": "NylC\nK-TS is a consequence of lack of remaining hydrolysable substrate\nfor this enzyme following 10 days of reaction. Furthermore, typically\nfor more extensive enzymatic plastic depolymerizations, both rate and\nextent of deconstruction are highly sensitive to substrate\ncrystallinity\n61. However, for PA6 depolymerizatio",
                "source": "Article https://doi.org/10.1038/s41467-024-45523-5",
                "title": ""
              }
            ],
            "edges": [
              {
                "type": "methodology_edge",
                "score": 0.37403368949890137,
                "relation": "mixed_with",
                "value": "Gibson\nassembly was performed using reagents from NEB Gibson Assembly Cloning Kit.",
                "source": "Citation: Edwards, S.; Le\u00f3n-Zayas,"
              },
              {
                "type": "methodology_edge",
                "score": 0.27018192410469055,
                "relation": "performed_at_temperature",
                "value": "It works by turning\nraw materials into syngas a mix of gases like carbon dioxide,\nwater vapor, and methane through reactions with oxygen at\nhigh temperatures.",
                "source": "Advanced technologies for plastic waste recycling:"
              },
              {
                "type": "methodology_edge",
                "score": 0.2634957432746887,
                "relation": "performed_at_temperature",
                "value": "The peptide solutions were incubated at room\ntemperature for 24 h for self-assembly.",
                "source": "fmicb-16-1599470 June 28, 2025 Time: 19:3 # 1"
              },
              {
                "type": "methodology_edge",
                "score": 0.33683592081069946,
                "relation": "performed_at_temperature",
                "value": "The reaction mixture was incubated at room temperature for 10 min\nbefore being directly used in the transformation.",
                "source": "polymers"
              },
              {
                "type": "methodology_edge",
                "score": 0.33455929160118103,
                "relation": "performed_at_temperature",
                "value": "This duration \nincludes two days for the saturation of transformation cultures, followed by an additional two days for the low-\ntemperature expression cultures to reach saturation.",
                "source": "1"
              }
            ],
            "assays": [],
            "queries": [
              "petase HiFi Assembly & DH5\u03b1 Transformation",
              "petase HiFi Assembly & DH5\u03b1 Transformation protocol",
              "petase assembly",
              "assembly",
              "petase hifi",
              "hifi",
              "petase gibson",
              "gibson",
              "petase transformation",
              "transformation",
              "petase dh5a",
              "dh5a"
            ]
          },
          "module_3": {
            "sections": [
              {
                "type": "methodology_section",
                "score": 0.2556597590446472,
                "heading": "Methods",
                "text": "CNN model\nMutCompute24 is a three-dimensional CNN (3DCNN) model in which \nthe architecture consists of nine layers divided into two blocks:  \n(1) feature extraction and (2) classification. The feature extraction block \nconsisted of six layers: two pairs of 3D convolutional layers followed by \na dimension reduction max ",
                "source": "662 | Nature | Vol 604 | 28 April 2022",
                "title": ""
              },
              {
                "type": "methodology_section",
                "score": 0.24060465395450592,
                "heading": "Supplementary Methods 1: Description of methods 368",
                "text": "Convolutional Neural Network (CNN) Model: 369 \nMutCompute19 is a 3D CNN model where the architecture consists of nine la yers divided into two 370 \nblocks: 1) feature extraction and 2) classification. The feature extraction block consisted of six layers: 371 \ntwo pairs of 3D convolutional layers followed by a dimension",
                "source": "1",
                "title": ""
              },
              {
                "type": "methodology_section",
                "score": 0.4526870548725128,
                "heading": "Results: Using the photosynthetic microalga Phaeodactylum tricornutum as a chassis we generated a microbial cell",
                "text": "factory capable of producing and secreting an engineered version of PETase into the surrounding culture medium. \nInitial degradation experiments using culture supernatant at 30 \u00b0C showed that PETase possessed activity against PET \nand the copolymer polyethylene terephthalate glycol (PETG) with an approximately 80\u2011fold ",
                "source": "Moog\u00a0et\u00a0al. Microb Cell Fact          (2019) 18:171",
                "title": ""
              }
            ],
            "edges": [],
            "assays": [],
            "queries": [
              "petase DH5\u03b1 Colony Picking & Culture",
              "petase DH5\u03b1 Colony Picking & Culture protocol",
              "petase colony",
              "colony",
              "petase picking",
              "picking",
              "petase deepwell",
              "deepwell",
              "petase culture",
              "culture"
            ]
          },
          "module_4": {
            "sections": [
              {
                "type": "methodology_section",
                "score": 0.49368852376937866,
                "heading": "Here, we developed a computational design approach based on the struc-",
                "text": "tural characteristics of PET polymersto modify the binding pocket of PET\nhydrolase Bhr-PETase. Through the remodeling and reconstruction of the\n\u03b26-\u03b27 loop, the variant Bhr-NMT (H218N/F222M/F243T) was successfully\nconstructed, exhibitingan activity 1.87 times higher than that of the wild-\ntype. Furthermore, the loop rec",
                "source": "communicationsbiology Article",
                "title": ""
              },
              {
                "type": "methodology_section",
                "score": 0.49253779649734497,
                "heading": "Computational enzyme design",
                "text": "The PET hydrolase Bhr-PETase was redesigned using our laboratory-\ndeveloped computational enzyme design software PRODA47,48.T h ew o r k -\n\ufb02ow is presented in Fig. S25. For the speci\ufb01c design tasks, the sequence\nselection positions that allowed variation of the amino acid type and the\nresidues that provided optimal sid",
                "source": "communicationsbiology Article",
                "title": ""
              },
              {
                "type": "methodology_section",
                "score": 0.4759710729122162,
                "heading": "In this work, we employ molecular dynamics (MD) and",
                "text": "well-tempered metadynamics\n28\nsimulations to explore the\nstructural basis of the improved catalytic activity of BurPL,\nTf Cut, and LCC upon incorporation of the IsPETase-based\nS214/I218 double substitution. Our results show that these\nsubstitutions increase the flexibility of both active site loop\nregions harboring key",
                "source": "Conformational Selection of a Tryptophan Side Chain Drives the",
                "title": ""
              },
              {
                "type": "methodology_section",
                "score": 0.4736108183860779,
                "heading": "Results We found expression in SHuffle T7 Express results in higher active expression of IsPETase compared",
                "text": "to standard E. coli production strains such as BL21(DE3), reaching a purified titer of 20 mg enzyme per L of culture \nfrom shake flasks using 2xLB medium. We characterized purified IsPETase on 4-nitrophenyl acetate and PET micro-\nplastics, showing the enzyme produced in the disulfide-bond promoting host has high activi",
                "source": "Carter\u00a0et\u00a0al. Microbial Cell Factories          (2024) 23:319",
                "title": ""
              },
              {
                "type": "methodology_section",
                "score": 0.4900970757007599,
                "heading": "To address the limitations of existing methods in developing",
                "text": "potential PETase mutants, a revolutionary platform has been\ndeveloped, which is capable of simultaneously evaluating large\nPET hydrolase libraries (10 4\u00f1105 variants) for protein solubility,\nthermostability, and catalytic activity (Groseclose et al., 2024).\nIt uses plate-based split green \ufb02uorescent protein assays and\n",
                "source": "fmicb-16-1599470 June 28, 2025 Time: 19:3 # 1",
                "title": ""
              },
              {
                "type": "methodology_section",
                "score": 0.3544253408908844,
                "heading": "Methods for mitigating the product inhibition during",
                "text": "enzymatic PET hydrolysis include the continuous removal of\nsmall-molecule products using ultrafiltration membranes,\n8\nthe\nuse of engineered PETase variants that are less affected by the\ninhibitors,\n9\nand the introduction of a helper enzyme with a\nspecific hydrolytic activity on the inhibitors. Ideonella sakaiensis\n(I. ",
                "source": "Structural Insights into (Tere)phthalate-Ester Hydrolysis by a",
                "title": ""
              },
              {
                "type": "methodology_section",
                "score": 0.1567111611366272,
                "heading": "Molecular Dynamics Simulations",
                "text": "All MD simulations were performed using AMBER20 (Case et al.,\n2021). The AMBER FF19SB force \ufb01eld was applied and the\nSHAKE algorithm used to restrict all covalent bonds involving\nhydrogen atoms, with a time step of 2fs. The Particle Mesh Ewald\nmethod was used to treat long-range electrostatic interactions.\nFor the solv",
                "source": "Catalytic Features and Thermal",
                "title": ""
              },
              {
                "type": "methodology_section",
                "score": 0.14683815836906433,
                "heading": "Optimization and simulation were performed using Math-",
                "text": "Works MATLAB software. Optimization was performed using\na multi-start approach with an interior point algorithm and\n2000 random initialization points for each enzyme. All pa-\nrameters were scaled by log(\u03b8) during optimization to improve\nthe speed of searching the parameter space and to constrain\nparameter values to pos",
                "source": "Analysis of Poly(ethylene terephthalate) degradation kinetics",
                "title": ""
              },
              {
                "type": "methodology_section",
                "score": 0.5977494716644287,
                "heading": "Methods",
                "text": "Plasmid construction, strains, and\u00a0cell cultivation\nAll plasmids, oligonucleotide primers, and strains used in \nthis study are listed in Table\u00a0 1. The amino acid sequence \nof PETase (ISF6_4831) was obtained from UniProt \n(http://www.unipr ot.org/). To obtain pIDT_PETase_Opt \nfrom a commercial service (Integrated DNA Te",
                "source": "Kim\u00a0et\u00a0al. Microb Cell Fact           (2020) 19:97",
                "title": ""
              },
              {
                "type": "methodology_section",
                "score": 0.5798366665840149,
                "heading": "Methods",
                "text": "Plasmid construction and\u00a0strains\nThe gene encoding PETase from Ideonella sakaiensis \n(IsPETase) was codon optimized for expression in E. coli \nwithout its 26 base pair signal sequence as was done pre -\nviously [5] (Supplemental Information). The gene was \nadded to a pET21b or pET24a plasmid between ndeI and \nxhoI cutsi",
                "source": "Carter\u00a0et\u00a0al. Microbial Cell Factories          (2024) 23:319",
                "title": ""
              },
              {
                "type": "methodology_section",
                "score": 0.5788401365280151,
                "heading": "Methods",
                "text": "Plasmid Construction. pET21b(+)-based expression plasmids forI. sakaiensis\ngenes, homologous genes, and mutants were generated as further described\nin Dataset S1.\nProtein Expression and Purification.E. coli-based protein expression and chro-\nmatographic purification is described inSI Appendix, Supplementary Materials\na",
                "source": "Characterization and engineering of a two-enzyme",
                "title": ""
              },
              {
                "type": "methodology_section",
                "score": 0.48645591735839844,
                "heading": "Materials and methods 253",
                "text": "254 \nStrains and plasmids 255 \nEscherichia coli strains and plasmids used are listed in Table S1. Molecular cloning and 256 \nvector propagation were performed in DH5\u03b1 (NEB). Polymerase chain reaction (PCR) based DNA 257 \nreplication was performed using KOD XTREME Hot Start Polymerase (MilliporeSigma) for 258 \nplasmid b",
                "source": "1",
                "title": ""
              },
              {
                "type": "methodology_section",
                "score": 0.41825592517852783,
                "heading": "Materials and Methods",
                "text": "Bacterial Strains, Growth Conditions, and Plasmid Construction\nAll bacterial strains, plasmids, and primers used in this study are listed in Tables S1 and S2. E. coli strains were\nroutinely grown at 37\u00b0C in Luria-Bertini (LB) broth (BD, USA) while shaking the solution at 180 rpm to achieve\ntransformation and enzyme pro",
                "source": "2025 \uf0efVol. 35",
                "title": ""
              },
              {
                "type": "methodology_section",
                "score": 0.38014718890190125,
                "heading": "Methods",
                "text": "Transformation\nGenes were codon optimized, synthesized, and cloned into pCDB179 (gifted to Addgene by Christopher Bahl, \n#91960) by Twist Biosciences. If codon optimized sequences for E. coli expression were available in the literature \nfor individual variants, those were used preferentially. All sequences are availabl",
                "source": "1",
                "title": ""
              },
              {
                "type": "methodology_section",
                "score": 0.45205289125442505,
                "heading": "Loop remodeling",
                "text": "The \u03b26-\u03b27 loop in the wild-type Bhr-PETase crystal structure (PDB ID:\n7EOA) was remodeled using the protein modeling tool Modeler 10.518. First,\nwater molecules and other small ligands were removed from the crystal\nstructure by PyMOL, and the Bhr-PETase sequence was extracted from the\nPDB \ufb01le. Next, residues L187 to T1",
                "source": "communicationsbiology Article",
                "title": ""
              },
              {
                "type": "methodology_section",
                "score": 0.31064772605895996,
                "heading": "Conceptualization, Funding acquisition, Methodology, Project administration, Resources,",
                "text": "Supervision, Validation, Writing \u2013 original draft, Writing \u2013 review and editing\nDATA AVAILABILITY\nThe genome sequences reported here were deposited in DDBJ under accession numbers \nAP028878 and AP028879, and the raw reads were deposited in the Sequence Read \nArchive (SRA) under BioProject accession number PRJNA1011029 ",
                "source": "| Bacteriology | Announcement",
                "title": ""
              },
              {
                "type": "methodology_section",
                "score": 0.27509862184524536,
                "heading": "Methodology: RMD, ES, EA 642",
                "text": "Investigation: RMD, ES, EA, PN 643 \nVisualization: RMD 644 \nFunding acquisition: AMK 645 \nProject administration: AMK, DGV 646 \n(which was not certified by peer review) is the author/funder. All rights reserved. No reuse allowed without permission. \nThe copyright holder for this preprintthis version posted October 1, 2",
                "source": "1",
                "title": ""
              },
              {
                "type": "methodology_section",
                "score": 0.27159228920936584,
                "heading": "Met177, results from the same study also indicated Gly105,",
                "text": "Gln138, and Ile224 as likely Cut190 interacting residues using a\npartial PBSA structure called BABSBA. Gly105 and Gln138 are\nmatched in BgP at positions 61 and 94, respectively. The Ile224\nis replaced with a Val178 at the corresponding location in BgP.\nAlthough valine is smaller than isoleucine, both are hydrophobic\nam",
                "source": "fmicb-13-888343 April 6, 2022 Time: 16:36 # 1",
                "title": ""
              },
              {
                "type": "methodology_section",
                "score": 0.25355589389801025,
                "heading": "The results of the colorimetric quantitative detection indicate that Gs no longer exhibits",
                "text": "BHET hydrolysis activity after being treated at 80\u25e6C, 90 \u25e6C, and 100 \u25e6C for 2 h. This finding\nsuggests that Gs lacks significant thermal stability when hydrolyzing BHET (Figure 4a).\nAdditionally, the absence of color change in the phenol red indicator before and after the\nreaction further confirms that Gs has lost its ",
                "source": "Academic Editor: Arnaud Chatonnet",
                "title": ""
              }
            ],
            "edges": [
              {
                "type": "methodology_edge",
                "score": 0.5208751559257507,
                "relation": "performed_at_temperature",
                "value": "A The relative enzyme activity of FAST-PETase \nsurface-displayed BL21 at different temperature.",
                "source": "Journal of Hazardous Materials 461 (2024) 132632"
              },
              {
                "type": "methodology_edge",
                "score": 0.5471007227897644,
                "relation": "mixed_with",
                "value": "Strains, plasmids, media and reagents.",
                "source": "ARTICLE"
              }
            ],
            "assays": [],
            "queries": [
              "petase Miniprep & BL21 Transformation",
              "petase Miniprep & BL21 Transformation protocol",
              "petase miniprep",
              "miniprep",
              "petase plasmid",
              "plasmid",
              "petase bl21",
              "bl21"
            ]
          },
          "module_5": {
            "sections": [
              {
                "type": "methodology_section",
                "score": 0.3845565915107727,
                "heading": "4 Discussion and conclusion",
                "text": "The rapid accumulation of PET waste poses a global\nenvironmental crisis, necessitating innovative and sustainable\nsolutions. This review systematically explores microbial-mediated\nPET biodegradation as a transformative strategy for plastic waste\nmanagement, emphasizing advancements in enzyme engineering,\nmetabolic path",
                "source": "fmicb-16-1599470 June 28, 2025 Time: 19:3 # 1",
                "title": ""
              },
              {
                "type": "methodology_section",
                "score": 0.5053088068962097,
                "heading": "These results established a theoretical basis for the design of",
                "text": "PET biodegradation systems. Most studies focused on the initial\ndegradation step. Hydrophobin has been used to convert PET to\na hydrophilic form so that it is easier for PETase to contact and\nthus catalyze the reaction (Ribitsch et al., 2015; Puspitasari et al.,\n2020). Another study examined how the proximity of the tw",
                "source": "fmicb-12-778828 December 17, 2021 Time: 14:33 # 1",
                "title": ""
              },
              {
                "type": "methodology_section",
                "score": 0.15660566091537476,
                "heading": "Results",
                "text": "Design of expression constructs\nAll factorial-based optimization experiments were car -\nried out using the enGenes e X-press V2 production \nstrain, harboring a pET30a.cer plasmid containing the \nlamB_T7A3_PHL7_His expression construct. To pro -\nmote extracellular expression the lamB signal sequence \nwas employed to dir",
                "source": "RESEARCH Open Access",
                "title": ""
              },
              {
                "type": "methodology_section",
                "score": 0.14338141679763794,
                "heading": "Results and Discussion",
                "text": "Instability of Heterologous Gene Expression in Living Systems\nTo assess the expression and catalytic activity of TfCut2 in bacteria, we constructed genetic circuits by cloning\nthe gene encoding the plastic-degrading enzyme into the pET28b plasmid, which carried an IPTG-inducible T7\npromoter system. The plasmid was intr",
                "source": "2025 \uf0efVol. 35",
                "title": ""
              }
            ],
            "edges": [],
            "assays": [],
            "queries": [
              "petase BL21 Colony Picking & Preculture",
              "petase BL21 Colony Picking & Preculture protocol",
              "petase preculture",
              "preculture",
              "petase inoculation",
              "inoculation",
              "petase expression",
              "expression"
            ]
          },
          "module_6": {
            "sections": [
              {
                "type": "methodology_section",
                "score": 0.5918858647346497,
                "heading": "Results",
                "text": "Overall structures of PETase. The recombinant protein of wild-\ntype PETase without signal peptide was expressed and crystallized\nin the orthorhombic space group P2\n12121 (Supplementary\nTable 2). The structure was solved at 1.58 \u00c5 resolution, and three\npolypeptide chains were observed in an asymmetric unit, which\nare de",
                "source": "ARTICLE",
                "title": ""
              },
              {
                "type": "methodology_section",
                "score": 0.5212116241455078,
                "heading": "Directed Evolution Results",
                "text": "In the directed evolution stage of the algorithm, the mutant enzyme of PETase developed as an \noutput after 29 iterations is the better enzyme to test in the lab as it more closely resembles the original \nPETase enzyme as compared to the mutant enzyme developed after 1000 iterations. The mutant enzyme \nof PETase after ",
                "source": "1",
                "title": ""
              },
              {
                "type": "methodology_section",
                "score": 0.5112271308898926,
                "heading": "Conclusions",
                "text": "We combined different enzyme engineering approaches;\nstructure-based rational design, ancestral sequence reconstruc-\ntion and mutations from AI/machine learning to develop a new\nvariant of PsPETase. We found the biggest improvements in the\nenzyme\u2019s properties from the early generations using a rational-\nbased design. B",
                "source": "Enhancing PET Degrading Enzymes: A Combinatory",
                "title": ""
              },
              {
                "type": "methodology_section",
                "score": 0.15202078223228455,
                "heading": "Results",
                "text": "A Machine-learning guided directed evolution algorithm was written in Python in order to \nengineer PETase for a higher thermostability. A flowchart of the approach is shown in Figures 1, 2 and 3. \nIn order to guide the directed evolution, a machine learning model was written to predict an enzyme\u2019s \noptimal reaction tem",
                "source": "1",
                "title": ""
              },
              {
                "type": "methodology_section",
                "score": 0.3851538300514221,
                "heading": "Results and\u00a0discussion",
                "text": "Secretion expression of\u00a0CtPL\u2011DM in\u00a0P . pastoris\nOur previous report indicated that CtPL-DM exhib -\nits potent PET hydrolytic activity that about sevenfold \nmore hydrolytic products were obtained from hydrolyz -\ning GfPET in comparison with Is PETase (Fig.\u00a0 1a). We \nthen aimed to explore the industrial application poten",
                "source": "Li\u00a0et\u00a0al. Bioresources and Bioprocessing           (2023) 10:26",
                "title": ""
              },
              {
                "type": "methodology_section",
                "score": 0.3620864152908325,
                "heading": "Computational Insights into the Catalytic Mechanism of",
                "text": "Is-PETase: An Enzyme Capable of Degrading Poly(ethylene)\nTerephthalate\nEugene Shrimpton-Phoenix,\n[a]\nJohn B. O. Mitchell,*\n[a]\nand Michael B\u00fchl*\n[a]\nAbstract: Is-PETase has become an enzyme of significant\ninterest due to its ability to catalyse the degradation of\npolyethylene terephthalate (PET) at mesophilic temperatu",
                "source": "Computational Insights into the Catalytic Mechanism of",
                "title": ""
              },
              {
                "type": "methodology_section",
                "score": 0.3567277193069458,
                "heading": "MethodsX",
                "text": "j o u r n a l h o m e p a g e: w w w . e l s e v i e r . c o m / l o c a t e / m e x \nMethod Article \nStandardized method for controlled modi\ufb01cation \nof poly (ethylene terephthalate) (PET) crystallinity \nfor assaying PET degrading enzymes \nThore Bach Thomsen, Cameron J. Hunt, Anne S. Meyer \u2217\nDepartment of Biotechnology",
                "source": "MethodsX 9 (2022) 101815",
                "title": ""
              },
              {
                "type": "methodology_section",
                "score": 0.1903841495513916,
                "heading": "2 Materials and methods",
                "text": "2.1 Materials\nPolyethylene terephthalate (PET) and polybutylene adipate co-\nterephthalate (PBAT) were purchased from Macklin (Shanghai,\nChina). Bis (2-hydroxyethyl) terephthalate (BHET) was purchased\nfrom Aladdin (Shanghai, China). Terephthalatebutanediol monoester\n(BT) was purchased from Aikon Biopharmaceutical R&D Co",
                "source": "Characterization and engineering",
                "title": ""
              },
              {
                "type": "methodology_section",
                "score": 0.16927017271518707,
                "heading": "Materials and Methods",
                "text": "A. Machine Learning Main Procedure and Training the Machine Learning Models:\nEnzyme data from the Brenda Database was used to train the machine learning models to predict \nthe enzyme\u2019s Topt. After obtaining the data, the algorithm split the data set into a training (90% of the \ndata set) and independent test set (10% o",
                "source": "1",
                "title": ""
              },
              {
                "type": "methodology_section",
                "score": 0.25589776039123535,
                "heading": "Performing directed evolution using machine learning on the computer is known as in silico",
                "text": "directed evolution. For in silico directed evolution, instead of producing those mutants in the lab, machine\nlearning is used to score and evaluate different possible mutations of enzymes. Based on the machine \nlearning scores, the algorithm then selects the best mutant and uses it as a starting point again. Machine \nl",
                "source": "1",
                "title": ""
              },
              {
                "type": "methodology_section",
                "score": 0.18276464939117432,
                "heading": "Identified Using Bioinformatics and Iterative Machine",
                "text": "Learning. We conducted a PET hydrolase homolog screen\nconsisting of three rounds (candidate ID per round: DP for\nRound 1, TEP for Round 2, and ESM for Round 3, vide infra),\neach augmented by machine learning on literature data or on\nprevious round data (Figure 1A). A summary of the PET\nhydrolase data we used for this s",
                "source": "Machine Learning-Guided Identification of PET Hydrolases from",
                "title": ""
              },
              {
                "type": "methodology_section",
                "score": 0.44156181812286377,
                "heading": "Our results align with these findings, showing that Thermo-",
                "text": "PETase has increased both global thermostability and local\nflexibility, potentially contributing to the overall enhancement\nof PET degradation observed in the experiments. The high\nsimilarity between the native structures of WT- and Thermo-\nPETase has resulted in a similar overall pattern of frustrated\ncontact. However",
                "source": "Unraveling the Interplay between Stability and Flexibility in the",
                "title": ""
              },
              {
                "type": "methodology_section",
                "score": 0.4217301607131958,
                "heading": "C simulations are",
                "text": "displayed using blue colors while the 50 \n\u25e6\nC simulations are displayed in shades of red. To reduce the noise in the original data ( Supplementary Fig. S2 ), Savitzky- \nGolay filter (window size: 11, polynomial order: 3) was applied. The original data and scripts used for plotting have been uploaded to https://github.c",
                "source": "Computational and Structural Biotechnology Journal 27 (2025) 969\u2013977",
                "title": ""
              },
              {
                "type": "methodology_section",
                "score": 0.3076859712600708,
                "heading": "Pressure Molecular Dynamics Simulation: The Langevin Piston",
                "text": "Method. J. Chem. Phys. 1995, 103 (11), 4613\u22124621.\n(76) Essmann, U.; Perera, L.; Berkowitz, M. L.; Darden, T.; Lee, H.;\nPedersen, L. G. A Smooth Particle Mesh Ewald Method. J. Chem. Phys.\n1995, 103 (19), 8577\u22128593.\n(77) Miyamoto, S.; Kollman, P. A. Settle: An Analytical Version of the\nSHAKE and RATTLE Algorithm for Rigi",
                "source": "Molecular Details of Polyester Decrystallization via Molecular",
                "title": ""
              },
              {
                "type": "methodology_section",
                "score": 0.25715965032577515,
                "heading": "44. Parrinello M, Rahman A. 1981. Polymorphic transiti ons in single crystals: a new molecular dynamics method. J. Appl. Phys. 52:",
                "text": "7182-7190.\n45. Nos\u00e9 S. 1984. A unified formulation of the constant temperature molecular dynamics methods. J. Chem. Phys. 81: 511-519.\n46. Hess B, Bekker H, Berendsen HJC, Fraaije JGEM. 1997. LINC S: a linear constraint solver for molecular simulations. J. Comput.\nChem. 18: 1463-1472.\n47. Miyamoto S, Kollman PA. 1992. ",
                "source": "September 2024 \uf0efVol. 34 \uf0efNo. 9",
                "title": ""
              },
              {
                "type": "methodology_section",
                "score": 0.19695323705673218,
                "heading": "All productionsimulationswereconductedunder theisothermal,isobaricconditions(NPT) with",
                "text": "1 bar pressure, using the Langevin Thermostat95 (friction coefficient 1 ps-1) and Montecarlo\nBarostat 96. Periodic boundary conditionsandParticleMeshEwald(real spacecutoff12\u00c5and\ngrid spacing 1.2\u00c5) wereemployedfor remoteelectrostaticinteractions 97,whileVander Waals\ncontacts were truncated at the real space cutoff. Prot",
                "source": "Single Distal Mutation Enhances Activity of known PETases via",
                "title": ""
              }
            ],
            "edges": [
              {
                "type": "methodology_edge",
                "score": 0.6087814569473267,
                "relation": "labeled_with",
                "value": "Particularly, these labeled substrates are well-\nsuited for screening mutant libraries or characterizing\nengineered PETases, providing valuable insights into enzyme\nperformance as they can promptly ev",
                "source": "New Labeled PET Analogues Enable the Functional Screening and"
              },
              {
                "type": "methodology_edge",
                "score": 0.2714880108833313,
                "relation": "performed_at_temperature",
                "value": "After induction the temperature was dropped to 18\u00b0C overnight 396 \nfor 18 h.",
                "source": "1"
              },
              {
                "type": "methodology_edge",
                "score": 0.22446060180664062,
                "relation": "mixed_with",
                "value": "Induction mechanism\nThe casein hydrolysate N-Z-Amine \u00ae, magnesium sul -\nphate, trace elements and 10\u00a0 g\u00a0  L\u22121 glucose as a carbon \nsource were added to the LB medium  (LBsupplemented) to \ntest whether",
                "source": "Fritzsche\u00a0et\u00a0al. Microbial Cell Factories          (2024) 23:274"
              },
              {
                "type": "methodology_edge",
                "score": 0.36219605803489685,
                "relation": "performed_at_temperature",
                "value": "coli using \nautoinduction media  (Autoinductionsupplemented) in a stirred-tank \nreactor at an expression temperature of 30 \u00b0C and lactose feeding.",
                "source": "Fritzsche\u00a0et\u00a0al. Microbial Cell Factories          (2024) 23:274"
              },
              {
                "type": "methodology_edge",
                "score": 0.2805514335632324,
                "relation": "induced_with",
                "value": "Furthermore, TPA negatively affected the transcription of the autoinducer synthase \ngene cqsA, which is involved in the cholera autoinducer I biosynthesis (CAI-I) ( Table S1; \nFig.",
                "source": "| Environmental Microbiology | Research Article"
              },
              {
                "type": "methodology_edge",
                "score": 0.39207887649536133,
                "relation": "performed_at_temperature",
                "value": "Samples were shaken (200 rpm) at various temperatures in a shaking\nincubator (IKA KS 3000i) (Staufen, Germany).",
                "source": "polymers"
              }
            ],
            "assays": [],
            "queries": [
              "petase Protein Expression Induction",
              "petase Protein Expression Induction protocol",
              "petase induction",
              "induction",
              "petase iptg",
              "iptg",
              "petase autoinduction",
              "autoinduction",
              "petase shaking",
              "shaking"
            ]
          },
          "module_7": {
            "sections": [],
            "edges": [],
            "assays": [],
            "queries": []
          },
          "module_8": {
            "sections": [
              {
                "type": "methodology_section",
                "score": 0.5983740091323853,
                "heading": "Taking all of the results and limitations into account, it is",
                "text": "noteworthy that fluorescent substrates serve as a valuable tool\nfor the rapid identification and assessment of enzymes with\nPETase activity. Particularly, these labeled substrates are well-\nsuited for screening mutant libraries or characterizing\nengineered PETases, providing valuable insights into enzyme\nperformance as",
                "source": "New Labeled PET Analogues Enable the Functional Screening and",
                "title": ""
              },
              {
                "type": "methodology_section",
                "score": 0.5747408866882324,
                "heading": "2 | RESULTS AND DISCUSSION",
                "text": "2.1 | Screening for novel PETases\nTo identify PETases from the marine environment, a\nprofile hidden Markov-Model (pHMM) search was\napplied to marine bacterial metagenomes, published by\nthe Tara Oceans project (Sunagawa et al., 2015).\nTwenty target proteins that showed a bit-score higher\nthan 100 were selected to analyz",
                "source": "RESEARCH ARTICLE",
                "title": ""
              },
              {
                "type": "methodology_section",
                "score": 0.13123999536037445,
                "heading": "Methodology, Project administration, Resources, Software, Validation, Visualization,",
                "text": "Writing \u2013 original draft, Writing \u2013 review and editing | Nikolai Pavlov, Formal analy\u00ad\nsis, Investigation, Writing \u2013 original draft | Paul Young, Conceptualization, Data cura\u00ad\ntion, Formal analysis, Investigation, Methodology, Software, Writing \u2013 original draft | \nStephanie Dawes, Data curation, Investigation, Methodol",
                "source": "| Editor\u2019s Pick | Environmental Microbiology | Research Article",
                "title": ""
              },
              {
                "type": "methodology_section",
                "score": 0.100438192486763,
                "heading": "Seong Hyeon Lee: conceptualization, methodology, investigation,",
                "text": "validation, visualization, writing\u2013 original draft, writing\u2013 review and\nediting, resources, data curation, formal analysis. Haemin Jeong:\nconceptualization, writing \u2013 original draft, methodology, formal anal-\nysis, project administration, supervision, resources. Injun Jung:\nmethodology, formal analysis, resources, conc",
                "source": "Journal of Basic Microbiology",
                "title": ""
              },
              {
                "type": "methodology_section",
                "score": 0.0983986184000969,
                "heading": "Program of China (2024YFA0917603), the Computational Biology Key",
                "text": "Program of Shanghai Science and Technology Commission\n(23JS1400600), Shanghai Municipal Education Commission\n(2024AIZD015), Shanghai Jiao Tong University Scienti \ufb01c and Techno-\nlogical Innovation Funds (21X010200843), and Science and Technol-\nogy Innovation Key R&D Program of Chongqing (CSTB2022TIAD-\nSTX0017, CSTB2024T",
                "source": "Article https://doi.org/10.1038/s41467-025-61599-z",
                "title": ""
              },
              {
                "type": "methodology_section",
                "score": 0.4354435205459595,
                "heading": "Lab (IAC) at KAUST for providing the computational and exper-",
                "text": "imental resources needed to carry out this work. We thank Kit\nXi Liew and Salim Al-Babili at KAUST for their help with HPLC\nmeasurements. We also thank Branimir Ayvazov, Yuanmin Zheng,\nIdentifying functional marine PETases | 13\nFei Xiang, and Maya Ayach for their advice a nd help with SEM\nimaging.\nAuthor contrib utions",
                "source": "Received:6 April 2025.Revised:2 June 2025.Accepted:10 June 2025",
                "title": ""
              },
              {
                "type": "methodology_section",
                "score": 0.1747094988822937,
                "heading": "Christina Gkountela : Methodology, Validation, Formal analysis,",
                "text": "Investigation, Writing \u2013 original draft, Visualization. Stamatina \nVouyiouka : Methodology, Validation, Resources, Writing \u2013 review & \nediting, Supervision, Funding acquisition. Evangelos Topakas : \nConceptualization, Resources, Writing \u2013 review & editing, Supervision, \nProject administration, Funding acquisition. \nDec",
                "source": "Journal of Hazardous Materials 455 (2023) 131574",
                "title": ""
              },
              {
                "type": "methodology_section",
                "score": 0.15231770277023315,
                "heading": "Availability of data and materials: The data supporting the results are provided with the",
                "text": "supplementary files and is open for access to readers. \nCompeting interests: The authors have no competing interests, or other interests that might be \nperceived to influence the results and/or discussion reported in this paper. \nFunding: The authors have not received any funding in the execution of this manuscript. \nA",
                "source": "Title: Identification of Prospective PETases Across Prokaryotes Using an in silico Approach",
                "title": ""
              },
              {
                "type": "methodology_section",
                "score": 0.16034141182899475,
                "heading": "METHODS",
                "text": "Homolog Identification and Candidate Selection. A\nprofile Hidden Markov Model (HMM) was constructed from a\nmultiple sequence alignment of 61 experimentally verified PET\nhydrolases identified from PAZy (extracted Sept. 21, 2021).\nMultiple sequence alignment was performed using\nMAFFT.\n12,29\nThe resulting profile HMM was ",
                "source": "Machine Learning-Guided Identification of PET Hydrolases from",
                "title": ""
              },
              {
                "type": "methodology_section",
                "score": 0.1556711345911026,
                "heading": "SB, RC contributed to methodology, investigation,",
                "text": "formal analysis, writing, and editing of the manuscript.\nHE, TU, AR contributed to investigation. AG, EP\nconceptualized and designed the research, contributed\nto formal analysis, writing, and editing of the manu-\nscript. All authors reviewed and approved the \ufb01nal\nversion of the manuscript.\nData availability statement\nA",
                "source": "Development of a highly active engineered PETase enzyme",
                "title": ""
              },
              {
                "type": "methodology_section",
                "score": 0.1506887972354889,
                "heading": "Results",
                "text": "Bioinformatics and ML enables identi\ufb01cation of 74 diverse\nputative thermotolerant PET hydrolases\nSimilar to other successes in identifying PET hydrolases with\nHMM17,50,51, we constructed an HMM from 17 characterized enzymes\nthat had been con\ufb01rmed to exhibit PET hydrolysis activity as of",
                "source": "Article https://doi.org/10.1038/s41467-022-35237-x",
                "title": ""
              },
              {
                "type": "methodology_section",
                "score": 0.5023858547210693,
                "heading": "The results demonstrate that Dm PETase was able to degrade all",
                "text": "tested PET samples, leading to the release of substantial amounts of \nwater-soluble products. Table 2 shows that both Dm PETase and LCC\nICCG \nexhibited the highest activity towards amorphous PET powder, pro -\nducing a total of 119 \u03bc g/mgPET and 414 \u03bc g/mgPET water-soluble \nproducts, respectively. As the crystallinity o",
                "source": "Journal of Hazardous Materials 455 (2023) 131574",
                "title": ""
              },
              {
                "type": "methodology_section",
                "score": 0.24767272174358368,
                "heading": "The results of the degradation study on PCL powder showed that",
                "text": "LCC\nICCG \nfully degraded (98.7%) the material in just 24 h, while Dm PE -\nTase led to a significant mass loss, degrading approximately 70% of the \nmaterial. The mass loss caused by Dm PETase was also followed by mo -\nlecular weight alterations in the remaining material, mainly in M\nn\n. The \ntreatment of PBS powder with",
                "source": "Journal of Hazardous Materials 455 (2023) 131574",
                "title": ""
              },
              {
                "type": "methodology_section",
                "score": 0.23183123767375946,
                "heading": "The 29 candidate enzyme variants originating from the different screening methods were then subject to",
                "text": "1 \u03bcs molecular dynamics (MD) simulations in explicit water and ranked based on their stability as assessed \nby RMSF analysis.25 Our MD-based ranking led to the selection of six candidate mutants ( C08, C09, P06, \nP08, X05, X09) for experimental production and characterization (Figure 1, Figure S1 and Table 2). \n \nTable",
                "source": "1",
                "title": ""
              },
              {
                "type": "methodology_section",
                "score": 0.5174423456192017,
                "heading": "The authors declare that all data supporting the findings of this study",
                "text": "are available in the article, its Extended Data, its Source Data or from \nthe corresponding authors upon request. The complete data set of \nMutCompute predictions used in this study can be acquired at https://\nmutcompute.com. Coordinates for the FAST-PETase structure have \nbeen deposited into the PDB with accession cod",
                "source": "662 | Nature | Vol 604 | 28 April 2022",
                "title": ""
              },
              {
                "type": "methodology_section",
                "score": 0.49233371019363403,
                "heading": "Initially, we started the MD simulation assuming the PET L-shape",
                "text": "as the most probable conformation for theIsPETase-PET complex, as\npreviously suggested in other studies.\n13,24 However, Wei et al indi-\ncated that the amorphous PET is highly stiff and its binding into the\nFIGURE 4 Essential motion described\nby the first principal component (PC1) of\neach analyzedIsPETase structure:\n(A)",
                "source": "RESEARCH ARTICLE",
                "title": ""
              },
              {
                "type": "methodology_section",
                "score": 0.3287928104400635,
                "heading": "Table 3Current methods used to assay PET degradation mainly monitoring hydrolytic TPA release",
                "text": "Detection method Structural/ functional traits\nReported or assumed\ndetection limit Reference\nPhysical\nWeight loss Mass loss of substrate due to enzymatic degradation Not reported, mg range\n(>102100\nmmol TPA)\n(48, 49)\nMicroscopy Observation of surface changes using various microscopy techniques Not reported/ Only\nqualit",
                "source": "An Ultra-SensitiveComamonas thiooxidansBiosensor for the",
                "title": ""
              },
              {
                "type": "methodology_section",
                "score": 0.3047553300857544,
                "heading": "Molecular simulations, modelling, and analysis were performed by",
                "text": "Peter Stockinger. Cornel Niederhauser performed the physical energy \ncalculations and supported the generation of illustrations. Sebastien \nFarnaud and Rebecca Buller acquired funding, designed the research, \nsupervised the project and wrote the manuscript together with Peter \nStockinger.\nAppendix A. Supporting informa",
                "source": "Computational and Structural Biotechnology Journal 27 (2025) 969\u2013977",
                "title": ""
              },
              {
                "type": "methodology_section",
                "score": 0.30042192339897156,
                "heading": "ing\u2014original draft, Writing\u2014review & editing BS: Investigation, Methodology, Writing\u2014review & editing KK:",
                "text": "Investigation, Methodology, Visualization, Writing\u2014review & editing CW: Investigation, Writing\u2014review & \nediting CJD: Investigation, Writing\u2014review & editing MT:  Investigation, Methodology, Writing\u2014review & ed-\niting RS: contributed to drafting and revising the original manuscript and secured funding for the research.",
                "source": "Efficient secretion of a plastic",
                "title": ""
              },
              {
                "type": "methodology_section",
                "score": 0.2926887571811676,
                "heading": "Results",
                "text": "BHET hydrolysis with selective product formation by pH\ncontrolling\nFirst, we studied the effect of pH during the hydrolysis of BHET cata-\nlyzed by CALB. To that aim, we performed the time reaction courses\nfor the BHET hydrolysis at different pH conditions and the reaction\nproducts were analyzed by UPLC-MS. In all cases",
                "source": "Article https://doi.org/10.1038/s41467-023-39201-1",
                "title": ""
              },
              {
                "type": "methodology_section",
                "score": 0.23681595921516418,
                "heading": "Discussion",
                "text": "The ability to degrade polymers to their monomeric units is im-\nportant for subsequent reuse in new products, which is a critical\ntechnical advance needed to enable a global circular materials\neconomy. In biological systems, complete depolymerization to\nmonomers can be necessary for microbial uptake and growth, as\nin I",
                "source": "Characterization and engineering of a two-enzyme",
                "title": ""
              },
              {
                "type": "methodology_section",
                "score": 0.23169641196727753,
                "heading": "Discussion",
                "text": "In summary, we propose a selectivity switch for the formation of either\nMHET or TPA from BHET by CALB by modulating the pH conditions,\nthrough classical and QM/MM MD simulations combined with\nexperimental Michaelis\u2013Menten kinetics. Our results show how the\nionization state of CALB under acidic conditions forms a neutra",
                "source": "Article https://doi.org/10.1038/s41467-023-39201-1",
                "title": ""
              },
              {
                "type": "methodology_section",
                "score": 0.23279118537902832,
                "heading": "Different pH values, drying methods and solutions were",
                "text": "tested to establish the optimal conditions for the 1H\u00a0NMR \nand absorption measurement and to determine the sensitiv -\nity. Since the products are insoluble or sparingly soluble in \naqueous solutions and therefore difficult to measure with \n1H\u00a0NMR as well as with bulk absorption at lower concentra-\ntions, the samples we",
                "source": "Vol.:(0123456789)",
                "title": ""
              },
              {
                "type": "methodology_section",
                "score": 0.224226176738739,
                "heading": "Based on the findings of the double mutation (DM) strategy",
                "text": "(Chen et\u00a0al., 2021), engineered TfCut was investigated for efficient \nbiodegradation of poly(butylene adipate-co-terephthalate) (PBAT) \n(Y ang et\u00a0al., 2023). The results showed that the mutant (TfCut-DM) is \na highly potent catalyst that can completely decompose PBAT films in \nFIGURE\u00a08\nThe structure alignment of TfCut2",
                "source": "Frontiers in Microbiology 01 frontiersin.org",
                "title": ""
              },
              {
                "type": "methodology_section",
                "score": 0.2181086540222168,
                "heading": "II, the already described ester bond breakage results in the production of a MHET monomer",
                "text": "(\ufb01rst product released) and a HE-PET(n-1). The digestion of this HE-PET molecule follows\nthe same steps as the \ufb01rst ester bond cleavage process [74]. The TPA-terminal PET molecule\npositions itself in the binding site with the TPA terminal at subsite I and the remaining\nthree PET moieties in subsite II. In this case, th",
                "source": "International Journal of",
                "title": ""
              },
              {
                "type": "methodology_section",
                "score": 0.21674199402332306,
                "heading": "RESULTS",
                "text": "Previous work demonstrated that the Gram-negative soil bacteriumC. thiooxidansis ca-\npable of degrading TPA using a dioxygenase and dehydrogenase for the initial conversion\nof TPA to protocatechuate (PCA), which is then converted further via PCA 4,5 cleavage path-\nway (25\u201329). To achieve this, theC. thiooxidansgenome i",
                "source": "An Ultra-SensitiveComamonas thiooxidansBiosensor for the",
                "title": ""
              },
              {
                "type": "methodology_section",
                "score": 0.3095281720161438,
                "heading": "The absorption measurement also provided the best results",
                "text": "under these conditions.\nSensitivity limits for\u00a0the\u00a0combined absorption/1H \nNMR method\nBulk absorbance measurements were carried out in 1-cm-\ngap UV-transparent cuvettes using a spectrophotometer. \nFor the measurements, the established optimal conditions \nwere applied, so that the samples in buffer with pH\u00a03.54 \nwere fr",
                "source": "Vol.:(0123456789)",
                "title": ""
              },
              {
                "type": "methodology_section",
                "score": 0.2933990955352783,
                "heading": "Results and discussion",
                "text": "Several published HPLC methods, employed for the analysis of PET-hydrolysis products (Fig.\u00a0 1a), determine \nthe overall TPA content (including also TPA equivalents calculated from the MHET and BHET contents) by \ncalibration curves based on the integration of the peak areas of the three different aromatic PET-degradatio",
                "source": "Fine tuning enzyme activity assays",
                "title": ""
              },
              {
                "type": "methodology_section",
                "score": 0.26070231199264526,
                "heading": "F-test on the results also shows that the automated addition with",
                "text": "mixing variance is significantly lower than the manual opera-\ntions. To quantify the amount of sfGFP that was produced, an \nsfGFP RFU to mass concentration calibration curve was used\n(Supplement 2) (19). \nThese data show that the low-cost, automated fluid han-\ndler has less variability than manual operation. It is note",
                "source": "Screening putative polyester polyurethane degrading",
                "title": ""
              },
              {
                "type": "methodology_section",
                "score": 0.6360840797424316,
                "heading": "Essen for helpful discussions and valuable technical advices supporting the",
                "text": "progress of the project. Moreover, we are grateful to ALPLA\u2011Werke Lehner \nGmbH & Co KG (Gem\u00fcnden, Germany) for providing industrially shredded PET, \nPage 14 of 15Moog\u00a0et\u00a0al. Microb Cell Fact          (2019) 18:171 \nwhich was used as a main substrate for plastic degradation experiments in \nthis work. We thank Dr. Ni\u00f1a C",
                "source": "Moog\u00a0et\u00a0al. Microb Cell Fact          (2019) 18:171",
                "title": ""
              },
              {
                "type": "methodology_section",
                "score": 0.6225200295448303,
                "heading": "Results",
                "text": "Mechanism of\u00a0PET degradation\nThe hydrolysis of PET is considered to proceed at ran -\ndom via endo-type degradation (Eberl et\u00a0al. 2009), which \nis expected to generate decreased molecular weights if \ndegradation occurs for all molecules, as observed in poly-\nvinyl alcohol degradation (Kawai & Hu 2009). However, \nno subs",
                "source": "Kawai\u00a0et\u00a0al. AMB Express          (2022) 12:134",
                "title": ""
              },
              {
                "type": "methodology_section",
                "score": 0.6184813976287842,
                "heading": "Results",
                "text": "The aim of the work was to establish a new 1H\u00a0NMR analysis \nmethod and optimize it, as well as to optimize the absorption \nmethod already described for the measurement of PET deg-\nradation products. The methods were compared and linked \nto establish a new combined absorption/1H\u00a0NMR method for \nthe quantitative and at t",
                "source": "Vol.:(0123456789)",
                "title": ""
              },
              {
                "type": "methodology_section",
                "score": 0.600579023361206,
                "heading": "As a validation of the methodology the effect of the X C , on the product release rate of the gold",
                "text": "standard thermostable PET-hydrolyzing enzyme LCC ICCG was investigated. The \ufb01ndings showed that \nthe enzymatic rate was heavily dependent on the X C . Especially between a X C of 13.8 and 18.8%, at \nwhich the reaction rate decreased \u223c10 fold. Furthermore, it was observed that the product release \nrates were not constan",
                "source": "MethodsX 9 (2022) 101815",
                "title": ""
              }
            ],
            "edges": [
              {
                "type": "methodology_edge",
                "score": 0.5882521867752075,
                "relation": "concentration",
                "value": "300 m",
                "source": "Functional and Structural Characterization of PETase SM14 from"
              }
            ],
            "assays": [
              {
                "type": "assay_edge",
                "score": 0.5855078101158142,
                "relation": "labeled_with",
                "value": "Particularly, these labeled substrates are well-\nsuited for screening mutant libraries or characterizing\nengineered PETases, providing valuable insights into enzyme\nperformance as they can promptly ev",
                "source": "New Labeled PET Analogues Enable the Functional Screening and"
              }
            ],
            "queries": [
              "petase E.coli screening - EchoMS",
              "petase E.coli screening - EchoMS protocol",
              "petase echo",
              "echo",
              "petase ms",
              "ms",
              "petase mrm",
              "mrm",
              "petase lc-ms",
              "lc-ms",
              "petase mass spec",
              "mass spec",
              "BHET MRM",
              "TPA MRM",
              "MHET calibration",
              "PETase EchoMS",
              "PET degradation LCMS"
            ]
          },
          "module_9": {
            "sections": [],
            "edges": [],
            "assays": [],
            "queries": []
          },
          "module_10": {
            "sections": [],
            "edges": [],
            "assays": [],
            "queries": []
          },
          "module_11": {
            "sections": [],
            "edges": [],
            "assays": [],
            "queries": []
          },
          "module_12": {
            "sections": [],
            "edges": [],
            "assays": [],
            "queries": []
          }
        },
        "llm_rationale": "The chosen organism, E. coli, has a score of 0.6228, which is slightly higher than the alternative yeast option at 0.6202, indicating a marginal preference for E. coli based on the sources provided, including \"New Labeled PET Analogues Enable the Functional Screening and.\" The selected readout, EchoMS, scores 0.5457, outperforming the PlateReader option at 0.5101, further supporting its suitability for this application. While the scores are close, they provide a clear rationale for the E. coli and EchoMS combination. It is important to note that the module order is locked to the chosen template, E.coli_EchoMS_protocol.md, and no new steps will be added."
      }
    }
  ],
  "output_root": "/taiga/illinois/eng/chbe/zhao5/vikas/iBF/BioAgentHub_iBF/outputs/biofoundry_output",
  "log_dir": "/taiga/illinois/eng/chbe/zhao5/vikas/iBF/BioAgentHub_iBF/outputs/logs/biofoundry/auto"
}
