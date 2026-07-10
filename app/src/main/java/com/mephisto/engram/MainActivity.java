package com.mephisto.engram;

import android.annotation.SuppressLint;
import android.os.Bundle;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.webkit.WebChromeClient;
import android.view.View;
import android.view.WindowManager;
import androidx.appcompat.app.AppCompatActivity;

/*
 * ENGRAM Android wrapper.
 * Loads engram.html from assets and bridges the whole-app JSON backup:
 *   - JS export calls  Android.saveFile(json, filename)  -> writes to Downloads
 *   - JS restore taps the hidden file input; the chosen file is read here and
 *     handed back to the page via  handleAndroidRestore(jsonString)
 * Place engram.html in app/src/main/assets/  and set applicationId to com.example.engram.
 */
public class MainActivity extends AppCompatActivity {

    private WebView webView;
    private android.webkit.ValueCallback<android.net.Uri[]> filePathCallback;

    @SuppressLint("SetJavaScriptEnabled")
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
        applyImmersive();

        webView = new WebView(this);
        setContentView(webView);

        WebSettings settings = webView.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);          // required: app uses localStorage
        settings.setAllowFileAccessFromFileURLs(true);
        settings.setAllowUniversalAccessFromFileURLs(true);
        settings.setDatabaseEnabled(true);
        settings.setCacheMode(WebSettings.LOAD_DEFAULT);
        settings.setMediaPlaybackRequiresUserGesture(false);

        webView.setWebViewClient(new WebViewClient());
        webView.setWebChromeClient(new WebChromeClient() {
            @Override
            public boolean onShowFileChooser(WebView view,
                                             android.webkit.ValueCallback<android.net.Uri[]> cb,
                                             FileChooserParams params) {
                MainActivity.this.filePathCallback = cb;
                android.content.Intent intent = new android.content.Intent(
                        android.content.Intent.ACTION_GET_CONTENT);
                intent.addCategory(android.content.Intent.CATEGORY_OPENABLE);
                intent.setType("application/json");
                startActivityForResult(android.content.Intent.createChooser(
                        intent, "Select ENGRAM backup"), 1);
                return true;
            }
        });
        webView.setScrollBarStyle(View.SCROLLBARS_INSIDE_OVERLAY);
        webView.addJavascriptInterface(new AndroidBridge(this), "Android");

        webView.loadUrl("file:///android_asset/engram.html");
    }

    private void applyImmersive() {
        getWindow().getDecorView().setSystemUiVisibility(
                View.SYSTEM_UI_FLAG_LAYOUT_STABLE
                        | View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION
                        | View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN
                        | View.SYSTEM_UI_FLAG_HIDE_NAVIGATION
                        | View.SYSTEM_UI_FLAG_FULLSCREEN
                        | View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY);
    }

    @Override
    public void onBackPressed() {
        if (webView.canGoBack()) webView.goBack();
        else super.onBackPressed();
    }

    @Override protected void onPause() { super.onPause(); webView.onPause(); }
    @Override protected void onResume() { super.onResume(); webView.onResume(); applyImmersive(); }
    @Override protected void onDestroy() { if (webView != null) webView.destroy(); super.onDestroy(); }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, android.content.Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (requestCode == 1) {
            if (resultCode == RESULT_OK && data != null && data.getData() != null) {
                try {
                    java.io.InputStream is = getContentResolver().openInputStream(data.getData());
                    java.io.ByteArrayOutputStream bos = new java.io.ByteArrayOutputStream();
                    byte[] buf = new byte[8192]; int n;
                    while ((n = is.read(buf)) != -1) bos.write(buf, 0, n);
                    is.close();
                    String json = new String(bos.toByteArray(), java.nio.charset.StandardCharsets.UTF_8);
                    String escaped = json.replace("\\", "\\\\")
                            .replace("'", "\\'")
                            .replace("\n", "\\n")
                            .replace("\r", "");
                    webView.post(() -> webView.evaluateJavascript(
                            "handleAndroidRestore('" + escaped + "')", null));
                } catch (Exception e) { e.printStackTrace(); }
            }
            if (filePathCallback != null) { filePathCallback.onReceiveValue(null); filePathCallback = null; }
        }
    }

    // ── Bridge exposed to JS as window.Android ──
    public class AndroidBridge {
        private final android.content.Context context;
        AndroidBridge(android.content.Context c) { this.context = c; }

        @android.webkit.JavascriptInterface
        public void saveFile(String content, String filename) {
            try {
                android.content.ContentValues values = new android.content.ContentValues();
                values.put(android.provider.MediaStore.Downloads.DISPLAY_NAME, filename);
                values.put(android.provider.MediaStore.Downloads.MIME_TYPE, "application/json");
                values.put(android.provider.MediaStore.Downloads.IS_PENDING, 1);

                android.content.ContentResolver resolver = context.getContentResolver();
                android.net.Uri uri = resolver.insert(
                        android.provider.MediaStore.Downloads.EXTERNAL_CONTENT_URI, values);
                try (java.io.OutputStream os = resolver.openOutputStream(uri)) {
                    os.write(content.getBytes(java.nio.charset.StandardCharsets.UTF_8));
                }
                values.clear();
                values.put(android.provider.MediaStore.Downloads.IS_PENDING, 0);
                resolver.update(uri, values, null, null);

                new android.os.Handler(android.os.Looper.getMainLooper()).post(() ->
                        android.widget.Toast.makeText(context,
                                "Saved to Downloads: " + filename,
                                android.widget.Toast.LENGTH_SHORT).show());
            } catch (Exception e) { e.printStackTrace(); }
        }
    }
}
