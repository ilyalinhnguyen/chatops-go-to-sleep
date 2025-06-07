FROM golang:1.24.3-alpine3.22 AS build
WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN go build -o chatops ./main.go
FROM alpine:3.22
COPY --from=build /usr/src/app/chatops .
CMD ["./chatops"]
