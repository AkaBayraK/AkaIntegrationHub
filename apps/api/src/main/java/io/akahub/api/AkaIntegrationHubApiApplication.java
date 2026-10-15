package io.akahub.api;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.context.properties.ConfigurationPropertiesScan;

@SpringBootApplication
@ConfigurationPropertiesScan
public class AkaIntegrationHubApiApplication {

    public static void main(String[] args) {
        SpringApplication.run(AkaIntegrationHubApiApplication.class, args);
    }
}
