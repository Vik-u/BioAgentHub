## Experimental Workflow

1. **Goal/Action** – Clone the engineered PETase library into an E. coli expression vector and transform into competent cells.  
   **Detailed instructions** – Use a 96‑well deep‑well format. In each well add 50 µL of LB medium containing 100 µg mL⁻¹ ampicillin, inoculate with 5 µL of chemically competent E. coli BL21(DE3) carrying the plasmid, and incubate at 37 °C for 16 h with gentle shaking.  
   **Instruments** – **Tecan Fluent 1080** (SetTemperature 37 °C, 16 h) to maintain uniform growth across all wells. The Fluent’s programmable temperature control ensures consistent induction conditions.  
   **Expected observation** – Visible turbidity in each well indicating cell growth; colonies should appear on agar plates if plated.  
   **Next step trigger** – Proceed to protein induction once OD₆₀₀ ≈ 0.6–0.8 is reached.

2. **Goal/Action** – Induce PETase expression with IPTG.  
   **Detailed instructions** – Add 5 µL of 1 mM IPTG to each well (final concentration 0.5 mM). Incubate at 30 °C for 4 h with shaking.  
   **Instruments** – **Tecan Fluent 1080** (SetTemperature 30 °C, 4 h). The lower temperature reduces misfolding and improves soluble expression.  
   **Expected observation** – Increased cell density and a shift in the culture’s color from pale to darker due to protein production.  
   **Next step trigger** – Harvest cells when the culture reaches OD₆₀₀ ≈ 1.2–1.4.

3. **Goal/Action** – Harvest cells and perform BugBuster‑mediated lysis.  
   **Detailed instructions** – Centrifuge each well at 4 °C, 4,000 × g for 10 min. Resuspend the pellet in 200 µL BugBuster reagent (1:1 volume with culture) per 1 mL of culture. Incubate at 25 °C for 30 min with gentle agitation.  
   **Instruments** – **Tecan Fluent 1080** (SetTemperature 25 °C, 30 min). The Fluent’s precise temperature control prevents premature protein denaturation during lysis.  
   **Expected observation** – Clear lysate with a slight yellow tint; activity assays should show higher MHET/TPA production compared to lysates prepared with lysozyme/polymyxin B.  
   **Next step trigger** – Transfer lysate to 96‑well plates for the PET hydrolysis assay.

4. **Goal/Action** – Prepare uniform PET film discs and set up the hydrolysis assay.  
   **Detailed instructions** – Cut 6 mm diameter discs from a 6.7 % crystallinity amorphous PET (amoPET) sheet using a sterile biopsy punch. Place one disc into each well of a 96‑deep‑well plate. Add 200 µL of 50 mM sodium acetate buffer, pH 5.0, to each well.  
   **Instruments** – **Tecan Fluent 1080** (SetTemperature 20 °C, 5 min) to equilibrate the buffer and discs before adding lysate. The Fluent’s plate‑level temperature control ensures all discs experience identical conditions.  
   **Expected observation** – Uniformly sized discs with no visible cracks; buffer should be clear.  
   **Next step trigger** – Add the lysate to the wells.

5. **Goal/Action** – Incubate the reaction mixture at the target temperature to drive PET hydrolysis.  
   **Detailed instructions** – Add 50 µL of the clarified lysate to each well (final enzyme concentration ≈ 0.5 µg mL⁻¹). Incubate at 60 °C for 1 h.  
   **Instruments** – **Tecan Fluent 1080** (SetTemperature 60 °C, 1 h). The Fluent’s rapid temperature ramp and uniform heating are critical for reproducible activity measurements.  
   **Expected observation** – Slight cloudiness in the supernatant due to released MHET/TPA; the reaction should be complete within the hour for the most active variants.  
   **Next step trigger** – Stop the reaction and prepare samples for analysis.

6. **Goal/Action** – Stop the reaction, store samples, and quantify released MHET/TPA.  
   **Detailed instructions** – Add 50 µL of 0.1 M H₂SO₄ to each well to quench the reaction. Transfer 100 µL of the supernatant to a new 96‑well plate, add 200 µL of 50 % methanol to precipitate proteins, and centrifuge at 4 °C, 10,000 × g for 5 min. Inject 10 µL of the clear supernatant into an UPLC system equipped with a C18 column and a UV detector set at 240 nm.  
   **Instruments** – **QuantStudio 7 Pro** (Store all plates at –20 °C) to preserve the samples for downstream analysis. The QuantStudio’s low‑temperature storage capability prevents degradation of MHET/TPA.  
   **Expected observation** – Retention times of MHET (~3.2 min) and TPA (~5.8 min) in the chromatogram; peak areas proportional to enzyme activity.  
   **Next step trigger** – Compile activity data and calculate specific activities for each variant.

7. **Goal/Action** – Determine the melting temperature (Tₘ) of each variant by differential scanning fluorimetry (DSF).  
   **Detailed instructions** – Prepare 10 µM protein solutions in 50 mM sodium acetate buffer, pH 5.0, with 5 µM SYPRO Orange dye. Load 20 µL into a 96‑well PCR plate. Perform a temperature gradient from 20 °C to 95 °C at 1 °C min⁻¹ on a real‑time PCR instrument.  
   **Instruments** – **QuantStudio 7 Pro** (SetTemperature ramp 1 °C min⁻¹, 20–95 °C). The QuantStudio’s fluorescence detection and precise temperature control make it ideal for DSF.  
   **Expected observation** – A sigmoidal fluorescence increase; the inflection point corresponds to the Tₘ. Variants with Tₘ > 80 °C (e.g., HOT‑PETase) will show a sharp transition near 82.5 °C.  
   **Next step trigger** – Feed Tₘ and activity data into the computational workflow for the next design cycle.

---

## Computational Workflow

The computational arm of the campaign is an iterative loop that transforms experimental data into actionable design hypotheses. First, the activity (MHET/TPA release) and thermostability (Tₘ) values obtained from the experimental workflow are collated into a structured database. These quantitative phenotypes serve as labels for a supervised machine‑learning pipeline that has been trained on a curated set of PETase sequences from the Brenda database. The training set includes features such as amino‑acid composition, predicted secondary‑structure propensity, and evolutionary conservation scores. Three models—linear regression, logistic regression, and random forest—are evaluated for their ability to predict the optimal reaction temperature (T_opt) of a given variant. The model with the highest cross‑validated R² (typically the random forest) is selected to score a computationally generated mutant library.

The mutant library is produced by a combinatorial in‑silico directed‑evolution engine that applies single‑ and double‑point mutations to the current best variant (e.g., HOT‑PETase). Each mutant is evaluated by the predictive model; only those with a predicted T_opt ≥ 70 °C and a predicted Tₘ ≥ 80 °C are retained for synthesis. The top 200 candidates are then subjected to constraint‑network analysis (CNAnalysis) to identify thermolabile sequence stretches that may compromise stability at high temperature. Molecular‑dynamics (MD) simulations at 50 °C are run for the top 20 candidates to assess backbone flexibility and active‑site dynamics; mutants that maintain low RMSF in the catalytic triad while reducing flexibility in the identified thermolabile regions are prioritized.

The selected mutants are chemically synthesized, cloned, and expressed following the experimental workflow. The resulting activity and Tₘ data are fed back into the database, retraining the machine‑learning models to refine their predictive accuracy. This closed‑loop cycle continues until the desired performance metrics—T_opt ≥ 70 °C, Tₘ ≥ 82 °C, and ≥ 40 % activity increase over the previous generation—are achieved. Throughout, the computational pipeline also monitors for trade‑offs such as loss of activity at ambient temperatures, ensuring that the evolved PETase retains broad operational flexibility, as exemplified by FAST‑PETase and HOT‑PETase.