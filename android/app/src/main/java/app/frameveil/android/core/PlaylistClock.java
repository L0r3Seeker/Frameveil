package app.frameveil.android.core;

/** Monotonic image clock. Video completion explicitly calls advance(). */
public final class PlaylistClock {
    private int count;
    private int index;
    private long interval = 5000;
    private long remaining = 5000;
    private long deadline;
    private boolean playing;
    private boolean repeat = true;

    public int index() { return index; }
    public boolean playing() { return playing; }
    public void setRepeat(boolean value) { repeat = value; }
    public void setInterval(long value, long now) {
        interval = Math.max(500, Math.min(3600000, value));
        remaining = interval;
        deadline = now + interval;
    }
    public void setCount(int value, long now) {
        count = Math.max(0, value);
        index = Math.min(index, Math.max(0, count - 1));
        remaining = interval;
        deadline = now + interval;
        if (count == 0) playing = false;
    }
    public void select(int value, long now) {
        if (value < 0 || value >= count) throw new IndexOutOfBoundsException();
        index = value;
        remaining = interval;
        deadline = now + interval;
    }
    public void pause(long now) {
        if (playing) remaining = Math.max(0, deadline - now);
        playing = false;
    }
    public void play(long now) {
        if (count == 0 || playing) return;
        deadline = now + remaining;
        playing = true;
    }
    public boolean tick(long now) {
        return playing && count > 0 && now >= deadline && advance(now);
    }
    public boolean advance(long now) {
        if (count == 0) return false;
        if (index + 1 < count) index++;
        else if (repeat) index = 0;
        else { playing = false; remaining = interval; return false; }
        remaining = interval;
        deadline = now + interval;
        return true;
    }
}
