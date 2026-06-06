---
title: 'NutriKen: A Clinical Nutritional Bioinformatics SaaS Platform for Healthcare Decision Support'
tags:
  - Python
  - Bioinformatics
  - Nutritional Genomics
  - Pharmacogenomics
  - Herb-Drug Interactions
authors:
  - name: Cesar Abrahan Manzo Carvajal
    orcid: 0009-0006-4438-7456
    affiliation: Independent Researcher
date: 6 June 2026
bibliography: paper.bib
---

# Summary
NutriKen is an open-source, clinical nutritional bioinformatics SaaS platform engineered for physicians, nutritionists, and healthcare professionals. The application compiles clinical evidence to map complex biomedical networks linking dietary supplements, herbal monographs, drug interactions, and polygenic genomic variants. Developed using Python and FastAPI, NutriKen provides structural computational annotation to translate genomic and chemical interactions into actionable clinical data frameworks.

# Statement of Need
While traditional bioinformatics software focuses heavily on raw sequence assembly or strict laboratory workflows, frontline healthcare providers often lack localized, data-driven platforms for translational nutritional genomics and pharmacogenomics. Dietary supplements and herbal medicines are widely utilized, yet mapping their molecular mechanisms, studied dosages, and specific herb-drug interaction hazards across polygenic networks remains highly fragmented.

NutriKen bridges this operational gap by integrating heterogenous data pipelines—such as clinical summaries from the Memorial Sloan Kettering Cancer Center (MSK), genomic contexts from NCBI Gene/Ensembl, and metabolic routes from KEGG Pathway—into a unified decision-support application. The platform features an automated server-side reporting system that yields paginated clinical outputs. This allows clinicians to quickly analyze single nucleotide polymorphisms (SNPs) and evaluate multi-source toxicological markers without reliance on external proprietary server stacks.

# State of the Field
Existing platforms in nutritional informatics frequently provide either non-technical patient-facing descriptions or purely academic cross-references lacking interactive diagnostic support layers. NutriKen differentiates itself by incorporating multi-source algorithmic triage. It automatically resolves genomic variants (such as mapping rs9939609 to the FTO gene loci), details molecular mechanisms (e.g., CYP3A4 pathways), and dynamically cross-references PharmGKB gene-chemical datasets and Tapirro interaction indices to offer audience-separated clinical insights.

# References
