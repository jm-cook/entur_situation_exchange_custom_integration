# Entur SX Integration - Enhanced Config Flow

## Overview
The config flow has been upgraded to provide a user-friendly, multi-step wizard that dynamically fetches operators and lines from the Entur API.

## Config Flow Steps

### Step 1: Device Setup
- **Device name**: User provides a friendly name
- **Include future deviations**: Boolean setting

### Step 2: Select Operator
- Fetches all available operators from Entur GraphQL API
- Displays both operator code (e.g., "SKY") and friendly name (e.g., "Skyss")
- Sorted alphabetically by name for easy browsing
- Fallback to hardcoded list if API call fails

### Step 3: Select Lines
- Fetches all lines for the selected operator from Entur GraphQL API
- Displays: Line number - Route name (transport mode)
  - Example: "1 - Bergen sentrum (bus)"
- Multi-select list allowing multiple lines
- Sorted for easy navigation

## API Integration

### Operators Query
```graphql
query {
  authorities {
    id
    name
  }
}
```
- Returns all transport authorities in Norway
- Extracts operator code from ID (e.g., "NSR:Authority:SKY" → "SKY")

### Lines Query
```graphql
query($authority: String!) {
  lines(authorities: [$authority]) {
    id
    name
    publicCode
    transportMode
  }
}
```
- Returns all lines for a specific operator
- Provides rich metadata for user-friendly display

## Benefits

1. **No Manual Lookup Required**
   - Users don't need to know line reference formats
   - No need to search external documentation

2. **Discovery**
   - Users can browse all available operators
   - Explore lines they might not know existed

3. **Accuracy**
   - Guaranteed correct line references
   - Always up-to-date with Entur's current data

4. **User Experience**
   - Clean dropdown/list selectors
   - Descriptive labels
   - Progress through logical steps

## Error Handling

- **API Failure**: Falls back to common operators list
- **No Lines Found**: Shows error, allows going back
- **Already Configured**: Prevents duplicate entries

## Technical Details

- Uses Entur's Journey Planner v3 GraphQL API
- Async/await pattern throughout
- Proper timeout handling (10 seconds)
- Comprehensive error logging
- Client name header: "homeassistant-entur-sx"
