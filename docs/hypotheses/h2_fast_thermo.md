# Hypothesis Module H2  
**Title:** FAST-PETase + ThermoPETase salt-bridge network for semicrystalline PET near Tg

## Dynamic Knowledge Refresh
- Run `python scripts/update_pipeline.py --full` whenever new PDFs are added so the PETase KG and vector store reflect the latest structural/kinetic data before initiating the workflow (`README.md:40-137`).

## Literature Evidence & Rationale
1. **ThermoPETase charge network** – S121E/D186H/R280A mutations create new salt bridges (notably involving D246 and R280) and extend the working temperature window to ~60 °C, albeit with lower activity than FAST (`KnowledgeGraph/text/fbioe-11-1263996.txt:232-474`).  
2. **MutCompute portability** – Deep-learning scans across WT, ThermoPETase, and DuraPETase scaffolds identified T140D, N233K, and R224Q as stabilizing residues, and assembling these on ThermoPETase increased Tm by up to 9 °C with strong PET hydrolysis gains at 30–60 °C (`KnowledgeGraph/text/2021.10.10.463845v1.full.txt:100-142`).  
3. **Industrial constraint** – Reviews stress that enzymes must hydrolyze semi-crystalline PET (30–50 % crystallinity) at ≥65 °C to rival LCC_ICCG without intense pretreatment, but existing IsPETase derivatives lack such tolerance (`KnowledgeGraph/text/253_2024_Article_13222.txt:1130-1155`).

**Hypothesis:** Layering ThermoPETase-like salt-bridge and surface-charge mutations (T140D/N246D/S242T/D246 network) onto FAST-PETase will keep FAST’s catalytic loop open and productive when encountering rigid semicrystalline PET at 60–70 °C.

## Mechanistic Reasoning
1. **Electrostatic buttressing** – T140D and N246D create additional charge-charge interactions bridging the β-sheets surrounding the active-site cleft, preventing collapse when engaging crystalline surfaces.  
2. **Loop rigidity vs flexibility** – By reinforcing surface loops without altering the FAST catalytic triad, we expect to maintain the favorable k_cat/K_M at 50 °C while reducing the drop in activity observed on crystalline substrates.  
3. **Empirical precedent** – MutCompute already demonstrated that the selected mutations combine additively with FAST’s core, implying compatibility and an expectation of improved Tm without sacrificing solubility.

## Expected Impact & Future Work
- **Crystallinity tolerance** – Success enables digestion of textile fibers and bottle-grade flakes with minimal amorphization.  
- **Energy savings** – Less pretreatment lowers steam/mechanical energy requirements, improving process economics.  
- **Protocol linkage** – Follow the stepwise instructions in `docs/protocols/h2_relaxed.md` (full automation) or `docs/protocols/h2_constrained.md` (biofoundry-only) to move from gene design to kinetic benchmarking under defined crystallinity loads.
