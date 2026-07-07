import random
from dataclasses import dataclass, field

from misty import turn_180


# ── Data structures ───────────────────────────────────────────────────────────

@dataclass
class Checkpoint:
    sequence:        list[int]
    hint:            str
    drive_map:       list[tuple]
    return_map:      list[tuple] = field(default_factory=list)
    location:        str = "destination"
    # Map 2 only: path back to Home(0,0) from this checkpoint's resting
    # position (after return_map has run). Empty = already at home.
    home_on_timeout: list[tuple] = field(default_factory=list)


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
                hint       = "Two cards forward to reach the School!",
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
                hint       = "Five cards — two left turns to reach the Supermarket!",
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
                hint       = "Five cards — a left then a right turn to the Ice-cream Shop!",
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
                hint       = "Six cards — watch for the double forward to the Restaurant!",
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
                hint       = "Six cards — double forward then a right turn to the Space Center!",
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
        # Fixed continuous path: School → Ice-cream Shop → Space Center → Home.
        # Misty never returns home between checkpoints. Home is the final puzzle.
        #
        # Physical layout (30 cm grid, home = origin, North = up):
        #   School(D1,0,60)  Ice-cream(D3,-30,60)  SpaceCenter(D5,-60,60)
        #   Home(0,0)        D2(-30,0)              D4(-60,0)
        #
        # Allowed corridors — Misty CANNOT cross the top row between checkpoints:
        #   Home ↔ D1   (vertical,   column x=0)
        #   Home ↔ D2   (horizontal, bottom row)
        #   D2   ↔ D4   (horizontal, bottom row)
        #   D2   ↔ D3   (vertical,   column x=-30)
        #   D4   ↔ D5   (vertical,   column x=-60)
        #
        # Every inter-checkpoint leg dips down to the bottom row:
        #   Leg 2  D1 → Home → D2 → D3
        #   Leg 3  D3 → D2  → D4 → D5
        #   Leg 4  D5 → D4  → D2 → Home
        #
        # Facing direction at start of each leg:
        #   Leg 1: North (game start)
        #   Leg 2: South (after turn_180 at D1)
        #   Leg 3: South (after turn_180 at D3)
        #   Leg 4: South (after turn_180 at D5)
        checkpoints = [

            # Leg 1: Home(N) → School(D1)
            # fwd, fwd
            Checkpoint(
                sequence        = [1, 1],
                hint            = "Two Forwards to reach the School!",
                location        = "School",
                drive_map       = [
                    ("forward", DISTANCE),
                    ("forward", DISTANCE),
                ],
                # D1(N) → turn_180 → D1 faces S
                return_map      = [("turn_180",)],
                # D1(S) → fwd×2(→Home) → turn_180(→N)
                home_on_timeout = [
                    ("forward", DISTANCE),
                    ("forward", DISTANCE),
                    ("turn_180",),
                ],
            ),

            # Leg 2: School(D1,S) → Ice-cream(D3)
            # Path uses bottom row: D1 → Home → D2 → D3
            # fwd,fwd(→Home), right(S→W), fwd(→D2), right(W→N), fwd,fwd(→D3)
            Checkpoint(
                sequence        = [1, 1, 3, 1, 3, 1, 1],
                hint            = "Forward, Forward, Right, Forward, Right, Forward, Forward to the Ice-cream Shop!",
                location        = "Ice-cream Shop",
                drive_map       = [
                    ("forward",    DISTANCE),
                    ("forward",    DISTANCE),
                    ("turn_right", TURN),
                    ("forward",    DISTANCE),
                    ("turn_right", TURN),
                    ("forward",    DISTANCE),
                    ("forward",    DISTANCE),
                ],
                # D3(N) → turn_180 → D3 faces S
                return_map      = [("turn_180",)],
                # D3(S) → fwd×2(→D2) → left(S→E) → fwd(→Home) → left(E→N)
                home_on_timeout = [
                    ("forward",   DISTANCE),
                    ("forward",   DISTANCE),
                    ("turn_left", TURN),
                    ("forward",   DISTANCE),
                    ("turn_left", TURN),
                ],
            ),

            # Leg 3: Ice-cream(D3,S) → Space Center(D5)
            # Path uses bottom row: D3 → D2 → D4 → D5
            # fwd,fwd(→D2), right(S→W), fwd(→D4), right(W→N), fwd,fwd(→D5)
            Checkpoint(
                sequence        = [1, 1, 3, 1, 3, 1, 1],
                hint            = "Forward, Forward, Right, Forward, Right, Forward, Forward to the Space Center!",
                location        = "Space Center",
                drive_map       = [
                    ("forward",    DISTANCE),
                    ("forward",    DISTANCE),
                    ("turn_right", TURN),
                    ("forward",    DISTANCE),
                    ("turn_right", TURN),
                    ("forward",    DISTANCE),
                    ("forward",    DISTANCE),
                ],
                # D5(N) → turn_180 → D5 faces S
                return_map      = [("turn_180",)],
                # D5(S) → fwd×2(→D4) → left(S→E) → fwd×2(→Home) → left(E→N)
                home_on_timeout = [
                    ("forward",   DISTANCE),
                    ("forward",   DISTANCE),
                    ("turn_left", TURN),
                    ("forward",   DISTANCE),
                    ("forward",   DISTANCE),
                    ("turn_left", TURN),
                ],
            ),

            # Leg 4: Space Center(D5,S) → Home
            # Path uses bottom row: D5 → D4 → D2 → Home
            # fwd,fwd(→D4), left(S→E), fwd,fwd(→Home)
            Checkpoint(
                sequence        = [1, 1, 2, 1, 1],
                hint            = "Forward, Forward, Left, Forward, Forward — bring me back home!",
                location        = "Home",
                drive_map       = [
                    ("forward",   DISTANCE),
                    ("forward",   DISTANCE),
                    ("turn_left", TURN),
                    ("forward",   DISTANCE),
                    ("forward",   DISTANCE),
                ],
                # Home(E) → turn_left(E→N) → ready for next game
                return_map      = [("turn_left", TURN)],
                home_on_timeout = [],  # already home
            ),
        ],
    ),
}


# ── Checkpoint randomisation ──────────────────────────────────────────────────

def select_checkpoints(map_obj: Map, n: int = 3) -> list[Checkpoint]:
    """Return the checkpoints to play this session.

    Map 1: checkpoint[0] (School) is always first; n-1 others randomly picked
           from the rest in shuffled order (each is independent out-and-back).
    Map 2: fixed path — all 4 checkpoints in order, n is ignored.
    """
    cps   = map_obj.checkpoints
    total = len(cps)

    if map_obj.map_id == 1:
        pool   = list(range(1, total))
        picked = random.sample(pool, min(n - 1, len(pool)))
        random.shuffle(picked)
        return [cps[i] for i in ([0] + picked)]

    # Map 2 (and any other map): play all checkpoints in order
    return list(cps)


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
            print(f"  Phase {i} ({cp.location}): sequence={cp.sequence}")
            print(f"    drive_map  = {cp.drive_map}")
            print(f"    return_map = {cp.return_map}")
        print()
