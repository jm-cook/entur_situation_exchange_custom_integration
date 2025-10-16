"""Test the reverted operator list with codespace display."""
import asyncio
import sys
sys.path.append("c:\\Users\\jeco\\Dev\\HA\\entur_situation_exchange_custom_integration\\custom_components\\entur_sx")

from api import EnturSXAPI


async def test_operator_list_with_codespaces():
    """Test that operators now show codespace and no deduplication."""
    
    api = EnturSXAPI()
    
    print("Fetching operator list with codespace display...")
    operators = await api.get_operators()
    
    print(f"\n{'=' * 100}")
    print(f"OPERATOR LIST (TOTAL: {len(operators)})")
    print('=' * 100)
    
    # Group by name prefix to show which ones would have been duplicates
    by_base_name = {}
    for op_id, op_name in operators.items():
        # Extract base name (before codespace)
        base = op_name.split(" (")[0] if " (" in op_name else op_name
        if base not in by_base_name:
            by_base_name[base] = []
        by_base_name[base].append((op_id, op_name))
    
    # Show operators that have multiple codespaces
    multiples = {name: ops for name, ops in by_base_name.items() if len(ops) > 1}
    
    if multiples:
        print(f"\n\n⚠️  OPERATORS WITH MULTIPLE CODESPACES ({len(multiples)}):")
        print("=" * 100)
        for base_name in sorted(multiples.keys()):
            ops = multiples[base_name]
            print(f"\n{base_name}: {len(ops)} variants")
            for op_id, op_name in sorted(ops):
                print(f"  - {op_name}")
                print(f"    ID: {op_id}")
    
    print(f"\n\n✅ FULL OPERATOR LIST:")
    print("=" * 100)
    for op_id in sorted(operators.keys()):
        print(f"{operators[op_id]}: {op_id}")
    
    print(f"\n{'=' * 100}")
    print("VERIFICATION")
    print('=' * 100)
    
    # Check specifically for Skyss and Kringom
    skyss_entries = {k: v for k, v in operators.items() if "Skyss" in v}
    
    if skyss_entries:
        print(f"\nSkyss-related operators: {len(skyss_entries)}")
        for op_id, op_name in skyss_entries.items():
            print(f"  {op_name}")
            if "SOF" in op_id:
                print(f"    ⚠️  Note: This is actually Kringom (Sogn og Fjordane) with incorrect API name")
            elif "SKY" in op_id:
                print(f"    ✅ This is Skyss (Hordaland)")


if __name__ == "__main__":
    asyncio.run(test_operator_list_with_codespaces())
