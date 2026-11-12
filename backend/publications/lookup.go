package publications

import (
	"encoding/json"
	"errors"
	"fmt"
	"main/backend"
	"main/database"
	"main/models"
	"net/http"
	"strconv"

	"github.com/jackc/pgx/v5"
)

func ListPublicationsApiCallHandler(w http.ResponseWriter, r *http.Request) {
	handler_action := "list"
	handler_route := fmt.Sprintf("/api/publications/%s/", handler_action)
	handler_method := http.MethodGet
	handler_name := fmt.Sprintf("%sPublicationsApiCallHandler", backend.CapitalizeFirst(handler_action))
	ok := backend.RouteMethodValidation(handler_route, handler_method, handler_name, w, r)
	if !ok {
		return
	}

	query := r.URL.Query()
	publicationIDs, hasPublicationID := query["pub_id"]
	targets, hasTarget := query["target"]
	validTarget := hasTarget && len(targets) == 1 && targets[0] == "all"
	publicationID := int64(0)
	validPublicationID := false
	if hasPublicationID && len(publicationIDs) == 1 {
		parsedID, err := strconv.ParseInt(publicationIDs[0], 10, 64)
		if err == nil && parsedID > 0 {
			publicationID = parsedID
			validPublicationID = true
		}
	}
	if len(query) != 1 || validPublicationID == validTarget {
		backend.HandleCommonError(handler_name, w, r, http.StatusBadRequest, "Incorrect query format", "Incorrect query format")
		return
	}

	const selectPublications = `SELECT PublicationID, PublicationTitle,
		COALESCE(PublicationKeywords, ARRAY[]::TEXT[]), COALESCE(DOI, '')
	FROM Publications`

	if validPublicationID {
		var publication models.Publications
		err := database.DbConn.QueryRow(
			r.Context(),
			selectPublications+" WHERE PublicationID = $1",
			publicationID,
		).Scan(
			&publication.PublicationID,
			&publication.PublicationTitle,
			&publication.PublicationKeywords,
			&publication.DOI,
		)
		if errors.Is(err, pgx.ErrNoRows) {
			backend.HandleCommonError(handler_name, w, r, http.StatusNotFound, "Such a datasets with given ID was not found", "Publication was not found")
			return
		}
		if err != nil {
			backend.HandleCommonError(handler_name, w, r, http.StatusInternalServerError, "Something went wrond during transaction", err.Error())
			return
		}

		w.Header().Set("Content-Type", "application/json")
		if err := json.NewEncoder(w).Encode(publication); err != nil {
			backend.HandleCommonError(handler_name, w, r, http.StatusInternalServerError, "Something went wrond during transaction", err.Error())
		}
		return
	}

	rows, err := database.DbConn.Query(r.Context(), selectPublications+" ORDER BY PublicationID")
	if err != nil {
		backend.HandleCommonError(handler_name, w, r, http.StatusInternalServerError, "Something went wrond during transaction", err.Error())
		return
	}
	defer rows.Close()

	publications := make([]models.Publications, 0)
	for rows.Next() {
		var publication models.Publications
		if err := rows.Scan(
			&publication.PublicationID,
			&publication.PublicationTitle,
			&publication.PublicationKeywords,
			&publication.DOI,
		); err != nil {
			backend.HandleCommonError(handler_name, w, r, http.StatusInternalServerError, "Something went wrond during transaction", err.Error())
			return
		}
		publications = append(publications, publication)
	}
	if err := rows.Err(); err != nil {
		backend.HandleCommonError(handler_name, w, r, http.StatusInternalServerError, "Something went wrond during transaction", err.Error())
		return
	}

	w.Header().Set("Content-Type", "application/json")
	if err := json.NewEncoder(w).Encode(publications); err != nil {
		backend.HandleCommonError(handler_name, w, r, http.StatusInternalServerError, "Something went wrond during transaction", err.Error())
	}
}
