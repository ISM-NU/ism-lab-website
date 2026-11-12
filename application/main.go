package main

import (
	"context"
	"log"
	"main/database"
	"main/server"
	"os"
	"path/filepath"
)

func main() {
	database.InitConnection()
	ensureDefaultPhoto()
	server.StartApplication()
}

func ensureDefaultPhoto() {
	const photoURL = "/static/icons/default_pict.png"

	photo, err := os.ReadFile(filepath.Join("web", "UI", "static", "icons", "default_pict.png"))
	if err != nil {
		log.Println("[ensureDefaultPhoto]: " + err.Error())
		return
	}

	err = database.EnsurePhotoExists(
		context.Background(),
		database.DbConn,
		photoURL,
		"a default photo of a newly created account",
		photo,
	)
	if err != nil {
		log.Println("[ensureDefaultPhoto]: " + err.Error())
	}
}
