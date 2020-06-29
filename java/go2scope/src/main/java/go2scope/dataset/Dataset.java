/**
 * Copyright (c) Luminous Point LLC, 2014. All rights reserved.
 * Provided under BSD license. Details in the license.txt file.
 *
 * Create, read and write Micro-manager classic file format (separate TIFs and position directories)
 * Part of the Go2Scope software platform.
 *
 * @author Nenad Amodaj
 * @author Milos Jovanovic
 * @version 2.0
 * @since 2014-03-01
 */
package go2scope.dataset;

import ij.ImagePlus;
import ij.io.FileSaver;
import ij.process.ByteProcessor;
import ij.process.ColorProcessor;
import ij.process.ImageProcessor;
import ij.process.ShortProcessor;
import org.apache.commons.io.FileUtils;
import org.json.JSONArray;
import org.json.JSONObject;

import java.awt.*;
import java.io.*;
import java.net.InetAddress;
import java.net.UnknownHostException;

import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.HashMap;
import java.util.Scanner;
import java.util.UUID;

/**
 * Class for reading, writing and creating Micro-manager multi-dimensional image data sets.
 */
public class Dataset {
    private String name = "";
    private String rootPath = "";
    private int numChannels = 0;
    private int numPositions = 0;
    private int numSlices = 0;
    private int numFrames = 0;
    private ChannelData[] channelData = new ChannelData[0];
    private String[] positionNames = new String[0];
    private String comment = "";
    private JSONObject summaryMeta = new JSONObject();
    private HashMap<String, G2SImage> imageMap = new HashMap<>();
    private Thread saveThread = null;

    private int bitDepth = 0;
    private String pixelType = Values.PIX_TYPE_NONE;
    private double pixelSizeUm = 1.0;
    private int numComponents = 1;
    private int width = 0;
    private int height = 0;

    public static final String SOURCE_MODULE = "Go2Scope";
    public static final String METADATA_FILE_NAME = "metadata.txt";
    public static final String KEY_SUMMARY = "Summary";
    public static final int METADATA_VERSION = 9;

    /**
     * Creates an empty and un-initialized data set.
     * @param label - name of the data set
     * @param numPositions - number of positions
     * @param numChannels - number of channels
     * @param numSlices - number of slices
     * @param numFrames - number of frames
     * @return Dataset object
     */
    public static Dataset create(String label, int numPositions, int numChannels, int numSlices, int numFrames) {
        Dataset ds = new Dataset();
        ds.name = label;
        ds.numPositions = numPositions;
        ds.numChannels = numChannels;
        ds.numSlices = numSlices;
        ds.numFrames = numFrames;

        return ds;
    }

    /**
     * Changes the name of the dataset. This works only on in-memory datasets.
     * @param newName
     * @throws DatasetException
     */
    public void setName(String newName) throws DatasetException {
        if (!rootPath.isEmpty())
            throw new DatasetException("Can't change the name of dataset stored on disk.");
        name = newName;
    }

    /**
     * Returns dataset name
     */
    public String getName() {
        return name;
    }

    /**
     * Initializes the Dataset object.
     * @param width - image width
     * @param height - image height
     * @param pixelType - pixel type string identifier
     * @param bitDepth - bit depth of each pixel
     * @param numberOfComponents - number of image components (1 for grayscale, 4 for RGBA)
     * @param meta - custom metadata which will be added to auto-generated metadata
     * @throws DatasetException
     */
    public void initialize(int width, int height, String pixelType, int bitDepth, int numberOfComponents, JSONObject meta) throws DatasetException {
        this.width = width;
        this.height = height;
        this.pixelType = pixelType;
        this.bitDepth = bitDepth;
        this.numComponents = numberOfComponents;

        // create default structure
        // ------------------------

        // channels
        channelData = new ChannelData[numChannels];
        for (int i=0; i<channelData.length; i++)
            channelData[i] = new ChannelData(String.format("Channel-%d", i), Color.gray.getRGB());

        // positions
        positionNames = new String[numPositions];
        for (int i=0; i<positionNames.length; i++) {
            String fmt = "Pos_%" + (int) (Math.log10(positionNames.length) + 1) + "d";
            positionNames[i] = String.format(fmt, i);
        }

        // image metadata
        for (int p=0; p<numPositions; p++) {
            for (int c=0; c<numChannels; c++) {
                for (int s=0; s<numSlices; s++) {
                    for (int f=0; f<numFrames; f++) {
                        JSONObject imgMeta = generateImageMetadata(p, c, s, f);
                        imageMap.put(getFrameKey(p, c, s, f, 4), new G2SImage(p, null, imgMeta));
                    }
                }
            }
        }

        // summary metadata is generated at this time and can't be changed later
        summaryMeta = meta; // start with custom metadata
        summaryMeta.put(SummaryMeta.PREFIX, name);
        summaryMeta.put(SummaryMeta.SOURCE, SOURCE_MODULE);
        summaryMeta.put(SummaryMeta.WIDTH, width);
        summaryMeta.put(SummaryMeta.HEIGHT, height);
        summaryMeta.put(SummaryMeta.PIXEL_TYPE, pixelType);
        summaryMeta.put(SummaryMeta.PIXEL_SIZE, pixelSizeUm);
        summaryMeta.put(SummaryMeta.BIT_DEPTH, bitDepth);
        summaryMeta.put(SummaryMeta.PIXEL_ASPECT, 1);
        summaryMeta.put(SummaryMeta.POSITIONS, numPositions);
        summaryMeta.put(SummaryMeta.CHANNELS, numChannels);
        JSONArray chNames = new JSONArray();
        JSONArray chColors = new JSONArray();
        for (int i=0; i<numChannels; i++) {
            chNames.put(channelData[i].name);
            chColors.put(channelData[i].color);
        }
        summaryMeta.put(SummaryMeta.CHANNEL_NAMES, chNames);
        summaryMeta.put(SummaryMeta.CHANNEL_COLORS, chColors);
        summaryMeta.put(SummaryMeta.SLICES, numSlices);
        summaryMeta.put(SummaryMeta.FRAMES, numFrames);
        summaryMeta.put(SummaryMeta.TIME_FIRST, true);
        summaryMeta.put(SummaryMeta.SLICES_FIRST, false);
        summaryMeta.put(SummaryMeta.NUMBER_OF_COMPONENTS, numComponents);
        summaryMeta.put(SummaryMeta.UUID, UUID.randomUUID().toString());
        summaryMeta.put(SummaryMeta.VERSION, METADATA_VERSION);
        summaryMeta.put(SummaryMeta.TIME, new SimpleDateFormat("yyyy.MM.dd.HH.mm.ss").format(new Date()));
        String hostName = "unknown";
        try {
            summaryMeta.put(SummaryMeta.COMPUTER_NAME, InetAddress.getLocalHost().getHostName());
        } catch (UnknownHostException e) {
            e.printStackTrace();
        }
        summaryMeta.put(SummaryMeta.USER_NAME, System.getProperty("user.name"));
    }


    /**
     * Loads dataset from disk path. Dataset name will be the name of the root directory.
     * @param path - path to the root directory of the dataset.
     * @param loadPix - if true, pixel data will be automatically loaded to memory
     * @return - dataset object
     * @throws DatasetException
     * @throws FileNotFoundException
     */
    public static Dataset loadFromPath(String path, boolean loadPix) throws DatasetException, FileNotFoundException {
        Dataset ds = new Dataset();
        File rootDir = new File(path);
        ds.rootPath = rootDir.getAbsolutePath();
        ds.name = rootDir.getName();
        ds.summaryMeta = new JSONObject();

        // parse directory structure
        File[] fileList = rootDir.listFiles();
        if (fileList == null) {
            throw new DatasetException("Invalid path for dataset: " + path);
        }
        for (File posDir : fileList) {
            if (posDir.isDirectory()) {
                // process one position
                File posMdFile = new File(posDir.getAbsolutePath() + "/" + METADATA_FILE_NAME);
                JSONObject md;
                if (posMdFile.exists()) {
                    String posName = posDir.getName();
                    StringBuilder metaContent = new StringBuilder();
                    Scanner scanner = new Scanner(new FileInputStream(posMdFile));
                    while (scanner.hasNextLine())
                        metaContent.append(scanner.nextLine());
                    scanner.close();

                    // fix the problem with MM metadata files generated by older versions
                    // pre 1.4.22. They might miss the last enclosing curly brace.
                    // JSON parsing would otherwise fail.
                    // Adding an extra curly brace at the end does not hurt.
                    metaContent.append("}");
                    md = new JSONObject(metaContent.toString());

                    // load summary metadata
                    if (ds.summaryMeta.keySet().size() == 0) {
                        ds.summaryMeta = md.getJSONObject(KEY_SUMMARY);

                        // extract basic info
                        ds.numPositions = ds.summaryMeta.getInt(SummaryMeta.POSITIONS);
                        ds.numChannels = ds.summaryMeta.getInt(SummaryMeta.CHANNELS);
                        ds.numSlices = ds.summaryMeta.getInt(SummaryMeta.SLICES);
                        ds.numFrames = ds.summaryMeta.getInt(SummaryMeta.FRAMES);

                        ds.width = ds.summaryMeta.getInt(SummaryMeta.WIDTH);
                        ds.height = ds.summaryMeta.getInt(SummaryMeta.HEIGHT);
                        ds.bitDepth = ds.summaryMeta.getInt(SummaryMeta.BIT_DEPTH);
                        ds.pixelType = ds.summaryMeta.getString(SummaryMeta.PIXEL_TYPE);
                        ds.pixelSizeUm = ds.summaryMeta.getDouble(SummaryMeta.PIXEL_SIZE);
                        ds.numComponents = ds.summaryMeta.getInt(SummaryMeta.NUMBER_OF_COMPONENTS);

                        JSONArray chNames = ds.summaryMeta.getJSONArray(SummaryMeta.CHANNEL_NAMES);
                        JSONArray chColors = ds.summaryMeta.getJSONArray(SummaryMeta.CHANNEL_COLORS);

                        ds.channelData = new ChannelData[ds.numChannels];
                        for (int i=0; i<ds.numChannels; i++) {
                            ds.channelData[i] = new ChannelData(chNames.getString(i), chColors.getInt(i));
                        }

                        ds.positionNames = new String[ds.numPositions];
                        for (int i=0; i<ds.numPositions; i++) ds.positionNames[i] = "Pos_" + i;
                    }

                    // determine position number
                    // this is tricky since position index is stored only in image meta
                    int posIndex=-1;
                    for (String key : md.keySet())
                        if (key.startsWith("FrameKey")) {
                            JSONObject imgMd = md.getJSONObject(key);
                            if (imgMd.getString(ImageMeta.POS_NAME).contentEquals(posName)) {
                                posIndex = imgMd.getInt(ImageMeta.POS_INDEX);
                                ds.positionNames[posIndex] = posName;
                                break;
                            }

                        }

                    if (posIndex < 0)
                        throw new DatasetException("Can't establish the correct position index for: " + posName);

                    // load images
                    for (int c = 0; c < ds.numChannels; c++) {
                        for (int s = 0; s < ds.numSlices; s++) {
                            for (int f = 0; f < ds.numFrames; f++) {
                                String imgFileName = getFileName(f, ds.channelData[c].name, s);
                                String frameKey = getFrameKey(posIndex, c, s, f, 4);
                                Object pixels = null;
                                if (loadPix) {
                                    String imgFilePath = posDir.getAbsolutePath() + "/" + imgFileName;
                                    pixels = ds.loadImagePixels(imgFilePath);
                                }

                                G2SImage img = new G2SImage(posIndex, pixels, md.getJSONObject(frameKey));
                                img.setSaved(true);
                                ds.imageMap.put(frameKey, img);
                            }
                        }
                    }
                }
            }
        }
        return ds;
    }

    /**
     * Saves dataset to disk. It works with incomplete datasets and can be called
     * multiple times during the lifetime of the dataset object.
     *
     * @param unloadImages - pixel data will be purged from memory upon save
     * @throws DatasetException
     * @throws IOException
     */
    public synchronized void save(boolean unloadImages) throws DatasetException, IOException {
        if (rootPath.length() == 0)
            throw new DatasetException("Root path is not defined. This is in-memory data set.");

        for (int p=0; p<numPositions; p++) {
            if (anyImagesOnPosition(p)) {
                File posDir = new File(rootPath + "/" + name + "/" + positionNames[p]);
                if (!posDir.exists()) {
                    if (!posDir.mkdir())
                        throw new DatasetException("Unable to create directory: " + posDir.getAbsolutePath());
                }
                generateAndSaveMetadataFile(p, posDir);

                // save all unsaved images on this position
                for (int c = 0; c < numChannels; c++) {
                    for (int s = 0; s < numSlices; s++) {
                        for (int f = 0; f < numFrames; f++) {
                            G2SImage img = imageMap.get(getFrameKey(p, c, s, f, 4));
                            if (img.hasPixels() && !img.isSaved()) {
                                String fPath = posDir.getAbsolutePath() + "/" + getFileName(f, channelData[c].name, s);
                                saveImagePixels(img.getPixels(), fPath);
                                img.setSaved(true);
                                if (unloadImages)
                                    img.setPixels(null); // this should release the memory
                            }
                        }
                    }
                }
            }
        }
    }

    /**
     * Save dataset (may be incomplete) asynchronously in a separate thread.
     * @param unloadImages - whether to remove pixels from memory after save to file
     * @throws InterruptedException
     */
    public void saveAsync(boolean unloadImages) throws InterruptedException {
        waitForSaveToFinish();
        saveThread = new Thread(() -> {
            try {
                Dataset.this.save(unloadImages);
            } catch (DatasetException | IOException e) {
                e.printStackTrace();
            }
        });
        saveThread.start();
    }

    /**
     * Wait for current save thread to exit
     * @throws InterruptedException
     */
    public void waitForSaveToFinish() throws InterruptedException {
        // if the thread is still running wait until it completes
        if (saveThread != null && saveThread.isAlive()) {
            saveThread.join();
        }
    }

    /**
     * Save in-memory data set to directory.
     * @param parentDir - path to the data set
     * @param unloadImages - release memory for image pixels after saving
     * @param overwrite - overwrite existing data sets (USE WITH CAUTION)
     * @throws DatasetException
     * @throws IOException
     */
    public void saveToDir(String parentDir, boolean unloadImages, boolean overwrite) throws DatasetException, IOException {
        if (rootPath.length() > 0) throw new DatasetException("Dataset has root directory already defined.");

        // create root directory
        File targetDir = new File(parentDir + "/" + name);
        if (targetDir.exists()) {
            if (overwrite) {
                FileUtils.deleteDirectory(targetDir);
            } else
                throw new DatasetException("Directory already exists: " + targetDir);
        }
        boolean ok = targetDir.mkdir();
        if (!ok)
            throw new DatasetException("Unable to create directory: " + targetDir.getAbsolutePath());

        rootPath = parentDir;
        name = targetDir.getName();
        save(unloadImages);
    }

    /**
     * Sets pixel size in microns
     * @param pixSizeUm
     * @throws DatasetException
     */
    public void setPixelSize(double pixSizeUm) throws DatasetException {
        for (int i=0; i<numPositions; i++) {
            if (anyImagesOnPosition(i))
                throw new DatasetException("Dataset already contains images. Can't change pixel size.");
        }
        pixelSizeUm = pixSizeUm;
        summaryMeta.put(SummaryMeta.PIXEL_SIZE, pixSizeUm);
    }

    /**
     * Sets channel names and colors
     * @param channels
     * @throws DatasetException
     */
    public void setChannelData(ChannelData[] channels) throws DatasetException {
        for (int i = 0; i < numPositions; i++) {
            if (anyImagesOnPosition(i))
                throw new DatasetException("Dataset already contains images. Can't change channel data.");
        }
        if (channels.length != numChannels)
            throw new DatasetException("Number of channels does not match.");
        channelData = channels;

        // update metadata
        JSONArray chNames = new JSONArray();
        JSONArray chColors = new JSONArray();
        for (int i = 0; i < numChannels; i++) {
            chNames.put(channelData[i].name);
            chColors.put(channelData[i].color);
        }
        summaryMeta.put(SummaryMeta.CHANNEL_NAMES, chNames);
        summaryMeta.put(SummaryMeta.CHANNEL_COLORS, chColors);

        // update image metadata
        updateFilenames();
    }

    /**
     * Set name for the position index.
     * @param name - new name
     * @param pos - position index
     * @throws DatasetException
     */
    public synchronized void setPositionName(String name, int pos) throws DatasetException {
        if (pos < 0 || pos > numPositions)
            throw new DatasetException("Invalid position coordinate");
        if (anyImagesOnPosition(pos))
            throw new DatasetException("There are already images on this position. Can't change the name.");
        positionNames[pos] = name;
        updateImageMetadata(pos, ImageMeta.POS_NAME, name);
    }

    /**
     * Adds new image to the dataset.
     * @param pixels - pixel array
     * @param position - position index
     * @param channel - channel index
     * @param slice - slice index
     * @param frame - frame index
     * @param imageMeta - custom image metadata that will be added to auto-generated metadata
     * @throws DatasetException
     */
    public synchronized void addImage(Object pixels, int position, int channel, int slice, int frame, JSONObject imageMeta) throws DatasetException {
        G2SImage img = imageMap.get(getFrameKey(position, channel, slice, frame, 4));
        img.setPixels(pixels);
        img.addMeta(imageMeta);
    }

    /**
     * Returns image pixels on a given coordinate position.
     * If the image is not in memory, it will be loaded from disk.
     * If the image was never acquired, a blank (black) image will be returned
     * @param position
     * @param channel
     * @param slice
     * @param frame
     * @return
     * @throws DatasetException
     */
    public synchronized Object getImagePixels(int position, int channel, int slice, int frame) throws DatasetException {
        G2SImage img = imageMap.get(getFrameKey(position, channel, slice, frame, 4));
        Object pixels = img.getPixels();
        if (img.getPixels() == null) {
            if (img.isAcquired()) {
                String imagePath = rootPath + "/" + positionNames[position] + "/" + getFileName(frame, channelData[channel].name, slice);
                return loadImagePixels(imagePath);
            } else {
                return createBlankImage();
            }
        }
        return pixels;
    }

    /**
     * Tells us whether the pixels are available for the current image.
     * There are two reasons why they might not be available:
     * 1. image has not been acquired yet, i.e. we are dealing with an incomplete data set
     * 2. image has been acquired, but the pixels are not retained in memory - only on disk
     * If we go ahead and call getImagePixels() when pixels are not available,
     * in case of 1, we will get an empty (black) image, while in case of 2. the image will
     * be automatically pulled from disk
     * @param position
     * @param channel
     * @param slice
     * @param frame
     * @return - true if image pixels are in memory
     * @throws DatasetException
     */
    public synchronized boolean hasImagePixels(int position, int channel, int slice, int frame) throws DatasetException {
        return imageMap.get(getFrameKey(position, channel, slice, frame, 4)).hasPixels();
    }

    /**
     * Tells us whether the image is actually acquired
     * @param position
     * @param channel
     * @param slice
     * @param frame
     * @return - true if image is acquired
     * @throws DatasetException
     */
    public synchronized boolean isImageAcquired(int position, int channel, int slice, int frame) throws DatasetException {
        return imageMap.get(getFrameKey(position, channel, slice, frame, 4)).isAcquired();
    }

    /**
     * Returns image metdata
     * @param position
     * @param channel
     * @param slice
     * @param frame
     * @return JSONObject with metdata
     * @throws DatasetException
     */
    public synchronized JSONObject getImageMetadata(int position, int channel, int slice, int frame) throws DatasetException {
        return imageMap.get(getFrameKey(position, channel, slice, frame, 4)).getMetadata();
    }

    /**
     * Returns summary metadata for the dataset
     * @return JSONObject with metadata
     */
    public JSONObject getSummaryMetadata() {
        return summaryMeta;
    }

    /**
     * Sets comment text
     * @param text
     */
    public void setComment(String text) {
        comment = text;
    }

    // ---------------------------------------------------------------------------------------------------------------
    // PRIVATE METHODS
    // ---------------------------------------------------------------------------------------------------------------

    /**
     * Automatically generates metadata from current dataset properties
     * @param p - position index
     * @return - metadata as JSONObject
     * @throws DatasetException
     */
    private JSONObject generateMetadata(int p) throws DatasetException {
        JSONObject md = new JSONObject();
        md.put(KEY_SUMMARY, summaryMeta);
        if (anyImagesOnPosition(p)) {
            for (int c = 0; c < numChannels; c++) {
                for (int s = 0; s < numSlices; s++) {
                    for (int f = 0; f < numFrames; f++) {
                        String fk = getFrameKey(p, c, s, f, 4);
                        G2SImage img = imageMap.get(fk);
                        md.put(fk, img.getMetadata());
                    }
                }
            }
        }
        return md;
    }

    private JSONObject generateImageMetadata(int p, int c, int s, int f) {
        JSONObject imgMeta = new JSONObject();
        imgMeta.put(ImageMeta.WIDTH, width);
        imgMeta.put(ImageMeta.HEIGHT, height);
        imgMeta.put(ImageMeta.CHANNEL_INDEX, c);
        imgMeta.put(ImageMeta.POS_INDEX, p);
        imgMeta.put(ImageMeta.SLICE_INDEX, s);
        imgMeta.put(ImageMeta.SLICE, s);
        imgMeta.put(ImageMeta.FRAME_INDEX, f);
        imgMeta.put(ImageMeta.FRAME, f);
        imgMeta.put(ImageMeta.CHANNEL_NAME, channelData[c].name);
        imgMeta.put(SummaryMeta.BIT_DEPTH, bitDepth);
        imgMeta.put(SummaryMeta.PIXEL_TYPE, pixelType);
        imgMeta.put(SummaryMeta.PIXEL_SIZE, pixelSizeUm);
        imgMeta.put(SummaryMeta.UUID, UUID.randomUUID().toString());
        imgMeta.put(ImageMeta.FILE_NAME, getFileName(f, channelData[c].name, s));
        imgMeta.put(ImageMeta.POS_NAME, positionNames[p]);
        return imgMeta;
    }


    private Object loadImagePixels(String imagePath) throws DatasetException {
        ImagePlus ip = new ImagePlus(imagePath);
        if (ip.getProcessor() == null)
            throw new DatasetException("Failed to load image: " + imagePath);
        return ip.getProcessor().getPixels();
    }

    private Object createBlankImage() throws DatasetException {
        Object img;
        if (pixelType.contentEquals(Values.PIX_TYPE_GRAY_16))
            img = new short[width*height];
        else if (pixelType.contentEquals(Values.PIX_TYPE_RGB_32))
            img = new int[width*height];
        else if (pixelType.contentEquals(Values.PIX_TYPE_GRAY_8))
            img = new byte[width*height];
        else
            throw new DatasetException("Unsupported pixel format (image buffer)");
        return img;
    }

    private void saveImagePixels(Object img, String imagePath) throws DatasetException {
        ImageProcessor ip;
        if (pixelType.contentEquals(Values.PIX_TYPE_GRAY_16))
            ip = new ShortProcessor(width, height, (short[]) img, null);
        else if (pixelType.contentEquals(Values.PIX_TYPE_RGB_32))
            ip = new ColorProcessor(width, height, (int[]) img);
        else if (pixelType.contentEquals(Values.PIX_TYPE_GRAY_8))
            ip = new ByteProcessor(width, height, (byte[]) img);
        else
            throw new DatasetException("Unsupported pixel format (image buffer)");

        ImagePlus imp = new ImagePlus();
        imp.setProcessor(ip);
        // imp.setProperty("Info", summaryMeta.toString()); // TODO this is probably not correct
        FileSaver saver = new FileSaver(imp);
        if (!saver.saveAsTiff(imagePath))
            throw new DatasetException("Unable to save file: " + imagePath);

    }

    private static String getFrameKey(int pos, int ch, int slice, int frame, int dims) throws DatasetException {
        if (dims == 4)
            return String.format("FrameKey-%d-%d-%d-%d", pos, frame, ch, slice);
        else if (dims == 3)
            return String.format("FrameKey-%d-%d-%d", frame, ch, slice);
        else
            throw new DatasetException("Invalid number of dimensions: " + dims);
    }

    private static String getFileName(int frame, String chName, int slice) {
        return String.format("img_%09d_%s_%03d.tif", frame, chName, slice);
    }

    /**
     * Decide if there are any images on the specified position
     * @param positionIndex - position index
     * @return - true if any images are available
     */
    private boolean anyImagesOnPosition(int positionIndex) {
        for (int c = 0; c < numChannels; c++) {
            for (int s = 0; s < numSlices; s++) {
                for (int f = 0; f < numFrames; f++) {
                    try {
                        G2SImage img = imageMap.get(getFrameKey(positionIndex, c, s, f, 4));
                        if (img.getPixels() != null || img.isSaved())
                            return true;
                    } catch (DatasetException e) {
                        e.printStackTrace();
                    }
                }
            }
        }
        return false;
    }

    private void updateImageMetadata(int positionIndex, String key, String value) {
        for (int c = 0; c < numChannels; c++) {
            for (int s = 0; s < numSlices; s++) {
                for (int f = 0; f < numFrames; f++) {
                    try {
                        imageMap.get(getFrameKey(positionIndex, c, s, f, 4)).getMetadata().put(key, value);
                    } catch (DatasetException e) {
                        e.printStackTrace();
                    }
                }
            }
        }
    }

    private void updateFilenames() {
        for (int p = 0; p < numPositions; p++) {
            for (int c = 0; c < numChannels; c++) {
                for (int s = 0; s < numSlices; s++) {
                    for (int f = 0; f < numFrames; f++) {
                        try {
                            imageMap.get(getFrameKey(p, c, s, f, 4)).getMetadata().put(ImageMeta.FILE_NAME, getFileName(f, channelData[c].name, s));
                        } catch (DatasetException e) {
                            e.printStackTrace();
                        }
                    }
                }
            }
        }
    }

    /**
     * Re-generates metadata based on the current content and saves the metadata file
     * @param p - position index
     * @param posDir
     * @throws DatasetException
     * @throws IOException
     */
    private void generateAndSaveMetadataFile(int p, File posDir) throws DatasetException, IOException {
        // create metadata file for this position
        JSONObject md = generateMetadata(p);
        FileWriter writer = new FileWriter(new File(posDir.getAbsolutePath() + "/" + METADATA_FILE_NAME));
        writer.write(md.toString(3));
        writer.flush();
        writer.close();
    }
}
