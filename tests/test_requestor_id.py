"""Test requestorId incremental updates with Entur API.

Tests how the requestorId parameter works:
- Creates a UUID requestorId
- Makes initial request (gets all data)
- Polls every 60 seconds for 10 minutes
- Logs response sizes and changes
- Tests session timeout (5 minute timeout documented)
- Tests maxSize parameter and MoreData flag

Documentation:
https://developer.entur.org/pages-real-time-api

requestorId behavior:
- First request creates a short-lived session (timeout after 5 minutes)
- Subsequent requests return only changes since last request
- If session times out, next request returns full data again

maxSize parameter:
- Limits number of results returned
- Default is 1500
- MoreData flag indicates if more data exists
"""
import asyncio
import aiohttp
import json
import uuid
from datetime import datetime
from collections import defaultdict

API_URL = "https://api.entur.io/realtime/v1/rest/sx"

# Test configuration
REQUESTOR_ID = str(uuid.uuid4())  # Generate unique ID for this test run
POLL_INTERVAL = 60  # seconds
TOTAL_POLLS = 10  # Run for 10 minutes
MAX_SIZE = None  # Set to a number to test truncation (e.g., 10, 50, 100), None for default (1500)
LINES_TO_MONITOR = [
    "SKY:Line:1",
    "SKY:Line:20",
    "SKY:Line:925",
]


class RequestorIdTester:
    """Test harness for requestorId incremental updates."""
    
    def __init__(self, requestor_id: str, lines: list[str]):
        self.requestor_id = requestor_id
        self.lines = lines
        self.session = None
        
        # Track state
        self.poll_count = 0
        self.state = {}  # Current known disruptions
        self.poll_history = []  # Record of each poll
        
    async def start(self):
        """Initialize aiohttp session."""
        self.session = aiohttp.ClientSession()
        print(f"🔑 Using requestorId: {self.requestor_id}")
        print(f"📍 Monitoring lines: {', '.join(self.lines)}")
        print(f"⏱️  Polling every {POLL_INTERVAL}s for {TOTAL_POLLS} polls")
        if MAX_SIZE:
            print(f"📏 maxSize: {MAX_SIZE} (testing truncation)")
        else:
            print(f"📏 maxSize: default (1500)")
        print("=" * 80)
        
    async def stop(self):
        """Cleanup aiohttp session."""
        if self.session:
            await self.session.close()
    
    async def poll(self):
        """Make a single poll with requestorId."""
        self.poll_count += 1
        poll_time = datetime.now()
        
        print(f"\n📡 POLL #{self.poll_count} at {poll_time.strftime('%H:%M:%S')}")
        print("-" * 80)
        
        # Build URL with requestorId and optional maxSize
        url = f"{API_URL}?requestorId={self.requestor_id}"
        if MAX_SIZE:
            url += f"&maxSize={MAX_SIZE}"
        headers = {"Content-Type": "application/json"}
        
        try:
            async with self.session.get(url, headers=headers) as response:
                response_time = datetime.now()
                duration_ms = (response_time - poll_time).total_seconds() * 1000
                
                # Get raw response
                text = await response.text()
                response_size = len(text.encode('utf-8'))
                
                print(f"   Status: {response.status}")
                print(f"   Duration: {duration_ms:.1f}ms")
                print(f"   Response size: {response_size:,} bytes ({response_size/1024:.1f} KB)")
                
                if response.status != 200:
                    print(f"   ❌ Error: {response.status}")
                    self.poll_history.append({
                        "poll": self.poll_count,
                        "time": poll_time,
                        "status": response.status,
                        "error": text[:200],
                    })
                    return
                
                # Debug: Check content type
                content_type = response.headers.get('Content-Type', 'unknown')
                print(f"   Content-Type: {content_type}")
                
                # Show first few characters
                preview = text[:200] if len(text) > 200 else text
                print(f"   Response preview: {preview[:100]}...")
                
                # Parse JSON
                try:
                    data = json.loads(text)
                except json.JSONDecodeError as e:
                    print(f"   ❌ JSON Parse Error: {e}")
                    print(f"   Response was: {preview}")
                    self.poll_history.append({
                        "poll": self.poll_count,
                        "time": poll_time,
                        "status": response.status,
                        "size_bytes": response_size,
                        "error": f"JSON parse error: {e}",
                    })
                    return
                
                # Analyze response
                analysis = self._analyze_response(data)
                
                # Check MoreData flag
                service_delivery = data.get("Siri", {}).get("ServiceDelivery", {})
                more_data = service_delivery.get("MoreData", False)
                
                # Record poll
                self.poll_history.append({
                    "poll": self.poll_count,
                    "time": poll_time,
                    "status": response.status,
                    "size_bytes": response_size,
                    "duration_ms": duration_ms,
                    "more_data": more_data,
                    **analysis,
                })
                
                # Print analysis
                print(f"\n   📊 Response Analysis:")
                print(f"      Situations total: {analysis['total_situations']}")
                print(f"      Lines affected: {analysis['lines_affected']}")
                print(f"      Monitored lines with disruptions: {analysis['monitored_lines_count']}")
                print(f"      MoreData flag: {more_data}")
                
                if more_data:
                    print(f"      ⚠️  TRUNCATED - More data available but not returned!")
                    print(f"         Response limited by maxSize parameter")
                
                if self.poll_count == 1:
                    print(f"      ℹ️  First poll - received full dataset")
                else:
                    print(f"      🔄 Changes detected:")
                    print(f"         NEW situations: {analysis['new_situations']}")
                    print(f"         REMOVED situations: {analysis['removed_situations']}")
                    print(f"         UNCHANGED situations: {analysis['unchanged_situations']}")
                    
                    if analysis['new_situations'] == 0 and analysis['removed_situations'] == 0:
                        print(f"      ✅ No changes - incremental update working!")
                
                # Show monitored lines status
                if analysis['monitored_lines_count'] > 0:
                    print(f"\n   📍 Monitored Lines Status:")
                    for line_ref in self.lines:
                        if line_ref in analysis['monitored_lines_data']:
                            count = len(analysis['monitored_lines_data'][line_ref])
                            print(f"      {line_ref}: {count} disruption(s)")
                            for sit in analysis['monitored_lines_data'][line_ref]:  # Show all
                                summary = sit.get('summary', 'No summary')[:60]
                                status = sit.get('status', 'unknown')
                                print(f"         - [{status}] {summary}")
                
        except asyncio.TimeoutError:
            print(f"   ❌ Timeout after 30s")
        except Exception as err:
            print(f"   ❌ Error: {err}")
            import traceback
            traceback.print_exc()
    
    def _analyze_response(self, data: dict) -> dict:
        """Analyze API response and compare with previous state."""
        
        # Extract situations
        situations = {}
        lines_affected = set()
        monitored_lines_data = defaultdict(list)
        
        # Parse SIRI response structure (following api.py logic)
        siri = data.get("Siri", {})
        service_delivery = siri.get("ServiceDelivery", {})
        sx_delivery = service_delivery.get("SituationExchangeDelivery", [])
        
        for sed in sx_delivery:
            sit_dict = sed.get("Situations", {})
            elements = sit_dict.get("PtSituationElement", [])
            
            for element in elements:
                # Get situation number
                sit_num_field = element.get("SituationNumber", "unknown")
                if isinstance(sit_num_field, dict):
                    sit_number = sit_num_field.get("value", "unknown")
                else:
                    sit_number = sit_num_field
                
                # Get progress/status
                progress = element.get("Progress", "unknown")
                if progress.lower() == "closed":
                    status = "expired"
                else:
                    status = "open"
                
                # Get summary
                summary_list = element.get("Summary", [])
                summary = summary_list[0].get("value", "") if summary_list else ""
                
                # Get affected lines
                affects = element.get("Affects", {})
                networks = affects.get("Networks", {})
                if not networks:
                    continue
                    
                affected_networks = networks.get("AffectedNetwork", [])
                affected_lines = []
                
                for an in affected_networks:
                    affected_line_list = an.get("AffectedLine", [])
                    for affected_line in affected_line_list:
                        # LineRef can be dict or string
                        line_ref_field = affected_line.get("LineRef", "")
                        if isinstance(line_ref_field, dict):
                            line_ref = line_ref_field.get("value", "")
                        else:
                            line_ref = line_ref_field
                        
                        if line_ref:
                            affected_lines.append(line_ref)
                            lines_affected.add(line_ref)
                            
                            # Track monitored lines
                            if line_ref in self.lines:
                                monitored_lines_data[line_ref].append({
                                    "situation_id": sit_number,
                                    "summary": summary,
                                    "status": status,
                                })
                
                # Store situation
                situations[sit_number] = {
                    "summary": summary,
                    "status": status,
                    "affected_lines": affected_lines,
                }
        
        # Compare with previous state
        new_situations = 0
        removed_situations = 0
        unchanged_situations = 0
        
        if self.state:
            # Find new situations
            new_sit_ids = set(situations.keys()) - set(self.state.keys())
            new_situations = len(new_sit_ids)
            
            # Find removed situations
            removed_sit_ids = set(self.state.keys()) - set(situations.keys())
            removed_situations = len(removed_sit_ids)
            
            # Count unchanged
            unchanged_situations = len(set(situations.keys()) & set(self.state.keys()))
        else:
            # First poll - all situations are "new" but we don't report it as changes
            pass
        
        # Update state (but preserve old state if current response is empty incremental update)
        # Empty response from incremental API means "no changes", not "everything deleted"
        if situations or not self.state:
            # Either we got data, or this is the first poll
            self.state = situations
        # else: keep previous state intact for empty incremental responses
        
        return {
            "total_situations": len(situations),
            "lines_affected": len(lines_affected),
            "monitored_lines_count": len(monitored_lines_data),
            "monitored_lines_data": dict(monitored_lines_data),
            "new_situations": new_situations,
            "removed_situations": removed_situations,
            "unchanged_situations": unchanged_situations,
        }
    
    def print_summary(self):
        """Print summary of all polls."""
        print("\n" + "=" * 80)
        print("📊 TEST SUMMARY")
        print("=" * 80)
        
        print(f"\nrequestorId: {self.requestor_id}")
        print(f"Total polls: {self.poll_count}")
        
        if not self.poll_history:
            print("No polls recorded!")
            return
        
        print(f"\n📈 Response Sizes:")
        for record in self.poll_history:
            poll_num = record['poll']
            size_kb = record.get('size_bytes', 0) / 1024
            total_sit = record.get('total_situations', 0)
            new_sit = record.get('new_situations', 0)
            removed_sit = record.get('removed_situations', 0)
            more_data = record.get('more_data', False)
            
            change_indicator = ""
            if poll_num > 1:
                if new_sit > 0 or removed_sit > 0:
                    change_indicator = f" (+{new_sit}/-{removed_sit})"
                else:
                    change_indicator = " (no changes)"
            
            truncated = " ⚠️ TRUNCATED" if more_data else ""
            
            print(f"   Poll #{poll_num}: {size_kb:6.1f} KB | "
                  f"{total_sit:3d} situations{change_indicator}{truncated}")
        
        # Calculate statistics
        sizes = [r.get('size_bytes', 0) / 1024 for r in self.poll_history if r.get('size_bytes')]
        truncated_count = sum(1 for r in self.poll_history if r.get('more_data', False))
        
        if sizes:
            print(f"\n📊 Statistics:")
            print(f"   First poll: {sizes[0]:.1f} KB (full dataset)")
            if len(sizes) > 1:
                avg_incremental = sum(sizes[1:]) / len(sizes[1:])
                print(f"   Avg incremental: {avg_incremental:.1f} KB")
                print(f"   Min: {min(sizes):.1f} KB")
                print(f"   Max: {max(sizes):.1f} KB")
                reduction = ((sizes[0] - avg_incremental) / sizes[0]) * 100
                print(f"   Data reduction: {reduction:.1f}%")
            
            if truncated_count > 0:
                print(f"\n⚠️  Truncation:")
                print(f"   {truncated_count} of {len(self.poll_history)} polls had MoreData=true")
                print(f"   Data was truncated by maxSize parameter")
                if MAX_SIZE:
                    print(f"   Current maxSize: {MAX_SIZE}")
                else:
                    print(f"   Using default maxSize: 1500")
        
        # Check for session timeout
        print(f"\n⏱️  Session Timeout Detection:")
        for i, record in enumerate(self.poll_history):
            if i == 0:
                continue
            
            size_bytes = record.get('size_bytes', 0)
            prev_size = self.poll_history[i-1].get('size_bytes', 0)
            
            # If size suddenly jumps, might indicate session timeout
            if size_bytes > prev_size * 2:
                time_diff = (record['time'] - self.poll_history[i-1]['time']).total_seconds()
                print(f"   ⚠️  Poll #{record['poll']}: Size jumped from "
                      f"{prev_size/1024:.1f} KB to {size_bytes/1024:.1f} KB")
                print(f"      Time since last poll: {time_diff:.0f}s")
                print(f"      Possible session timeout and re-initialization")


async def main():
    """Run the requestorId test."""
    tester = RequestorIdTester(REQUESTOR_ID, LINES_TO_MONITOR)
    
    try:
        await tester.start()
        
        for i in range(TOTAL_POLLS):
            await tester.poll()
            
            # Wait before next poll (except after last one)
            if i < TOTAL_POLLS - 1:
                print(f"\n⏳ Waiting {POLL_INTERVAL}s until next poll...")
                await asyncio.sleep(POLL_INTERVAL)
        
        tester.print_summary()
        
    finally:
        await tester.stop()


if __name__ == "__main__":
    print("🧪 Entur requestorId Incremental Update Test")
    print("=" * 80)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"This test will run for approximately {TOTAL_POLLS * POLL_INTERVAL / 60:.0f} minutes")
    print("")
    
    asyncio.run(main())
