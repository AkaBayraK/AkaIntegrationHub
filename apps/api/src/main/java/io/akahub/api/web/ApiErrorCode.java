package io.akahub.api.web;

import java.util.Arrays;
import org.springframework.http.HttpStatusCode;

public enum ApiErrorCode {

    BAD_REQUEST("AIH-COMMON-400", 400),
    UNAUTHORIZED("AIH-COMMON-401", 401),
    FORBIDDEN("AIH-COMMON-403", 403),
    NOT_FOUND("AIH-COMMON-404", 404),
    METHOD_NOT_ALLOWED("AIH-COMMON-405", 405),
    NOT_ACCEPTABLE("AIH-COMMON-406", 406),
    CONFLICT("AIH-COMMON-409", 409),
    UNSUPPORTED_MEDIA_TYPE("AIH-COMMON-415", 415),
    VALIDATION_FAILED("AIH-COMMON-422", 422),
    TOO_MANY_REQUESTS("AIH-COMMON-429", 429),
    INTERNAL_ERROR("AIH-COMMON-500", 500),
    SERVICE_UNAVAILABLE("AIH-COMMON-503", 503);

    private final String code;
    private final int status;

    ApiErrorCode(String code, int status) {
        this.code = code;
        this.status = status;
    }

    public String code() {
        return code;
    }

    public static ApiErrorCode fromStatus(HttpStatusCode status) {
        return Arrays.stream(values())
                .filter(candidate -> candidate.status == status.value())
                .findFirst()
                .orElse(status.is4xxClientError() ? BAD_REQUEST : INTERNAL_ERROR);
    }
}
