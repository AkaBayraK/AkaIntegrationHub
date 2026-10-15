package io.akahub.common.correlation;

import java.util.Optional;
import java.util.UUID;
import java.util.regex.Pattern;

public final class CorrelationIds {

    public static final String HEADER = "X-Correlation-Id";
    public static final String MDC_KEY = "correlationId";

    private static final Pattern ALLOWED = Pattern.compile("[A-Za-z0-9._-]{8,64}");

    private CorrelationIds() {
    }

    public static String newId() {
        return UUID.randomUUID().toString();
    }

    public static Optional<String> sanitize(String candidate) {
        if (candidate == null || !ALLOWED.matcher(candidate).matches()) {
            return Optional.empty();
        }
        return Optional.of(candidate);
    }

    public static String resolve(String candidate) {
        return sanitize(candidate).orElseGet(CorrelationIds::newId);
    }
}
