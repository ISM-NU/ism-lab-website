package datasets

import (
	"encoding/json"
	"fmt"
	"main/backend"
	"main/database"
	"main/models"
	"net/http"
	"strconv"
)

func UpdateDatasetsApiCallHandler(w http.ResponseWriter, r *http.Request) {
	handler_action := "update"
	handler_route := fmt.Sprintf("/api/datasets/%s/", handler_action)
	handler_method := http.MethodPut
	handler_name := fmt.Sprintf("%sDatasetsApiCallHandler", backend.CapitalizeFirst(handler_action))
	ok := backend.RouteMethodValidation(handler_route, handler_method, handler_name, w, r)
	if !ok {
		return
	}

	_, signed_in := backend.AuthorizeRequest(handler_name, w, r)
	if !signed_in {
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
		backend.HandleCommonError(handler_name, w, r, http.StatusNotFound, "Such an entry with given ID does not found", "Dataset was not found")
		return
	}

	var dataset models.Datasets
	if err := json.NewDecoder(r.Body).Decode(&dataset); err != nil {
		backend.HandleCommonError(handler_name, w, r, http.StatusBadRequest, "Incorrect body format", err.Error())
		return
	}

	_, err = database.DbConn.Exec(
		r.Context(),
		`UPDATE Datasets
		SET Name = $1,
			Type = $2,
			Description = $3,
			Date = $4,
			Version = $5,
			Size = $6,
			Format = $7
		WHERE DataID = $8`,
		dataset.DataName,
		dataset.DataType,
		dataset.DataDescription,
		dataset.Date.Format("2006-01-02"),
		dataset.Version,
		dataset.Size,
		dataset.Format,
		datasetID,
	)
	if err != nil {
		backend.HandleCommonError(handler_name, w, r, http.StatusInternalServerError, "Something went wrond during transaction", err.Error())
		return
	}

	w.WriteHeader(http.StatusOK)
}
