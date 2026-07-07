import threading
import time

import misty
import narrator
import id_scanner
from recorder     import GameRecorder
from maps         import MAPS
from detector     import run_detector, wait_for_tags_removed
from validator    import validate_and_message, ValidationResult
from game_logger  import GameLogger

GAME_DURATION = 8 * 60   # 480 seconds


def select_map():
    available = {mid: m for mid, m in MAPS.items() if m.checkpoints}
    if not available:
        raise RuntimeError("No maps with checkpoints defined in maps.py.")

    print("\nAvailable maps:")
    for mid, m in available.items():
        print(f"  [{mid}] {m.name}  ({len(m.checkpoints)} rounds)")

    while True:
        choice = input("\nSelect a map number: ").strip()
        if choice.isdigit() and int(choice) in available:
            return available[int(choice)]
        print(f"  Please enter one of: {list(available.keys())}")


def run_game(active_map, players: list[dict]):
    total = len(active_map.checkpoints)
    p1    = players[0]["name"]
    p2    = players[1]["name"]

    logger   = GameLogger(players=players, map_name=active_map.name)
    logger.start()
    recorder = GameRecorder(session_id=logger.session_id)
    recorder.start()

    print(f"\n{'='*50}")
    print(f"  MISTY MAZE GAME")
    print(f"  Map     : {active_map.name}")
    print(f"  Players : {p1} & {p2}")
    print(f"  Rounds  : {total}")
    print(f"{'='*50}\n")

    misty.set_volume()
    misty.disable_hazards()

    # ── Timer setup ───────────────────────────────────────────────────────────
    first_tag_event = threading.Event()
    game_over_event = threading.Event()

    def _timer_thread():
        first_tag_event.wait()
        print(f"\n  [TIMER] 8-minute game clock started.")
        game_over_event.wait(timeout=GAME_DURATION)
        if not game_over_event.is_set():
            print("\n  [TIMER] Time's up!")
            game_over_event.set()

    threading.Thread(target=_timer_thread, daemon=True).start()

    # ── Intro narration ───────────────────────────────────────────────────────
    print("\nLoading intro narration...")
    intro = narrator.load_intro()

    misty.led_ready()
    misty.speak(f"Welcome {p1} and {p2}! I am so excited to play with you today!")
    misty.speak(f"Today's map is {active_map.name} with {total} rounds.")
    misty.speak(intro["how_to_play"])
    misty.speak(intro["good_luck"])

    cp0 = active_map.checkpoints[0]
    narrator.prefetch(1, total, cp0.location, cp0.sequence)

    # ── Game loop ─────────────────────────────────────────────────────────────
    for i, checkpoint in enumerate(active_map.checkpoints, 1):
        is_last = (i == total)

        if game_over_event.is_set():
            break

        print(f"\n── Phase {i} of {total} ──────────────────────────────")
        print(f"   Location   : {checkpoint.location}")
        print(f"   Sequence   : {checkpoint.sequence}")

        misty.led_ready()
        misty.speak(narrator.live(i, total, checkpoint.location, checkpoint.sequence, "hint"))

        attempts = 0
        while True:
            if game_over_event.is_set():
                break

            print(f"\n   [Attempt {attempts + 1}] Waiting for cards — press SPACE to submit...")
            logger.begin_checkpoint_attempt()

            scanned = run_detector(
                first_tag_event=first_tag_event,
                game_over_event=game_over_event,
            )

            if game_over_event.is_set():
                break

            if scanned is None:
                print("\nGame aborted by player.")
                misty.speak("Game cancelled. See you next time!")
                misty.led(0, 0, 0)
                misty.enable_hazards()
                logger.end(outcome="Aborted")
                recorder.stop()
                id_scanner.update_play_counts(players)
                return

            attempts += 1
            print(f"   Scanned : {scanned}")
            result, _ = validate_and_message(scanned, checkpoint.sequence)
            print(f"   Result  : {result.value}")
            logger.log_attempt(
                checkpoint_label=checkpoint.location,
                attempt_num=attempts,
                scanned=scanned,
                expected=checkpoint.sequence,
                result=result.value,
            )

            if result == ValidationResult.CORRECT:
                misty.led_success()
                misty.speak(narrator.live(i, total, checkpoint.location,
                                          checkpoint.sequence, "success"))

                if not is_last:
                    next_cp = active_map.checkpoints[i]
                    narrator.prefetch(i + 1, total, next_cp.location, next_cp.sequence)

                print(f"\n   Driving out...")
                misty.execute_drive_map(checkpoint.drive_map)

                if game_over_event.is_set():
                    break

                if checkpoint.return_map:
                    misty.speak(narrator.live(i, total, checkpoint.location,
                                              checkpoint.sequence, "returning"))
                    print(f"   Returning home...")
                    misty.execute_drive_map(checkpoint.return_map)
                    misty.speak("Remove all the RFID tags now", True)
                    wait_for_tags_removed()

                if game_over_event.is_set():
                    break

                if is_last:
                    print("\n   Final phase complete!")
                    misty.celebrate()
                else:
                    misty.speak(f"Great work! On to Round {i + 1}.")
                break

            elif result == ValidationResult.WRONG_ORDER:
                misty.led_error()
                misty.speak(narrator.live(i, total, checkpoint.location,
                                          checkpoint.sequence, "wrong_order"))
                misty.led_ready()

            else:
                misty.led_error()
                misty.speak(narrator.live(i, total, checkpoint.location,
                                          checkpoint.sequence, "wrong_ids"))
                misty.led_ready()

        if game_over_event.is_set():
            break

    # ── End of game ───────────────────────────────────────────────────────────
    if game_over_event.is_set():
        print(f"\n{'='*50}")
        print("  TIME'S UP — GAME OVER")
        print(f"{'='*50}\n")
        misty.led_error()
        misty.speak(f"Time is up! Amazing effort {p1} and {p2}. Goodbye!")
        misty.led(0, 0, 0)
        logger.end(outcome="TimeUp")
    else:
        print(f"\n{'='*50}")
        print("  GAME COMPLETE")
        print(f"{'='*50}\n")
        logger.end(outcome="Completed")

    recorder.stop()
    misty.enable_hazards()
    id_scanner.update_play_counts(players)


def run_forever():
    """Main loop: scan IDs → play game → repeat."""
    print("\n" + "="*50)
    print("  MISTY MAZE — STARTING UP")
    print("="*50)

    active_map = select_map()

    while True:
        players = id_scanner.wait_for_players(n=2)

        try:
            run_game(active_map, players)
        except Exception as e:
            print(f"\n[ERROR] Game crashed: {e}")
            misty.led_error()
            misty.speak("Oops, something went wrong. Please ask a grown-up for help.")

        print("\n  Game over. Ready for the next players!")
        misty.led_ready()
        time.sleep(3)


if __name__ == "__main__":
    run_forever()
