# Change log — Rev 4.1 → Rev 4.2

**Header-only change. No value, row, sign or column order was changed.** The data rows are byte-for-byte identical to Rev 4.1 (checked).

| Old column name | New column name | Reason |
|---|---|---|
| `nu_cfd` | `Nu_closure_input` | It is a fixed model input (4.48, derived once from 3-D conjugate CFD), not a per-case CFD output |
| `nu_basis` | `Nu_closure_basis` | Matches the renamed column |
| `mean_T_pow4_K4` | `Tmean_pow4_K4` | It holds (mean T)⁴, not mean(T⁴) |

Rev 4.1 is kept unchanged as the archival record. The data dictionary has been updated to match.
