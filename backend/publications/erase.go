package publications

import (
	"fmt"
	"main/backend"
	"main/database"
	"net/http"
	"strconv"
)

func ErasePublicationsApiCallHandler(w http.ResponseWriter, r *http.Request) {
	handler_action := "erase"
	handler_route := fmt.Sprintf("/api/publications/%s/", handler_action)
	handler_method := http.MethodDelete
	handler_name := fmt.Sprintf("%sPublicationsApiCallHandler", backend.CapitalizeFirst(handler_action))
	ok := backend.RouteMethodValidation(handler_route, handler_method, handler_name, w, r)
	if !ok {
		return
	}

	_, signed_in := backend.AuthorizeRequest(handler_name, w, r)
	if !signed_in {
		return
	}

	isAdmin := backend.CheckAdministratorRole(handler_name, w, r)
	if !isAdmin {
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
		backend.HandleCommonError(handler_name, w, r, http.StatusNotFound, "Such an entry with given ID was not found", "Publication was not found")
		return
	}

	_, err = database.DbConn.Exec(
		r.Context(),
		`DELETE FROM Publications WHERE PublicationID = $1`,
		publicationID,
	)
	if err != nil {
		backend.HandleCommonError(handler_name, w, r, http.StatusInternalServerError, "Something went wrond during transaction", err.Error())
		return
	}

	w.WriteHeader(http.StatusOK)
}
