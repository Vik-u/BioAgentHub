# Automated protein Engineering Pipeline 

## Module 1 — Mutagenesis PCR & DpnI Treatment

### Subprocess 1.1: Mutagenesis PCR Setup

- **Objective**
  - Introduce defined point mutations into enzyme ORFs
  - Provide amplified fragment for HiFi assembly

- **Description**
  - Forward and reverse mutagenic PCRs performed in 96-well format

- **Actions**
  - Dispense linearized plasmid templates and primers via worklists
  - Execute PCR amplification protocol

- **Labware**
  - 96-well PCR plates with forward primers
  - 96-well PCR plates with reverse primers

- **Instruments**
  - Tecan Fluent liquid handler
  - Themocycler

- **Materials**
  - plasmid DNA
  - Mutagenic primers (96-well format)
  - Q5 DNA polymerase

- **Parameters**
  - Reaction volume: 50 µL
  - PCR cycles: 18
  - Annealing temperature: 65 °C

---

### Subprocess 1.2: PCR Quality Control

- **Objective**
  - Confirm successful amplification prior to assembly

- **Description**
  - EvaGreen fluorescence assay on PCR products

- **Actions**
  - Mix PCR aliquot with EvaGreen dye
  - Measure fluorescence

- **Labware**
  - 96-well assay plates

- **Instruments**
  - Tecan Fluent liquid handler
  - Tecan Infinite plate reader

- **Materials**
  - EvaGreen dye

- **Parameters**
  - Excitation: 498 nm
  - Emission: 535 nm

---

### Subprocess 1.3: DpnI Digestion

- **Objective**
  - Remove methylated parental plasmid DNA

- **Description**
  - Enzymatic digestion of PCR products

- **Actions**
  - Add DpnI
  - Incubate digestion reaction

- **Labware**
  - PCR plates

- **Instruments**
  - Thermocycler

- **Materials**
  - DpnI restriction enzyme

- **Parameters**
  - 37 °C, ~4 h incubation

---

## Module 2 — HiFi Assembly & DH5α Transformation

### Subprocess 2.1: HiFi DNA Assembly

- **Objective**
  - Reconstruct full plasmids containing desired mutations

- **Description**
  - Three-fragment HiFi assembly (forward fragment, reverse fragment, backbone)

- **Actions**
  - Dispense fragments into assembly reactions using Echo worklists
  - Incubate assembly reaction

- **Labware**
  - 384-well source plate
  - 96-well destination plate

- **Instruments**
  - Echo liquid handler
  - Thermocycler

- **Materials**
  - HiFi DNA Assembly Master Mix

- **Parameters**
  - 50 °C, 30 min incubation

---

### Subprocess 2.2: DH5α Heat-Shock Transformation

- **Objective**
  - Clone assembled plasmids into propagation host

- **Description**
  - Automated heat-shock transformation in 96-well format

- **Actions**
  - Mix assembly product with competent cells
  - Heat shock and recovery

- **Labware**
  - 96-well plates

- **Instruments**
  - Tecan Fluent (onboard heating/cooling block)

- **Materials**
  - DH5α competent cells

- **Parameters**
  - Heat shock: ~42 °C, ~30 s

---

### Subprocess 2.3: Plating & Incubation

- **Objective**
  - Obtain clonal transformant colonies

- **Description**
  - Automated spreading on 8-well agar omnitray plates
  - Overnight growth fo plated transformant

- **Actions**
  - Plate transformed cells
  - Incubate overnight

- **Labware**
  - 8-well omnitray agar plates
  - 96-well transformant plates

- **Instruments**
  - Tecan Fluent liquid handler
  - Cytomat automated incubator

- **Materials**
  - LB agar + kanamycin

- **Parameters**
  - 37 °C, overnight

---

## Module 3 — DH5α Colony Picking & Culture

### Subprocess 3.1: Colony Picking

- **Objective**
  - Establish 96-well plasmid cultures

- **Description**
  - Automated colony picking while preserving plate mapping

- **Actions**
  - Pick colonies from omnitrays
  - Inoculate deepwell cultures

- **Labware**
  - 96-deepwell plates
  - 8-well omnitray agar plates

- **Instruments**
  - Pickolo colony picker integrated with Tecan Fluent

- **Materials**
  - Terrific Broth (TB) + kanamycin

- **Parameters**
  - Culture volume: 1 mL

---

### Subprocess 3.2: Overnight Culture

- **Objective**
  - Amplify plasmid DNA

- **Description**
  - Shaking incubation of bacterial cultures

- **Actions**
  - Incubate cultures overnight

- **Labware**
  - 96-deepwell plates

- **Instruments**
  - Cytomat shaking incubator

- **Parameters**
  - 37 °C, 900 rpm

---

## Module 4 — Miniprep & BL21 Transformation

### Subprocess 4.1: Plasmid Miniprep

- **Objective**
  - Purify plasmids for expression host transformation

- **Description**
  - Automated vacuum-based 96-well plasmid purification

- **Actions**
  - Execute miniprep protocol

- **Labware**
  - 96-well miniprep plates

- **Instruments**
  - Tecan Fluent (vacuum module)

- **Materials**
  - PureLink Pro Quick96 Plasmid Kit

- **Parameters**
  - miniprep protocol

---

### Subprocess 4.2: BL21 Transformation

- **Objective**
  - Generate protein expression strains

- **Description**
  - Heat-shock transformation into BL21 cells

- **Actions**
  - Transform purified plasmids
  - Plate and incubate

- **Labware**
  - 96-well plates
  - 8-well omnitrays

- **Instruments**
  - Tecan Fluent
  - Cytomat incubator

- **Materials**
  - BL21 competent cells
  - LB agar + kanamycin

- **Parameters**
  - Heat shock: ~42 °C, ~30 s

---

## Module 5 — BL21 Colony Picking & Preculture

### Subprocess 5.1: BL21 Colony Picking

- **Objective**
  - Establish expression precultures

- **Description**
  - Automated picking of BL21 colonies

- **Actions**
  - Pick colonies
  - Inoculate LB precultures

- **Labware**
  - 96-deepwell plates
  - 8-well omnitrays

- **Instruments**
  - Pickolo colony picker

- **Materials**
  - LB + kanamycin

- **Parameters**
  - Overnight incubation

---

## Module 6 — Protein Expression Induction

### Subprocess 6.1: Expression Induction

- **Objective**
  - Express enzyme variants in BL21

- **Description**
  - IPTG-induced or autoinduction expression

- **Actions**
  - Inoculate expression cultures
  - Induce protein expression

- **Labware**
  - 96-deepwell plates

- **Instruments**
  - Tecan Fluent
  - Cytomat incubator

- **Materials**
  - IPTG or autoinduction media

- **Parameters**
  - 30–37 °C
  - Overnight expression

---

## Module 7 — E.coli screening - Plate reader

### Subprocess 7.1: Cell Lysis

- **Objective**
  - Release enzyme into crude lysate

- **Description**
  - Chemical lysis followed by clarification

- **Actions**
  - Lyse cells
  - Centrifuge to remove debris

- **Labware**
  - 96-deepwell plates

- **Instruments**
  - Automated centrifuge
  - Tecan Fluent

- **Materials**
  - lysis buffer

- **Parameters**
  - 30–37 °C, 1–1.5 h
  - 300 μL of lysis buffer
  - 20 min at 2900xg centrifugation

---

### Subprocess 7.2: Functional Enzyme Assay

- **Objective**
  - Quantify enzyme fitness in high throughput

- **Description**
  - Plate-based absorbance or fluorescence assays

- **Actions**
  - Dispense substrates and reagents
  - Measure reaction kinetics

- **Labware**
  - 96-well assay plates

- **Instruments**
  - Tecan Infinite plate reader
  - Tecan Fluent

- **Materials**
  - AtHMT assay: SAH, ethyl iodide, TMB, CiVCPO
  - Phytase assay: 4-MUP

- **Parameters**
  - AtHMT: absorbance 570 nm
  - Phytase: fluorescence 354 / 465 nm



## Module 8 — E.coli screening - EchoMS

### Subprocess 8.1: Cell Lysis

- **Objective**
  - Release enzyme into crude lysate

- **Description**
  - Chemical lysis followed by clarification

- **Actions**
  - Lyse cells
  - Centrifuge to remove debris

- **Labware**
  - 96-deepwell plates

- **Instruments**
  - Automated centrifuge
  - Tecan Fluent

- **Materials**
  - lysis buffer

- **Parameters**
  - 30–37 °C, 1–1.5 h
  - 300 μL of lysis buffer
  - 20 min at 2900xg centrifugation

---

### Subprocess 8.2: Functional Enzyme Assay

- **Objective**
  - Quantify enzyme fitness in high throughput

- **Description**
  - EchoMS-based Mass spectrometry quantification

- **Actions**
  - Dispense substrates and reagents
  - Quantify taraget molecule

- **Labware**
  - 96-well plates
  - 384-well plates

- **Instruments**
  - SCIEX Echo MS System
  - Tecan Fluent

- **Materials**
  - cell lysate

- **Parameters**
  - volume: 60 μL
  - Mass spectrometry method



## Module 9 - Yeast transformation and plating
- **Objective**
  - Transform yeast cells with 96-well plasmid DNA

- **Description**
  - Heat shock transformation and plating on SC-Ura agar plates

- **Actions**
  - Mix plasmid DNA with yeast competent cells
  - Heat shock and recovery
  - Plate on agar plates

- **Labware**
  - 96-well plates
  - 384-well plates
  - 96-deepwell plates
  - omnitray SC-Ura agar plates

- **Instruments**
  - Tecan Fluent
  - Cytomat
  - Centrifuge
  - Echo650

- **Materials**
  - yeast competent cells
  - plasmid DNA

- **Parameters**
  - volume: 60 μL
  - yeast transformation worklist

## Module 10 - Yeast colony picking and fermentation
- **Objective**
  - Pick yeast colonies and run fermentation

- **Description**
  - Pick yeast colonies and run fermentation

- **Actions**
  - Pick yeast colonies
  - Inoculate yeast seeding cultures
  - Subculture and ferment

- **Labware**
  - 96-deepwell plates
  - omnitray SC-Ura agar plates

- **Instruments**
  - Tecan Fluent
  - PIXL

- **Materials**
  - yeast colonies
  - SC-Ura medium

- **Parameters**
  - fermentation time: 24 h


## Module 11 - Yeast Screening - plate reader

- **Objective**
  - Screen yeast colonies in high throughput fluorescence assays

- **Description**
  - Plate-based absorbance and fluorescence assays

- **Actions**
  - Dilute yeast cultures
  - Measure fluorescence and OD600

- **Labware**
  - 96-deepwell plates
  - 96-well NUNC dark plates flat bottom

- **Instruments**
  - Tecan Infinite plate reader
  - Tecan Fluent

- **Materials**
  - yeast cultures

- **Parameters**
  - volume: 200 μL
  - plate reader method


## Module 12 - Yeast Screening - EchoMS
- **Objective**
  - Quantify enzyme fitness in high throughput

- **Description**
  - EchoMS-based Mass spectrometry quantification

- **Actions**
  - Spin down yeast cultures
  - Take supernatant for quantification

- **Labware**
  - 96-deepwell plates
  - 384-well plates

- **Instruments**
  - SCIEX Echo MS System
  - Tecan Fluent
  - Centrifuge

- **Materials**
  - yeast cultures

- **Parameters**
  - volume: 60 μL
  - EchoMS method