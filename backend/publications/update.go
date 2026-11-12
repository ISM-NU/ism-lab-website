package publications

import (
	"encoding/json"
	"fmt"
	"main/backend"
	"main/database"
	"main/models"
	"net/http"
	"strconv"
)

func UpdatePublicationsApiCallHandler(w http.ResponseWriter, r *http.Request) {
	handler_action := "update"
	handler_route := fmt.Sprintf("/api/publications/%s/", handler_action)
	handler_method := http.MethodPut
	handler_name := fmt.Sprintf("%sPublicationsApiCallHandler", backend.CapitalizeFirst(handler_action))
	ok := backend.RouteMethodValidation(handler_route, handler_method, handler_name, w, r)
	if !ok {
		return
	}

	_, signed_in := backend.AuthorizeRequest(handler_name, w, r)
	if !signed_in {
		return
	}

	query := r.URL.Query()
	publicationIDs, hasPublicationID := query["pub_id"]
	if len(query) != 1 || !hasPublicationID || len(publicationIDs) != 1 {
		backend.HandleCommonError(handler_name, w, r, http.StatusBadRequest, "Incorrect query format", "Incorrect query format")
		return
	}
	publicationID, err := strconv.ParseInt(publicationIDs[0], 10, 64)
	if err != nil || publicationID <= 0 {
		backend.HandleCommonError(handler_name, w, r, http.StatusBadRequest, "Incorrect query format", "Incorrect query format")
		return
	}

	var publicationExists bool
	err = database.DbConn.QueryRow(
		r.Context(),
		`SELECT EXISTS (SELECT 1 FROM Publications WHERE PublicationID = $1)`,
		publicationID,
	).Scan(&publicationExists)
	if err != nil {
		backend.HandleCommonError(handler_name, w, r, http.StatusInternalServerError, "Something went wrond during transaction", err.Error())
		return
	}
	if !publicationExists {
		backend.HandleCommonError(handler_name, w, r, http.StatusNotFound, "Such an entry with given ID does not found", "Publication was not found")
		return
	}

	var publication models.Publications
	if err := json.NewDecoder(r.Body).Decode(&publication); err != nil {
		backend.HandleCommonError(handler_name, w, r, http.StatusBadRequest, "Incorrect body format", err.Error())
		return
	}

	_, err = database.DbConn.Exec(
		r.Context(),
		`UPDATE Publications
		SET PublicationTitle = $1,
			PublicationKeywords = $2,
			DOI = $3
		WHERE PublicationID = $4`,
		publication.PublicationTitle,
		publication.PublicationKeywords,
		publication.DOI,
		publicationID,
	)
	if err != nil {
		backend.HandleCommonError(handler_name, w, r, http.StatusInternalServerError, "Something went wrond during transaction", err.Error())
		return
	}

	w.WriteHeader(http.StatusOK)
}
