/**
 * Copyright (c) Luminous Point LLC, 2014. All rights reserved.
 * Provided under BSD license. Details in the license.txt file.
 *
 * Definition of micro-manager summary metadata tags
 *
 * @author Nenad Amodaj
 * @author Milos Jovanovic
 * @version 2.0
 * @since 2014-03-01
 */
package go2scope.dataset;

public class SummaryMeta {

    // MANDATORY
    // ---------
    public static final String PREFIX = "Prefix";
    public static final String SOURCE = "Source";
    public static final String VERSION = "MetadataVersion";
    public static final String UUID = "UUID";

    public static final String CHANNELS = "Channels";
    public static final String SLICES = "Slices";
    public static final String FRAMES = "Frames";
    public static final String POSITIONS = "Positions";
    public static final String CHANNEL_NAMES = "ChNames";
    public static final String CHANNEL_COLORS = "ChColors";

    public static final String STAGE_POSITIONS = "StagePositions";

    public static final String WIDTH = "Width";
    public static final String HEIGHT = "Height";
    public static final String PIXEL_TYPE = "PixelType";
    public static final String PIXEL_SIZE = "PixelSize_um";
    public static final String BIT_DEPTH = "BitDepth";
    public static final String PIXEL_ASPECT = "PixelAspect";
    public static final String NUMBER_OF_COMPONENTS = "NumComponents";

    public static final String TIME_FIRST = "TimeFirst";
    public static final String SLICES_FIRST = "SlicesFirst";
    public static final String COMPUTER_NAME = "ComputerName";
    public static final String USER_NAME = "UserName";
    public static final String TIME = "Time";

}
