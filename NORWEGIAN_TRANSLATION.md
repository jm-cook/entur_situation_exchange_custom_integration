# Norwegian Translation and Default Name Changes

## Changes Made

### 1. Default Device Name
Changed from "Entur Deviations" to "Entur Avvik" (Norwegian)

**Files Modified:**
- `custom_components/entur_sx/const.py`
  - Changed `DEFAULT_DEVICE_NAME = "Entur Deviations"` → `"Entur Avvik"`
  
- `custom_components/entur_sx/sensor.py`
  - Changed fallback value from `"Entur Deviations"` → `"Entur Avvik"`

**Impact:**
- New installations will default to "Entur Avvik"
- Existing installations keep their configured name (no change)
- Only affects users who don't specify a custom device name

---

### 2. Norwegian Translation (nb.json)
Created complete Norwegian Bokmål translation file.

**File:** `custom_components/entur_sx/translations/nb.json`

**Translations:**

#### Initial Setup Flow
- "Set up Entur Situation Exchange" → "Sett opp Entur Situasjonsutveksling"
- "Monitor service deviations" → "Overvåk avvik for spesifikke kollektivlinjer"
- "Device name" → "Enhetsnavn"
- "Select Operator" → "Velg operatør"
- "Select Lines to Monitor" → "Velg linjer å overvåke"

#### Options Flow (Reconfiguration)
- "Modify Monitored Lines" → "Endre overvåkede linjer"
- "Add or remove lines" → "Legg til eller fjern linjer"
- "Lines to monitor" → "Linjer å overvåke"

#### Error Messages
- "You must select at least one line" → "Du må velge minst én linje å overvåke"
- "Failed to connect to Entur API" → "Kunne ikke koble til Entur API"
- "No lines found for this operator" → "Ingen linjer funnet for denne operatøren"

#### Other Messages
- "Already configured" → "Denne kombinasjonen av operatør og linjer er allerede konfigurert"
- "Operator" → "Operatør"
- "Select the public transport company" → "Velg kollektivselskapet"

---

### 3. Options Flow Translations Added
Both English and Norwegian now include options flow translations.

**Sections Added:**
```json
"options": {
  "step": {
    "init": {
      "title": "...",
      "description": "...",
      "data": { ... },
      "data_description": { ... }
    }
  },
  "error": { ... }
}
```

**Files Updated:**
- `strings.json` - Base translation file (English)
- `translations/en.json` - English translations
- `translations/nb.json` - Norwegian translations (NEW)

---

## Language Detection

Home Assistant automatically detects the user's language preference and uses the appropriate translation:

- **Norwegian users** (language set to `nb` or `no`): See Norwegian text
- **English users**: See English text
- **Other languages**: Fall back to English (base strings.json)

---

## Testing

### How to Test Norwegian Translation

1. **Change Home Assistant language:**
   - Settings → System → General
   - Change "Language" to "Norsk bokmål"
   - Refresh browser

2. **Add the integration:**
   - Settings → Devices & Services → Add Integration
   - Search for "Entur"
   - Should see "Sett opp Entur Situasjonsutveksling"

3. **Check default name:**
   - Leave device name blank
   - Should default to "Entur Avvik"

4. **Use options flow:**
   - Click "Configure" on the integration
   - Should see "Endre overvåkede linjer"

### How to Test English Translation

1. Set language to English
2. Same steps as above
3. Should see English text: "Modify Monitored Lines"

---

## Translation Coverage

| Section | English | Norwegian |
|---------|---------|-----------|
| Initial setup steps | ✅ | ✅ |
| Options flow | ✅ | ✅ |
| Error messages | ✅ | ✅ |
| Field labels | ✅ | ✅ |
| Field descriptions | ✅ | ✅ |
| Abort reasons | ✅ | ✅ |

---

## Norwegian Language Notes

**Language Code:** `nb` (Norwegian Bokmål)
- `nb` = Bokmål (most common written Norwegian)
- `nn` = Nynorsk (alternative written Norwegian)
- `no` = Generic Norwegian (fallback)

Home Assistant uses `nb` for Norwegian Bokmål, which is what most Norwegians use (85-90% of the population).

**Key Terms:**
- Avvik = Deviation/discrepancy
- Operatør = Operator
- Linje = Line
- Overvåke = Monitor/supervise
- Kollektiv = Public transport

---

## Files Changed Summary

1. ✅ `const.py` - Default device name
2. ✅ `sensor.py` - Fallback device name
3. ✅ `strings.json` - Base translations with options flow
4. ✅ `translations/en.json` - English with options flow
5. ✅ `translations/nb.json` - Complete Norwegian translation (NEW)

---

## Backward Compatibility

✅ **No breaking changes:**
- Existing installations keep their configured names
- Default only affects new installations
- English remains fully functional
- Other languages fall back to English

---

## Future Enhancements

Consider adding translations for:
- Sensor state attributes (if any custom attributes are added)
- Device class descriptions
- Additional error messages
- Documentation/README in Norwegian
