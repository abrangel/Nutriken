title: "NutriKen: A Clinical Nutritional Bioinformatics SaaS Platform for Healthcare Decision Support"
tags:

Python

Bioinformatics

Nutritional Genomics

Pharmacogenomics

Herb-Drug Interactions
authors:

name: "Cesar Abrahan Manzo Carvajal"
orcid: "0009-0006-4438-7456"
affiliation: "1"
affiliations:

name: "Independent Researcher"
index: 1
date: "2026-06-06"
bibliography: paper.bib

Summary

NutriKen is an open-source, clinical nutritional bioinformatics SaaS platform engineered specifically for physicians, clinical dietitians, and healthcare educators. The application dynamically compiles clinical evidence to map complex biomedical networks linking dietary supplements, herbal monographs, pharmacological interactions, and polygenic genomic variants. Developed using Python and FastAPI, NutriKen provides structural computational annotation to translate raw genomic data and chemical interactions into actionable clinical frameworks. By aggregating disparate public databases into a unified, high-speed interface, NutriKen enables healthcare professionals to transition from generalized dietary guidelines to quantified, precision nutrition interventions tailored to an individual's unique biological phenotype and genotype.

Statement of Need

While traditional bioinformatics software focuses heavily on raw sequence assembly, molecular dynamics, or strict laboratory workflows (such as FASTQ alignments), frontline healthcare providers operate in a vastly different environment. During a standard clinical consultation, clinicians often lack localized, data-driven platforms for translational nutritional genomics and pharmacogenomics. Dietary supplements and herbal medicines are widely utilized by patients, yet mapping their specific molecular mechanisms, clinically studied dosages, and critical herb-drug interaction hazards across polygenic networks remains a highly fragmented and manual process.

Clinicians are frequently forced to cross-reference multiple disjointed databases—such as searching PubMed for supplement efficacy, Ensembl for genetic variants, and separate toxicological databases for drug interactions—a process that is unsustainable in routine clinical practice. Furthermore, existing electronic health records (EHRs) rarely alert providers to the complex pharmacokinetic interactions between botanical compounds and standard allopathic medications, such as the inhibition of cytochrome P450 enzymes (e.g., CYP3A4).

NutriKen bridges this critical operational gap by integrating heterogenous data pipelines into a unified decision-support application. It aggregates clinical summaries from the Memorial Sloan Kettering Cancer Center (MSK) integrative medicine database, genomic contexts from NCBI Gene and Ensembl [@sayers2022ncbi], and metabolic pathways from KEGG [@kanehisa2000kegg]. The platform features an automated server-side reporting system that yields clinically formatted, paginated PDF outputs. This allows clinicians to rapidly analyze single nucleotide polymorphisms (SNPs) and evaluate multi-source toxicological markers without reliance on expensive, proprietary clinical software stacks.

State of the Field

Existing platforms in nutritional informatics frequently suffer from a binary limitation: they either provide non-technical, patient-facing descriptions that lack molecular depth, or they are purely academic cross-referencing tools (like Enrichr or raw NCBI portals) that lack interactive, diagnostic support layers tailored for daily clinical workflows [@kuleshov2016enrichr]. Many proprietary tools in the market also restrict access behind costly paywalls, limiting the democratization of precision nutrition.

NutriKen differentiates itself by incorporating a multi-source algorithmic triage designed specifically for the clinician's thought process. It automatically resolves broad phenotypic natural language terms and specific genomic variants (such as mapping the rs9939609 polymorphism directly to the FTO gene locus). It details molecular mechanisms of action, and dynamically cross-references PharmGKB gene-chemical datasets [@whirl2021pharmgkb] alongside Tapirro interaction indices (incorporating EMA/HMPC guidelines). Furthermore, NutriKen uniquely presents this data through audience-separated clinical insights, offering simplified narratives for patient education alongside highly technical biomedical data for the healthcare provider.

Software design

The architecture of NutriKen was designed with a focus on high concurrency, low latency, and lightweight deployment capabilities, ensuring the platform can be hosted on accessible infrastructure such as Hugging Face Spaces Docker containers.

The backend is built on Python 3.11 utilizing the FastAPI framework [@ramirez2020fastapi]. FastAPI was selected for its native asynchronous capabilities, which are essential for the NutriKen engine. When a clinician queries a condition or a gene, the backend routinely performs concurrent non-blocking HTTP requests via httpx to multiple external APIs (NCBI eUtils, Ensembl REST, and KEGG Pathway) to aggregate the biological cascade in real-time.

To prevent rate-limiting from public institutional APIs (such as the NCBI's strict request limits) and to accelerate clinical response times to under 200 milliseconds, NutriKen implements a Local SQLite Cache. This localized database stores previously resolved gene networks and MSK botanical monographs, significantly reducing redundant network overhead. Additionally, a connected Supabase PostgreSQL database serves as a robust repository for a pre-translated and curated index of 307 medicinal herbs, ensuring immediate data retrieval without relying on slow, runtime machine translations.

The frontend is intentionally decoupled from heavy JavaScript frameworks, utilizing Vanilla JS, HTML5, and CSS3. This architectural decision ensures the application remains ultra-lightweight and accessible on lower-end clinical hardware. For documentation and clinical output, NutriKen utilizes a custom recursive client-side pagination algorithm (nkPaginateReport) that smartly formats complex biological data into readable A4 pages without breaking atomic informational cards. Server-side, the Reportlab library is utilized to generate immutable, clinical-grade PDF reports complete with auto-generated Vancouver-style bibliographies, bypassing the need for heavy native dependencies like headless browsers.

Research impact statement

NutriKen serves as a vital translational bridge in the rapidly evolving field of precision medicine and nutritional genomics. For researchers and clinical educators, the software provides a demonstrative platform to teach how raw omics data translates into applied clinical interventions (N=1 nutrition).

By automating the mapping of 18 clinical conditions, over 100 genes, and 307 botanical compounds, NutriKen empowers dietitians and physicians to bypass physiological and genetic bottlenecks safely. For example, rather than relying on generalized supplementation, practitioners can use the tool to trace a metabolic roadblock in the folate cycle and definitively choose a biologically active metabolite (such as 5-Methyltetrahydrofolate) over synthetic precursors.

Furthermore, NutriKen has a direct impact on patient safety. By instantly highlighting severe herb-drug interactions—such as the risk of myopathy when combining specific statins with CYP3A4-inhibiting botanicals—it acts as a critical pharmacological safety net. Ultimately, NutriKen democratizes access to advanced bioinformatic analysis, allowing healthcare professionals without computational training to leverage global genomic and metabolic databases to improve patient outcomes.

AI usage disclosure

Generative AI tools and large language models were used to assist in translating, structuring, and refining the grammatical flow of the English text within this paper, as well as providing non-substantive structural coding assistance during the software's initial UI prototyping. However, all evaluative decisions, algorithmic architectures, clinical logic, literature curation, and technical claims were solely conceived, developed, and rigorously verified by the author, who bears full responsibility for the content and functionality of the software.
