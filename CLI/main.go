package main

import (
	"bufio"
	"context"
	"crypto/sha256"
	"fmt"
	"main/database"
	"main/models"
	"os"
	"path/filepath"
	"strings"

	"github.com/jackc/pgx/v5/pgxpool"
)

var db *pgxpool.Pool

func main() {

	database.InitConnection()

	db = database.DbConn
	createDefaultPict()

	scanner := bufio.NewScanner(os.Stdin)
	for {
		fmt.Print("Enter command (mng, adm, list, exit): ")
		if !scanner.Scan() {
			return
		}

		switch strings.TrimSpace(scanner.Text()) {
		case "mng":
			createManager(scanner)
		case "adm":
			createAdmin(scanner)
		case "list":
			listUsers()
		case "exit":
			return
		default:
			fmt.Println("Unknown command")
		}
	}
}

func createManager(scanner *bufio.Scanner) {
	login := readPrompt(scanner, "Manager login: ")
	password := readPrompt(scanner, "Manager password: ")
	firstName := readPrompt(scanner, "Manager first name: ")
	lastName := readPrompt(scanner, "Manager last name: ")
	email := readPrompt(scanner, "Manager email: ")

	if userExists(login, email) {
		return
	}

	manager := models.Managers{
		ManagerLogin:     login,
		ManagerPassHash:  hashPassword(password),
		ManagerFirstName: firstName,
		ManagerLastName:  lastName,
		ManagerEmail:     email,
		ManagerIconUrl:   "/static/icons/default_pict.png",
	}

	if err := database.InsertNewManager(db, manager); err != nil {
		fmt.Println("Failed to create manager:", err)
		return
	}
	fmt.Println("Manager created")
}

func createAdmin(scanner *bufio.Scanner) {
	login := readPrompt(scanner, "Admin login: ")
	password := readPrompt(scanner, "Admin password: ")
	firstName := readPrompt(scanner, "Admin first name: ")
	lastName := readPrompt(scanner, "Admin last name: ")
	email := readPrompt(scanner, "Admin email: ")

	if userExists(login, email) {
		return
	}

	admin := models.Admins{
		AdminLogin:     login,
		AdminPassHash:  hashPassword(password),
		AdminFirstName: firstName,
		AdminLastName:  lastName,
		AdminEmail:     email,
		AdminIconUrl:   "/static/icons/default_pict.png",
	}

	if err := database.InsertNewAdministrator(db, admin); err != nil {
		fmt.Println("Failed to create administrator:", err)
		return
	}
	fmt.Println("Administrator created")
}

func userExists(login string, email string) bool {
	loginExists, err := database.CheckIfLoginAlreadyExists(db, login)
	if err != nil {
		fmt.Println("Failed to check login:", err)
		return true
	}
	if loginExists {
		fmt.Println("A user with such a login already exists")
		return true
	}

	emailExists, err := database.CheckIfEmailAlreadyExists(db, email)
	if err != nil {
		fmt.Println("Failed to check email:", err)
		return true
	}
	if emailExists {
		fmt.Println("A user with such an email already exists")
		return true
	}

	return false
}

func listUsers() {
	rows, err := db.Query(
		context.Background(),
		`SELECT AdminLogin, AdminEmail, 'administrator' FROM Administrator
		UNION ALL
		SELECT MngLogin, MngEmail, 'manager' FROM Manager`,
	)
	if err != nil {
		fmt.Println("Failed to list users:", err)
		return
	}
	defer rows.Close()

	for rows.Next() {
		var login string
		var email string
		var role string
		if err := rows.Scan(&login, &email, &role); err != nil {
			fmt.Println("Failed to read user:", err)
			return
		}
		fmt.Printf("%s\t%s\t%s\n", login, email, role)
	}
	if err := rows.Err(); err != nil {
		fmt.Println("Failed to list users:", err)
	}
}

func readPrompt(scanner *bufio.Scanner, prompt string) string {
	fmt.Print(prompt)
	if !scanner.Scan() {
		return ""
	}
	return strings.TrimSpace(scanner.Text())
}

func hashPassword(password string) string {
	hash := sha256.Sum256([]byte(password))
	return fmt.Sprintf("%x", hash)
}

func createDefaultPict() {
	const photoURL = "/static/icons/default_pict.png"

	var exists bool
	err := db.QueryRow(
		context.Background(),
		`SELECT EXISTS (SELECT 1 FROM Photo WHERE PhotoURL = $1)`,
		photoURL,
	).Scan(&exists)
	if err != nil {
		fmt.Println("Failed to check default photo:", err)
		return
	}
	if exists {
		return
	}

	photo, err := os.ReadFile(filepath.Join("web", "UI", "static", "icons", "default_pict.png"))
	if err != nil {
		fmt.Println("Failed to read default photo:", err)
		return
	}

	_, err = db.Exec(
		context.Background(),
		`INSERT INTO Photo (PhotoURL, PhotoDescription, Photo)
		VALUES ($1, $2, $3)`,
		photoURL,
		"a default photo of a newly created account",
		photo,
	)
	if err != nil {
		fmt.Println("Failed to create default photo:", err)
	}
}
