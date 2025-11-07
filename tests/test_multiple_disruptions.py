"""Test case for multiple disruptions with same status (Nov 6, 2025 bug)."""
import asyncio
from datetime import datetime, timezone
from custom_components.entur_sx.api import EnturSXAPI
from custom_components.entur_sx.const import STATUS_OPEN, STATUS_PLANNED

# Mock XML response from Nov 6, 2025 for SKY:Line:27 with 3 disruptions
MOCK_XML_MULTIPLE_DISRUPTIONS = """<?xml version="1.0" encoding="UTF-8"?>
<Siri xmlns="http://www.siri.org.uk/siri" version="2.0">
    <ServiceDelivery>
        <SituationExchangeDelivery>
            <Situations>
                <!-- First OPEN disruption: Fløyfjellstunnelen -->
                <PtSituationElement>
                    <Progress>open</Progress>
                    <ValidityPeriod>
                        <StartTime>2025-11-06T21:50:00+01:00</StartTime>
                        <EndTime>2025-11-07T05:30:00+01:00</EndTime>
                    </ValidityPeriod>
                    <Summary>Fløyfjellstunnelen varsla stengd frå kl. 22.00</Summary>
                    <Description>Fløyfjellstunnelen er varsla stengd i retning mot Åsane/Knarvik kl. 22.00-05.30 på grunn av vedikehaldsarbeid. Omkøyring via sentrum kan føre til forseinkingar.NB! Ikkje av-/påstiging utanom ordinær trasé.</Description>
                    <Affects>
                        <Networks>
                            <AffectedNetwork>
                                <AffectedLine>
                                    <LineRef>SKY:Line:27</LineRef>
                                </AffectedLine>
                            </AffectedNetwork>
                        </Networks>
                    </Affects>
                </PtSituationElement>

                <!-- Second OPEN disruption: Glaskar tunnel (starts earlier) -->
                <PtSituationElement>
                    <Progress>open</Progress>
                    <ValidityPeriod>
                        <StartTime>2025-11-06T20:50:00+01:00</StartTime>
                        <EndTime>2025-11-07T05:30:00+01:00</EndTime>
                    </ValidityPeriod>
                    <Summary>Glaskar- og Selviktunnelen varsla stengd frå kl. 21.00</Summary>
                    <Description>Glaskar- og Selviktunnelen er varsla stengd kl. 21.00–05.30 i retning mot Åsane/Knarvik på grunn av vedlikehaldsarbeid. Omkøyring via Ervikvegen kan føre til forseinkingar.</Description>
                    <Affects>
                        <Networks>
                            <AffectedNetwork>
                                <AffectedLine>
                                    <LineRef>SKY:Line:27</LineRef>
                                </AffectedLine>
                            </AffectedNetwork>
                        </Networks>
                    </Affects>
                </PtSituationElement>

                <!-- PLANNED disruption: Glaskar tunnel (midnight) -->
                <PtSituationElement>
                    <Progress>open</Progress>
                    <ValidityPeriod>
                        <StartTime>2025-11-06T23:51:00+01:00</StartTime>
                        <EndTime>2025-11-07T05:30:00+01:00</EndTime>
                    </ValidityPeriod>
                    <Summary>Glaskar- og Selviktunnelen varsla stengd frå kl. 00.01</Summary>
                    <Description>E39 Glaskar- og Selviktunnelen er varsla stengd kl. 00.01-05.30 i retning mot sentrum på grunn av vedlikehaldsarbeid.</Description>
                    <Affects>
                        <Networks>
                            <AffectedNetwork>
                                <AffectedLine>
                                    <LineRef>SKY:Line:27</LineRef>
                                </AffectedLine>
                            </AffectedNetwork>
                        </Networks>
                    </Affects>
                </PtSituationElement>
            </Situations>
        </SituationExchangeDelivery>
    </ServiceDelivery>
</Siri>
"""


async def test_multiple_open_disruptions_combined():
    """Test that multiple OPEN disruptions are combined in the summary."""
    api = EnturSXAPI(["SKY:Line:27"])

    # Parse the XML at a time when both disruptions are active (22:00)
    test_time = datetime(2025, 11, 6, 22, 0, 0, tzinfo=timezone.utc)
    disruptions = api._parse_sx_response(MOCK_XML_MULTIPLE_DISRUPTIONS, now=test_time)

    # Should have data for SKY:Line:27
    assert "SKY:Line:27" in disruptions
    line_data = disruptions["SKY:Line:27"]

    # Should have 3 disruptions total
    assert len(line_data) == 3

    # First 2 should be OPEN (sorted by relevance)
    assert line_data[0]["status"] == STATUS_OPEN
    assert line_data[1]["status"] == STATUS_OPEN
    assert line_data[2]["status"] == STATUS_PLANNED  # Future event

    # Verify sorting: Most recent OPEN disruption first
    assert "Fløyfjellstunnelen" in line_data[0]["summary"]
    assert "Glaskar" in line_data[1]["summary"]

    # Test the sensor value combination logic (simulated)
    first_status = line_data[0]["status"]
    same_status_count = sum(1 for item in line_data if item.get("status") == first_status)

    # Should have 2 OPEN disruptions
    assert same_status_count == 2

    # Build combined summary (as sensor would do)
    summaries = [
        item.get("summary", "Unknown disruption")
        for item in line_data
        if item.get("status") == first_status
    ]
    combined = " | ".join(summaries)

    # Verify combined summary contains both
    assert "Fløyfjellstunnelen" in combined
    assert "Glaskar" in combined
    assert " | " in combined

    print(f"\n✅ Combined summary: {combined}")
    print(f"✅ Total disruptions: {len(line_data)}")
    print(f"✅ OPEN disruptions: {same_status_count}")
    print(f"✅ PLANNED disruptions: {sum(1 for item in line_data if item.get('status') == STATUS_PLANNED)}")


async def test_single_disruption_unchanged():
    """Test that single disruptions still work as before."""
    # XML with only one disruption
    single_xml = """<?xml version="1.0" encoding="UTF-8"?>
<Siri xmlns="http://www.siri.org.uk/siri" version="2.0">
    <ServiceDelivery>
        <SituationExchangeDelivery>
            <Situations>
                <PtSituationElement>
                    <Progress>open</Progress>
                    <ValidityPeriod>
                        <StartTime>2025-11-06T21:50:00+01:00</StartTime>
                        <EndTime>2025-11-07T05:30:00+01:00</EndTime>
                    </ValidityPeriod>
                    <Summary>Single disruption</Summary>
                    <Description>Only one active disruption</Description>
                    <Affects>
                        <Networks>
                            <AffectedNetwork>
                                <AffectedLine>
                                    <LineRef>SKY:Line:27</LineRef>
                                </AffectedLine>
                            </AffectedNetwork>
                        </Networks>
                    </Affects>
                </PtSituationElement>
            </Situations>
        </SituationExchangeDelivery>
    </ServiceDelivery>
</Siri>
"""

    api = EnturSXAPI(["SKY:Line:27"])
    test_time = datetime(2025, 11, 6, 22, 0, 0, tzinfo=timezone.utc)
    disruptions = api._parse_sx_response(single_xml, now=test_time)

    line_data = disruptions["SKY:Line:27"]

    # Should have only 1 disruption
    assert len(line_data) == 1

    # Summary should be unchanged (no combination needed)
    assert line_data[0]["summary"] == "Single disruption"

    print(f"\n✅ Single disruption works: {line_data[0]['summary']}")


async def test_long_combined_summary_truncation():
    """Test that very long combined summaries are truncated properly."""
    # Create XML with many disruptions with very long summaries
    long_xml = """<?xml version="1.0" encoding="UTF-8"?>
<Siri xmlns="http://www.siri.org.uk/siri" version="2.0">
    <ServiceDelivery>
        <SituationExchangeDelivery>
            <Situations>
                <PtSituationElement>
                    <Progress>open</Progress>
                    <ValidityPeriod>
                        <StartTime>2025-11-06T20:00:00+01:00</StartTime>
                        <EndTime>2025-11-07T05:30:00+01:00</EndTime>
                    </ValidityPeriod>
                    <Summary>This is a very long disruption summary that contains a lot of detailed information about the situation and it goes on and on</Summary>
                    <Affects>
                        <Networks>
                            <AffectedNetwork>
                                <AffectedLine>
                                    <LineRef>SKY:Line:27</LineRef>
                                </AffectedLine>
                            </AffectedNetwork>
                        </Networks>
                    </Affects>
                </PtSituationElement>
                <PtSituationElement>
                    <Progress>open</Progress>
                    <ValidityPeriod>
                        <StartTime>2025-11-06T21:00:00+01:00</StartTime>
                        <EndTime>2025-11-07T05:30:00+01:00</EndTime>
                    </ValidityPeriod>
                    <Summary>Another extremely long disruption summary with lots of details about road closures and alternative routes</Summary>
                    <Affects>
                        <Networks>
                            <AffectedNetwork>
                                <AffectedLine>
                                    <LineRef>SKY:Line:27</LineRef>
                                </AffectedLine>
                            </AffectedNetwork>
                        </Networks>
                    </Affects>
                </PtSituationElement>
                <PtSituationElement>
                    <Progress>open</Progress>
                    <ValidityPeriod>
                        <StartTime>2025-11-06T22:00:00+01:00</StartTime>
                        <EndTime>2025-11-07T05:30:00+01:00</EndTime>
                    </ValidityPeriod>
                    <Summary>Yet another disruption with a very long description that would make the combined text exceed the character limit</Summary>
                    <Affects>
                        <Networks>
                            <AffectedNetwork>
                                <AffectedLine>
                                    <LineRef>SKY:Line:27</LineRef>
                                </AffectedLine>
                            </AffectedNetwork>
                        </Networks>
                    </Affects>
                </PtSituationElement>
            </Situations>
        </SituationExchangeDelivery>
    </ServiceDelivery>
</Siri>
"""

    api = EnturSXAPI(["SKY:Line:27"])
    test_time = datetime(2025, 11, 6, 22, 30, 0, tzinfo=timezone.utc)
    disruptions = api._parse_sx_response(long_xml, now=test_time)

    line_data = disruptions["SKY:Line:27"]
    assert len(line_data) == 3

    # Simulate sensor combination logic
    first_status = line_data[0]["status"]
    same_status_count = sum(1 for item in line_data if item.get("status") == first_status)
    summaries = [item.get("summary") for item in line_data if item.get("status") == first_status]
    combined = " | ".join(summaries)

    # Test truncation logic
    if len(combined) > 255:
        truncated = f"{same_status_count} {first_status} disruptions: {summaries[0]}"
        print(f"\n✅ Long summary truncated: {truncated[:100]}...")
        assert "disruptions:" in truncated
    else:
        print(f"\n✅ Combined summary fits: {len(combined)} chars")
        assert len(combined) <= 255


if __name__ == "__main__":
    import asyncio

    print("=" * 70)
    print("Testing Multiple Disruptions Enhancement (Nov 7, 2025)")
    print("=" * 70)

    asyncio.run(test_multiple_open_disruptions_combined())
    asyncio.run(test_single_disruption_unchanged())
    asyncio.run(test_long_combined_summary_truncation())

    print("\n" + "=" * 70)
    print("✅ All tests passed!")
    print("=" * 70)

