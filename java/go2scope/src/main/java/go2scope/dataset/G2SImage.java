package go2scope.dataset;

import org.json.JSONObject;

public class G2SImage {
    private Object pixels = null;
    private JSONObject meta = new JSONObject();

    G2SImage(Object pixels, JSONObject basicMeta) {
        this.pixels = pixels;
        this.meta = basicMeta;
    }

    public void setPixels(byte[] pixels) {
        this.pixels = pixels;
    }

    public void addMeta(JSONObject m) {
        for (String key : m.keySet()) {
            meta.put(key, m.get(key));
        }
    }
}
