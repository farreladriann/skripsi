# Network Selection QA

## Network

- Network file: `data/external/rru_with_intersections.geojson`
- Edge count: 470
- Node count: 470
- Connected components: 1
- Largest component nodes: 470
- Total OSM length: 15.31 km

## Matched MPD/GPS Coverage

- Matched file found: True
- Matched pings: 625,755
- Unique MAIDs: 12,892
- Unique network edges used: 470
- Edge usage: 100.0%
- Match distance P50: 13.4 m
- Match distance P90: 40.7 m
- Match distance P95: 45.1 m
- Match distance P99: 49.0 m

## Interpretation Checklist

- `Connected components` should be 1 for the main fishbone network.
- High P90/P95 match distance suggests the selected network is too narrow, the candidate radius is too loose, or the input still contains off-corridor points.
- Low edge usage can mean unused branch segments, excessive branch length, or demand concentrated only on the RRU backbone.
- Repeat this report for branch lengths 300 m, 400 m, and 500 m before finalizing the network.
