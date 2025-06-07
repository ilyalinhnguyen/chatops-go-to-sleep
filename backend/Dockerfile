FROM golang:1.24-alpine AS build

WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download

COPY . .
RUN go build -o chatops ./main.go

FROM alpine:3.22

WORKDIR /app
COPY --from=build /app/chatops .
COPY --from=build /app/config ./config
COPY .env .
EXPOSE 8000
CMD ["./chatops"]
