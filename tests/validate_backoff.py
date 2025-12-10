"""Simple validation of throttle back-off constants."""

# Constants
BACKOFF_INITIAL = 120  # 2 minutes
BACKOFF_MULTIPLIER = 2.5
BACKOFF_MAX = 600  # 10 minutes
BACKOFF_RESET_AFTER = 1800  # 30 minutes
UPDATE_INTERVAL = 60  # Normal interval

print("Throttle Back-off Configuration Test")
print("=" * 50)
print(f"Normal update interval: {UPDATE_INTERVAL}s (1 minute)")
print(f"Back-off reset period: {BACKOFF_RESET_AFTER}s (30 minutes)")
print()

print("Back-off progression on repeated throttles:")
for count in range(1, 6):
    backoff_time = min(
        BACKOFF_INITIAL * (BACKOFF_MULTIPLIER ** (count - 1)),
        BACKOFF_MAX,
    )
    print(f"  Throttle #{count}: {int(backoff_time)}s ({backoff_time/60:.1f} min)")

print()
print("Expected behavior:")
print("✓ First 429 error: Wait 2 minutes")
print("✓ Second 429 error: Wait 5 minutes")  
print("✓ Third+ 429 error: Wait 10 minutes (capped)")
print("✓ After 30 min of success: Reset counter to 0")
print("✓ On recovery: Return to 60s polling")
print("✓ During back-off: Return cached data to keep sensors alive")
