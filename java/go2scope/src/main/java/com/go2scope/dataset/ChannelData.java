/**
 * Copyright (c) Luminous Point LLC, 2014. All rights reserved.
 * Provided under BSD license. Details in the license.txt file.
 *
 * Channel-specific properties
 *
 * @author Nenad Amodaj
 * @author Milos Jovanovic
 * @version 2.0
 * @since 2014-03-01
 */
package com.go2scope.dataset;

public class ChannelData {
    public String name = "";        // channel name
    public int color = 0xFFFFFF;    // channel color

    public ChannelData(String chName, int c) {
        name = chName;
        color = c;
    }
}
