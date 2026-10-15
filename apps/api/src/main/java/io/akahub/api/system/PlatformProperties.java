package io.akahub.api.system;

import jakarta.validation.constraints.Pattern;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.validation.annotation.Validated;

@Validated
@ConfigurationProperties(prefix = "aih.platform")
public record PlatformProperties(@Pattern(regexp = "local|dev|test|staging|prod") String environment) {
}
