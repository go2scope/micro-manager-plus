/**
 * Copyright (c) Luminous Point LLC, 2014. All rights reserved.
 * Provided under BSD license. Details in the license.txt file.
 *
 * Definition of micro-manager image metadata tags
 *
 * @author Nenad Amodaj
 * @author Milos Jovanovic
 * @version 2.0
 * @since 2014-03-01
 */
package go2scope.dataset;

public class ImageMeta {
    public static final String WIDTH = "Width";
    public static final String HEIGHT = "Height";
    public static final String CHANNEL = "Channel";
    public static final String CHANNEL_NAME = "Channel";
    public static final String  FRAME = "Frame";
    public static final String  SLICE = "Slice";
    public static final String  CHANNEL_INDEX = "ChannelIndex";
    public static final String  SLICE_INDEX = "SliceIndex";
    public static final String  FRAME_INDEX = "FrameIndex";
    public static final String  POS_NAME = "PositionName";
    public static final String  POS_INDEX = "PositionIndex";
    public static final String  XUM = "XPositionUm";
    public static final String  YUM = "YPositionUm";
    public static final String  ZUM = "ZPositionUm";
    public static final String FILE_NAME = "FileName";
    public static final String ELAPSED_TIME_MS = "ElapsedTime-ms";
}
