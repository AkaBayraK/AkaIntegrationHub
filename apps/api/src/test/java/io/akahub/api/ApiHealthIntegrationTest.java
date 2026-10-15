package io.akahub.api;

import static org.assertj.core.api.Assertions.assertThat;

import io.akahub.common.correlation.CorrelationIds;
import java.io.IOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.context.SpringBootTest.WebEnvironment;
import org.springframework.boot.test.web.server.LocalManagementPort;
import org.springframework.boot.test.web.server.LocalServerPort;
import org.springframework.context.annotation.Import;
import org.springframework.jdbc.core.JdbcTemplate;

@SpringBootTest(webEnvironment = WebEnvironment.RANDOM_PORT, properties = "management.server.port=0")
@Import(TestInfrastructure.class)
class ApiHealthIntegrationTest {

    private final HttpClient http = HttpClient.newHttpClient();

    @LocalServerPort
    private int port;

    @LocalManagementPort
    private int managementPort;

    @Autowired
    private JdbcTemplate jdbcTemplate;

    @Test
    void readinessIsUpWhenPostgresValkeyAndRabbitAreReachable() throws Exception {
        HttpResponse<String> response = get(managementPort, "/actuator/health/readiness", null);

        assertThat(response.statusCode()).isEqualTo(200);
        assertThat(response.body()).contains("\"status\":\"UP\"");
    }

    @Test
    void livenessIsUp() throws Exception {
        assertThat(get(managementPort, "/actuator/health/liveness", null).statusCode()).isEqualTo(200);
    }

    @Test
    void flywayCreatedInstallationRecord() {
        Integer rows = jdbcTemplate.queryForObject("SELECT count(*) FROM platform.installation", Integer.class);

        assertThat(rows).isEqualTo(1);
    }

    @Test
    void actuatorIsNotExposedOnApplicationPort() throws Exception {
        assertThat(get(port, "/actuator/health", null).statusCode()).isEqualTo(404);
    }

    @Test
    void systemInfoEchoesCorrelationId() throws Exception {
        HttpResponse<String> response = get(port, "/v1/system/info", "it-correlation-0001");

        assertThat(response.statusCode()).isEqualTo(200);
        assertThat(response.headers().firstValue(CorrelationIds.HEADER)).contains("it-correlation-0001");
        assertThat(response.body()).contains("Aka Integration Hub");
    }

    @Test
    void unknownPathReturnsProblemDetailWithCode() throws Exception {
        HttpResponse<String> response = get(port, "/v1/does-not-exist", null);

        assertThat(response.statusCode()).isEqualTo(404);
        assertThat(response.headers().firstValue("Content-Type")).hasValueSatisfying(
                type -> assertThat(type).startsWith("application/problem+json"));
        assertThat(response.body()).contains("\"code\":\"AIH-COMMON-404\"").doesNotContain("trace");
    }

    private HttpResponse<String> get(int targetPort, String path, String correlationId)
            throws IOException, InterruptedException {
        HttpRequest.Builder request = HttpRequest.newBuilder(URI.create("http://localhost:" + targetPort + path));
        if (correlationId != null) {
            request.header(CorrelationIds.HEADER, correlationId);
        }
        return http.send(request.GET().build(), HttpResponse.BodyHandlers.ofString());
    }
}
