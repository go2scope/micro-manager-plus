import go2scope.dataset.*;
import org.json.JSONObject;

import java.io.IOException;

public class TestDataset {
    public static void main(String[] args) {
        int numPositions = 3;
        ChannelData[] channels = {new ChannelData("DAPI", 0x6666FF), new ChannelData("Cy5", 0xFF0000)};
        int numSlices = 4;
        int numFrames = 5;
        int width = 256;
        int height = 200;
        String pixType = Values.PIX_TYPE_GRAY_16;
        int bitDepth = 14;
        double pixSizeUm = 0.5;

        Dataset ds = Dataset.create("Test1", numPositions, channels.length, numSlices, numFrames);
        System.out.println("Creating in-memory dataset " + ds.getName());

        try {
            ds.initialize(width, height, pixType, bitDepth, 1, new JSONObject());
            ds.setPixelSize(pixSizeUm);
            ds.setChannelData(channels);

            double timeMs = 0.0;
            double intervalMs = 500.0;
            double startZUm = 0.0;
            double zStepUm = 1.5;

            for (int p=0; p<numPositions; p++) {
                ds.setPositionName(String.format("POS-%02d", p), p);
                for (int f=0; f<numFrames; f++) {
                    double zUm = startZUm;
                    for (int s=0; s<numSlices; s++) {
                        for (int c=0; c<channels.length; c++) {
                            JSONObject imgMeta = new JSONObject();
                            imgMeta.put(ImageMeta.ELAPSED_TIME_MS, timeMs);
                            imgMeta.put(ImageMeta.ZUM, zUm);
                            imgMeta.put(ImageMeta.XUM, p * 13.0);
                            imgMeta.put(ImageMeta.YUM, p + 12.0);
                            imgMeta.put(ImageMeta.CHANNEL_NAME, channels[c].name);
                            short[] pixels = new short[width * height];
                            for (int i=0; i<pixels.length; i++)
                                pixels[i] = (short) ((int)(Math.random()*65535) & 0xFF);
                            ds.addImage(pixels, p, c, s, f, imgMeta);
                        }
                        zUm += zStepUm;
                    }
                    timeMs += intervalMs;
                }
            }

        } catch (DatasetException e) {
            e.printStackTrace();
        }

    }
}
