import json
import random
from datetime import datetime, timezone
import os

SCENARIOS_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../data/qa_emergency_scenarios.json")
)

class TestDataGenerator:
    """Generates synthetic alert batches and load testing payloads for QA automation."""

    @classmethod
    def load_scenarios(cls) -> list[dict]:
        with open(SCENARIOS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("emergency_scenarios", [])

    @classmethod
    def generate_random_alert_payload(cls) -> dict:
        scenarios = cls.load_scenarios()
        scenario = random.choice(scenarios)
        loc = scenario["location"]
        return {
            "emergency_type": scenario["hazard_type"],
            "building_id": loc["building_id"],
            "room_number": loc["room_number"],
            "floor": loc["floor"],
            "description": f"Simulated QA Alert: {scenario['name']} - {scenario['description']}",
            "latitude": 12.9716 + random.uniform(-0.003, 0.003),
            "longitude": 77.5946 + random.uniform(-0.003, 0.003),
            "generated_at": datetime.now(timezone.utc).isoformat()
        }

    @classmethod
    def generate_batch(cls, count: int = 10) -> list[dict]:
        return [cls.generate_random_alert_payload() for _ in range(count)]

if __name__ == "__main__":
    batch = TestDataGenerator.generate_batch(3)
    print(f"Generated {len(batch)} test alerts:")
    print(json.dumps(batch, indent=2))
