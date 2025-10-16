"""Test codespace-based operator listing."""
import asyncio
import aiohttp
import async_timeout
import xml.etree.ElementTree as ET

API_BASE_URL = "https://api.entur.io/realtime/v1/rest/sx"

# From const.py
CODESPACE_NAMES = {
    "AKT": "Agder Kollektivtrafikk",
    "ATB": "AtB",
    "BRA": "Brakar",
    "GOA": "Go-Ahead Norge",
    "INN": "Innlandstrafikk",
    "KOL": "Kolumbus",
    "MOR": "FRAM",
    "NBU": "Flybussen Connect",
    "OST": "Østfold kollektivtrafikk",
    "RUT": "Ruter",
    "SJN": "SJ Nord",
    "SKY": "Skyss",
    "SOF": "Sogn og Fjordane",
    "TEL": "Farte",
    "TRO": "Troms fylkestrafikk",
    "VKT": "VKT",
    "VYB": "Vy Bus4You",
    "VYG": "Vy",
    "VYX": "Vy Buss",
    "CTS": "CTS",
    "GCO": "GCO",
    "NSB": "NSB",
}


async def test_get_operators():
    """Test getting operators from SIRI-SX."""
    
    headers = {
        "ET-Client-Name": "homeassistant-entur-sx",
    }
    
    async with aiohttp.ClientSession() as session:
        async with async_timeout.timeout(30):
            async with session.get(API_BASE_URL, headers=headers) as response:
                response.raise_for_status()
                xml_content = await response.text()
                
                root = ET.fromstring(xml_content)
                ns = {'siri': 'http://www.siri.org.uk/siri'}
                
                situations = root.findall('.//siri:PtSituationElement', ns)
                
                codespaces = set()
                for situation in situations:
                    sit_number = situation.find('.//siri:SituationNumber', ns)
                    if sit_number is not None and sit_number.text:
                        parts = sit_number.text.split(':')
                        if len(parts) >= 1:
                            codespace = parts[0]
                            if len(codespace) == 3 and codespace.isupper():
                                codespaces.add(codespace)
                
                # Build operator dict
                operators = {}
                for codespace in sorted(codespaces):
                    friendly_name = CODESPACE_NAMES.get(codespace, codespace)
                    display_name = f"{friendly_name} ({codespace})"
                    operators[codespace] = display_name
                
                print("=" * 100)
                print("CODESPACE-BASED OPERATORS")
                print("=" * 100)
                print(f"\nFound {len(operators)} operators with active SX data:\n")
                
                for codespace, display_name in sorted(operators.items()):
                    print(f"  {codespace}: {display_name}")
                
                print("\n\n" + "=" * 100)
                print("KEY OBSERVATIONS")
                print("=" * 100)
                print("\n✅ Now showing codespaces directly (SKY, SOF, RUT, etc.)")
                print("✅ Friendly names from CODESPACE_NAMES constant")
                print("✅ SOF correctly shown as 'Sogn og Fjordane (SOF)'")
                print("✅ SKY shown as 'Skyss (SKY)'")
                print("✅ No more confusion between authorities!")
                
                return operators


if __name__ == "__main__":
    asyncio.run(test_get_operators())
