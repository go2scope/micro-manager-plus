package go2scope.dataset;

import org.json.JSONObject;

public class G2SImage {
    private Object pixels = null;
    private JSONObject meta = new JSONObject();
    private int positionIndex = 0;
    private boolean saved = false;

    G2SImage(int posIndex, Object pixels, JSONObject basicMeta) {
        this.positionIndex = posIndex;
        this.pixels = pixels;
        this.meta = basicMeta;
    }

    public void setPixels(Object pixels) {
        this.pixels = pixels;
    }

    public void addMeta(JSONObject m) {
        for (String key : m.keySet()) {
            meta.put(key, m.get(key));
        }
    }

    public int getPositionIndex() {
        return positionIndex;
    }

    public Object getPixels() {
        return pixels;
    }

    public void setSaved(boolean b) {
        saved = true;
    }

    public boolean isSaved() {
        return saved;
    }

    public boolean hasPixels() {
        return pixels != null;
    }

    public JSONObject getMetadata() {
        return meta;
    }
}