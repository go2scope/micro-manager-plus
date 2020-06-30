/**
 * Copyright (c) Luminous Point LLC, 2014. All rights reserved.
 * Provided under BSD license. Details in the license.txt file.
 *
 * Test for the Dataset class.
 * The program generates a new dataset in memory, saves it to disk and reads it back.
 *
 * @author Nenad Amodaj
 * @author Milos Jovanovic
 * @version 2.0
 * @since 2014-03-01
 */
package com.go2scope.dataset;
import org.json.JSONObject;

import java.io.IOException;

public class TestDataset {
    public static void main(String[] args) {
        int numPositions = 3;
        ChannelData[] channels = {new ChannelData("DAPI", 0x6666FF), new ChannelData("Cy5", 0xFF0000)};
        int numSlices = 4;
        int numFrames = 5;
        int width = 1920;
        int height = 1080;
        String pixType = Values.PIX_TYPE_GRAY_16;
        int bitDepth = 14;
        double pixSizeUm = 0.5;
        double exposureMs = 300.0;
        double xyMoveMs = 300.0;
        double filterSwitchMs = 400.0;
        final boolean asyncSave = true;

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

            String dsParentDir = args[0];
            System.out.println(String.format("Saving dataset %s to directory %s...", ds.getName(), dsParentDir));

            long startTime = System.currentTimeMillis();
            if (asyncSave)
                ds.saveToDir(dsParentDir, true, true); // unload images and overwrite

            for (int p=0; p<numPositions; p++) {
                Thread.sleep((long) xyMoveMs);
                ds.setPositionName(String.format("POS_%02d", p), p);
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
                            Thread.sleep((long) exposureMs);
                            ds.addImage(pixels, p, c, s, f, imgMeta);
                        }
                        zUm += zStepUm;
                    }
                    timeMs += intervalMs;
                }
                if (asyncSave) {
                    System.out.println("Saving data...");
                    ds.saveAsync(false);
                }
            }
            if (asyncSave)
                ds.waitForSaveToFinish();
            else {
                ds.saveToDir(dsParentDir, true, true); // unload images and overwrite
            }
            System.out.println(String.format("Dataset completed and saved in %d ms, %s mode.",
                    System.currentTimeMillis() - startTime,
                    asyncSave ? "async" : "sequential"));

            String savedDsPath = dsParentDir + "/" + ds.getName();

            System.out.println(String.format("Loading dataset %s from path %s...", ds.getName(), savedDsPath));
            Dataset savedDs = Dataset.loadFromPath(savedDsPath, true);
            System.out.println(String.format("Dataset %s loaded.", savedDs.getName()));

        } catch (DatasetException | InterruptedException | IOException e) {
            e.printStackTrace();
        }
    }
}
