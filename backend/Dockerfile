FROM golang:1.24-alpine AS build

WORKDIR /app

COPY go.mod go.sum ./
RUN go mod download

COPY . .
RUN go build -o chatops ./main.go

FROM alpine:3.19

WORKDIR /app
COPY --from=build /app/chatops .
COPY --from=build /app/config ./config

CMD ["./chatops"]
