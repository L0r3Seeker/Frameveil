package app.frameveil.android;

import android.content.Context;
import android.content.pm.PackageManager;
import android.hardware.camera2.CameraManager;
import android.os.Build;
import org.json.JSONArray;
import org.json.JSONObject;

final class EnvironmentReport {
    static String collect(Context context) throws Exception {
        JSONObject out = new JSONObject();
        out.put("app", "Frameveil Android 0.1.0-prototype");
        out.put("manufacturer", Build.MANUFACTURER);
        out.put("model", Build.MODEL);
        out.put("android", Build.VERSION.RELEASE);
        out.put("sdk", Build.VERSION.SDK_INT);
        out.put("abis", new JSONArray(Build.SUPPORTED_ABIS));
        out.put("create_virtual_device_permission", context.checkSelfPermission("android.permission.CREATE_VIRTUAL_DEVICE") == PackageManager.PERMISSION_GRANTED);
        JSONArray cameras = new JSONArray();
        try {
            CameraManager manager = (CameraManager) context.getSystemService(Context.CAMERA_SERVICE);
            for (String id : manager.getCameraIdList()) cameras.put(id);
        } catch (Exception error) { out.put("camera_inventory_error", error.getClass().getSimpleName()); }
        out.put("camera_ids", cameras);
        JSONObject clients = new JSONObject();
        for (String pkg : new String[]{"com.tencent.mm", "com.alibaba.android.rimet"}) {
            try { clients.put(pkg, context.getPackageManager().getPackageInfo(pkg, 0).versionName); }
            catch (PackageManager.NameNotFoundException absent) { clients.put(pkg, "not installed or not visible"); }
        }
        out.put("clients", clients);
        out.put("camera_output_implemented", false);
        out.put("note", "Only capability inventory; no camera opened, no root command executed. Root status and virtual-camera compatibility are not inferred.");
        return out.toString(2);
    }
}
