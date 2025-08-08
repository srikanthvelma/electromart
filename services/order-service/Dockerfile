FROM maven:3.9.5-openjdk-17 AS build

WORKDIR /app

# Copy pom.xml and download dependencies
COPY pom.xml .
RUN mvn dependency:go-offline -B

# Copy source code and build
COPY src ./src
RUN mvn clean package -DskipTests

# Production stage
FROM openjdk:17-jre-slim

# Create app user
RUN addgroup --system --gid 1001 appuser && \
    adduser --system --uid 1001 --ingroup appuser appuser

WORKDIR /app

# Copy jar from build stage
COPY --from=build /app/target/order-service-1.0.0.jar app.jar

# Change ownership to app user
RUN chown -R appuser:appuser /app

USER appuser

# Expose port
EXPOSE 8003

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=60s --retries=3 \
  CMD curl -f http://localhost:8003/actuator/health || exit 1

# Start the application
ENTRYPOINT ["java", "-jar", "app.jar"]
