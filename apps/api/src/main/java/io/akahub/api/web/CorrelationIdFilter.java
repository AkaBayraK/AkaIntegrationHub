package io.akahub.api.web;

import io.akahub.common.correlation.CorrelationIds;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import java.io.IOException;
import org.slf4j.MDC;
import org.springframework.core.Ordered;
import org.springframework.core.annotation.Order;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

@Component
@Order(Ordered.HIGHEST_PRECEDENCE)
public class CorrelationIdFilter extends OncePerRequestFilter {

    @Override
    protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response, FilterChain chain)
            throws ServletException, IOException {
        String correlationId = CorrelationIds.resolve(request.getHeader(CorrelationIds.HEADER));
        request.setAttribute(CorrelationIds.MDC_KEY, correlationId);
        response.setHeader(CorrelationIds.HEADER, correlationId);
        MDC.put(CorrelationIds.MDC_KEY, correlationId);
        try {
            chain.doFilter(request, response);
        } finally {
            MDC.remove(CorrelationIds.MDC_KEY);
        }
    }
}
