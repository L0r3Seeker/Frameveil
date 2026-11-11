package app.frameveil.android;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.Intent;
import android.content.SharedPreferences;
import android.database.Cursor;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.net.Uri;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.os.SystemClock;
import android.provider.OpenableColumns;
import android.view.View;
import android.widget.*;
import app.frameveil.android.core.PlaylistClock;
import app.frameveil.android.output.CameraOutput;
import app.frameveil.android.output.UnavailableOutput;
import org.json.JSONArray;
import java.io.InputStream;
import java.io.OutputStream;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;

public final class MainActivity extends Activity {
    private static final int PICK = 10, REPORT = 11;
    private static final int BG = 0xff101117, CARD = 0xff1b1e29, MINT = 0xffaef3d5;
    private final ArrayList<Uri> items = new ArrayList<>();
    private final ArrayList<String> names = new ArrayList<>();
    private final ArrayList<Boolean> videos = new ArrayList<>();
    private final PlaylistClock clock = new PlaylistClock();
    private final CameraOutput output = new UnavailableOutput();
    private final Handler handler = new Handler(Looper.getMainLooper());
    private final ExecutorService decoder = Executors.newSingleThreadExecutor();
    private Future<?> pendingImage;
    private int generation;
    private boolean resumed, prepared, mirrored, black;
    private ImageView image;
    private VideoView video;
    private View blackout;
    private TextView filename, intervalLabel, status;
    private Button play;
    private LinearLayout library;
    private SharedPreferences prefs;

    private long now() { return SystemClock.elapsedRealtime(); }
    private final Runnable ticker = new Runnable() {
        public void run() {
            if (!resumed) return;
            if (!items.isEmpty() && !videos.get(clock.index()) && clock.tick(now())) display();
            updateState();
            handler.postDelayed(this, 100);
        }
    };

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        prefs = getSharedPreferences("frameveil", MODE_PRIVATE);
        mirrored = prefs.getBoolean("mirror", false);
        ScrollView scroll = new ScrollView(this);
        scroll.setBackgroundColor(BG);
        LinearLayout root = column(); root.setPadding(dp(20), dp(20), dp(20), dp(40));
        // Insets remain correct on Android 15+ when target SDK enforces edge-to-edge.
        root.setOnApplyWindowInsetsListener((view, insets) -> {
            view.setPadding(dp(20) + insets.getSystemWindowInsetLeft(), dp(20) + insets.getSystemWindowInsetTop(),
                    dp(20) + insets.getSystemWindowInsetRight(), dp(40) + insets.getSystemWindowInsetBottom());
            return insets;
        });
        scroll.addView(root); setContentView(scroll);
        root.addView(label("FRAMEVEIL / ANDROID", 12, MINT));
        root.addView(label("帧幕 · 素材工作台", 27, Color.WHITE));
        root.addView(label("0.1 研发预览 · 仅本地预览", 13, 0xffb5bad0));
        FrameLayout canvas = new FrameLayout(this); canvas.setBackgroundColor(Color.BLACK);
        LinearLayout.LayoutParams canvasParams = new LinearLayout.LayoutParams(-1, dp(216));
        canvasParams.setMargins(0, dp(22), 0, dp(12)); root.addView(canvas, canvasParams);
        image = new ImageView(this); image.setScaleType(ImageView.ScaleType.FIT_CENTER);
        video = new VideoView(this); video.setVisibility(View.GONE);
        canvas.addView(image, new FrameLayout.LayoutParams(-1, -1));
        FrameLayout.LayoutParams vp = new FrameLayout.LayoutParams(-1, -1, android.view.Gravity.CENTER);
        canvas.addView(video, vp);
        blackout = new View(this); blackout.setBackgroundColor(Color.BLACK); blackout.setVisibility(View.GONE);
        canvas.addView(blackout, new FrameLayout.LayoutParams(-1, -1));
        filename = label("导入图片或视频，开始预览", 14, 0xffd7dbee); root.addView(filename);
        LinearLayout controls = new LinearLayout(this);
        addButton(controls, "上一项", () -> move(-1));
        play = addButton(controls, "播放", this::togglePlay);
        addButton(controls, "下一项", () -> move(1)); root.addView(controls);
        addButton(root, "＋ 导入图片 / 视频", this::pick);
        LinearLayout settings = panel(root);
        settings.addView(label("播放参数", 19, Color.WHITE));
        intervalLabel = label("", 14, 0xffd7dbee); settings.addView(intervalLabel);
        SeekBar interval = new SeekBar(this); interval.setMax(59);
        int progress = Math.max(0, Math.min(59, prefs.getInt("interval", 9)));
        interval.setProgress(progress); clock.setInterval((progress + 1) * 500L, now());
        intervalLabel.setText("图片轮播：" + ((progress + 1) / 2.0) + " 秒 / 张");
        interval.setOnSeekBarChangeListener(new SeekBar.OnSeekBarChangeListener() {
            public void onProgressChanged(SeekBar bar, int value, boolean user) {
                clock.setInterval((value + 1) * 500L, now());
                intervalLabel.setText("图片轮播：" + ((value + 1) / 2.0) + " 秒 / 张");
                if (user) prefs.edit().putInt("interval", value).apply();
            }
            public void onStartTrackingTouch(SeekBar bar) { }
            public void onStopTrackingTouch(SeekBar bar) { }
        }); settings.addView(interval);
        Switch loop = new Switch(this); loop.setText("循环整个列表");
        loop.setChecked(prefs.getBoolean("loop", true)); clock.setRepeat(loop.isChecked());
        loop.setOnCheckedChangeListener((button, checked) -> { clock.setRepeat(checked); prefs.edit().putBoolean("loop", checked).apply(); });
        settings.addView(loop);
        Switch mirror = new Switch(this); mirror.setText("水平镜像"); mirror.setChecked(mirrored);
        mirror.setOnCheckedChangeListener((button, checked) -> {
            mirrored = checked; applyMirror(); prefs.edit().putBoolean("mirror", checked).apply();
        }); settings.addView(mirror);
        Switch blackoutSwitch = new Switch(this); blackoutSwitch.setText("黑屏预览");
        blackoutSwitch.setOnCheckedChangeListener((button, checked) -> { black = checked; blackout.setVisibility(black ? View.VISIBLE : View.GONE); });
        settings.addView(blackoutSwitch);
        LinearLayout outputPanel = panel(root);
        outputPanel.addView(label("手机摄像头输出 · 尚未适配", 19, Color.WHITE));
        outputPanel.addView(label(output.unavailableReason(), 14, 0xffb5bad0));
        addButton(outputPanel, "导出设备适配报告", this::exportReport);
        LinearLayout mediaPanel = panel(root);
        mediaPanel.addView(label("素材库", 19, Color.WHITE));
        library = column(); mediaPanel.addView(library);
        addButton(mediaPanel, "移除当前项", this::removeCurrent);
        addButton(mediaPanel, "清空列表", () -> new AlertDialog.Builder(this).setMessage("清空素材列表？不会删除原文件。")
            .setPositiveButton("清空", (dialog, which) -> { items.clear(); names.clear(); videos.clear(); clock.setCount(0, now()); persist(); display(); })
            .setNegativeButton("取消", null).show());
        status = label("", 12, 0xff929bb8); root.addView(status);
        try {
            JSONArray saved = new JSONArray(prefs.getString("uris", "[]"));
            for (int i = 0; i < Math.min(50, saved.length()); i++) addUri(Uri.parse(saved.getString(i)));
        } catch (Exception ignored) { }
        clock.setCount(items.size(), now()); display();
    }

    private void applyMirror() { image.setScaleX(mirrored ? -1 : 1); video.setScaleX(mirrored ? -1 : 1); }
    private void pick() {
        Intent intent = new Intent(Intent.ACTION_OPEN_DOCUMENT).setType("*/*");
        intent.addCategory(Intent.CATEGORY_OPENABLE);
        intent.putExtra(Intent.EXTRA_MIME_TYPES, new String[]{"image/*", "video/*"});
        intent.putExtra(Intent.EXTRA_ALLOW_MULTIPLE, true);
        intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION | Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION);
        startActivityForResult(intent, PICK);
    }
    private void exportReport() {
        Intent intent = new Intent(Intent.ACTION_CREATE_DOCUMENT).setType("application/json");
        intent.addCategory(Intent.CATEGORY_OPENABLE);
        intent.putExtra(Intent.EXTRA_TITLE, "Frameveil-Android-device-report.json");
        startActivityForResult(intent, REPORT);
    }
    @Override protected void onActivityResult(int request, int result, Intent data) {
        super.onActivityResult(request, result, data);
        if (result != RESULT_OK || data == null) return;
        try {
            if (request == REPORT && data.getData() != null) {
                try (OutputStream stream = getContentResolver().openOutputStream(data.getData())) {
                    if (stream == null) throw new IllegalStateException("无法写入报告");
                    stream.write(EnvironmentReport.collect(this).getBytes(StandardCharsets.UTF_8));
                }
                toast("报告已保存，可检查后分享"); return;
            }
            if (request != PICK) return;
            ArrayList<Uri> selected = new ArrayList<>();
            if (data.getClipData() != null) {
                for (int i = 0; i < data.getClipData().getItemCount(); i++) selected.add(data.getClipData().getItemAt(i).getUri());
            } else if (data.getData() != null) selected.add(data.getData());
            int added = 0;
            for (Uri uri : selected) {
                if (items.size() >= 50) break;
                int flags = data.getFlags() & Intent.FLAG_GRANT_READ_URI_PERMISSION;
                try { getContentResolver().takePersistableUriPermission(uri, flags); } catch (SecurityException ignored) { }
                if (addUri(uri)) added++;
            }
            clock.setCount(items.size(), now()); persist(); display(); toast("已导入 " + added + " 项；上限 50 项");
        } catch (Exception error) { toast("操作失败：" + error.getMessage()); }
    }
    private boolean addUri(Uri uri) {
        if (items.contains(uri)) return false;
        try {
            String mime = getContentResolver().getType(uri);
            if (mime == null || !(mime.startsWith("image/") || mime.startsWith("video/"))) return false;
            String name = "未命名素材";
            try (Cursor cursor = getContentResolver().query(uri, new String[]{OpenableColumns.DISPLAY_NAME}, null, null, null)) {
                if (cursor != null && cursor.moveToFirst()) name = cursor.getString(0);
            }
            items.add(uri); names.add(name); videos.add(mime.startsWith("video/")); return true;
        } catch (Exception unavailable) { return false; }
    }
    private void persist() {
        JSONArray saved = new JSONArray(); for (Uri uri : items) saved.put(uri.toString());
        prefs.edit().putString("uris", saved.toString()).apply();
    }
    private void removeCurrent() {
        if (items.isEmpty()) return;
        int index = clock.index(); items.remove(index); names.remove(index); videos.remove(index);
        clock.setCount(items.size(), now()); persist(); display();
    }
    private void move(int delta) {
        if (items.isEmpty()) return;
        clock.select((clock.index() + delta + items.size()) % items.size(), now()); display();
    }
    private void togglePlay() {
        if (clock.playing()) {
            clock.pause(now()); if (prepared && video.isPlaying()) video.pause();
        } else {
            clock.play(now()); if (!items.isEmpty() && videos.get(clock.index()) && prepared) video.start();
        }
        updateState();
    }
    private void display() {
        final int ticket = ++generation;
        if (pendingImage != null) pendingImage.cancel(true);
        prepared = false; video.stopPlayback(); video.setVisibility(View.GONE); image.setVisibility(View.VISIBLE); image.setImageDrawable(null);
        applyMirror(); library.removeAllViews();
        for (int i = 0; i < items.size(); i++) {
            final int selected = i;
            Button entry = addButton(library, (i == clock.index() ? "● " : "") + names.get(i), () -> { clock.select(selected, now()); display(); });
            entry.setAllCaps(false);
        }
        if (items.isEmpty()) { filename.setText("导入图片或视频，开始预览"); updateState(); return; }
        final Uri uri = items.get(clock.index());
        filename.setText((clock.index() + 1) + " / " + items.size() + " · " + names.get(clock.index()));
        if (videos.get(clock.index())) {
            image.setVisibility(View.GONE); video.setVisibility(View.VISIBLE);
            video.setOnPreparedListener(player -> {
                if (ticket != generation) return;
                prepared = true; player.setVolume(0, 0); player.setLooping(false);
                if (clock.playing() && resumed) video.start(); else video.seekTo(1);
            });
            video.setOnCompletionListener(player -> { if (ticket == generation && clock.advance(now())) display(); else updateState(); });
            video.setOnErrorListener((player, what, extra) -> {
                clock.pause(now()); toast("无法解码此视频，请尝试 H.264 MP4"); updateState(); return true;
            });
            video.setVideoURI(uri);
        } else {
            pendingImage = decoder.submit(() -> {
                try {
                    BitmapFactory.Options options = new BitmapFactory.Options(); options.inJustDecodeBounds = true;
                    try (InputStream stream = getContentResolver().openInputStream(uri)) { BitmapFactory.decodeStream(stream, null, options); }
                    if (options.outWidth <= 0 || options.outHeight <= 0) throw new IllegalArgumentException("无法解码图片");
                    options.inSampleSize = 1;
                    while (Math.max(options.outWidth, options.outHeight) / options.inSampleSize > 1920) options.inSampleSize *= 2;
                    options.inJustDecodeBounds = false;
                    Bitmap bitmap;
                    try (InputStream stream = getContentResolver().openInputStream(uri)) { bitmap = BitmapFactory.decodeStream(stream, null, options); }
                    if (bitmap == null) throw new IllegalArgumentException("图片读取失败");
                    runOnUiThread(() -> { if (ticket == generation && !isDestroyed()) image.setImageBitmap(bitmap); });
                } catch (Exception error) {
                    runOnUiThread(() -> { if (ticket == generation && !isDestroyed()) { clock.pause(now()); toast("素材读取失败，请移除或重新导入"); updateState(); } });
                }
            });
        }
        updateState();
    }
    private void updateState() {
        if (play != null) play.setText(clock.playing() ? "暂停" : "播放");
        if (status != null) status.setText("LOCAL FIRST · " + items.size() + " 项 · " + (clock.playing() ? "播放中" : "已暂停") + "\n手机端微信／钉钉摄像头尚未接入");
    }
    @Override protected void onStart() { super.onStart(); resumed = true; handler.post(ticker); }
    @Override protected void onStop() {
        resumed = false; handler.removeCallbacks(ticker); clock.pause(now());
        if (prepared && video.isPlaying()) video.pause(); super.onStop();
    }
    @Override protected void onDestroy() {
        generation++; video.stopPlayback(); decoder.shutdownNow(); output.close(); super.onDestroy();
    }
    private void toast(String message) { Toast.makeText(this, message, Toast.LENGTH_LONG).show(); }
    private int dp(int value) { return Math.round(value * getResources().getDisplayMetrics().density); }
    private LinearLayout column() { LinearLayout view = new LinearLayout(this); view.setOrientation(LinearLayout.VERTICAL); return view; }
    private TextView label(String text, int size, int color) {
        TextView view = new TextView(this); view.setText(text); view.setTextSize(size); view.setTextColor(color); view.setPadding(0, dp(6), 0, dp(6));
        if (size >= 19) view.setTypeface(null, Typeface.BOLD); return view;
    }
    private LinearLayout panel(LinearLayout parent) {
        LinearLayout view = column(); view.setPadding(dp(18), dp(16), dp(18), dp(16));
        GradientDrawable background = new GradientDrawable(); background.setColor(CARD); background.setCornerRadius(dp(18)); view.setBackground(background);
        LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(-1, -2); params.setMargins(0, dp(18), 0, 0); parent.addView(view, params); return view;
    }
    private Button addButton(LinearLayout parent, String text, Runnable action) {
        Button view = new Button(this); view.setText(text); view.setTextColor(MINT); view.setAllCaps(false);
        view.setOnClickListener(v -> action.run()); parent.addView(view); return view;
    }
}
