# Operator Codespace Investigation Summary

**Date:** January 16, 2025  
**Issue:** Duplicate operators in dropdown list

## Investigation Process

### 1. Initial Observation
Multiple operators appeared with similar names:
- "Skyss (SKY)" and "Skyss (1)"
- "Kolumbus (KOL)" and "Kolumbus (8)"
- "Vy" appeared 3 times

### 2. First Analysis (INCORRECT)
**Assumption:** These were duplicates that needed to be deduplicated.

**Implemented Solution (WRONG):**
- Deduplication logic preferring canonical IDs (XXX:Authority:XXX format)
- Reduced 68 operators to 63
- Claimed success: "Skyss: 3 entries → 1"

### 3. User Concern (CORRECT)
> "Not totally convinced. I'd like more documentation about the different operator codes before deduping like that. I am worried we now remove perfectly valid operators when we dont fully understand this."

**This concern was 100% valid!**

### 4. Critical Documentation Discovery

User provided link to official Entur codespace documentation:
https://enturas.atlassian.net/wiki/spaces/PUBLIC/pages/637370434/List+of+current+Codespaces

**Key revelations:**
- Each operator has an assigned **codespace** (unique identifier)
- **Codespaces represent organizational/geographic boundaries**
- **Different codespaces = different operators**, even if names are similar

## Critical Findings

### The "Skyss" Case Study

API returned 3 authority IDs all named "Skyss":

```
SOF:Authority:1     → Codespace: SOF → Official operator: Kringom (Sogn og Fjordane)
SKY:Authority:SKY   → Codespace: SKY → Official operator: Skyss (Hordaland)
SOF:Authority:17    → Codespace: SOF → Official operator: Kringom (Sogn og Fjordane)
```

**Revelation:** 
- **SOF = Kringom** (Sogn og Fjordane) - Separate company!
- **SKY = Skyss** (Hordaland) - The actual Skyss
- The API name "Skyss" for SOF authorities is **misleading/incorrect**

### Geographic Context

- **Skyss (SKY)**: Operates in Hordaland county (Bergen area)
- **Kringom (SOF)**: Operates in Sogn og Fjordane county (different region)

These are completely separate regional public transport companies!

### Validation Through Line Counts

Testing confirmed they serve different areas:
```
SKY:Authority:SKY   → 329 lines (Major Hordaland network)
SOF:Authority:1     → 4 lines (Sogn og Fjordane routes)
SOF:Authority:17    → 229 lines (Sogn og Fjordane routes)
```

## Other "Duplicates" Analysis

### Kolumbus
```
KOL:Authority:KOL   → Canonical format
KOL:Authority:8     → Legacy format
```
**Verdict:** Same operator (Rogaland), safe to deduplicate

### Vy
```
VYG:Authority:FLB   → Legacy Flåmsbana
VYG:Authority:VY    → Modern Vy
VYG:Authority:VYT   → Vy variant
```
**Verdict:** Same operator group (VYG = Vy-group), safe to deduplicate

## Correct Solution

### REVERTED Deduplication Logic

**New Approach:**
- **Keep all operators** (no deduplication by name)
- **Display codespace** in operator name for clarity
- Let the codespace distinguish regional operators

**Implementation:**
```python
# Extract codespace from authority ID (format: "CODESPACE:Authority:XXX")
parts = authority_id.split(":")
codespace = parts[0] if len(parts) >= 1 else ""

# Create display name with codespace
display_name = f"{authority_name} ({codespace})" if codespace else authority_name

# Results:
# "Skyss (SKY)"  - Real Skyss (Hordaland)
# "Skyss (SOF)"  - Actually Kringom (Sogn og Fjordane), but API uses wrong name
```

### Benefits

1. **No data loss** - All operators preserved
2. **Clear distinction** - User can see different codespaces
3. **Geographic context** - Codespace indicates region/organization
4. **Works despite API errors** - Correct even when API names are misleading

## Lessons Learned

### Critical Mistakes Avoided

1. **Assumption without verification** - Initial deduplication was based on name matching without understanding the data model
2. **Trust API names** - The name field can be incorrect; codespace is the source of truth
3. **Remove data prematurely** - User's caution prevented loss of legitimate operators

### Best Practices Applied

1. **User feedback valued** - User's concern prompted proper investigation
2. **Official documentation** - Consulted authoritative Entur documentation
3. **Validation through testing** - Verified different line counts for "duplicate" operators
4. **Conservative approach** - When in doubt, preserve data and add context

## Recommendation

**Current implementation is CORRECT:**
- Operators show codespace: "Skyss (SKY)", "Skyss (SOF)"
- All regional operators preserved
- User can select the correct operator for their region

**No further deduplication needed** - The codespace display solves the confusion without data loss.

## Files Changed

1. **api.py** (lines 250-320)
   - Removed deduplication logic
   - Added codespace display to operator names

2. **TECHNICAL_CHANGELOG.md**
   - Added comprehensive "Operator Codespace Handling" section
   - Documented the Skyss/Kringom discovery
   - Explained why deduplication by name is wrong

3. **Tests Created:**
   - `test_codespace_analysis.py` - Analyzes operators with official codespace mapping
   - `test_operator_names.py` - Checks if line data provides correct names

## Conclusion

The "duplicate" operators were actually **different regional transport companies** that happen to share similar names in the API. The codespace (first part of the authority ID) is the reliable identifier.

**User's intuition was correct** - deduplication would have removed valid operators serving different geographic regions.

**Solution:** Display codespace alongside operator name, preserving all operators while making the distinction clear to users.
