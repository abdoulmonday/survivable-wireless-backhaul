# Suggested experiments

```bash
python -m backhaul.demo --sigma 1.0 --alpha 0.0 --output outputs/no_protection
python -m backhaul.demo --sigma 0.5 --alpha 0.0 --output outputs/diversification
python -m backhaul.demo --sigma 1.0 --alpha 1.0 --output outputs/reservation
python -m backhaul.demo --sigma 0.5 --alpha 1.0 --output outputs/hybrid
```

Note: alpha=0 with a failure scenario still enforces zero flow there, but not surviving throughput. Compare cost and scenario flows, not just the final network image.
