import random
from dataclasses import dataclass, field, replace

from misty import turn_180


# ── Data structures ───────────────────────────────────────────────────────────

@dataclass
class Checkpoint:
    sequence:        list[int]
    hint:            str
    drive_map:       list[tuple]
    return_map:      list[tuple] = field(default_factory=list)
    # Path back to home(0,0) after this checkpoint's return_map has run.
    # Only defined for Map 2 (Map 1 always returns home via return_map).
    return_home_map: list[tuple] = field(default_factory=list)
    location:        str = "destination"
    # Moves to execute silently before this checkpoint's puzzle (Map 2 only,
    # filled by select_checkpoints when intermediate checkpoints are skipped).
    auto_transit:    list[tuple] = field(default_factory=list)


@dataclass
class Map:
    name:        str
    checkpoints: list[Checkpoint]
    map_id:      int = 0


# ── ✏️  EDIT HERE ─────────────────────────────────────────────────────────────

DISTANCE = 30
TURN     = 90

MAPS: dict[int, Map] = {
    1: Map(
        name   = "Map 1 — Out and Back",
        map_id = 1,
        checkpoints = [

            # Phase 1: School
            Checkpoint(
                sequence   = [1, 1],
                hint       = "Leg one — place two cards to send me forward.",
                location   = "School",
                drive_map  = [
                    ("forward",  DISTANCE),
                    ("forward",  DISTANCE),
                ],
                return_map = [
                    ("turn_180",),
                    ("forward",  DISTANCE),
                    ("forward",  DISTANCE),
                    ("turn_180",),
                ],
            ),

            # Phase 2: Supermarket
            Checkpoint(
                sequence   = [1, 2, 1, 2, 1],
                hint       = "Leg two — five cards. Two left turns! Heading to the supermarket.",
                location   = "Supermarket",
                drive_map  = [
                    ("forward",   DISTANCE),
                    ("turn_left", TURN),
                    ("forward",   DISTANCE),
                    ("turn_left", TURN),
                    ("forward",   DISTANCE),
                ],
                return_map = [
                    ("turn_180",),
                    ("forward",    DISTANCE),
                    ("turn_right", TURN),
                    ("forward",    DISTANCE),
                    ("turn_right", TURN),
                    ("forward",    DISTANCE),
                    ("turn_180",),
                ],
            ),

            # Phase 3: Ice-cream Shop
            Checkpoint(
                sequence   = [1, 2, 1, 3, 1],
                hint       = "Leg three — five cards. A left then a right turn!",
                location   = "Ice-cream Shop",
                drive_map  = [
                    ("forward",    DISTANCE),
                    ("turn_left",  TURN),
                    ("forward",    DISTANCE),
                    ("turn_right", TURN),
                    ("forward",    DISTANCE),
                ],
                return_map = [
                    ("turn_180",),
                    ("forward",    DISTANCE),
                    ("turn_left",  TURN),
                    ("forward",    DISTANCE),
                    ("turn_right", TURN),
                    ("forward",    DISTANCE),
                    ("turn_180",),
                ],
            ),

            # Phase 4: Restaurant
            Checkpoint(
                sequence   = [1, 2, 1, 1, 2, 1],
                hint       = "Leg four — six cards. Watch for the double forward! Heading to the restaurant.",
                location   = "Restaurant",
                drive_map  = [
                    ("forward",   DISTANCE),
                    ("turn_left", TURN),
                    ("forward",   DISTANCE),
                    ("forward",   DISTANCE),
                    ("turn_left", TURN),
                    ("forward",   DISTANCE),
                ],
                return_map = [
                    ("turn_180",),
                    ("forward",    DISTANCE),
                    ("turn_right", TURN),
                    ("forward",    DISTANCE),
                    ("forward",    DISTANCE),
                    ("turn_right", TURN),
                    ("forward",    DISTANCE),
                    ("turn_180",),
                ],
            ),

            # Phase 5: Space Center
            Checkpoint(
                sequence   = [1, 2, 1, 1, 3, 1],
                hint       = "Final leg — six cards. Double forward then a right turn! Heading to the Space Center!",
                location   = "Space Center",
                drive_map  = [
                    ("forward",    DISTANCE),
                    ("turn_left",  TURN),
                    ("forward",    DISTANCE),
                    ("forward",    DISTANCE),
                    ("turn_right", TURN),
                    ("forward",    DISTANCE),
                ],
                return_map = [
                    ("turn_180",),
                    ("forward",    DISTANCE),
                    ("turn_left",  TURN),
                    ("forward",    DISTANCE),
                    ("forward",    DISTANCE),
                    ("turn_right", TURN),
                    ("forward",    DISTANCE),
                    ("turn_180",),
                ],
            ),
        ],
    ),

    2: Map(
        name   = "Map 2 — Waypoints",
        map_id = 2,
        # Misty travels a continuous path: each leg starts where the previous
        # one ended (Misty turns 180 in place instead of returning home).
        #
        # Physical layout (30 cm grid, home = origin, North = up):
        #   D1 (0,60)  D3 (-30,60)  D5 (-60,60)
        #   Home(0,0)  D2 (-30,0)   D4 (-60,0)
        #
        # Odd legs face North  -> forward, forward         [1,1]
        # Even legs face South -> right,fwd,left,fwd,fwd  [3,1,2,1,1]
        #
        # return_home_map: path back to Home(0,0) after this checkpoint's
        # return_map (turn_180) has already been executed.
        checkpoints = [

            # Phase 1: School — at D1(0,60), after turn_180 faces South
            Checkpoint(
                sequence        = [1, 1],
                hint            = "Leg one — two cards to send me forward!",
                location        = "School",
                drive_map       = [
                    ("forward", DISTANCE),
                    ("forward", DISTANCE),
                ],
                return_map      = [("turn_180",)],
                return_home_map = [("forward", 2 * DISTANCE)],
            ),

            # Phase 2: Supermarket — at D2(-30,0), after turn_180 faces North
            Checkpoint(
                sequence        = [3, 1, 2, 1, 1],
                hint            = "Leg two — five cards. A right turn, then a left! Heading to the supermarket.",
                location        = "Supermarket",
                drive_map       = [
                    ("turn_right", TURN),
                    ("forward",    DISTANCE),
                    ("turn_left",  TURN),
                    ("forward",    DISTANCE),
                    ("forward",    DISTANCE),
                ],
                return_map      = [("turn_180",)],
                return_home_map = [("turn_right", TURN), ("forward", DISTANCE)],
            ),

            # Phase 3: Ice-cream Shop — at D3(-30,60), after turn_180 faces South
            Checkpoint(
                sequence        = [1, 1],
                hint            = "Leg three — two cards straight ahead again!",
                location        = "Ice-cream Shop",
                drive_map       = [
                    ("forward", DISTANCE),
                    ("forward", DISTANCE),
                ],
                return_map      = [("turn_180",)],
                return_home_map = [
                    ("forward",    2 * DISTANCE),
                    ("turn_left",  TURN),
                    ("forward",    DISTANCE),
                ],
            ),

            # Phase 4: Restaurant — at D4(-60,0), after turn_180 faces North
            Checkpoint(
                sequence        = [3, 1, 2, 1, 1],
                hint            = "Leg four — five cards. Right then left again! Heading to the restaurant.",
                location        = "Restaurant",
                drive_map       = [
                    ("turn_right", TURN),
                    ("forward",    DISTANCE),
                    ("turn_left",  TURN),
                    ("forward",    DISTANCE),
                    ("forward",    DISTANCE),
                ],
                return_map      = [("turn_180",)],
                return_home_map = [("turn_right", TURN), ("forward", 2 * DISTANCE)],
            ),

            # Phase 5: Space Center — at D5(-60,60), drive_map ends facing North
            # (no return_map); return_home starts from North-facing D5
            Checkpoint(
                sequence        = [1, 1],
                hint            = "Final leg — two cards straight to the Space Center!",
                location        = "Space Center",
                drive_map       = [
                    ("forward", DISTANCE),
                    ("forward", DISTANCE),
                ],
                return_map      = [],
                return_home_map = [
                    ("turn_180",),
                    ("forward",   2 * DISTANCE),
                    ("turn_left", TURN),
                    ("forward",   2 * DISTANCE),
                ],
            ),
        ],
    ),
}


# ── Checkpoint randomisation ──────────────────────────────────────────────────

def select_checkpoints(map_obj: "Map", n: int = 3) -> list[Checkpoint]:
    """Return n checkpoints for this playthrough with per-run randomisation.

    Map 1: checkpoint[0] (School) is always first; n-1 others randomly from
           the remaining checkpoints in any order.
    Map 2: checkpoint[-1] (Space Center) is always last; n-1 others randomly
           from checkpoints[:-1] in ascending order (path must be continuous).
           auto_transit is set on each entry to silently drive through any
           skipped intermediate checkpoints.
    """
    cps = map_obj.checkpoints
    total = len(cps)

    if map_obj.map_id == 1:
        pool = list(range(1, total))
        picked = random.sample(pool, min(n - 1, len(pool)))
        random.shuffle(picked)
        selected_indices = [0] + picked
    elif map_obj.map_id == 2:
        pool = list(range(0, total - 1))
        picked = sorted(random.sample(pool, min(n - 1, len(pool))))
        selected_indices = picked + [total - 1]
    else:
        selected_indices = list(range(min(n, total)))

    result: list[Checkpoint] = []
    for pos, idx in enumerate(selected_indices):
        transit: list[tuple] = []
        if map_obj.map_id == 2 and pos > 0:
            prev_idx = selected_indices[pos - 1]
            for skip_idx in range(prev_idx + 1, idx):
                transit.extend(cps[skip_idx].drive_map)
                transit.extend(cps[skip_idx].return_map)
        result.append(replace(cps[idx], auto_transit=transit))

    return result

ACTIVE_MAP_ID = 1


def get_active_map() -> Map:
    if ACTIVE_MAP_ID not in MAPS:
        raise ValueError(
            f"ACTIVE_MAP_ID={ACTIVE_MAP_ID} not found. "
            f"Available IDs: {list(MAPS.keys())}"
        )
    return MAPS[ACTIVE_MAP_ID]


if __name__ == "__main__":
    for map_id, m in MAPS.items():
        marker = " ← active" if map_id == ACTIVE_MAP_ID else ""
        print(f"[{map_id}] {m.name}{marker}")
        for i, cp in enumerate(m.checkpoints, 1):
            print(f"  Phase {i}: sequence={cp.sequence}")
            print(f"    drive_map  = {cp.drive_map}")
            print(f"    return_map = {cp.return_map}")
        print()