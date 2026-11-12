package publications

import (
	"encoding/json"
	"fmt"
	"main/backend"
	"main/database"
	"main/models"
	"net/http"
)

func CreatePublicationsApiCallHandler(w http.ResponseWriter, r *http.Request) {
	handler_action := "create"
	handler_route := fmt.Sprintf("/api/publications/%s/", handler_action)
	handler_method := http.MethodPost
	handler_name := fmt.Sprintf("%sPublicationsApiCallHandler", backend.CapitalizeFirst(handler_action))
	ok := backend.RouteMethodValidation(handler_route, handler_method, handler_name, w, r)
	if !ok {
		return
	}

	_, signed_in := backend.AuthorizeRequest(handler_name, w, r)
	if !signed_in {
		return
	}

	var publication models.Publications
	if err := json.NewDecoder(r.Body).Decode(&publication); err != nil {
		backend.HandleCommonError(handler_name, w, r, http.StatusBadRequest, "Incorrect body format", err.Error())
		return
	}

	_, err := database.DbConn.Exec(
		r.Context(),
		`INSERT INTO Publications (PublicationTitle, PublicationKeywords, DOI)
		VALUES ($1, $2, $3)`,
		publication.PublicationTitle,
		publication.PublicationKeywords,
		publication.DOI,
	)
	if err != nil {
		backend.HandleCommonError(handler_name, w, r, http.StatusInternalServerError, "Something went wrond during transaction", err.Error())
		return
	}

	w.WriteHeader(http.StatusOK)
}
