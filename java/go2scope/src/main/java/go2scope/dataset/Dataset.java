package go2scope.dataset;

import org.json.JSONArray;
import org.json.JSONObject;

import java.awt.*;
import java.net.InetAddress;
import java.net.UnknownHostException;
import java.util.Arrays;
import java.util.HashMap;
import java.util.UUID;

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

    private int bitDepth = 0;
    private String pixelType = Values.PIX_TYPE_NONE;
    private double pixelSizeUm = 1.0;
    private int numComponents = 1;
    private int width = 0;
    private int height = 0;

    public static final String SOURCE_MODULE = "Go2Scope";

    // factory method to create new empty in-memory dataset
    public static Dataset create(String label, int numPositions, int numChannels, int numSlices, int numFrames) {
        Dataset ds = new Dataset();
        ds.name = label;
        ds.numPositions = numPositions;
        ds.numChannels = numChannels;
        ds.numSlices = numSlices;
        ds.numFrames = numFrames;
        ds.summaryMeta = new JSONObject();
        return ds;
    }

    // factory method to load existing dataset from disk
    public static Dataset loadFromPath(String path) {
        return null;
    }

    // save current state of the dataset to disk
    public void save() throws DatasetException {
        if (rootPath.isEmpty())
            throw new DatasetException("Root path is not defined. This is in-memory data set.");
    }

    // save in-memory dataset to disk
    public void saveToDir(String parentDir) {

        // TODO
    }

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
        for (int i=0; i<channelData.length; i++) {
            channelData[i].color = Color.gray.getRGB();
            channelData[i].name = String.format("Channel-%d", i);
        }

        // positions
        positionNames = new String[numPositions];
        for (int i=0; i<positionNames.length; i++) {
            String fmt = "Pos-%" + (int) (Math.log10(positionNames.length) + 1) + "d";
            positionNames[i] = String.format(fmt, i);
        }

        // image metadata
        for (int p=0; p<numPositions; p++) {
            for (int c=0; c<numChannels; c++) {
                for (int s=0; s<numSlices; s++) {
                    for (int f=0; f<numFrames; f++) {
                        JSONObject imgMeta = new JSONObject();
                        imgMeta.put(ImageMeta.WIDTH, width);
                        imgMeta.put(ImageMeta.HEIGHT, height);
                        imgMeta.put(ImageMeta.CHANNEL_INDEX, c);
                        imgMeta.put(ImageMeta.POS_INDEX, p);
                        imgMeta.put(ImageMeta.SLICE_INDEX, s);
                        imgMeta.put(ImageMeta.FRAME_INDEX, f);
                        imgMeta.put(ImageMeta.CHANNEL_NAME, channelData[c].name);
                        imgMeta.put(SummaryMeta.BIT_DEPTH, bitDepth);
                        imgMeta.put(SummaryMeta.PIXEL_TYPE, pixelType);
                        imgMeta.put(SummaryMeta.PIXEL_SIZE, pixelSizeUm);
                        imgMeta.put(SummaryMeta.UUID, UUID.randomUUID().toString());
                        String fName = String.format("img_%09d_%s_%03d.tif", f, channelData[c].name, s);
                        imgMeta.put(ImageMeta.FILE_NAME, fName);

                        imgMeta.put(ImageMeta.POS_NAME, positionNames[p]); // this can be changed later

                        imageMap.put(getFrameKey(p, c, s, f, 4), new G2SImage(null, imgMeta));
                    }
                }
            }
        }

        // summary metadadata
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
        summaryMeta.put(SummaryMeta.VERSION, 9);
        String hostName = "unknown";
        try {
            summaryMeta.put(SummaryMeta.COMPUTER_NAME, InetAddress.getLocalHost().getHostName());
        } catch (UnknownHostException e) {
            e.printStackTrace();
        }
        summaryMeta.put(SummaryMeta.USER_NAME, System.getProperty("user.name"));
    }

    public void close() {

    }

    public void setPixelSize(double pixSizeUm) {

    }

    public void setChannelData(ChannelData[] channels) throws DatasetException {
        if (channels.length != numChannels)
            throw new DatasetException("Number of channels does not match.");
        channelData = channels;
    }

    public void setPositionName(String name, int pos) throws DatasetException {
        if (pos < 0 || pos > numPositions)
            throw new DatasetException("Invalid position coordinate");
        positionNames[pos] = name;

    }

    public void addImage(byte[] pixels, int position, int channel, int slice, int frame, JSONObject imageMeta) throws DatasetException {
        G2SImage img = imageMap.get(getFrameKey(position, channel, slice, frame, 4));
        img.setPixels(pixels);
        img.addMeta(imageMeta);
    }

    public void setComment(String text) {
        comment = text;
    }

    public int getWidth() {
        return width;
    }

    private static String getFrameKey(int pos, int ch, int slice, int frame, int dims) throws DatasetException {
        if (dims == 4)
            return String.format("FrameKey-%d-%d-%d-%d", pos, frame, ch, slice);
        else if (dims == 3)
            return String.format("FrameKey-%d-%d-%d", frame, ch, slice);
        else
            throw new DatasetException("Invalid number of dimensions: " + dims);
    }
}
