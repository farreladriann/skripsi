# Network Selection QA

## Network

- Network file: `data/external/network_variants/rru_fishbone_500m.geojson`
- Edge count: 503
- Node count: 503
- Connected components: 1
- Largest component nodes: 503
- Total OSM length: 16.31 km

## Matched MPD/GPS Coverage

- Matched file found: False
- Matched pings: 0
- Unique MAIDs: 0
- Unique network edges used: 0
- Edge usage: 0.0%
- Match distance P50: 0.0 m
- Match distance P90: 0.0 m
- Match distance P95: 0.0 m
- Match distance P99: 0.0 m

## Interpretation Checklist

- `Connected components` should be 1 for the main fishbone network.
- High P90/P95 match distance suggests the selected network is too narrow, the candidate radius is too loose, or the input still contains off-corridor points.
- Low edge usage can mean unused branch segments, excessive branch length, or demand concentrated only on the RRU backbone.
- Repeat this report for branch lengths 300 m, 400 m, and 500 m before finalizing the network.
