## Experimental Workflow

1. **Deck and Carrier Preparation**  
   *Action:* Mount a 96‑well PCR plate (SBS, 200 µL capacity) on the RGA finger set “Plate‑96‑SBS” in the central deck slot. Place a 1 mL reagent reservoir (SDS‑compatible) on the FCA carrier “Reservoir‑1mL” and a 96‑channel tip box (filtered, 200 µL tips) on the FCA carrier “TipBox‑200µL”.  
   *Parameters:* Plate type: 96‑well, 200 µL; Reservoir: 1 mL; Tip box: 200 µL, filtered.  
   *Fluent‑specific:* Assign the plate to site A1, reservoir to site B1, tip box to site C1. Enable “Tip‑Check” interlock for all 96 channels. [source:Operating Manual Fluent V2.md, score=0.398]

2. **Reagent Loading – Buffer Matrix**  
   *Action:* Using the 8‑channel arm, dispense 50 µL of each buffer condition into the first 8 wells of the plate (wells A1–H1).  
   *Parameters:* Volume: 50 µL; Temperature: 4 °C; Liquid class: “Standard‑96‑well‑Low‑Speed” (to minimise shear on surface‑displayed PETase).  
   *Fluent‑specific:* Channels 1–8, tip type: filtered 200 µL, speed: 200 µL/s, dwell: 0.5 s. Set “Mix‑Cycles” to 3 for each dispense. [source:FluentControl Application Software Manual 3.7 SP1.md, score=0.457]

3. **Enzyme Dispensation – PETase Concentration Gradient**  
   *Action:* Dispense 10 µL of PETase stock (10 µg/mL) into wells A2–H2, varying concentration across the row (e.g., 0.1, 0.2, …, 1.0 µg/mL).  
   *Parameters:* Volume: 10 µL; Temperature: 25 °C; Liquid class: “Mix‑96‑well‑Fast” (to ensure rapid mixing).  
   *Fluent‑specific:* Channels 1–8, tip type: filtered 200 µL, speed: 300 µL/s, mix: 5 × 5 µL. Use “Tip‑Exchange” after every 12 wells to avoid cross‑contamination. [source:Operating Manual Fluent V2.md, score=0.398]

4. **Incubation – Surface Display Activation**  
   *Action:* Transfer the plate to the incubator‑shaker (DeviceID INC‑01) set to 37 °C, 300 rpm.  
   *Parameters:* Temperature: 37 °C; Shaking speed: 300 rpm; Time: 60 min.  
   *Fluent‑specific:* Use the “Schedule‑Add” command to lock the plate in the incubator for 60 min. Ensure the incubator is pre‑equilibrated; enable “Temperature‑Check” interlock. [source:Operating Manual Fluent V2.md, score=0.398]

5. **Post‑Incubation Wash – Buffer Exchange**  
   *Action:* Remove the plate from the incubator, place it back on the RGA, and dispense 100 µL of wash buffer (PBS, pH 7.4) into each well, then aspirate 100 µL.  
   *Parameters:* Volume: 100 µL; Temperature: 4 °C; Liquid class: “Wash‑96‑well‑Slow”.  
   *Fluent‑specific:* Channels 1–8, tip type: filtered 200 µL, dispense speed: 150 µL/s, aspiration speed: 150 µL/s, dwell: 1 s. Use “Tip‑Check” before each aspiration. [source:FluentControl Application Software Manual 3.7 SP1.md, score=0.457]

6. **Sealing – Preparation for MS**  
   *Action:* Seal the plate with a breathable adhesive film (e.g., Breathe‑Seal) using the built‑in plate sealer.  
   *Parameters:* Seal type: breathable film; Seal time: 30 s.  
   *Fluent‑specific:* Activate the “Seal‑Device” command; enable “Seal‑Integrity” interlock to confirm film adhesion. [source:Operating Manual Fluent V2.md, score=0.398]

7. **Sample Transfer – MS‑Ready Plate**  
   *Action:* Transfer 10 µL from each well of the sealed plate to a fresh 96‑well MS plate (SDS‑compatible, 200 µL).  
   *Parameters:* Volume: 10 µL; Temperature: 4 °C; Liquid class: “Transfer‑96‑well‑Fast”.  
   *Fluent‑specific:* Use the 8‑channel arm, channels 1–8, tip type: filtered 200 µL, dispense speed: 250 µL/s, aspiration speed: 250 µL/s. After each transfer, perform a “Tip‑Exchange” to avoid carry‑over. [source:FluentControl Application Software Manual 3.7 SP1.md, score=0.457]

8. **Internal Standard Addition**  
   *Action:* Add 5 µL of an isotopically labeled PETase internal standard to each MS plate well.  
   *Parameters:* Volume: 5 µL; Temperature: 4 °C; Liquid class: “Standard‑96‑well‑Low‑Speed”.  
   *Fluent‑specific:* Channels 1–8, tip type: filtered 200 µL, speed: 200 µL/s, mix: 3 × 3 µL. Use “Tip‑Check” before dispensing. [source:Operating Manual Fluent V2.md, score=0.398]

9. **Final Seal – MS Plate**  
   *Action:* Seal the MS plate with a low‑profile, non‑SDS‑compatible film (e.g., MicroSeal).  
   *Parameters:* Seal type: low‑profile film; Seal time: 30 s.  
   *Fluent‑specific:* Activate the “Seal‑Device” command; enable “Seal‑Integrity” interlock. [source:Operating Manual Fluent V2.md, score=0.398]

10. **Plate Transfer to Sciex ZenoTOF 7600**  
    *Action:* Place the sealed MS plate into the Sciex autosampler tray, ensuring the plate is correctly indexed by the barcode reader.  
    *Parameters:* Plate type: 96‑well, 200 µL; Volume per well: 15 µL (10 µL sample + 5 µL standard).  
    *Fluent‑specific:* Use the “Plate‑Transfer” command to move the plate from the RGA to the autosampler tray (DeviceID AUTO‑01). Confirm barcode read; enable “Barcode‑Check” interlock. The plate is now ready for injection into the ZenoTOF 7600 MS/MS. [source:Operating Manual Fluent V2.md, score=0.398]

---

## Computational Workflow

1. **Condition Matrix Design**  
   Generate a full factorial matrix of experimental variables (pH, temperature, buffer type, PETase concentration). Use a Python script to output a CSV mapping each well to its condition. Store the mapping in a database for traceability.  

2. **Plate Layout Generation**  
   Convert the matrix into a 96‑well layout file (e.g., .xlsx or .csv) that the FluentControl “Plate‑Layout” module can ingest. Include metadata (well ID, condition, reagent IDs).  

3. **MS Data Parsing**  
   After acquisition, run a custom Analyst‑compatible parser (Python/Perl) to read the .wiff files, extract peak areas for the PETase product and internal standard, and compute relative activity per well.  

4. **Data Normalization & QC**  
   Apply baseline correction, normalize to the internal standard, and flag wells with signal‑to‑noise < 5. Store results in a relational table linked to the original condition matrix.  

5. **Statistical Analysis**  
   Perform ANOVA or regression to identify significant factors. Visualize results with heatmaps (e.g., seaborn) to spot optimal conditions.  

6. **Iterative Design Loop**  
   Feed the statistical output back into the condition generator to refine the next round (e.g., narrow pH range, adjust temperature). Automate the loop with a scheduler that triggers the next Fluent run once the data is uploaded.  

7. **Reporting**  
   Compile a PDF report summarizing the optimal condition set, MS spectra, and activity metrics. Archive the report with the plate metadata for regulatory compliance.  

This computational pipeline ensures that each wet‑lab iteration is data‑driven, reproducible, and tightly coupled to the Tecan Fluent workflow.