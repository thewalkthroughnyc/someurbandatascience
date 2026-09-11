# Methods

<!-- Scaffold only — headers and TODOs. Prose is Jordan's to write. -->

## Research question

<!-- TODO -->

## Background

<!-- TODO: the Dec 2024 protection install, the Jul/Aug 2025 partial removal,
     why this corridor, why this treatment/control split. -->

## Data sources

<!-- TODO: cite each source with the exact dataset ID / URL and pull date.
     - NYPD Motor Vehicle Collisions (Crashes: h9gi-nx95, Person: f55k-p6yu)
     - Citi Bike monthly system data
     - OSM/Overpass street centerline + intersection data
     Note any known limitations (reporting bias in crash data, Citi Bike
     trip data excluding non-Citi-Bike cyclists, etc). -->

## Treatment definition

<!-- TODO: justify TREATMENT_DATE (config/corridor.py) — what evidence
     pinned it to 2025-08-06, and what the uncertainty around that date
     implies for the before/after window. -->

## Block segmentation

<!-- TODO: once segmentation.segment_corridor() is implemented, document the
     method (centerline source, how block boundaries were decided, how the
     Monroe St / Gates Ave gap was resolved) and link back to the geometry
     source. -->

## Exposure denominator

<!-- TODO: once denominator.py is implemented, document the routing
     methodology (OSRM profile, what "traverses a block" means precisely,
     how sparse-data blocks were handled) and its limitations (Citi Bike
     undercounts total cycling volume; routing assumes shortest/fastest
     path, not actual rider behavior). -->

## Statistical approach

<!-- TODO: once stats/did.py and stats/interval.py are implemented, document
     the difference-in-differences specification, the small-count interval
     method and why it was chosen, and the null-result criterion. -->

## Level of traffic stress (LTS)

<!-- TODO: document the fieldwork methodology behind config/lts.yaml — when
     surveyed, by whom, what rubric. -->

## Results

<!-- TODO -->

## Limitations

<!-- TODO -->
