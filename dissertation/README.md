# Dissertation

| File | What it is |
|---|---|
| [`SCHC_NRP_Dissertation_revised.pdf`](SCHC_NRP_Dissertation_revised.pdf) | **Revised edition (November 2026). Read this one.** The text is corrected to agree with the final results and code; every change is listed in its Appendix A. |
| [`SCHC_NRP_Dissertation.pdf`](SCHC_NRP_Dissertation.pdf) | The version submitted and assessed in May 2026. Its content is unchanged; only the two signature images on the declarations page have been blanked for public release. |
| [`ERRATA.md`](ERRATA.md) | The corrections, with how to verify each one against the repository. |
| [`source/`](source/) | LaTeX source of the revised edition. |

To build the revised edition from source:

```bash
cd dissertation/source
latexmk -pdf main.tex
```

The source supplied for the revision was a draft slightly later than the submitted PDF
(capitalisation of scale names, minor rewording, and one additional reference), so the revised
edition also includes those changes. The signature images on the declarations page are omitted
from the public edition.
