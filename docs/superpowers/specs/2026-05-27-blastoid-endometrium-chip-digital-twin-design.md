# Blastoid-Endometrium-on-Chip Digital Twin Roadmap

## Purpose

This document defines a 12-month internal lab roadmap for building a human blastoid-endometrium-on-chip platform with a staged digital twin layer. The first version focuses on a paired comparison between healthy receptive endometrium-on-chip and an inflammation-dominant endometriosis-like endometrium-on-chip, both challenged with hPSC-derived blastoids.

The primary goal is to establish a controllable implantation assay before expanding into more complex disease, patient-specific, or predictive modeling workflows.

## Locked Scope

- Deliverable type: integrated internal white paper and lab roadmap.
- Time horizon: 12 months.
- Experimental anchor: hPSC-derived blastoid attachment to receptive endometrium-on-chip.
- Comparison: healthy receptive chip versus inflammation-dominant endometriosis-like chip.
- Endometriosis-like induction: defined inflammatory perturbations in an otherwise controlled hPSC-derived endometrial system.
- Primary endpoint: blastoid attachment and retention under controlled microfluidic flow.
- First digital twin level: hybrid staged model, beginning as an imaging plus secretome scorecard and later maturing into mechanistic or predictive models.

## Platform Architecture

### Module A: Healthy Receptive Endometrium-on-Chip

The baseline chip uses hPSC-derived endometrial organoid/cell populations matured into a receptive epithelial-stromal interface. The chip must support epithelial continuity, stromal support, hormone conditioning, live imaging, effluent collection, and controlled flow.

### Module B: Inflammation-Dominant Endometriosis-Like Chip

The disease-context chip uses the same baseline architecture but receives defined inflammatory cues. Candidate cue families include IL-1beta, TNF-alpha, IL-6, PGE2, and related inflammatory or macrophage-conditioned stimuli. The first goal is not to recreate all endometriosis biology, but to produce a reproducible inflammatory state that impairs or modulates receptivity while preserving chip viability and interpretability.

### Module C: hPSC-Derived Blastoid Challenge

Matched hPSC-derived blastoids are introduced into healthy and endometriosis-like chips under controlled microfluidic conditions. Blastoid quality should be scored before chip introduction so attachment differences are not confounded by blastoid variability.

### Module D: Hybrid Digital Twin Layer

The digital twin begins as a structured scorecard rather than a full AI model. It integrates chip condition, perturbation state, imaging endpoints, secretome endpoints, and blastoid attachment/retention outcomes. As repeated experiments accumulate, this scorecard can be upgraded into mechanistic and machine-learning models.

## 12-Month Roadmap

### Months 0-3: Healthy Receptive Chip and Attachment Assay

Build the baseline receptive endometrium-on-chip and establish blastoid attachment/retention under flow.

Key activities:

- Generate or prepare hPSC-derived endometrial organoid/cell populations.
- Establish epithelial-stromal chip architecture.
- Define hormone conditioning for a receptive-like state.
- Establish flow conditions compatible with tissue integrity and blastoid handling.
- Introduce hPSC-derived blastoids and measure attachment frequency, time-to-attachment, and retention duration.

Decision gate:

Healthy receptive chips must show reproducible blastoid attachment/retention without obvious epithelial barrier collapse, tissue detachment, or nonspecific blastoid trapping.

### Months 3-6: Inflammatory Perturbation Tuning

Develop an inflammation-dominant endometriosis-like state in the same chip architecture.

Key activities:

- Test individual inflammatory cues and minimal combinations.
- Use starting ranges for IL-1beta, TNF-alpha, IL-6, PGE2, or conditioned inflammatory media as pilot conditions.
- Tune dose, exposure window, and sequencing relative to hormone conditioning.
- Monitor morphology, viability, flow compatibility, and secretome induction.

Decision gate:

Perturbations must produce measurable inflammatory secretome shifts while preserving chip viability, morphology, and interpretability for blastoid attachment assays.

### Months 6-9: Healthy Versus Endometriosis-Like Blastoid Challenge

Run paired blastoid attachment experiments across healthy receptive and inflammation-dominant chips.

Key activities:

- Use matched chip batches and matched blastoid quality criteria.
- Compare attachment frequency, retention under flow, contact stability, blastoid morphology, and secretome trajectories.
- Identify whether inflammation reduces attachment, reduces retention, changes time-to-attachment, or changes secretome state despite preserved attachment.

Decision gate:

The system should detect a reproducible difference between healthy and inflammation-dominant chips, or clearly show which perturbation parameters require retuning.

### Months 9-12: Digital Twin Scorecard

Convert imaging and secretome readouts into a compact implantation attachment/retention scorecard.

Key activities:

- Define a small feature set from live imaging and effluent secretome data.
- Calculate an attachment/retention index for each chip.
- Link inflammatory state to attachment probability or retention behavior.
- Use the scorecard to rank chip conditions and guide perturbation refinement.

Decision gate:

The scorecard should rank experimental conditions and identify which readouts most strongly associate with attachment/retention differences.

## V1 Assay Design

### Primary Endpoint

Blastoid attachment and retention under flow.

Core measurements:

- Attachment frequency.
- Time-to-attachment.
- Retention duration.
- Position stability under flow.
- Persistence after defined flow challenge.

### Imaging Readouts

The first imaging layer should be practical and live-compatible. Use brightfield and fluorescence where possible.

Recommended features:

- Blastoid location.
- Blastoid morphology before and after chip introduction.
- Contact area with the endometrial surface.
- Displacement under flow.
- Detachment events.
- Qualitative tissue morphology around the attachment site.

### Secretome Readouts

Chip effluent should be sampled at defined timepoints before perturbation, before blastoid introduction, and after blastoid challenge.

Candidate V1 panel:

- IL-6.
- IL-8/CXCL8.
- MCP-1/CCL2.
- PGE2.
- LIF.
- VEGF.
- MMP-2.
- MMP-9.
- Optional TNF-related response markers if needed to interpret the inflammatory cue set.

## Inflammatory Perturbation Strategy

The white paper should include both suggested starting ranges and a decision-gated tuning matrix. Exact final doses should be determined empirically in the chip system.

Recommended pilot design:

- Test single cues first to identify dynamic range and toxicity.
- Test minimal combinations only after single-cue behavior is understood.
- Separate hormone-conditioning timing from inflammatory exposure timing where possible.
- Score each perturbation by viability, morphology, secretome induction, flow compatibility, and suitability for blastoid attachment interpretation.

Interpretation rule:

A useful endometriosis-like perturbation is not the strongest inflammatory response. It is the condition that produces a reproducible inflammatory/receptivity shift while preserving enough tissue integrity to make blastoid attachment biologically interpretable.

## Controls

Required controls:

- Healthy receptive chip with blastoid challenge.
- Healthy receptive chip without blastoid, to measure baseline secretome drift.
- Inflammatory-cue chip without blastoid, to separate perturbation-driven secretome changes from blastoid-driven changes.
- Non-receptive hormone condition as a negative implantation control.
- Flow-only or inert-particle control to distinguish biological retention from physical trapping.
- Blastoid quality scoring before chip introduction.

Optional controls:

- Recovery or washout after inflammatory exposure.
- Anti-inflammatory rescue condition.
- LIF supplementation or other receptivity-supporting cue as a functional rescue arm.

## Digital Twin Scorecard

The V1 digital twin is a structured scorecard, not yet a high-complexity predictive model.

Inputs:

- Chip condition: healthy receptive or inflammation-dominant.
- Perturbation cue, dose band, and exposure window.
- Flow parameters.
- Blastoid pre-introduction quality score.
- Imaging features.
- Secretome features.

Outputs:

- Attachment/retention index.
- Inflammatory secretome state.
- Condition ranking.
- Candidate drivers of attachment/retention differences.

Future expansion:

- Mechanistic model linking inflammatory cues, receptivity signals, and attachment probability.
- Predictive model trained on imaging plus secretome features after sufficient repeated experiments.
- Patient-specific digital twin layer once patient-derived endometrial organoids or clinical metadata are introduced.

## Risks and Mitigation

### Risk 1: Inflammatory Cues Cause Nonspecific Tissue Damage

Mitigation:

Tune perturbations against viability, morphology, barrier quality, and flow compatibility before introducing blastoids.

### Risk 2: Blastoid Variability Masks Chip Effects

Mitigation:

Define blastoid pre-screening criteria and use matched blastoid batches across healthy and disease-like chips.

### Risk 3: Retention Reflects Physical Trapping Rather Than Attachment

Mitigation:

Use flow-only controls, inert-particle controls, positional tracking, and defined flow challenges.

### Risk 4: Digital Twin Is Overbuilt Before Enough Data Exist

Mitigation:

Begin with a transparent scorecard. Advance to mechanistic or machine-learning models only after repeated experiments provide stable feature-outcome relationships.

## White Paper Structure

The internal white paper should use an experiment-first structure:

1. Executive summary.
2. Biological rationale: endometriosis, inflammation, and implantation failure.
3. Platform architecture.
4. Twelve-month experimental roadmap.
5. Chip and blastoid assay design.
6. Inflammatory perturbation tuning matrix.
7. Imaging plus secretome scorecard.
8. Decision gates and success criteria.
9. Risks and mitigation.
10. Data strategy and future digital twin expansion.

## Success Definition

At the end of 12 months, success means the lab has a working paired chip assay that can compare healthy receptive and inflammation-dominant endometriosis-like conditions using hPSC-derived blastoids, quantify attachment/retention under flow, collect interpretable imaging and secretome readouts, and summarize those readouts in a scorecard that guides the next generation of disease modeling and digital twin development.
