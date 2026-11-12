package backend

import (
	"crypto/sha512"
	"encoding/json"
	"fmt"
	"log"
	"main/database"
	error_handling "main/errors"
	"main/models"
	"net/http"
	"time"
)

func ActiveSessionsApiCallHandler(w http.ResponseWriter, r *http.Request) {
	if r.URL.Path != "/api/sessions/active/" {
		current_error := models.ErrorPage{
			ErrorCode:       http.StatusNotFound,
			OfficialMessage: http.StatusText(http.StatusNotFound),
			Explanation:     "Incorrect path was called",
		}
		error_handling.ErrorPageHandler(current_error, w, r)
		log.Println("[ActiveSessionsApiCallHandler]: Incorrect path was applied")
		return
	}
	if r.Method != http.MethodGet {
		current_error := models.ErrorPage{
			ErrorCode:       http.StatusMethodNotAllowed,
			OfficialMessage: http.StatusText(http.StatusMethodNotAllowed),
			Explanation:     "Only GET method is allowed",
		}
		error_handling.ErrorPageHandler(current_error, w, r)
		log.Println("[ActiveSessionsApiCallHandler]: Incorrect method was applied")
		return
	}

	sessionIdCookie, err := r.Cookie("session-id")
	if err != nil {
		current_error := models.ErrorPage{
			ErrorCode:       http.StatusBadRequest,
			OfficialMessage: http.StatusText(http.StatusBadRequest),
			Explanation:     "Only authorized users can access this route",
		}
		error_handling.ErrorPageHandler(current_error, w, r)
		log.Println("[ActiveSessionsApiCallHandler]: Missing session-id cookie")
		return
	}

	userLoginCookie, err := r.Cookie("user-login")
	if err != nil {
		current_error := models.ErrorPage{
			ErrorCode:       http.StatusBadRequest,
			OfficialMessage: http.StatusText(http.StatusBadRequest),
			Explanation:     "Only authorized users can access this route",
		}
		error_handling.ErrorPageHandler(current_error, w, r)
		log.Println("[ActiveSessionsApiCallHandler]: Missing user-login cookie")
		return
	}

	sessionExists, err := database.CheckIfSessionExists(database.DbConn, userLoginCookie.Value, sessionIdCookie.Value)
	if err != nil || !sessionExists {
		current_error := models.ErrorPage{
			ErrorCode:       http.StatusBadRequest,
			OfficialMessage: http.StatusText(http.StatusBadRequest),
			Explanation:     "Only authorized users can access this route",
		}
		error_handling.ErrorPageHandler(current_error, w, r)
		if err != nil {
			log.Println("[ActiveSessionsApiCallHandler]: " + err.Error())
		} else {
			log.Println("[ActiveSessionsApiCallHandler]: Unauthorized active sessions attempt")
		}
		return
	}

	_, err = database.DbConn.Exec(
		r.Context(),
		`UPDATE Sessions
		SET SessionStatus = $1
		WHERE SessionStatus = $2
		AND LoggedInDate IS NOT NULL
		AND LoggedInTime IS NOT NULL
		AND LoggedInDate::timestamp + LoggedInTime < NOW() - INTERVAL '6 hours'`,
		"Non-Active",
		"Active",
	)
	if err != nil {
		current_error := models.ErrorPage{
			ErrorCode:       http.StatusInternalServerError,
			OfficialMessage: http.StatusText(http.StatusInternalServerError),
			Explanation:     "Something went wrong during the work",
		}
		error_handling.ErrorPageHandler(current_error, w, r)
		log.Println("[ActiveSessionsApiCallHandler]: " + err.Error())
		return
	}

	rows, err := database.DbConn.Query(
		r.Context(),
		`SELECT UserLogin, UserRole
		FROM Sessions
		WHERE SessionStatus = $1
		ORDER BY UserLogin`,
		"Active",
	)
	if err != nil {
		current_error := models.ErrorPage{
			ErrorCode:       http.StatusInternalServerError,
			OfficialMessage: http.StatusText(http.StatusInternalServerError),
			Explanation:     "Something went wrong during the work",
		}
		error_handling.ErrorPageHandler(current_error, w, r)
		log.Println("[ActiveSessionsApiCallHandler]: " + err.Error())
		return
	}
	defer rows.Close()

	activeUsers := make([]models.CurrentlyOnlineUsers, 0)
	for rows.Next() {
		var activeUser models.CurrentlyOnlineUsers
		err = rows.Scan(&activeUser.UserLogin, &activeUser.UserRole)
		if err != nil {
			current_error := models.ErrorPage{
				ErrorCode:       http.StatusInternalServerError,
				OfficialMessage: http.StatusText(http.StatusInternalServerError),
				Explanation:     "Something went wrong during the work",
			}
			error_handling.ErrorPageHandler(current_error, w, r)
			log.Println("[ActiveSessionsApiCallHandler]: " + err.Error())
			return
		}
		activeUser.IsCurrentUser = activeUser.UserLogin == userLoginCookie.Value
		activeUsers = append(activeUsers, activeUser)
	}
	if err = rows.Err(); err != nil {
		current_error := models.ErrorPage{
			ErrorCode:       http.StatusInternalServerError,
			OfficialMessage: http.StatusText(http.StatusInternalServerError),
			Explanation:     "Something went wrong during the work",
		}
		error_handling.ErrorPageHandler(current_error, w, r)
		log.Println("[ActiveSessionsApiCallHandler]: " + err.Error())
		return
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	if err := json.NewEncoder(w).Encode(activeUsers); err != nil {
		current_error := models.ErrorPage{
			ErrorCode:       http.StatusInternalServerError,
			OfficialMessage: http.StatusText(http.StatusInternalServerError),
			Explanation:     "Something went wrong during the work",
		}
		error_handling.ErrorPageHandler(current_error, w, r)
		log.Println("[ActiveSessionsApiCallHandler]: " + err.Error())
		return
	}
}

func LoginSessionsApiCallHandler(w http.ResponseWriter, r *http.Request) {
	if r.URL.Path != "/api/sessions/login/" {
		current_error := models.ErrorPage{
			ErrorCode:       http.StatusNotFound,
			OfficialMessage: http.StatusText(http.StatusNotFound),
			Explanation:     "Wrong path was called",
		}
		error_handling.ErrorPageHandler(current_error, w, r)
		log.Println("[LoginSessionsApiCallHandler]: Wrong route was applied in request")
		return
	}
	if r.Method != http.MethodPost {
		current_error := models.ErrorPage{
			ErrorCode:       http.StatusMethodNotAllowed,
			OfficialMessage: http.StatusText(http.StatusMethodNotAllowed),
			Explanation:     "Only POST method is available on this route",
		}
		error_handling.ErrorPageHandler(current_error, w, r)
		log.Println("[LoginSessionsApiCallHandler]: Incorrect method was applied")
		return
	}

	userLoginCookie, err := r.Cookie("user-login")
	if err != nil {
		current_error := models.ErrorPage{
			ErrorCode:       http.StatusBadRequest,
			OfficialMessage: http.StatusText(http.StatusBadRequest),
			Explanation:     "Login or passwrod incorrect",
		}
		error_handling.ErrorPageHandler(current_error, w, r)
		log.Println("[LoginSessionsApiCallHandler]: Missing user-login cookie")
		return
	}

	passwordHashCookie, err := r.Cookie("password-hash")
	if err != nil {
		current_error := models.ErrorPage{
			ErrorCode:       http.StatusBadRequest,
			OfficialMessage: http.StatusText(http.StatusBadRequest),
			Explanation:     "Login or passwrod incorrect",
		}
		error_handling.ErrorPageHandler(current_error, w, r)
		log.Println("[LoginSessionsApiCallHandler]: Missing password-hash cookie")
		return
	}

	loginExists, err := database.CheckIfLoginAlreadyExists(database.DbConn, userLoginCookie.Value)
	if err != nil {
		current_error := models.ErrorPage{
			ErrorCode:       http.StatusInternalServerError,
			OfficialMessage: http.StatusText(http.StatusInternalServerError),
			Explanation:     "Something went wrong during the transaction",
		}
		error_handling.ErrorPageHandler(current_error, w, r)
		log.Println("[LoginSessionsApiCallHandler]: " + err.Error())
		return
	}
	if !loginExists {
		current_error := models.ErrorPage{
			ErrorCode:       http.StatusBadRequest,
			OfficialMessage: http.StatusText(http.StatusBadRequest),
			Explanation:     "Login or passwrod incorrect",
		}
		error_handling.ErrorPageHandler(current_error, w, r)
		log.Println("[LoginSessionsApiCallHandler]: Login does not exist")
		return
	}

	var userEmail string
	var storedPasswordHash string
	err = database.DbConn.QueryRow(
		r.Context(),
		`SELECT AdminEmail, AdminPassHash
		FROM Administrator
		WHERE AdminLogin = $1
		UNION ALL
		SELECT MngEmail, MngPassHash
		FROM Manager
		WHERE MngLogin = $1
		LIMIT 1`,
		userLoginCookie.Value,
	).Scan(&userEmail, &storedPasswordHash)
	if err != nil {
		current_error := models.ErrorPage{
			ErrorCode:       http.StatusInternalServerError,
			OfficialMessage: http.StatusText(http.StatusInternalServerError),
			Explanation:     "Something went wrong during the transaction",
		}
		error_handling.ErrorPageHandler(current_error, w, r)
		log.Println("[LoginSessionsApiCallHandler]: " + err.Error())
		return
	}

	passwordHash := sha512.Sum512([]byte(passwordHashCookie.Value))
	if fmt.Sprintf("%x", passwordHash) != storedPasswordHash {
		current_error := models.ErrorPage{
			ErrorCode:       http.StatusBadRequest,
			OfficialMessage: http.StatusText(http.StatusBadRequest),
			Explanation:     "Login or passwrod incorrect",
		}
		error_handling.ErrorPageHandler(current_error, w, r)
		log.Println("[LoginSessionsApiCallHandler]: Incorrect password")
		return
	}

	sessionId, err := database.CreateNewSession(database.DbConn, userLoginCookie.Value, userEmail)
	if err != nil {
		current_error := models.ErrorPage{
			ErrorCode:       http.StatusInternalServerError,
			OfficialMessage: http.StatusText(http.StatusInternalServerError),
			Explanation:     "Something went wrong during the transaction",
		}
		error_handling.ErrorPageHandler(current_error, w, r)
		log.Println("[LoginSessionsApiCallHandler]: " + err.Error())
		return
	}

	cookieMaxAge := int((6 * time.Hour).Seconds())
	http.SetCookie(w, &http.Cookie{
		Name:     "session-id",
		Value:    sessionId,
		Path:     "/",
		MaxAge:   cookieMaxAge,
		HttpOnly: true,
		SameSite: http.SameSiteLaxMode,
	})
	http.SetCookie(w, &http.Cookie{
		Name:     "user-login",
		Value:    userLoginCookie.Value,
		Path:     "/",
		MaxAge:   cookieMaxAge,
		HttpOnly: true,
		SameSite: http.SameSiteLaxMode,
	})

	w.WriteHeader(http.StatusOK)

}

func RefreshSessionsApiCallHandler(w http.ResponseWriter, r *http.Request) {
	if r.URL.Path != "/api/sessions/refresh/" {
		current_error := models.ErrorPage{
			ErrorCode:       http.StatusNotFound,
			OfficialMessage: http.StatusText(http.StatusNotFound),
			Explanation:     "Incorrect path was called",
		}
		error_handling.ErrorPageHandler(current_error, w, r)
		log.Println("[RefreshSessionsApiCallHandler]: Wrong route was applied to the request")
		return
	}
	if r.Method != http.MethodPut {
		current_error := models.ErrorPage{
			ErrorCode:       http.StatusMethodNotAllowed,
			OfficialMessage: http.StatusText(http.StatusMethodNotAllowed),
			Explanation:     "Only PUT method is allowed",
		}
		error_handling.ErrorPageHandler(current_error, w, r)
		log.Println("[RefreshSessionsApiCallHandler]: Incorrect method was applied to the request")
		return
	}

	sessionIdCookie, err := r.Cookie("session-id")
	if err != nil {
		current_error := models.ErrorPage{
			ErrorCode:       http.StatusBadRequest,
			OfficialMessage: http.StatusText(http.StatusBadRequest),
			Explanation:     "Only authorized users can refresh sessions",
		}
		error_handling.ErrorPageHandler(current_error, w, r)
		log.Println("[RefreshSessionsApiCallHandler]: Missing session-id cookie")
		return
	}

	userLoginCookie, err := r.Cookie("user-login")
	if err != nil {
		current_error := models.ErrorPage{
			ErrorCode:       http.StatusBadRequest,
			OfficialMessage: http.StatusText(http.StatusBadRequest),
			Explanation:     "Only authorized users can refresh sessions",
		}
		error_handling.ErrorPageHandler(current_error, w, r)
		log.Println("[RefreshSessionsApiCallHandler]: Missing user-login cookie")
		return
	}

	sessionExists, err := database.CheckIfSessionExists(database.DbConn, userLoginCookie.Value, sessionIdCookie.Value)
	if err != nil || !sessionExists {
		current_error := models.ErrorPage{
			ErrorCode:       http.StatusBadRequest,
			OfficialMessage: http.StatusText(http.StatusBadRequest),
			Explanation:     "Only authorized users can refresh sessions",
		}
		error_handling.ErrorPageHandler(current_error, w, r)
		if err != nil {
			log.Println("[RefreshSessionsApiCallHandler]: " + err.Error())
		} else {
			log.Println("[RefreshSessionsApiCallHandler]: Unauthorized refresh sessions attempt")
		}
		return
	}

	var userEmail string
	err = database.DbConn.QueryRow(
		r.Context(),
		`SELECT AdminEmail
		FROM Administrator
		WHERE AdminLogin = $1
		UNION ALL
		SELECT MngEmail
		FROM Manager
		WHERE MngLogin = $1
		LIMIT 1`,
		userLoginCookie.Value,
	).Scan(&userEmail)
	if err != nil {
		current_error := models.ErrorPage{
			ErrorCode:       http.StatusInternalServerError,
			OfficialMessage: http.StatusText(http.StatusInternalServerError),
			Explanation:     "Something went wrong during the resigning of cookies",
		}
		error_handling.ErrorPageHandler(current_error, w, r)
		log.Println("[RefreshSessionsApiCallHandler]: " + err.Error())
		return
	}

	sessionId, err := database.CreateNewSession(database.DbConn, userLoginCookie.Value, userEmail)
	if err != nil {
		current_error := models.ErrorPage{
			ErrorCode:       http.StatusInternalServerError,
			OfficialMessage: http.StatusText(http.StatusInternalServerError),
			Explanation:     "Something went wrong during the resigning of cookies",
		}
		error_handling.ErrorPageHandler(current_error, w, r)
		log.Println("[RefreshSessionsApiCallHandler]: " + err.Error())
		return
	}

	cookieMaxAge := int((6 * time.Hour).Seconds())
	http.SetCookie(w, &http.Cookie{
		Name:     "session-id",
		Value:    sessionId,
		Path:     "/",
		MaxAge:   cookieMaxAge,
		HttpOnly: true,
		SameSite: http.SameSiteLaxMode,
	})
	http.SetCookie(w, &http.Cookie{
		Name:     "user-login",
		Value:    userLoginCookie.Value,
		Path:     "/",
		MaxAge:   cookieMaxAge,
		HttpOnly: true,
		SameSite: http.SameSiteLaxMode,
	})

	w.WriteHeader(http.StatusOK)

}

func LogoutSessionsApiCallHandler(w http.ResponseWriter, r *http.Request) {
	if r.URL.Path != "/api/sessions/logout/" {
		current_error := models.ErrorPage{
			ErrorCode:       http.StatusNotFound,
			OfficialMessage: http.StatusText(http.StatusNotFound),
			Explanation:     "Incorrect path was called",
		}
		error_handling.ErrorPageHandler(current_error, w, r)
		log.Println("[LogoutSessionsApiCallHandler]: Wrong route was applied to the request")
		return
	}
	if r.Method != http.MethodDelete {
		current_error := models.ErrorPage{
			ErrorCode:       http.StatusMethodNotAllowed,
			OfficialMessage: http.StatusText(http.StatusMethodNotAllowed),
			Explanation:     "Only DELETE method is available on this route",
		}
		error_handling.ErrorPageHandler(current_error, w, r)
		log.Println("[LogoutSessionsApiCallHandler]: Incorrect method was applied to the request")
		return
	}

	expireSessionCookies(w)

	sessionIdCookie, err := r.Cookie("session-id")
	if err != nil {
		current_error := models.ErrorPage{
			ErrorCode:       http.StatusBadRequest,
			OfficialMessage: http.StatusText(http.StatusBadRequest),
			Explanation:     "Only authorized users can logout",
		}
		error_handling.ErrorPageHandler(current_error, w, r)
		log.Println("[LogoutSessionsApiCallHandler]: Missing session-id cookie")
		return
	}

	userLoginCookie, err := r.Cookie("user-login")
	if err != nil {
		current_error := models.ErrorPage{
			ErrorCode:       http.StatusBadRequest,
			OfficialMessage: http.StatusText(http.StatusBadRequest),
			Explanation:     "Only authorized users can logout",
		}
		error_handling.ErrorPageHandler(current_error, w, r)
		log.Println("[LogoutSessionsApiCallHandler]: Missing user-login cookie")
		return
	}

	sessionExists, err := database.CheckIfSessionExists(database.DbConn, userLoginCookie.Value, sessionIdCookie.Value)
	if err != nil || !sessionExists {
		current_error := models.ErrorPage{
			ErrorCode:       http.StatusBadRequest,
			OfficialMessage: http.StatusText(http.StatusBadRequest),
			Explanation:     "Only authorized users can logout",
		}
		error_handling.ErrorPageHandler(current_error, w, r)
		if err != nil {
			log.Println("[LogoutSessionsApiCallHandler]: " + err.Error())
		} else {
			log.Println("[LogoutSessionsApiCallHandler]: Unauthorized logout attempt")
		}
		return
	}

	now := time.Now()
	_, err = database.DbConn.Exec(
		r.Context(),
		`UPDATE Sessions
		SET SessionStatus = $1,
			LoggedOutTime = $2,
			LoggedOutDate = $3
		WHERE SessionID = $4 AND UserLogin = $5`,
		"Non-Active",
		now,
		now,
		sessionIdCookie.Value,
		userLoginCookie.Value,
	)
	if err != nil {
		current_error := models.ErrorPage{
			ErrorCode:       http.StatusInternalServerError,
			OfficialMessage: http.StatusText(http.StatusInternalServerError),
			Explanation:     "Something went wrong during the logging out process",
		}
		error_handling.ErrorPageHandler(current_error, w, r)
		log.Println("[LogoutSessionsApiCallHandler]: " + err.Error())
		return
	}

	w.WriteHeader(http.StatusOK)

}

func expireSessionCookies(w http.ResponseWriter) {
	expiredAt := time.Unix(0, 0)

	http.SetCookie(w, &http.Cookie{
		Name:     "session-id",
		Value:    "",
		Path:     "/",
		Expires:  expiredAt,
		MaxAge:   -1,
		HttpOnly: true,
		SameSite: http.SameSiteLaxMode,
	})
	http.SetCookie(w, &http.Cookie{
		Name:     "user-login",
		Value:    "",
		Path:     "/",
		Expires:  expiredAt,
		MaxAge:   -1,
		HttpOnly: true,
		SameSite: http.SameSiteLaxMode,
	})
}
