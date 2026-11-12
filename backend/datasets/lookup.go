package datasets

import (
	"encoding/json"
	"errors"
	"fmt"
	"main/backend"
	"main/database"
	"main/models"
	"net/http"
	"strconv"
	"time"

	"github.com/jackc/pgx/v5"
)

func ListDatasetsApiCallHandler(w http.ResponseWriter, r *http.Request) {
	handler_action := "list"
	handler_route := fmt.Sprintf("/api/datasets/%s/", handler_action)
	handler_method := http.MethodGet
	handler_name := fmt.Sprintf("%sDatasetsApiCallHandler", backend.CapitalizeFirst(handler_action))
	ok := backend.RouteMethodValidation(handler_route, handler_method, handler_name, w, r)
	if !ok {
		return
	}

	query := r.URL.Query()
	datasetIDs, hasDatasetID := query["data_id"]
	targets, hasTarget := query["target"]
	validTarget := hasTarget && len(targets) == 1 && targets[0] == "all"
	datasetID := int64(0)
	validDatasetID := false
	if hasDatasetID && len(datasetIDs) == 1 {
		parsedID, err := strconv.ParseInt(datasetIDs[0], 10, 64)
		if err == nil && parsedID > 0 {
			datasetID = parsedID
			validDatasetID = true
		}
	}
	if len(query) != 1 || validDatasetID == validTarget {
		backend.HandleCommonError(handler_name, w, r, http.StatusBadRequest, "Incorrect query format", "Incorrect query format")
		return
	}

	const selectDatasets = `SELECT DataID, Name, COALESCE(Type, ''), COALESCE(Description, ''),
		COALESCE(Date, '0001-01-01'), COALESCE(Version, 0), COALESCE(Size, 0), COALESCE(Format, '')
	FROM Datasets`

	if validDatasetID {
		var dataset models.Datasets
		var datasetDate string
		err := database.DbConn.QueryRow(
			r.Context(),
			selectDatasets+" WHERE DataID = $1",
			datasetID,
		).Scan(
			&dataset.DataID,
			&dataset.DataName,
			&dataset.DataType,
			&dataset.DataDescription,
			&datasetDate,
			&dataset.Version,
			&dataset.Size,
			&dataset.Format,
		)
		if errors.Is(err, pgx.ErrNoRows) {
			backend.HandleCommonError(handler_name, w, r, http.StatusNotFound, "Such a datasets with given ID was not found", "Dataset was not found")
			return
		}
		if err != nil {
			backend.HandleCommonError(handler_name, w, r, http.StatusInternalServerError, "Something went wrond during transaction", err.Error())
			return
		}
		dataset.Date, err = time.Parse("2006-01-02", datasetDate)
		if err != nil {
			backend.HandleCommonError(handler_name, w, r, http.StatusInternalServerError, "Something went wrond during transaction", err.Error())
			return
		}

		w.Header().Set("Content-Type", "application/json")
		if err := json.NewEncoder(w).Encode(dataset); err != nil {
			backend.HandleCommonError(handler_name, w, r, http.StatusInternalServerError, "Something went wrond during transaction", err.Error())
		}
		return
	}

	rows, err := database.DbConn.Query(r.Context(), selectDatasets+" ORDER BY DataID")
	if err != nil {
		backend.HandleCommonError(handler_name, w, r, http.StatusInternalServerError, "Something went wrond during transaction", err.Error())
		return
	}
	defer rows.Close()

	datasets := make([]models.Datasets, 0)
	for rows.Next() {
		var dataset models.Datasets
		var datasetDate string
		if err := rows.Scan(
			&dataset.DataID,
			&dataset.DataName,
			&dataset.DataType,
			&dataset.DataDescription,
			&datasetDate,
			&dataset.Version,
			&dataset.Size,
			&dataset.Format,
		); err != nil {
			backend.HandleCommonError(handler_name, w, r, http.StatusInternalServerError, "Something went wrond during transaction", err.Error())
			return
		}
		dataset.Date, err = time.Parse("2006-01-02", datasetDate)
		if err != nil {
			backend.HandleCommonError(handler_name, w, r, http.StatusInternalServerError, "Something went wrond during transaction", err.Error())
			return
		}
		datasets = append(datasets, dataset)
	}
	if err := rows.Err(); err != nil {
		backend.HandleCommonError(handler_name, w, r, http.StatusInternalServerError, "Something went wrond during transaction", err.Error())
		return
	}

	w.Header().Set("Content-Type", "application/json")
	if err := json.NewEncoder(w).Encode(datasets); err != nil {
		backend.HandleCommonError(handler_name, w, r, http.StatusInternalServerError, "Something went wrond during transaction", err.Error())
	}
}
