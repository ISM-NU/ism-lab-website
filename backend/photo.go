package backend

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"log"
	"main/database"
	error_handling "main/errors"
	"main/models"
	"net/http"
	"os"
	"path/filepath"
	"strconv"
	"strings"
	"time"

	"github.com/jackc/pgx/v5"
)

func ListPhotoApiCallHandler(w http.ResponseWriter, r *http.Request) {
	if r.URL.Path != "/api/photo/list/" {
		current_err := models.ErrorPage{
			ErrorCode:       http.StatusNotFound,
			OfficialMessage: http.StatusText(http.StatusNotFound),
			Explanation:     "Wrong path mentioned",
		}
		error_handling.ErrorPageHandler(current_err, w, r)
		log.Println("[ListPhotoApiCallHandler]: Incorrect path was called")
		return
	}
	if r.Method != http.MethodGet {
		current_err := models.ErrorPage{
			ErrorCode:       http.StatusMethodNotAllowed,
			OfficialMessage: http.StatusText(http.StatusMethodNotAllowed),
			Explanation:     "Only GET is allowed on this route",
		}
		error_handling.ErrorPageHandler(current_err, w, r)
		log.Println("[ListPhotoApiCallHandler]: Wrong method was applied")
		return
	}

	query := r.URL.Query()
	photoIDs, hasPhotoID := query["photo_id"]
	photoURLs, hasPhotoURL := query["photo_url"]

	if len(query) != 1 || hasPhotoID == hasPhotoURL || (hasPhotoID && len(photoIDs) != 1) || (hasPhotoURL && len(photoURLs) != 1) || (hasPhotoID && photoIDs[0] == "") || (hasPhotoURL && photoURLs[0] == "") {
		current_err := models.ErrorPage{
			ErrorCode:       http.StatusForbidden,
			OfficialMessage: http.StatusText(http.StatusForbidden),
			Explanation:     "The url format for photo is incorrect",
		}
		error_handling.ErrorPageHandler(current_err, w, r)
		log.Println("[ListPhotoApiCallHandler]: Incorrect photo query format")
		return
	}

	var photo models.Photo
	var err error

	if hasPhotoID {
		photoID, convertErr := strconv.Atoi(photoIDs[0])
		if convertErr != nil {
			current_err := models.ErrorPage{
				ErrorCode:       http.StatusForbidden,
				OfficialMessage: http.StatusText(http.StatusForbidden),
				Explanation:     "The url format for photo is incorrect",
			}
			error_handling.ErrorPageHandler(current_err, w, r)
			log.Println("[ListPhotoApiCallHandler]: Incorrect photo ID format")
			return
		}

		err = database.DbConn.QueryRow(
			r.Context(),
			`SELECT PhotoURL, PhotoID, PhotoDescription, Photo
			FROM Photo
			WHERE PhotoID = $1`,
			photoID,
		).Scan(&photo.PhotoURL, &photo.PhotoID, &photo.PhotoDescription, &photo.Photo)
		if errors.Is(err, pgx.ErrNoRows) {
			current_err := models.ErrorPage{
				ErrorCode:       http.StatusForbidden,
				OfficialMessage: http.StatusText(http.StatusForbidden),
				Explanation:     "No such a photo with given photo ID exists",
			}
			error_handling.ErrorPageHandler(current_err, w, r)
			log.Println("[ListPhotoApiCallHandler]: No photo with given ID exists")
			return
		}
	} else {
		err = database.DbConn.QueryRow(
			r.Context(),
			`SELECT PhotoURL, PhotoID, PhotoDescription, Photo
			FROM Photo
			WHERE PhotoURL = $1`,
			photoURLs[0],
		).Scan(&photo.PhotoURL, &photo.PhotoID, &photo.PhotoDescription, &photo.Photo)
		if errors.Is(err, pgx.ErrNoRows) {
			current_err := models.ErrorPage{
				ErrorCode:       http.StatusForbidden,
				OfficialMessage: http.StatusText(http.StatusForbidden),
				Explanation:     "No such a photo with given photo URL exists",
			}
			error_handling.ErrorPageHandler(current_err, w, r)
			log.Println("[ListPhotoApiCallHandler]: No photo with given URL exists")
			return
		}
	}

	if err != nil {
		log.Println("[ListPhotoApiCallHandler]: " + err.Error())
		http.Error(w, http.StatusText(http.StatusInternalServerError), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	if err := json.NewEncoder(w).Encode([]models.Photo{photo}); err != nil {
		log.Println("[ListPhotoApiCallHandler]: " + err.Error())
		http.Error(w, http.StatusText(http.StatusInternalServerError), http.StatusInternalServerError)
		return
	}
}

func CreatePhotoApiCallHandler(w http.ResponseWriter, r *http.Request) {
	if r.URL.Path != "/api/photo/create/" {
		current_error := models.ErrorPage{
			ErrorCode:       http.StatusNotFound,
			OfficialMessage: http.StatusText(http.StatusNotFound),
			Explanation:     "Wrong path was called",
		}
		error_handling.ErrorPageHandler(current_error, w, r)
		log.Println("[CreatePhotoApiCallHandler]: Wrong path was applied")
		return
	}
	if r.Method != http.MethodPost {
		current_error := models.ErrorPage{
			ErrorCode:       http.StatusMethodNotAllowed,
			OfficialMessage: http.StatusText(http.StatusMethodNotAllowed),
			Explanation:     "Only POST method is allowed",
		}
		error_handling.ErrorPageHandler(current_error, w, r)
		log.Println("[CreatePhotoApiCallHandler]: Wrong method was applied")
		return
	}

	sessionIdCookie, err := r.Cookie("session-id")
	if err != nil {
		current_error := models.ErrorPage{
			ErrorCode:       http.StatusBadRequest,
			OfficialMessage: http.StatusText(http.StatusBadRequest),
			Explanation:     "Only authorized users can upload images",
		}
		error_handling.ErrorPageHandler(current_error, w, r)
		log.Println("[CreatePhotoApiCallHandler]: Missing session-id cookie")
		return
	}

	userLoginCookie, err := r.Cookie("user-login")
	if err != nil {
		current_error := models.ErrorPage{
			ErrorCode:       http.StatusBadRequest,
			OfficialMessage: http.StatusText(http.StatusBadRequest),
			Explanation:     "Only authorized users can upload images",
		}
		error_handling.ErrorPageHandler(current_error, w, r)
		log.Println("[CreatePhotoApiCallHandler]: Missing user-login cookie")
		return
	}

	sessionExists, err := database.CheckIfSessionExists(database.DbConn, userLoginCookie.Value, sessionIdCookie.Value)
	if err != nil || !sessionExists {
		current_error := models.ErrorPage{
			ErrorCode:       http.StatusBadRequest,
			OfficialMessage: http.StatusText(http.StatusBadRequest),
			Explanation:     "Only authorized users can upload images",
		}
		error_handling.ErrorPageHandler(current_error, w, r)
		if err != nil {
			log.Println("[CreatePhotoApiCallHandler]: " + err.Error())
		} else {
			log.Println("[CreatePhotoApiCallHandler]: Unauthorized photo upload attempt")
		}
		return
	}

	var uploadPhotoData models.UploadPhotoData
	if err := json.NewDecoder(r.Body).Decode(&uploadPhotoData); err != nil {
		current_error := models.ErrorPage{
			ErrorCode:       http.StatusInternalServerError,
			OfficialMessage: http.StatusText(http.StatusInternalServerError),
			Explanation:     "Unable to upload the image to the server",
		}
		error_handling.ErrorPageHandler(current_error, w, r)
		log.Println("[CreatePhotoApiCallHandler]: " + err.Error())
		return
	}

	var totalPhotos int
	err = database.DbConn.QueryRow(
		context.Background(),
		`SELECT COUNT(PhotoURL)
		FROM Photo`,
	).Scan(&totalPhotos)
	if err != nil {
		current_error := models.ErrorPage{
			ErrorCode:       http.StatusInternalServerError,
			OfficialMessage: http.StatusText(http.StatusInternalServerError),
			Explanation:     "Unable to upload the image to the server",
		}
		error_handling.ErrorPageHandler(current_error, w, r)
		log.Println("[CreatePhotoApiCallHandler]: " + err.Error())
		return
	}

	photoID := fmt.Sprintf("%s_%s_%d", userLoginCookie.Value, time.Now().Format("06_01_02_15_04_05"), totalPhotos+1)
	photoURL := fmt.Sprintf("/static/icons/%s_%s", photoID, uploadPhotoData.Description)

	_, err = database.DbConn.Exec(
		context.Background(),
		`INSERT INTO Photo (PhotoURL, PhotoDescription, Photo)
		VALUES ($1, $2, $3)`,
		photoURL,
		uploadPhotoData.Description,
		uploadPhotoData.Photo,
	)
	if err != nil {
		current_error := models.ErrorPage{
			ErrorCode:       http.StatusInternalServerError,
			OfficialMessage: http.StatusText(http.StatusInternalServerError),
			Explanation:     "Unable to upload the image to the server",
		}
		error_handling.ErrorPageHandler(current_error, w, r)
		log.Println("[CreatePhotoApiCallHandler]: " + err.Error())
		return
	}

	lastSlashIndex := strings.LastIndex(photoURL, "/")
	photoFilename := photoURL[lastSlashIndex+1:]
	photoPath := filepath.Join("web", "UI", "static", "icons", photoFilename)
	if err := os.WriteFile(photoPath, uploadPhotoData.Photo, 0644); err != nil {
		current_error := models.ErrorPage{
			ErrorCode:       http.StatusInternalServerError,
			OfficialMessage: http.StatusText(http.StatusInternalServerError),
			Explanation:     "Unable to upload the image to the server",
		}
		error_handling.ErrorPageHandler(current_error, w, r)
		log.Println("[CreatePhotoApiCallHandler]: " + err.Error())
		return
	}

	w.WriteHeader(http.StatusCreated)
	_ = json.NewEncoder(w).Encode(models.ReturnPhotoData{
		PhotoURL: photoURL,
	})
}

func UpdatePhotoApiCallHandler(w http.ResponseWriter, r *http.Request) {
	if r.URL.Path != "/api/photo/update/" {
		current_error := models.ErrorPage{
			ErrorCode:       http.StatusNotFound,
			OfficialMessage: http.StatusText(http.StatusNotFound),
			Explanation:     "Wrong path was called",
		}
		error_handling.ErrorPageHandler(current_error, w, r)
		log.Println("[UpdatePhotoApiCallHandler]: Wrong path was applied")
		return
	}
	if r.Method != http.MethodPut {
		current_error := models.ErrorPage{
			ErrorCode:       http.StatusMethodNotAllowed,
			OfficialMessage: http.StatusText(http.StatusMethodNotAllowed),
			Explanation:     "Only PUT method is allowed",
		}
		error_handling.ErrorPageHandler(current_error, w, r)
		log.Println("[UpdatePhotoApiCallHandler]: Wrong method was applied")
		return
	}

	sessionIdCookie, err := r.Cookie("session-id")
	if err != nil {
		current_error := models.ErrorPage{
			ErrorCode:       http.StatusBadRequest,
			OfficialMessage: http.StatusText(http.StatusBadRequest),
			Explanation:     "Only authorized users can update",
		}
		error_handling.ErrorPageHandler(current_error, w, r)
		log.Println("[UpdatePhotoApiCallHandler]: Missing session-id cookie")
		return
	}

	userLoginCookie, err := r.Cookie("user-login")
	if err != nil {
		current_error := models.ErrorPage{
			ErrorCode:       http.StatusBadRequest,
			OfficialMessage: http.StatusText(http.StatusBadRequest),
			Explanation:     "Only authorized users can update",
		}
		error_handling.ErrorPageHandler(current_error, w, r)
		log.Println("[UpdatePhotoApiCallHandler]: Missing user-login cookie")
		return
	}

	sessionExists, err := database.CheckIfSessionExists(database.DbConn, userLoginCookie.Value, sessionIdCookie.Value)
	if err != nil || !sessionExists {
		current_error := models.ErrorPage{
			ErrorCode:       http.StatusBadRequest,
			OfficialMessage: http.StatusText(http.StatusBadRequest),
			Explanation:     "Only authorized users can update",
		}
		error_handling.ErrorPageHandler(current_error, w, r)
		if err != nil {
			log.Println("[UpdatePhotoApiCallHandler]: " + err.Error())
		} else {
			log.Println("[UpdatePhotoApiCallHandler]: Unauthorized photo update attempt")
		}
		return
	}

	query := r.URL.Query()
	photoIDs, hasPhotoID := query["photo_id"]
	photoURLs, hasPhotoURL := query["photo_url"]

	if len(query) != 1 || hasPhotoID == hasPhotoURL || (hasPhotoID && len(photoIDs) != 1) || (hasPhotoURL && len(photoURLs) != 1) || (hasPhotoID && photoIDs[0] == "") || (hasPhotoURL && photoURLs[0] == "") {
		current_error := models.ErrorPage{
			ErrorCode:       http.StatusBadRequest,
			OfficialMessage: http.StatusText(http.StatusBadRequest),
			Explanation:     "Incorrect query format",
		}
		error_handling.ErrorPageHandler(current_error, w, r)
		log.Println("[UpdatePhotoApiCallHandler]: Incorrect query format")
		return
	}

	var photoURL string
	if hasPhotoID {
		photoID, convertErr := strconv.Atoi(photoIDs[0])
		if convertErr != nil {
			current_error := models.ErrorPage{
				ErrorCode:       http.StatusBadRequest,
				OfficialMessage: http.StatusText(http.StatusBadRequest),
				Explanation:     "Incorrect query format",
			}
			error_handling.ErrorPageHandler(current_error, w, r)
			log.Println("[UpdatePhotoApiCallHandler]: Incorrect photo ID format")
			return
		}

		err = database.DbConn.QueryRow(
			context.Background(),
			`SELECT PhotoURL
			FROM Photo
			WHERE PhotoID = $1`,
			photoID,
		).Scan(&photoURL)
	} else {
		photoURL = photoURLs[0]
		err = database.DbConn.QueryRow(
			context.Background(),
			`SELECT PhotoURL
			FROM Photo
			WHERE PhotoURL = $1`,
			photoURL,
		).Scan(&photoURL)
	}
	if errors.Is(err, pgx.ErrNoRows) {
		current_error := models.ErrorPage{
			ErrorCode:       http.StatusBadRequest,
			OfficialMessage: http.StatusText(http.StatusBadRequest),
			Explanation:     "No such photo existed",
		}
		error_handling.ErrorPageHandler(current_error, w, r)
		log.Println("[UpdatePhotoApiCallHandler]: No such photo existed")
		return
	}
	if err != nil {
		current_error := models.ErrorPage{
			ErrorCode:       http.StatusInternalServerError,
			OfficialMessage: http.StatusText(http.StatusInternalServerError),
			Explanation:     "Unable to update the given photo",
		}
		error_handling.ErrorPageHandler(current_error, w, r)
		log.Println("[UpdatePhotoApiCallHandler]: " + err.Error())
		return
	}

	var uploadPhotoData models.UploadPhotoData
	if err := json.NewDecoder(r.Body).Decode(&uploadPhotoData); err != nil {
		current_error := models.ErrorPage{
			ErrorCode:       http.StatusInternalServerError,
			OfficialMessage: http.StatusText(http.StatusInternalServerError),
			Explanation:     "Unable to update the given photo",
		}
		error_handling.ErrorPageHandler(current_error, w, r)
		log.Println("[UpdatePhotoApiCallHandler]: " + err.Error())
		return
	}

	_, err = database.DbConn.Exec(
		context.Background(),
		`UPDATE Photo
		SET PhotoDescription = $1,
			Photo = $2
		WHERE PhotoURL = $3`,
		uploadPhotoData.Description,
		uploadPhotoData.Photo,
		photoURL,
	)
	if err != nil {
		current_error := models.ErrorPage{
			ErrorCode:       http.StatusInternalServerError,
			OfficialMessage: http.StatusText(http.StatusInternalServerError),
			Explanation:     "Unable to update the given photo",
		}
		error_handling.ErrorPageHandler(current_error, w, r)
		log.Println("[UpdatePhotoApiCallHandler]: " + err.Error())
		return
	}

	lastSlashIndex := strings.LastIndex(photoURL, "/")
	photoFilename := photoURL[lastSlashIndex+1:]
	photoPath := filepath.Join("web", "UI", "static", "icons", photoFilename)
	if err := os.Remove(photoPath); err != nil && !os.IsNotExist(err) {
		current_error := models.ErrorPage{
			ErrorCode:       http.StatusInternalServerError,
			OfficialMessage: http.StatusText(http.StatusInternalServerError),
			Explanation:     "Unable to update the given photo",
		}
		error_handling.ErrorPageHandler(current_error, w, r)
		log.Println("[UpdatePhotoApiCallHandler]: " + err.Error())
		return
	}
	if err := os.WriteFile(photoPath, uploadPhotoData.Photo, 0644); err != nil {
		current_error := models.ErrorPage{
			ErrorCode:       http.StatusInternalServerError,
			OfficialMessage: http.StatusText(http.StatusInternalServerError),
			Explanation:     "Unable to update the given photo",
		}
		error_handling.ErrorPageHandler(current_error, w, r)
		log.Println("[UpdatePhotoApiCallHandler]: " + err.Error())
		return
	}

	w.WriteHeader(http.StatusOK)
}

func ErasePhotoApiCallHandler(w http.ResponseWriter, r *http.Request) {
	if r.URL.Path != "/api/photo/erase/" {
		current_error := models.ErrorPage{
			ErrorCode:       http.StatusNotFound,
			OfficialMessage: http.StatusText(http.StatusNotFound),
			Explanation:     "Wrong path was applied in the request",
		}
		error_handling.ErrorPageHandler(current_error, w, r)
		log.Println("[ErasePhotoApiCallHandler]: Incorrect path was called")
		return
	}
	if r.Method != http.MethodDelete {
		current_error := models.ErrorPage{
			ErrorCode:       http.StatusMethodNotAllowed,
			OfficialMessage: http.StatusText(http.StatusMethodNotAllowed),
			Explanation:     "Only DETELE method can be applied",
		}
		error_handling.ErrorPageHandler(current_error, w, r)
		log.Println("[ErasePhotoApiCallHandler]: Incorrect method was applied")
		return
	}

	sessionIdCookie, err := r.Cookie("session-id")
	if err != nil {
		current_error := models.ErrorPage{
			ErrorCode:       http.StatusBadRequest,
			OfficialMessage: http.StatusText(http.StatusBadRequest),
			Explanation:     "Only authorized users can delete images",
		}
		error_handling.ErrorPageHandler(current_error, w, r)
		log.Println("[ErasePhotoApiCallHandler]: Missing session-id cookie")
		return
	}

	userLoginCookie, err := r.Cookie("user-login")
	if err != nil {
		current_error := models.ErrorPage{
			ErrorCode:       http.StatusBadRequest,
			OfficialMessage: http.StatusText(http.StatusBadRequest),
			Explanation:     "Only authorized users can delete images",
		}
		error_handling.ErrorPageHandler(current_error, w, r)
		log.Println("[ErasePhotoApiCallHandler]: Missing user-login cookie")
		return
	}

	sessionExists, err := database.CheckIfSessionExists(database.DbConn, userLoginCookie.Value, sessionIdCookie.Value)
	if err != nil || !sessionExists {
		current_error := models.ErrorPage{
			ErrorCode:       http.StatusBadRequest,
			OfficialMessage: http.StatusText(http.StatusBadRequest),
			Explanation:     "Only authorized users can delete images",
		}
		error_handling.ErrorPageHandler(current_error, w, r)
		if err != nil {
			log.Println("[ErasePhotoApiCallHandler]: " + err.Error())
		} else {
			log.Println("[ErasePhotoApiCallHandler]: Unauthorized photo deletion attempt")
		}
		return
	}

	query := r.URL.Query()
	photoIDs, hasPhotoID := query["photo_id"]
	photoURLs, hasPhotoURL := query["photo_url"]

	if len(query) != 1 || hasPhotoID == hasPhotoURL || (hasPhotoID && len(photoIDs) != 1) || (hasPhotoURL && len(photoURLs) != 1) || (hasPhotoID && photoIDs[0] == "") || (hasPhotoURL && photoURLs[0] == "") {
		current_error := models.ErrorPage{
			ErrorCode:       http.StatusBadRequest,
			OfficialMessage: http.StatusText(http.StatusBadRequest),
			Explanation:     "Incorrect query format",
		}
		error_handling.ErrorPageHandler(current_error, w, r)
		log.Println("[ErasePhotoApiCallHandler]: Incorrect query format")
		return
	}

	var photoURL string
	if hasPhotoID {
		photoID, convertErr := strconv.Atoi(photoIDs[0])
		if convertErr != nil {
			current_error := models.ErrorPage{
				ErrorCode:       http.StatusBadRequest,
				OfficialMessage: http.StatusText(http.StatusBadRequest),
				Explanation:     "Incorrect query format",
			}
			error_handling.ErrorPageHandler(current_error, w, r)
			log.Println("[ErasePhotoApiCallHandler]: Incorrect photo ID format")
			return
		}

		err = database.DbConn.QueryRow(
			context.Background(),
			`SELECT PhotoURL
			FROM Photo
			WHERE PhotoID = $1`,
			photoID,
		).Scan(&photoURL)
	} else {
		photoURL = photoURLs[0]
		err = database.DbConn.QueryRow(
			context.Background(),
			`SELECT PhotoURL
			FROM Photo
			WHERE PhotoURL = $1`,
			photoURL,
		).Scan(&photoURL)
	}
	if errors.Is(err, pgx.ErrNoRows) {
		current_error := models.ErrorPage{
			ErrorCode:       http.StatusNotFound,
			OfficialMessage: http.StatusText(http.StatusNotFound),
			Explanation:     "Photo with given URL/ID did not found",
		}
		error_handling.ErrorPageHandler(current_error, w, r)
		log.Println("[ErasePhotoApiCallHandler]: Photo with given URL/ID did not found")
		return
	}
	if err != nil {
		current_error := models.ErrorPage{
			ErrorCode:       http.StatusInternalServerError,
			OfficialMessage: http.StatusText(http.StatusInternalServerError),
			Explanation:     "Something went wrong during photo deletion",
		}
		error_handling.ErrorPageHandler(current_error, w, r)
		log.Println("[ErasePhotoApiCallHandler]: " + err.Error())
		return
	}

	_, err = database.DbConn.Exec(
		context.Background(),
		`DELETE FROM Photo
		WHERE PhotoURL = $1`,
		photoURL,
	)
	if err != nil {
		current_error := models.ErrorPage{
			ErrorCode:       http.StatusInternalServerError,
			OfficialMessage: http.StatusText(http.StatusInternalServerError),
			Explanation:     "Something went wrong during photo deletion",
		}
		error_handling.ErrorPageHandler(current_error, w, r)
		log.Println("[ErasePhotoApiCallHandler]: " + err.Error())
		return
	}

	lastSlashIndex := strings.LastIndex(photoURL, "/")
	photoFilename := photoURL[lastSlashIndex+1:]
	photoPath := filepath.Join("web", "UI", "static", "icons", photoFilename)
	if err := os.Remove(photoPath); err != nil {
		current_error := models.ErrorPage{
			ErrorCode:       http.StatusInternalServerError,
			OfficialMessage: http.StatusText(http.StatusInternalServerError),
			Explanation:     "Something went wrong during photo deletion",
		}
		error_handling.ErrorPageHandler(current_error, w, r)
		log.Println("[ErasePhotoApiCallHandler]: " + err.Error())
		return
	}

	w.WriteHeader(http.StatusOK)
}
