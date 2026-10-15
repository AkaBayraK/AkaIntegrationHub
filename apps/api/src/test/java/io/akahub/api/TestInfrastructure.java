package io.akahub.api;

import org.springframework.boot.test.context.TestConfiguration;
import org.springframework.boot.testcontainers.service.connection.ServiceConnection;
import org.springframework.context.annotation.Bean;
import org.testcontainers.containers.GenericContainer;
import org.testcontainers.postgresql.PostgreSQLContainer;
import org.testcontainers.rabbitmq.RabbitMQContainer;
import org.testcontainers.utility.DockerImageName;

@TestConfiguration(proxyBeanMethods = false)
public class TestInfrastructure {

    @Bean
    @ServiceConnection
    PostgreSQLContainer postgres() {
        return new PostgreSQLContainer(DockerImageName.parse("postgres:17.6-alpine"));
    }

    @Bean
    @ServiceConnection(name = "redis")
    GenericContainer<?> valkey() {
        return new GenericContainer<>(DockerImageName.parse("valkey/valkey:8.1.4-alpine")).withExposedPorts(6379);
    }

    @Bean
    @ServiceConnection
    RabbitMQContainer rabbit() {
        return new RabbitMQContainer(DockerImageName.parse("rabbitmq:4.1.4-management-alpine"));
    }
}
