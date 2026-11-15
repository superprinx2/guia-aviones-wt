package pe.gabriel.su30guia;

import android.app.Activity;
import android.content.Intent;
import android.graphics.Color;
import android.net.Uri;
import android.os.Bundle;
import android.webkit.JavascriptInterface;
import android.webkit.ValueCallback;
import android.webkit.WebChromeClient;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;

import java.io.OutputStream;

/** Contenedor WebView de la guia: carga assets/index.html, guarda/abre archivos .blk y abre enlaces externos en el navegador. */
public class MainActivity extends Activity {
    private static final int PICK = 1, SAVE = 2;
    private WebView w;
    private ValueCallback<Uri[]> fileCb;
    private String pendingText;

    @Override
    protected void onCreate(Bundle b) {
        super.onCreate(b);
        w = new WebView(this);
        w.setBackgroundColor(Color.rgb(13, 17, 21));
        WebSettings s = w.getSettings();
        s.setJavaScriptEnabled(true);
        s.setDomStorageEnabled(true);
        s.setAllowFileAccess(true);
        s.setBuiltInZoomControls(false);
        s.setMixedContentMode(WebSettings.MIXED_CONTENT_COMPATIBILITY_MODE);
        w.addJavascriptInterface(new Bridge(), "Android");
        w.setWebViewClient(new WebViewClient() {
            @Override
            public boolean shouldOverrideUrlLoading(WebView v, String url) {
                if (url.startsWith("http://") || url.startsWith("https://")) {
                    openExternal(url);
                    return true;
                }
                return false;
            }
        });
        w.setWebChromeClient(new WebChromeClient() {
            @Override
            public boolean onShowFileChooser(WebView v, ValueCallback<Uri[]> cb, FileChooserParams p) {
                if (fileCb != null) fileCb.onReceiveValue(null);
                fileCb = cb;
                Intent i = new Intent(Intent.ACTION_GET_CONTENT);
                i.addCategory(Intent.CATEGORY_OPENABLE);
                i.setType("*/*");
                startActivityForResult(Intent.createChooser(i, "Elegir archivo .blk"), PICK);
                return true;
            }

            @Override
            public boolean onCreateWindow(WebView v, boolean dialog, boolean user, android.os.Message msg) {
                // enlaces target=_blank: se resuelven con una WebView temporal y se abren fuera
                WebView tmp = new WebView(MainActivity.this);
                tmp.setWebViewClient(new WebViewClient() {
                    @Override
                    public boolean shouldOverrideUrlLoading(WebView vv, String url) {
                        openExternal(url);
                        return true;
                    }
                });
                ((WebView.WebViewTransport) msg.obj).setWebView(tmp);
                msg.sendToTarget();
                return true;
            }
        });
        s.setSupportMultipleWindows(true);
        s.setJavaScriptCanOpenWindowsAutomatically(true);
        w.loadUrl("file:///android_asset/index.html");
        setContentView(w);
    }

    private void openExternal(String url) {
        try {
            startActivity(new Intent(Intent.ACTION_VIEW, Uri.parse(url)));
        } catch (Exception ignored) {
        }
    }

    public class Bridge {
        @JavascriptInterface
        public void saveFile(final String name, final String text) {
            runOnUiThread(new Runnable() {
                public void run() {
                    pendingText = text;
                    Intent i = new Intent(Intent.ACTION_CREATE_DOCUMENT);
                    i.addCategory(Intent.CATEGORY_OPENABLE);
                    i.setType("application/octet-stream");
                    i.putExtra(Intent.EXTRA_TITLE, name);
                    startActivityForResult(i, SAVE);
                }
            });
        }
    }

    @Override
    protected void onActivityResult(int req, int res, Intent data) {
        if (req == SAVE) {
            boolean ok = false;
            if (res == RESULT_OK && data != null && data.getData() != null && pendingText != null) {
                try {
                    OutputStream o = getContentResolver().openOutputStream(data.getData());
                    o.write(pendingText.getBytes("UTF-8"));
                    o.close();
                    ok = true;
                } catch (Exception ignored) {
                }
            }
            pendingText = null;
            w.evaluateJavascript("window.onSavedFile&&onSavedFile(" + ok + ")", null);
        } else if (req == PICK && fileCb != null) {
            Uri[] r = (res == RESULT_OK && data != null && data.getData() != null) ? new Uri[]{data.getData()} : null;
            fileCb.onReceiveValue(r);
            fileCb = null;
        }
    }

    @Override
    public void onBackPressed() {
        w.evaluateJavascript("window.appBack?appBack():0", new ValueCallback<String>() {
            public void onReceiveValue(String v) {
                if (!"1".equals(v)) MainActivity.super.onBackPressed();
            }
        });
    }
}
