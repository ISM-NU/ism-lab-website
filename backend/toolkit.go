package backend

import (
	"fmt"
	"log"
	"main/database"
	error_handling "main/errors"
	"main/models"
	"net/http"
	"unicode"
	"unicode/utf8"
)

func RouteMethodValidation(route string, method string, handler_name string, w http.ResponseWriter, r *http.Request) bool {
	if r.URL.Path != route {
		handler_error := models.ErrorPage{
			ErrorCode:       http.StatusNotFound,
			OfficialMessage: http.StatusText(http.StatusNotFound),
			Explanation:     "Wrong path was called",
		}
		error_handling.ErrorPageHandler(handler_error, w, r)
		log.Printf("[%s]: Incorrect route was applied to the request\n", handler_name)
		return false
	}
	if r.Method != method {
		handler_error := models.ErrorPage{
			ErrorCode:       http.StatusMethodNotAllowed,
			OfficialMessage: http.StatusText(http.StatusMethodNotAllowed),
			Explanation:     fmt.Sprintf("Only %s method is allowed on this route", method),
		}
		error_handling.ErrorPageHandler(handler_error, w, r)
		log.Printf("[%s]: Inccorrect method was applied to the request\n", handler_name)
		return false
	}
	return true
}

func HandleCommonError(handlerName string, w http.ResponseWriter, r *http.Request, statusCode int, explanation string, logMessage string) {
	current_error := models.ErrorPage{
		ErrorCode:       statusCode,
		OfficialMessage: http.StatusText(statusCode),
		Explanation:     explanation,
	}
	error_handling.ErrorPageHandler(current_error, w, r)
	log.Println("[" + handlerName + "]: " + logMessage)
}

func AuthorizeRequest(handlerName string, w http.ResponseWriter, r *http.Request) (string, bool) {
	sessionIdCookie, err := r.Cookie("session-id")
	if err != nil {
		HandleCommonError(handlerName, w, r, http.StatusBadRequest, "Only authorized users can access this route", "Missing session-id cookie")
		return "", false
	}

	userLoginCookie, err := r.Cookie("user-login")
	if err != nil {
		HandleCommonError(handlerName, w, r, http.StatusBadRequest, "Only authorized users can access this route", "Missing user-login cookie")
		return "", false
	}

	sessionExists, err := database.CheckIfSessionExists(database.DbConn, userLoginCookie.Value, sessionIdCookie.Value)
	if err != nil || !sessionExists {
		logMessage := "Unauthorized events access attempt"
		if err != nil {
			logMessage = err.Error()
		}
		HandleCommonError(handlerName, w, r, http.StatusBadRequest, "Only authorized users can access this route", logMessage)
		return "", false
	}

	return userLoginCookie.Value, true
}

func CheckAdministratorRole(handlerName string, w http.ResponseWriter, r *http.Request) bool {
	userLoginCookie, err := r.Cookie("user-login")
	if err != nil {
		HandleCommonError(handlerName, w, r, http.StatusBadRequest, "Only Admins can access this route", "Missing user-login cookie")
		return false
	}

	var administratorExists bool
	err = database.DbConn.QueryRow(
		r.Context(),
		`SELECT EXISTS (
			SELECT 1
			FROM Administrator
			WHERE AdminLogin = $1
		)`,
		userLoginCookie.Value,
	).Scan(&administratorExists)
	if err != nil {
		HandleCommonError(handlerName, w, r, http.StatusInternalServerError, "Something went wrong during the transaction", err.Error())
		return false
	}
	if !administratorExists {
		HandleCommonError(handlerName, w, r, http.StatusBadRequest, "Only Admins can access this route", "Non-administrator attempted to access an administrator route")
		return false
	}

	return true
}

func CapitalizeFirst(s string) string {
	if s == "" {
		return s
	}

	r, size := utf8.DecodeRuneInString(s)
	return string(unicode.ToUpper(r)) + s[size:]
}
