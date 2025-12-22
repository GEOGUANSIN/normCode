# NormCode File Format Guide

This document explains the purpose and characteristics of the three primary file formats used in the NormCode AI Planning Pipeline: `.ncd`, `.ncn`, and `.nc`.

---

## 1. `.ncd` - NormCode Draft

The **annotated blueprint** of the plan, designed for human review and debugging of the translation logic.

**Key Characteristics:**
-   **Semi-Formal:** Uses formal syntax but is not yet ready for execution.
-   **Rich with Annotations:** Includes `?:` (Question), `/:` (Description), and `...:` (Source Text) to document the translation process.
-   **Hierarchical:** Preserves the full, indented structure of the plan's logic.

---

## 2. `.ncn` - NormCode Natural

The **readable summary** of the plan, optimized for clarity and quick comprehension.

**Key Characteristics:**
-   **Natural Language Concepts:** Formal NormCode concepts are replaced with descriptive sentences.
-   **Structure Preservation:** Maintains the exact same hierarchical structure as the `.ncd` file.
-   **No Annotations:** All annotations (`?:`, `/:`, `...:`) are stripped out.

---

## 3. `.nc` - NormCode (Formal)

The **formal, machine-readable script** that is ready for the Orchestrator to execute.

**Key Characteristics:**
-   **Fully Formal:** The syntax is strict, consistent, and designed to be parsed.
-   **No Annotations:** All descriptive annotations are removed.
-   **Execution-Critical Information:** Enriched with `flow_indices` for unique identification of each inference, `agent sequence types`, and formalized operators.
