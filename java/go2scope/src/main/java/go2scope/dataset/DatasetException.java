/**
 * Copyright (c) Luminous Point LLC, 2014. All rights reserved.
 * Provided under BSD license. Details in the license.txt file.
 *
 * Dataset specific exception
 *
 * @author Nenad Amodaj
 * @author Milos Jovanovic
 * @version 2.0
 * @since 2014-03-01
 */
package go2scope.dataset;

public class DatasetException extends Exception {
    private Throwable cause;

    /**
     * Constructs a DartException with an explanatory message.
     * @param message - the reason for the exception.
     */
    public DatasetException(String message) {
        super(message);
    }

    public DatasetException(Throwable t) {
        super(t.getMessage());
        this.cause = t;
    }

    @Override
    public Throwable getCause() {
        return this.cause;
    }
}
