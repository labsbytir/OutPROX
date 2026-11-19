FROM cgr.dev/chainguard/wolfi-base:latest
RUN apk add --no-cache python-3.12
WORKDIR /app
COPY outprox/ outprox/
COPY harness.html ./
EXPOSE 8080
ENV PORT=8080
CMD ["python3", "-m", "outprox.server"]
