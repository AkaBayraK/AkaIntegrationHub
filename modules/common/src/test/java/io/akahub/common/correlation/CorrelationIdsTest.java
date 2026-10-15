package io.akahub.common.correlation;

import static org.assertj.core.api.Assertions.assertThat;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.NullAndEmptySource;
import org.junit.jupiter.params.provider.ValueSource;

class CorrelationIdsTest {

    @Test
    void keepsWellFormedId() {
        assertThat(CorrelationIds.resolve("abc-123_DEF.456")).isEqualTo("abc-123_DEF.456");
    }

    @ParameterizedTest
    @NullAndEmptySource
    @ValueSource(strings = {"short", "has space inside", "inject\r\nheader", "<script>alert(1)</script>"})
    void replacesMissingOrUnsafeIdWithUuid(String candidate) {
        String resolved = CorrelationIds.resolve(candidate);

        assertThat(resolved).isNotEqualTo(candidate).hasSize(36);
    }

    @Test
    void rejectsIdLongerThanLimit() {
        assertThat(CorrelationIds.sanitize("a".repeat(65))).isEmpty();
    }
}
