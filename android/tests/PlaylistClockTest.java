import app.frameveil.android.core.PlaylistClock;

public class PlaylistClockTest {
    static void check(boolean condition, String name) { if (!condition) throw new AssertionError(name); }
    public static void main(String[] args) {
        PlaylistClock clock = new PlaylistClock();
        clock.setCount(3, 0); clock.play(0);
        check(!clock.tick(4999), "no early switch");
        clock.pause(2000); clock.play(10000);
        check(!clock.tick(12999), "pause preserves remaining time");
        check(clock.tick(13000) && clock.index() == 1, "resume deadline");
        check(clock.advance(15000) && clock.index() == 2, "video completion");
        check(clock.advance(16000) && clock.index() == 0, "repeat wraps");
        clock.setRepeat(false); clock.select(2, 20000);
        check(!clock.advance(21000) && !clock.playing() && clock.index() == 2, "single pass stops");
        clock.setCount(0, 22000); clock.play(22000);
        check(!clock.playing(), "empty list cannot play");
        clock.setCount(2, 23000); clock.setInterval(1, 23000); clock.play(23000);
        check(!clock.tick(23499) && clock.tick(23500), "minimum interval");
        System.out.println("PlaylistClock: 8 checks passed");
    }
}
