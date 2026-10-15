package io.akahub.api.system;

import java.util.Optional;
import org.springframework.beans.factory.ObjectProvider;
import org.springframework.boot.info.BuildProperties;
import org.springframework.stereotype.Service;

@Service
public class SystemInfoService {

    static final String PRODUCT = "Aka Integration Hub";
    static final String UNKNOWN_VERSION = "dev";

    private final Optional<BuildProperties> buildProperties;
    private final PlatformProperties platformProperties;

    public SystemInfoService(ObjectProvider<BuildProperties> buildProperties, PlatformProperties platformProperties) {
        this.buildProperties = Optional.ofNullable(buildProperties.getIfAvailable());
        this.platformProperties = platformProperties;
    }

    public SystemInfo current() {
        String version = buildProperties.map(BuildProperties::getVersion).orElse(UNKNOWN_VERSION);
        return new SystemInfo(PRODUCT, version, platformProperties.environment());
    }
}
