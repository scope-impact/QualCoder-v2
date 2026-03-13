---
name: qualitative-coding
description: |
  Qualitative coding methodology expertise for QualCoder v2 development.
  Provides research-grounded knowledge of coding methods, frameworks, and AI-assisted analysis.

  **Invoke when:**
  - Implementing coding features (code creation, hierarchy, memos, segments)
  - Designing AI-assisted coding workflows (LLM suggestions, auto-coding)
  - Making UX decisions about coding interfaces
  - Writing domain entities, events, or invariants for the coding bounded context
  - Evaluating feature parity with NVivo, ATLAS.ti, MAXQDA
  - Discussing qualitative research methodology with users

  **Provides:**
  - Saldana's coding method taxonomy (35+ methods across 7 categories)
  - Framework knowledge (Grounded Theory, Thematic Analysis, Framework Analysis, IPA)
  - Quality criteria (Lincoln & Guba trustworthiness, inter-coder reliability)
  - AI-assisted coding best practices and ethical guardrails
  - Feature-to-methodology mapping for implementation decisions
---

# Qualitative Coding Methodology Reference

Domain knowledge for building QualCoder v2's coding features grounded in established qualitative research methodology.

---

## 1. What Is Qualitative Coding?

Coding is the process of assigning short labels (codes) to segments of qualitative data (text, images, audio, video) to categorize, summarize, and find patterns. As Saldana states: "coding is just one way, not *the* way to analyze qualitative data."

### Core Terminology

| Term | Definition | QualCoder Entity |
|------|-----------|-----------------|
| **Code** | A word/phrase labeling a data segment | `Code` entity |
| **Category** | A grouping of related codes | Code hierarchy (parent) |
| **Theme** | An interpretive pattern across categories | Derived from categories |
| **Memo** | Researcher's reflective notes on codes/data | `Memo` / Journal |
| **Codebook** | Structured list of all codes with definitions | Export feature |
| **Segment** | A marked portion of data linked to a code | `Segment` entity |
| **Annotation** | A note attached to a specific data segment | Annotation feature |
| **Saturation** | Point where new data yields no new codes | Analytics indicator |

### The Coding Hierarchy

```
Theme (interpretive pattern)
  └── Category (grouping)
        └── Code (label)
              └── Segment (data excerpt)
                    └── Source (document/media)
```

---

## 2. Saldana's Coding Methods Taxonomy

Reference: Saldana, J. (2021). *The Coding Manual for Qualitative Researchers* (4th ed.). SAGE.

### First Cycle Coding (Initial pass — applied directly to data)

#### Grammatical Methods
| Method | Description | Use Case |
|--------|------------|----------|
| **Attribute Coding** | Logs metadata (participant demographics, setting, dates) | Managing multi-site/multi-participant datasets |
| **Magnitude Coding** | Adds intensity/frequency qualifiers to codes (e.g., ANXIETY [HIGH]) | Studies needing degree/intensity differentiation |
| **Simultaneous Coding** | Applies two or more codes to a single segment | When data is complex and multi-layered |
| **Sub-coding** | Adds second-order detail to a primary code | Refining broad codes into nuanced subcategories |

#### Elemental Methods (foundational, widely used)
| Method | Description | Use Case |
|--------|------------|----------|
| **Descriptive Coding** | Topic labels summarizing passage content | Beginners; ethnographies; inventorying topics |
| **In Vivo Coding** | Uses participant's own words as codes | Grounded theory; honoring participant voice |
| **Process Coding** | Uses gerunds (-ing words) to capture actions | Studies focused on processes, sequences, change |
| **Initial Coding** | Open-ended, line-by-line breaking apart of data | Grounded theory first pass |
| **Structural Coding** | Codes based on research questions applied to segments | Multi-participant interview studies |

#### Affective Methods (subjective experience)
| Method | Description | Use Case |
|--------|------------|----------|
| **Emotion Coding** | Labels emotions experienced or recalled | Intrapersonal/interpersonal experience studies |
| **Values Coding** | Codes for values, attitudes, and beliefs (V/A/B) | Studies of cultural identity, worldview |
| **Versus Coding** | Identifies dichotomies and conflicts (X vs. Y) | Power dynamics, conflict studies |
| **Evaluation Coding** | Assigns judgments of merit or worth | Policy, program evaluation research |

#### Literary and Language Methods
| Method | Description | Use Case |
|--------|------------|----------|
| **Dramaturgical Coding** | Applies theatrical concepts (objectives, conflicts, tactics) | Performance studies, identity research |
| **Motif Coding** | Identifies recurring symbolic elements | Folklore, literary, narrative studies |
| **Narrative Coding** | Codes story elements (setting, conflict, resolution) | Narrative inquiry, oral histories |
| **Verbal Exchange Coding** | Codes conversational dynamics | Sociolinguistics, interaction analysis |

#### Exploratory Methods (preliminary investigation)
| Method | Description | Use Case |
|--------|------------|----------|
| **Holistic Coding** | Single code per large data chunk | First pass on large datasets, quick overview |
| **Provisional Coding** | Starts with pre-set code list from theory/literature | Deductive studies, literature-driven research |
| **Hypothesis Coding** | Tests researcher's hunches against data | Theory testing, mixed methods |

#### Procedural Methods
| Method | Description | Use Case |
|--------|------------|----------|
| **Protocol Coding** | Codes from pre-established instruments | Structured observation, standardized protocols |
| **OCM Coding** | Uses Outline of Cultural Materials categories | Cross-cultural, anthropological research |
| **Domain & Taxonomic** | Identifies cultural domains and taxonomies | Ethnographic research |
| **Causation Coding** | Maps cause-effect relationships | Policy analysis, process tracing |

#### Themeing the Data (4th edition addition)
| Method | Description | Use Case |
|--------|------------|----------|
| **Themeing the Data** | Applies theme-level labels directly (phrases/sentences) | When patterns are immediately apparent |
| **Metaphor Coding** | Identifies figurative language and metaphors | Studies where metaphor reveals worldview |

### Second Cycle Coding (Analytical refinement of first cycle codes)

Second cycle methods work with the *codes themselves*, not raw data:

| Method | Description | Use Case |
|--------|------------|----------|
| **Pattern Coding** | Groups first-cycle codes into smaller themes/constructs | Condensing large code sets |
| **Focused Coding** | Selects most frequent/significant codes to develop categories | Grounded theory (Charmaz) |
| **Axial Coding** | Relates categories to subcategories along properties/dimensions | Grounded theory (Strauss & Corbin) |
| **Theoretical Coding** | Integrates categories into a coherent theory | Grounded theory final stage |
| **Elaborative Coding** | Builds on previous studies' codes to refine theory | Longitudinal or replication studies |
| **Longitudinal Coding** | Tracks code changes across time | Longitudinal designs |

### Implementation Guidance for QualCoder v2

```
First Cycle → User applies codes to data segments
              QualCoder supports: code creation, hierarchy, color, memo
              AI can: suggest codes, auto-code with provisional lists

Second Cycle → User reorganizes codes into categories/themes
               QualCoder supports: drag-drop hierarchy, merge codes, code reports
               AI can: suggest groupings, identify patterns, co-occurrence analysis
```

---

## 3. Major Qualitative Frameworks

### Grounded Theory (GT)

**Origins**: Glaser & Strauss (1967). Three major schools:

| School | Key Figure | Coding Stages | Philosophy |
|--------|-----------|---------------|------------|
| **Classic GT** | Glaser (1978) | Open → Selective → Theoretical | Objectivist; theory "emerges" |
| **Straussian GT** | Strauss & Corbin (1990) | Open → Axial → Selective | Systematic procedures |
| **Constructivist GT** | Charmaz (2006) | Initial → Focused → Theoretical | Interpretivist; meaning co-constructed |

**Core GT Procedures:**
- **Constant comparison**: Continuously compare data↔codes, codes↔codes, codes↔categories
- **Theoretical sampling**: Let emerging theory guide further data collection
- **Theoretical saturation**: Stop when new data adds no new insights
- **Memo writing**: Record analytical thinking throughout

**QualCoder implications**: Support iterative coding, code merging, code frequency tracking, memo linking, saturation indicators.

### Braun & Clarke's Reflexive Thematic Analysis (RTA)

**Reference**: Braun, V. & Clarke, V. (2006, 2022). Most cited qualitative method (190,000+ citations).

**Six Phases:**

| Phase | Activity | QualCoder Support |
|-------|----------|-------------------|
| 1. **Familiarization** | Read/re-read data, take initial notes | Source viewer, annotations |
| 2. **Initial Coding** | Systematically code interesting features | Code creation, segment marking |
| 3. **Searching for Themes** | Group codes into candidate themes | Code hierarchy, drag-drop grouping |
| 4. **Reviewing Themes** | Check themes against coded segments and full dataset | Code reports, segment review |
| 5. **Defining & Naming** | Refine theme names and scope | Code renaming, memo writing |
| 6. **Writing Up** | Produce report with data extracts | Export, reports |

**TA as a family of methods** (Braun & Clarke 2022 typology):
- **Coding reliability TA**: Multiple coders, ICR, codebook-driven
- **Codebook TA**: Structured codebook, more deductive
- **Reflexive TA**: Researcher subjectivity as resource, iterative

**2024 Update**: Reflexive Thematic Analysis Reporting Guidelines (RTARG) published as alternative to COREQ/SRQR.

### Content Analysis

**Reference**: Krippendorff, K. (2018). *Content Analysis: An Introduction to Its Methodology* (4th ed.).

- Systematic, replicable analysis of text
- Quantitative orientation: code frequencies, co-occurrence matrices
- Strong emphasis on inter-coder reliability
- **QualCoder support**: Code frequency reports, co-occurrence matrices, coding comparison

### Framework Analysis (Ritchie & Spencer)

- Developed at UK National Centre for Social Research
- Matrix-based: cases (rows) × themes (columns)
- Good for applied policy research with specific questions
- Supports both inductive and deductive approaches
- **QualCoder support**: Case management, cross-case comparison, matrix displays

### Interpretative Phenomenological Analysis (IPA)

**Reference**: Smith, Flowers & Larkin (2009).

- Focus on lived experience and meaning-making
- Idiographic: each case analyzed in depth before cross-case patterns
- Double hermeneutic: researcher interprets participant's interpretation
- Small samples (typically 3-6 participants)
- **QualCoder support**: Case-by-case coding, individual case memos, cross-case themes

### Discourse Analysis

- Analyzes how language constructs social reality
- Focus on rhetorical strategies, power dynamics, positioning
- Codes are about linguistic function, not content
- **QualCoder support**: Fine-grained text coding, verbal exchange coding

### Narrative Analysis

- Analyzes story structures (setting, characters, plot, resolution)
- Codes story elements and narrative arcs
- **QualCoder support**: Narrative coding, temporal ordering, case linking

---

## 4. Quality & Rigor Criteria

### Lincoln & Guba's Trustworthiness (1985)

The gold standard for qualitative research quality:

| Criterion | Parallel to | Strategies | QualCoder Support |
|-----------|------------|------------|-------------------|
| **Credibility** | Internal validity | Prolonged engagement, triangulation, member checking, peer debriefing | Memo trails, annotation |
| **Transferability** | External validity | Thick description | Rich segment exports, context |
| **Dependability** | Reliability | Audit trail, process documentation | Coding history, journals |
| **Confirmability** | Objectivity | Reflexive memos, audit trail | Memo system, code history |

### Inter-Coder Reliability (ICR)

When multiple coders work on same data:

| Measure | Best For | Notes |
|---------|----------|-------|
| **Percent agreement** | Quick check | Doesn't account for chance |
| **Cohen's kappa** | 2 coders, nominal data | Most widely used; κ > 0.8 = strong |
| **Krippendorff's alpha** | 2+ coders, any data level | Most flexible; handles missing data |
| **Scott's pi** | 2 coders | Alternative to kappa |

**Interpretation (Landis & Koch, 1977):**
- < 0.00 = no agreement
- 0.21–0.40 = fair
- 0.41–0.60 = moderate
- 0.61–0.80 = substantial
- 0.81–1.00 = near-perfect

**Best practices:**
- Calculate ICR throughout project, not just at end
- Train coders on codebook before independent coding
- Use at least 10-20% of data for reliability testing
- Document and resolve disagreements through discussion

### Codebook Development

A codebook should include for each code:
1. **Code name** — Short, descriptive label
2. **Definition** — Clear boundary of what the code means
3. **Inclusion criteria** — When to apply this code
4. **Exclusion criteria** — When NOT to apply
5. **Example** — Typical data excerpt
6. **Counter-example** — Data that looks similar but doesn't fit

---

## 5. AI-Assisted Qualitative Coding

### Current Landscape (2024-2026)

Commercial QDA tools with AI:
- **ATLAS.ti 25**: GPT-powered auto-coding, AI Lab for intent-based coding
- **NVivo 15**: ML-based autocode, AI summarization, suggest codes
- **MAXQDA 24/Tailwind**: AI-assisted coding and theme generation

### Three Emerging Paradigms

1. **Rigorous Manual Analysis** — Traditional hand-coding, transparent audit trail
2. **AI-Augmented Manual Analysis** — AI suggests, human decides (QualCoder v2 approach)
3. **AI-Native Structured Analysis** — AI-first but maintaining academic rigor

### QualCoder v2's AI Philosophy

QualCoder uses AI transparently:
- Prompts are visible and modifiable by the researcher
- AI suggestions require human approval (never auto-applied)
- Full audit trail of AI-generated vs. human-generated codes
- Researcher remains the analytical authority

### Best Practices for AI-Assisted Coding

**DO:**
- Use AI for initial code suggestions on large datasets
- Let AI identify potential patterns for human review
- Use AI to check coding consistency across documents
- Maintain audit trail: save prompts, AI outputs, human decisions
- Validate AI coding against manual coding of a subset
- Use provisional coding with AI-generated start lists

**DON'T:**
- Auto-accept AI-generated codes without review
- Use AI as sole coder (no human verification)
- Assume AI understands context, power dynamics, or cultural nuance
- Skip reflexivity because "the AI did it"
- Claim methodological rigor without human analytical engagement

### Prompt Engineering for Qualitative Coding

When implementing AI coding features, prompts should:
1. Specify the coding method (e.g., "Use descriptive coding to label topics")
2. Provide codebook context (existing codes, definitions)
3. Include research question for structural/theoretical alignment
4. Request rationale alongside code suggestions
5. Ask for confidence levels to guide human review priority

---

## 6. Feature-to-Methodology Mapping

When implementing QualCoder features, map them to methodology:

| Feature | Methodology Support | Priority |
|---------|-------------------|----------|
| Code creation with color + memo | All methods | P0 |
| Code hierarchy (tree) | All methods (categories→themes) | P0 |
| In vivo coding (select text → auto-name) | Grounded Theory, many first-cycle methods | P1 |
| Code co-occurrence matrix | Content Analysis, pattern identification | P1 |
| Code frequency reports | Content Analysis, saturation tracking | P1 |
| Case-by-case coding view | IPA, Framework Analysis | P1 |
| Framework matrix (cases × themes) | Framework Analysis | P2 |
| Codebook export (name, definition, examples) | All methods, ICR workflows | P1 |
| Inter-coder comparison | Coding reliability TA, Content Analysis | P2 |
| AI code suggestions | AI-augmented workflows | P1 |
| AI pattern/theme detection | Second cycle assistance | P2 |
| Memo linking (code↔memo↔source) | Grounded Theory, Reflexive TA | P1 |
| Saturation indicator | Grounded Theory | P3 |
| Coding history / audit trail | All methods (trustworthiness) | P1 |
| Simultaneous coding (multiple codes per segment) | Complex data, mixed methods | P1 |
| Process coding view (temporal) | Process Coding, Narrative Analysis | P3 |

---

## 7. Glossary of Key Concepts

| Term | Definition |
|------|-----------|
| **Abductive reasoning** | Moving between data and theory iteratively |
| **Axial coding** | Relating categories to subcategories (Strauss & Corbin) |
| **Code** | A researcher-generated label for a data segment |
| **Code co-occurrence** | When two codes overlap or appear in proximity |
| **Codebook** | Structured reference of all codes with definitions |
| **Coding cycle** | A complete pass through data applying/refining codes |
| **Constant comparison** | Continuously comparing data, codes, and categories |
| **Core category** | Central concept around which theory is built (GT) |
| **Deductive coding** | Applying pre-existing codes from theory/literature |
| **Double hermeneutic** | Researcher interpreting participant's interpretation (IPA) |
| **Focused coding** | Selecting significant first-cycle codes for categories |
| **Inductive coding** | Generating codes from the data itself |
| **In vivo code** | A code using participant's exact words |
| **Member checking** | Validating findings with participants |
| **Memo** | Researcher's analytical notes during coding |
| **Open coding** | Initial, unrestricted coding of data |
| **Pattern coding** | Grouping first-cycle codes into meta-codes |
| **Reflexivity** | Researcher's awareness of their own influence |
| **Saturation** | No new codes/themes emerging from additional data |
| **Segment** | A portion of data to which a code is applied |
| **Theoretical sampling** | Data collection guided by emerging theory |
| **Theme** | An interpretive pattern capturing meaning across data |
| **Thick description** | Detailed contextual account enabling transferability |
| **Triangulation** | Using multiple data sources/methods/researchers |
| **Trustworthiness** | Overall quality of qualitative research (Lincoln & Guba) |

---

## 8. Key References

### Foundational Texts
- **Saldana, J. (2021)**. *The Coding Manual for Qualitative Researchers* (4th ed.). SAGE.
- **Braun, V. & Clarke, V. (2006)**. Using thematic analysis in psychology. *Qualitative Research in Psychology*, 3(2), 77-101.
- **Braun, V. & Clarke, V. (2022)**. *Thematic Analysis: A Practical Guide*. SAGE.
- **Charmaz, K. (2014)**. *Constructing Grounded Theory* (2nd ed.). SAGE.
- **Corbin, J. & Strauss, A. (2015)**. *Basics of Qualitative Research* (4th ed.). SAGE.
- **Glaser, B.G. & Strauss, A.L. (1967)**. *The Discovery of Grounded Theory*. Aldine.
- **Krippendorff, K. (2018)**. *Content Analysis: An Introduction to Its Methodology* (4th ed.). SAGE.
- **Lincoln, Y.S. & Guba, E.G. (1985)**. *Naturalistic Inquiry*. SAGE.
- **Smith, J.A., Flowers, P. & Larkin, M. (2009)**. *Interpretative Phenomenological Analysis*. SAGE.
- **Ritchie, J. & Spencer, L. (1994)**. Qualitative data analysis for applied policy research. In *Analyzing Qualitative Data*.

### Recent Developments
- **Braun, V. & Clarke, V. (2024)**. RTARG: Reflexive Thematic Analysis Reporting Guidelines. *Palliative Medicine*.
- **O'Connor, C. & Joffe, H. (2020)**. Intercoder reliability in qualitative research. *International Journal of Qualitative Methods*.
- **Lumivero (2025)**. The State of AI in Qualitative Research.

---

## 9. Decision Guide: Which Coding Method?

```
START
  │
  ├── Do you have pre-existing codes from theory?
  │     YES → Provisional Coding / Hypothesis Coding
  │     NO ↓
  │
  ├── Is this your first pass through the data?
  │     YES ↓
  │     │   ├── Large dataset, need overview? → Holistic Coding
  │     │   ├── Want participant voice? → In Vivo Coding
  │     │   ├── Want topic inventory? → Descriptive Coding
  │     │   ├── Studying processes/actions? → Process Coding
  │     │   └── Grounded theory study? → Initial Coding (line-by-line)
  │     │
  │     NO → Second Cycle Methods ↓
  │           ├── Need to group codes? → Pattern Coding / Focused Coding
  │           ├── Need relationships? → Axial Coding
  │           └── Building theory? → Theoretical Coding
  │
  ├── What aspect interests you?
  │     ├── Emotions → Emotion Coding
  │     ├── Values/beliefs → Values Coding
  │     ├── Conflicts → Versus Coding
  │     ├── Program effectiveness → Evaluation Coding
  │     ├── Stories → Narrative Coding
  │     └── Performance/identity → Dramaturgical Coding
  │
  └── Multiple coders?
        YES → Codebook approach + ICR measurement
        NO → Reflexive approach + memo trail
```
