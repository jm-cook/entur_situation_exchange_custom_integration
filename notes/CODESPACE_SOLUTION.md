# Codespace-Based Operator Selection - Final Solution

**Date:** January 16, 2025  
**Status:** ✅ IMPLEMENTED

## Summary

Changed from using GraphQL authorities to using codespaces extracted directly from SIRI-SX API, with friendly names from a curated constant based on official Entur documentation.

## The Journey

### 1. Initial Problem
- SKY operator returned "No lines found"
- AMBU (ambulance) entries cluttering the list

### 2. First Fix (Partial)
- Fixed GraphQL authority ID format
- Filtered out AMBU noise
- ✅ SKY now returned 329 lines

### 3. New Problem Discovered
- Multiple operators with same/similar names
- "Skyss (SKY)", "Skyss (1)", "Skyss (17)"
- User: "Some operators seem to be represented more than once"

### 4. Attempted Solution (WRONG)
- Implemented deduplication by name
- Preferred canonical IDs (XXX:Authority:XXX)
- Reduced 68 → 63 operators

### 5. User Raised Valid Concern
> "Not totally convinced. I'd like more documentation about the different operator codes before deduping like that. I am worried we now remove perfectly valid operators when we dont fully understand this."

**This was 100% correct!**

### 6. Critical Discovery
- Found official Entur codespace documentation
- **SOF = Sogn og Fjordane** (different region!)
- **SKY = Skyss** (Hordaland)
- GraphQL API returns "Skyss" for SOF authorities (misleading!)

### 7. Deep Investigation
- API testing revealed: `SOF:Authority:1` has name "Skyss" but represents Sogn og Fjordane regional authority
- Lines under SOF may be **operated by** Skyss, but belong to SOF **authority**
- The GraphQL "authority" entity doesn't represent what we need

### 8. Final Solution
**Use codespaces directly from SIRI-SX API + curated friendly names**

## Implementation

### Step 1: Query SIRI-SX for Active Codespaces

```python
# Get all situation data
xml_data = fetch_from_siri_sx_api()

# Extract codespaces from situation IDs
# Format: "SKY:SituationNumber:12345" → codespace = "SKY"
codespaces = set()
for situation in situations:
    sit_id = situation.get_situation_number()
    codespace = sit_id.split(':')[0]
    if len(codespace) == 3 and codespace.isupper():
        codespaces.add(codespace)

# Result: ["SKY", "SOF", "RUT", "ATB", ...]
```

### Step 2: Map to Friendly Names

```python
# In const.py - curated from official Entur documentation
CODESPACE_NAMES = {
    "SKY": "Skyss",
    "SOF": "Sogn og Fjordane",  # Correct regional authority name
    "RUT": "Ruter",
    "ATB": "AtB",
    # ... 22 total codespaces with active SX data
}
```

### Step 3: Present to User

```python
operators = {}
for codespace in codespaces:
    friendly_name = CODESPACE_NAMES.get(codespace, codespace)
    display_name = f"{friendly_name} ({codespace})"
    operators[codespace] = display_name

# Result:
# {
#   "SKY": "Skyss (SKY)",
#   "SOF": "Sogn og Fjordane (SOF)",
#   "RUT": "Ruter (RUT)",
#   ...
# }
```

### Step 4: Store Codespace Directly

```python
# In config entry
CONF_OPERATOR = "operator"  # Now stores "SKY", not "SKY:Authority:SKY"

# Use directly in SIRI-SX API
url = f"{API_BASE_URL}?datasetId={operator}"  # e.g., datasetId=SKY
```

## Benefits

| Aspect | Old Approach (GraphQL Authorities) | New Approach (SIRI-SX Codespaces) |
|--------|-----------------------------------|-----------------------------------|
| **Data Source** | GraphQL metadata | Actual SIRI-SX situation data |
| **Operator Count** | 68+ (with duplicates/noise) | 22 (only active codespaces) |
| **Name Accuracy** | Misleading (SOF returns "Skyss") | Correct (from curated constant) |
| **Clarity** | Confusing duplicates | Clear, distinct operators |
| **API Match** | Had to convert IDs | Direct match with datasetId |
| **Maintenance** | Dependent on GraphQL schema | Uses standard SIRI-SX format |

## Results

### Before
```
Operators list (68 items with noise):
- "Skyss (SKY:Authority:SKY)"
- "Skyss (SOF:Authority:1)"  ← Misleading name!
- "Skyss (SOF:Authority:17)" ← Misleading name!
- "AMBU (MOR:Authority:AM01)" ← Noise
- ... many others
```

### After
```
Operators list (22 clean items):
- "Skyss (SKY)"
- "Sogn og Fjordane (SOF)"  ← Correctly named!
- "Ruter (RUT)"
- "AtB (ATB)"
- "Kolumbus (KOL)"
... only operators with active SX data
```

## Files Changed

1. **const.py**
   - Added `CODESPACE_NAMES` dictionary with 22 mappings
   - Source: Official Entur documentation + SIRI-SX active codespaces

2. **api.py** - `async_get_operators()`
   - Changed from GraphQL `authorities` query
   - Now queries SIRI-SX API directly
   - Extracts codespaces from situation IDs
   - Maps to friendly names using `CODESPACE_NAMES`

3. **api.py** - `async_get_lines_for_operator()`
   - Changed from querying specific authority ID
   - Now filters all lines by codespace prefix
   - Works with 3-letter code instead of full authority ID

4. **api.py** - `__init__()`
   - Simplified: operator parameter is now just codespace (e.g., "SKY")
   - No more authority ID parsing needed
   - Directly usable in SIRI-SX `datasetId` parameter

## Validation

Tested with:
```
SKY (Skyss): ✅ Works
SOF (Sogn og Fjordane): ✅ Works  
RUT (Ruter): ✅ Works
```

Sample output:
```
Found 22 operators with active SX data:
  AKT: Agder Kollektivtrafikk (AKT)
  ATB: AtB (ATB)
  SKY: Skyss (SKY)
  SOF: Sogn og Fjordane (SOF)  ← Correctly distinguished!
  RUT: Ruter (RUT)
  ...
```

## Key Learnings

1. **User feedback is valuable**: User's caution prevented data loss
2. **Authoritative sources matter**: Official documentation revealed the truth
3. **GraphQL !== SIRI**: Different data models, different purposes
4. **Simplicity wins**: Using codespaces directly is cleaner than authority IDs
5. **Test with real data**: API testing revealed misleading names

## Conclusion

The codespace-based approach is:
- ✅ **Simpler**: Fewer moving parts
- ✅ **More accurate**: Curated names, not misleading API data
- ✅ **More reliable**: Uses actual SIRI-SX data source
- ✅ **More maintainable**: Clear mapping in one constant
- ✅ **User-friendly**: Clean, distinct operator names

**This is the correct and final solution.**
