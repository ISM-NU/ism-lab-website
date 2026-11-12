package database

import (
	"context"
	"log"
	"os"

	"github.com/jackc/pgx/v5/pgxpool"
)

var DbConn *pgxpool.Pool
var dbConnTryFail error

const session_duration_hours = 6

// InitConnection reads the connection string from DATABASE_URL, e.g.
// postgres://user:password@127.0.0.1:6660/ism_lab. Credentials must never be
// written into the source.
func InitConnection() {
	connectionURL := os.Getenv("DATABASE_URL")
	if connectionURL == "" {
		log.Fatal("DATABASE_URL is not set")
	}
	DbConn, dbConnTryFail = pgxpool.New(context.Background(), connectionURL)
	if dbConnTryFail != nil {
		log.Fatal(dbConnTryFail)
	}
	log.Println("Connection established")
}
