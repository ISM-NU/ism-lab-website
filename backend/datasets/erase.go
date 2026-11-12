package datasets

import (
	"fmt"
	"main/backend"
	"main/database"
	"net/http"
	"strconv"
)

func EraseDatasetsApiCallHandler(w http.ResponseWriter, r *http.Request) {
	handler_action := "erase"
	handler_route := fmt.Sprintf("/api/datasets/%s/", handler_action)
	handler_method := http.MethodDelete
	handler_name := fmt.Sprintf("%sDatasetsApiCallHandler", backend.CapitalizeFirst(handler_action))
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
	datasetIDs, hasDatasetID := query["data_id"]
	if len(query) != 1 || !hasDatasetID || len(datasetIDs) != 1 {
		backend.HandleCommonError(handler_name, w, r, http.StatusBadRequest, "Incorrect query format", "Incorrect query format")
		return
	}
	datasetID, err := strconv.ParseInt(datasetIDs[0], 10, 64)
	if err != nil || datasetID <= 0 {
		backend.HandleCommonError(handler_name, w, r, http.StatusBadRequest, "Incorrect query format", "Incorrect query format")
		return
	}

	var datasetExists bool
	err = database.DbConn.QueryRow(
		r.Context(),
		`SELECT EXISTS (SELECT 1 FROM Datasets WHERE DataID = $1)`,
		datasetID,
	).Scan(&datasetExists)
	if err != nil {
		backend.HandleCommonError(handler_name, w, r, http.StatusInternalServerError, "Something went wrond during transaction", err.Error())
		return
	}
	if !datasetExists {
		backend.HandleCommonError(handler_name, w, r, http.StatusNotFound, "Such an entry with given ID was not found", "Dataset was not found")
		return
	}

	_, err = database.DbConn.Exec(
		r.Context(),
		`DELETE FROM Datasets WHERE DataID = $1`,
		datasetID,
	)
	if err != nil {
		backend.HandleCommonError(handler_name, w, r, http.StatusInternalServerError, "Something went wrond during transaction", err.Error())
		return
	}

	w.WriteHeader(http.StatusOK)
}
