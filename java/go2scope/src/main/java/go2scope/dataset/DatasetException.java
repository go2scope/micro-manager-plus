package go2scope.dataset;

public class DatasetException extends Exception {
    private static final long serialVersionUID = -8829247065013272369L;
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
