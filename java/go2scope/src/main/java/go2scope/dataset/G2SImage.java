/**
 * Copyright (c) Luminous Point LLC, 2014. All rights reserved.
 * Provided under BSD license. Details in the license.txt file.
 *
 * Internal image representation, private class
 *
 * @author Nenad Amodaj
 * @author Milos Jovanovic
 * @version 2.0
 * @since 2014-03-01
 */
package go2scope.dataset;
import org.json.JSONObject;

class G2SImage {
    private Object pixels = null;
    private JSONObject meta = new JSONObject();
    private int positionIndex = 0;
    private boolean saved = false;
    private boolean acquired = false;

    G2SImage(int posIndex, Object pixels, JSONObject basicMeta) {
        this.positionIndex = posIndex;
        this.pixels = pixels;
        this.meta = basicMeta;
        if (pixels != null)
            acquired = true;
    }

    public void setPixels(Object pixels) {
        this.pixels = pixels;
        if (pixels != null)
            acquired = true;
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

    public boolean isAcquired() {
        return acquired;
    }

    public JSONObject getMetadata() {
        return meta;
    }
}
