package database

import (
	"crypto/sha512"
	"encoding/hex"
)

func GenerateNewSessionId(login string, email string, passHash string, dateTime string) (string, error) {
	sessionId := sha512.Sum512([]byte(login + passHash + email + dateTime))
	return hex.EncodeToString(sessionId[:]), nil
}
