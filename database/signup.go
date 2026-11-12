package database

import (
	"context"
	"crypto/sha512"
	"errors"
	"fmt"
	"log"
	"main/models"
	"time"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
)

func InsertNewAdministrator(db *pgxpool.Pool, adminData models.Admins) error {
	passHash := sha512.Sum512([]byte(adminData.AdminPassHash))
	adminData.AdminPassHash = fmt.Sprintf("%x", passHash)

	_, err := db.Exec(
		context.Background(),
		`INSERT INTO Administrator (
			AdminLogin,
			AdminPassHash,
			AdminFirstName,
			AdminLastName,
			AdminEmail,
			AdminIcon
		) VALUES ($1, $2, $3, $4, $5, $6)`,
		adminData.AdminLogin,
		adminData.AdminPassHash,
		adminData.AdminFirstName,
		adminData.AdminLastName,
		adminData.AdminEmail,
		adminData.AdminIconUrl,
	)
	if err != nil {
		log.Println("[InsertNewAdministrator]: " + err.Error())
		return err
	}
	return nil
}

func CheckIfLoginAlreadyExists(db *pgxpool.Pool, login string) (bool, error) {
	var exists bool

	err := db.QueryRow(
		context.Background(),
		`SELECT EXISTS (
			SELECT 1 FROM Administrator WHERE AdminLogin = $1
			UNION
			SELECT 1 FROM Manager WHERE MngLogin = $1
		)`,
		login,
	).Scan(&exists)
	if err != nil {
		log.Println("[CheckIfLoginAlreadyExists]: " + err.Error())
		return false, err
	}

	return exists, nil
}

func InsertNewManager(db *pgxpool.Pool, manager models.Managers) error {
	passHash := sha512.Sum512([]byte(manager.ManagerPassHash))
	manager.ManagerPassHash = fmt.Sprintf("%x", passHash)

	_, err := db.Exec(
		context.Background(),
		`INSERT INTO Manager (
			MngLogin,
			MngPassHash,
			MngFirstName,
			MngLastName,
			MngEmail,
			MngIcon
		) VALUES ($1, $2, $3, $4, $5, $6)`,
		manager.ManagerLogin,
		manager.ManagerPassHash,
		manager.ManagerFirstName,
		manager.ManagerLastName,
		manager.ManagerEmail,
		manager.ManagerIconUrl,
	)
	if err != nil {
		log.Println("[InsertNewManager]: " + err.Error())
		return err
	}
	return nil
}

func EnsurePhotoExists(ctx context.Context, db *pgxpool.Pool, photoURL string, photoDescription string, photo []byte) error {
	var exists bool

	err := db.QueryRow(
		ctx,
		`SELECT EXISTS (
			SELECT 1
			FROM Photo
			WHERE PhotoURL = $1
		)`,
		photoURL,
	).Scan(&exists)
	if err != nil {
		log.Println("[EnsurePhotoExists]: " + err.Error())
		return err
	}
	if exists {
		return nil
	}

	_, err = db.Exec(
		ctx,
		`INSERT INTO Photo (PhotoURL, PhotoDescription, Photo)
		VALUES ($1, $2, $3)`,
		photoURL,
		photoDescription,
		photo,
	)
	if err != nil {
		log.Println("[EnsurePhotoExists]: " + err.Error())
		return err
	}

	return nil
}

func CheckIfEmailAlreadyExists(db *pgxpool.Pool, email string) (bool, error) {
	var exists bool

	err := db.QueryRow(
		context.Background(),
		`SELECT EXISTS (
			SELECT 1 FROM Administrator WHERE AdminEmail = $1
			UNION
			SELECT 1 FROM Manager WHERE MngEmail = $1
		)`,
		email,
	).Scan(&exists)
	if err != nil {
		log.Println("[CheckIfEmailAlreadyExists]: " + err.Error())
		return false, err
	}

	return exists, nil
}

func CreateNewSession(db *pgxpool.Pool, userLogin string, userEmail string) (string, error) {
	var passHash string
	var userRole string

	err := db.QueryRow(
		context.Background(),
		`SELECT AdminPassHash, 'Administrator'
		FROM Administrator
		WHERE AdminLogin = $1
		UNION ALL
		SELECT MngPassHash, 'Manager'
		FROM Manager
		WHERE MngLogin = $1
		LIMIT 1`,
		userLogin,
	).Scan(&passHash, &userRole)
	if err != nil {
		if errors.Is(err, pgx.ErrNoRows) {
			return "", errors.New("No such user login exists")
		}
		log.Println("[CreateNewSession]: " + err.Error())
		return "", err
	}

	now := time.Now()
	dateTime := now.String()
	sessionId, err := GenerateNewSessionId(userLogin, userEmail, passHash, dateTime)
	if err != nil {
		log.Println("[CreateNewSession]: " + err.Error())
		return "", err
	}

	loggedOut := now.AddDate(1000, 0, 0)
	_, err = db.Exec(
		context.Background(),
		`INSERT INTO Sessions (
			SessionID,
			UserLogin,
			UserRole,
			LoggedInTime,
			LoggedInDate,
			LoggedOutTime,
			LoggedOutDate,
			SessionStatus
		) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)`,
		sessionId,
		userLogin,
		userRole,
		now,
		now,
		loggedOut,
		loggedOut,
		"Active",
	)
	if err != nil {
		log.Println("[CreateNewSession]: " + err.Error())
		return "", err
	}

	return sessionId, nil
}

func CheckIfSessionExists(db *pgxpool.Pool, userLogin string, sessionId string) (bool, error) {
	var sessionUserLogin string
	var loggedInAt time.Time

	err := db.QueryRow(
		context.Background(),
		`SELECT UserLogin, LoggedInDate::timestamp + LoggedInTime
		FROM Sessions
		WHERE SessionID = $1 AND SessionStatus = $2`,
		sessionId,
		"Active",
	).Scan(&sessionUserLogin, &loggedInAt)
	if err != nil {
		if errors.Is(err, pgx.ErrNoRows) {
			return false, nil
		}
		log.Println("[CheckIfSessionExists]: " + err.Error())
		return false, err
	}

	if sessionUserLogin == "" || sessionUserLogin != userLogin {
		return false, nil
	}

	if time.Since(loggedInAt) > 6*time.Hour {
		_, err = db.Exec(
			context.Background(),
			`UPDATE Sessions
			SET SessionStatus = $1
			WHERE SessionID = $2 AND SessionStatus = $3`,
			"Timeout",
			sessionId,
			"Active",
		)
		if err != nil {
			log.Println("[CheckIfSessionExists]: " + err.Error())
			return false, err
		}
		return false, nil
	}

	return true, nil

}
